# Standard imports
from datetime import datetime
import hashlib
import json
from pathlib import Path
import time

# Third-party imports
from anthropic.types import MessageParam

# Local imports
from config import EMAIL_LINK, GITHUB_APP_USER_NAME, PRODUCT_ID, UTF8
from constants.agent import COST_CAP_RATIO, MAX_ITERATIONS
from constants.general import MAX_GITAUTO_COMMITS_PER_PR, MAX_INFRA_RETRIES
from constants.messages import PERMISSION_DENIED_MESSAGE, CHECK_RUN_FAILED_MESSAGE
from services.agents.verify_task_is_complete import verify_task_is_complete
from services.agents.verify_task_is_ready import verify_task_is_ready
from services.aws.s3.refresh_mongodb_cache import refresh_mongodb_cache
from services.chat_with_agent import chat_with_agent
from services.circleci.get_build_logs import get_circleci_build_logs
from services.circleci.get_workflow_jobs import get_circleci_workflow_jobs
from services.claude.tools.tools import TOOLS_FOR_PRS
from services.codecov.get_commit_coverage import get_codecov_commit_coverage
from services.git.create_empty_commit import create_empty_commit
from services.git.get_clone_dir import get_clone_dir
from services.git.get_clone_url import get_clone_url
from services.git.get_local_head_sha import get_local_head_sha
from services.git.clone_repo_and_install_dependencies import (
    clone_repo_and_install_dependencies,
)
from services.git.git_merge_base_into_pr import git_merge_base_into_pr
from services.github.commits.get_head_commit_count_behind_base import (
    get_head_commit_count_behind_base,
)
from services.github.check_suites.get_failed_check_runs import (
    get_failed_check_runs_from_check_suite,
)
from services.github.comments.create_comment import create_comment
from services.github.comments.get_pr_comments import get_pr_comments
from services.github.comments.update_comment import update_comment
from services.github.installations.get_installation_permissions import (
    get_installation_permissions,
)
from services.github.pulls.get_pull_request import get_pull_request
from services.github.pulls.get_pull_request_commits import get_pull_request_commits
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.github_types import CheckSuiteCompletedPayload
from services.github.users.get_email_from_commits import get_email_from_commits
from services.github.users.get_user_public_email import get_user_public_info
from services.github.utils.create_permission_url import create_permission_url
from services.github.workflow_runs.cancel_workflow_runs import cancel_workflow_runs
from services.github.workflow_runs.get_workflow_run_logs import get_workflow_run_logs
from services.node.ensure_node_packages import ensure_node_packages
from services.node.set_npm_token_env import set_npm_token_env
from services.php.ensure_php_packages import ensure_php_packages
from services.slack.slack_notify import slack_notify
from services.supabase.check_suites.insert_check_suite import insert_check_suite
from services.supabase.credits.check_purchase_exists import check_purchase_exists
from services.supabase.credits.get_credit_price import get_credit_price
from services.supabase.circleci_tokens.get_circleci_token import get_circleci_token
from services.supabase.codecov_tokens.get_codecov_token import get_codecov_token
from services.supabase.create_user_request import create_user_request
from services.supabase.llm_requests.get_total_cost_for_pr import get_total_cost_for_pr
from services.supabase.repositories.get_repository import get_repository
from services.supabase.usage.check_older_active_test_failure import (
    check_older_active_test_failure_request,
)
from services.supabase.usage.get_retry_error_hashes import get_retry_error_hashes
from services.supabase.usage.update_retry_error_hashes import (
    update_retry_error_hashes,
)
from services.supabase.usage.update_usage import update_usage
from services.types.base_args import BaseArgs
from services.webhook.utils.create_system_message import create_system_message
from services.webhook.utils.get_preferred_model import get_preferred_model
from services.webhook.utils.maybe_switch_to_free_model import maybe_switch_to_free_model
from services.webhook.utils.should_bail import should_bail
from utils.files.get_local_file_tree import get_local_file_tree
from utils.logging.add_log_message import add_log_message
from utils.logging.logging_config import logger, set_pr_number
from utils.logs.clean_logs import clean_logs
from utils.logs.detect_infra_failure import detect_infra_failure
from utils.logs.label_log_source import label_log_source
from utils.logs.normalize_log_for_hashing import normalize_log_for_hashing
from utils.logs.save_ci_log_to_file import (
    CI_LOG_PATH,
    MAX_INLINE_LOG_CHARS,
    save_ci_log_to_file,
)
from utils.memory.gc_collect_and_log import gc_collect_and_log
from utils.progress_bar.progress_bar import create_progress_bar


async def handle_check_suite(
    payload: CheckSuiteCompletedPayload,
    lambda_info: dict[str, str | None] | None = None,
):
    current_time = time.time()
    trigger = "test_failure"

    # Extract repository and installation info
    repo = payload["repository"]
    owner_name = repo["owner"]["login"]
    repo_name = repo["name"]
    installation_id = payload["installation"]["id"]
    check_suite_id = payload["check_suite"]["id"]
    delivery_id = (
        lambda_info.get("delivery_id", "unknown") if lambda_info else "unknown"
    )

    logger.info(
        "handle_check_suite called check_suite_id=%s delivery_id=%s",
        check_suite_id,
        delivery_id,
    )

    # Deduplicate by check_suite_id (GitHub may send duplicate webhooks with different delivery_ids)
    if not insert_check_suite(check_suite_id=check_suite_id):
        logger.info("Duplicate check_suite_id=%s ignored", check_suite_id)
        return

    # Check if this is a GitAuto PR by branch name. Return early when it is not.
    # `head_branch` can be None when:
    # - Check suite runs on a tag push (tags don't have branches)
    # - Check suite runs on a deleted branch
    # - Check suite runs on a direct commit without PR
    # - Orphan commits or detached HEAD state
    check_suite = payload["check_suite"]
    head_branch = check_suite["head_branch"]
    if not head_branch or not head_branch.startswith(PRODUCT_ID):
        logger.info(
            "Ignoring check_suite: head_branch=%s is not a GitAuto branch", head_branch
        )
        return

    # Get failed check runs from the check suite
    token = get_installation_access_token(installation_id=installation_id)
    failed_check_runs = get_failed_check_runs_from_check_suite(
        owner=owner_name,
        repo=repo_name,
        check_suite_id=check_suite["id"],
        github_token=token,
    )

    if not failed_check_runs:
        logger.info("No failed check runs in check_suite_id=%s", check_suite["id"])
        return

    # Use the first failed check run
    check_run = failed_check_runs[0]
    details_url = check_run.get("details_url")
    check_run_name = check_run.get("name", "Unknown Check")

    is_circleci = "circleci.com" in details_url if details_url else False
    is_codecov = "codecov.io" in details_url if details_url else False
    is_deepsource = "deepsource.com" in details_url if details_url else False
    is_side8 = "side8.io" in details_url if details_url else False
    circleci_project_slug = ""
    circleci_workflow_id = ""
    github_run_id = 0

    if is_circleci:
        # URL: https://app.circleci.com/pipelines/circleci/J2wtzLah5rmzRnx6qn4RyQ/UUb5FLNgQCnif8mB6mQn7s/7/workflows/772ddda7-d6b7-49ad-9123-108d9f8164b5
        logger.info("Detected CircleCI, parsing workflow/project from details_url")
        circleci_workflow_id = details_url.split("/workflows/")[1].split("?")[0]
        url_parts = details_url.split("/pipelines/")[1].split("/")
        circleci_project_slug = f"{url_parts[0]}/{url_parts[1]}/{url_parts[2]}"
    elif is_codecov:
        logger.info("Detected Codecov, no extra metadata to extract")
    elif is_deepsource:
        # DeepSource: https://app.deepsource.com/gh/guibranco/projects-monitor-ui/
        logger.info("Detected DeepSource, skipping check_suite (unsupported provider)")
        return
    elif is_side8:
        # Side8: https://admin.pipeline.side8.io
        logger.info("Detected Side8, skipping check_suite (unsupported provider)")
        return
    else:
        # Check if this is a GitHub Actions URL with run ID
        if details_url and "/actions/runs/" in details_url:
            # https://github.com/hiroshinishio/tetris/actions/runs/11393174689/job/31710113401
            logger.info("Detected GitHub Actions, parsing run id from details_url")
            github_run_id = int(details_url.split(sep="/")[-3])
        else:
            # Other CI/CD services or external apps - skip processing
            logger.info("Unknown CI provider (details_url=%s), skipping", details_url)
            return

    # Extract repository related variables
    repo_id = repo["id"]
    is_fork = repo.get("fork", False)

    # Extract owner related variables
    owner = repo.get("owner", None)
    owner_type = owner["type"]
    owner_id = owner["id"]
    set_npm_token_env(owner_id)

    # Extract sender related variables
    sender_id = payload["sender"]["id"]
    sender_name = payload["sender"]["login"]
    sender_info = get_user_public_info(username=sender_name, token=token)
    if not sender_info.email:
        logger.info("Sender public email missing, falling back to commit history")
        email = get_email_from_commits(
            owner=owner_name, repo=repo_name, username=sender_name, token=token
        )
        if email:
            logger.info("Resolved sender email from commit history")
            sender_info.email = email

    # Extract PR related variables and return if no PR is associated with this check suite
    pull_requests = check_suite["pull_requests"]
    if not pull_requests:
        logger.info(
            "No pull requests associated with check_suite_id=%s", check_suite["id"]
        )
        return

    pull_request = pull_requests[0]
    pr_number = pull_request["number"]
    base_branch = pull_request["base"]["ref"]
    set_pr_number(pr_number)

    full_pr = get_pull_request(
        owner=owner_name, repo=repo_name, pr_number=pr_number, token=token
    )
    pr_title = full_pr["title"]

    # Get repository settings - check if trigger_on_test_failure is enabled
    repo_settings = get_repository(owner_id=owner_id, repo_id=repo_id)
    if not repo_settings or not repo_settings.get("trigger_on_test_failure"):
        logger.info("trigger_on_test_failure disabled for PR #%s", pr_number)
        return

    has_purchased = check_purchase_exists(owner_id=owner_id)
    model_id = get_preferred_model(
        repo_settings=repo_settings,
        is_paid=has_purchased,
    )

    # Start notification
    start_msg = f"Check run handler started for `{check_run_name}` in PR #{pr_number} in `{owner_name}/{repo_name}`"
    thread_ts = slack_notify(start_msg)

    clone_dir = get_clone_dir(owner_name, repo_name, pr_number)
    base_args: BaseArgs = {
        # Required fields
        "owner_type": owner_type,
        "owner_id": owner_id,
        "owner": owner_name,
        "repo_id": repo_id,
        "repo": repo_name,
        "clone_url": get_clone_url(owner_name, repo_name, token),
        "is_fork": is_fork,
        "pr_number": pr_number,
        "pr_title": pr_title,
        "pr_body": full_pr["body"] or "",
        "pr_comments": [
            f"@{c['user']['login']} ({c['created_at']}): {c['body']}"
            for c in get_pr_comments(
                owner=owner_name,
                repo=repo_name,
                pr_number=pr_number,
                token=token,
                exclude_self=True,
            )
        ],
        "latest_commit_sha": check_run["head_sha"],
        "pr_creator": sender_name,
        "base_branch": base_branch,
        "new_branch": head_branch,
        "installation_id": installation_id,
        "token": token,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "sender_email": sender_info.email,
        "sender_display_name": sender_info.display_name,
        "reviewers": [],
        "github_urls": [],
        "other_urls": [],
        "clone_dir": clone_dir,
        "model_id": model_id,
        "verify_consecutive_failures": 0,
        "quality_gate_fail_count": 0,
        "usage_id": 0,  # Placeholder — set after create_user_request
        "workflow_id": circleci_workflow_id if is_circleci else github_run_id,
        "check_run_name": check_run_name,
        "trigger": trigger,
        "skip_ci": True,
        "slack_thread_ts": thread_ts,
    }

    # Clone repo to tmp
    clone_repo_and_install_dependencies(
        owner=owner_name,
        repo=repo_name,
        base_branch=base_branch,
        pr_branch=head_branch,
        token=token,
        clone_dir=clone_dir,
    )

    # Fire-and-forget: refresh mongodb-binaries on S3 for the next run
    refresh_mongodb_cache(
        owner_id=owner_id,
        owner_name=owner_name,
        repo_name=repo_name,
        clone_dir=clone_dir,
    )

    mergeable_state = full_pr.get("mergeable_state")
    if mergeable_state == "dirty":
        logger.info("Merging base branch, mergeable_state=%s", mergeable_state)
        behind_by = get_head_commit_count_behind_base(
            owner=owner_name,
            repo=repo_name,
            base=base_branch,
            head=head_branch,
            token=token,
        )
        git_merge_base_into_pr(
            clone_dir=clone_dir, base_branch=base_branch, behind_by=behind_by
        )
    else:
        logger.info("Skipping merge, mergeable_state=%s", mergeable_state)

    # Install dependencies (read repo files from clone_dir, cache on S3)
    node_ready = ensure_node_packages(
        owner_id=owner_id,
        clone_dir=clone_dir,
        owner_name=owner_name,
        repo_name=repo_name,
    )
    logger.info("node: ready=%s", node_ready)

    php_ready = ensure_php_packages(
        owner_id=owner_id,
        clone_dir=clone_dir,
        owner_name=owner_name,
        repo_name=repo_name,
    )
    logger.info("php: ready=%s", php_ready)

    # Check if CI-failed comment already exists (skip if GitAuto is already handling this PR).
    # Exception: if the LATEST CI-failed comment is from an infra retry (contains "Re-triggering CI"), proceed because CI was re-triggered and failed with real errors.
    comments = get_pr_comments(
        owner=owner_name,
        repo=repo_name,
        pr_number=pr_number,
        token=token,
        exclude_self=False,
    )
    gitauto_failed_comments = [
        c
        for c in comments
        if c.get("user", {}).get("login") == GITHUB_APP_USER_NAME
        and CHECK_RUN_FAILED_MESSAGE in c.get("body", "")
    ]
    if gitauto_failed_comments:
        logger.info(
            "Found prior GitAuto CI-failed comment(s); deciding whether to proceed"
        )
        latest_failed = gitauto_failed_comments[-1]
        if "Re-triggering CI" not in latest_failed.get("body", ""):
            msg = f"Skipped - CI-failed comment exists for PR #{pr_number}"
            logger.info(
                "%s (check_suite_id=%s terminal, not infra retry)",
                msg,
                check_suite["id"],
            )
            slack_notify(f"{msg} in `{owner_name}/{repo_name}`", thread_ts)
            return

    # Check if permission denied comment exists (reuse comments already fetched above)
    has_permission_denied = any(
        c
        for c in comments
        if c.get("user", {}).get("login") == GITHUB_APP_USER_NAME
        and PERMISSION_DENIED_MESSAGE in c.get("body", "")
    )
    if has_permission_denied:
        msg = f"Skipped - permission request pending for PR #{pr_number}"
        logger.error(msg)
        slack_notify(f"{msg} in `{owner_name}/{repo_name}`", thread_ts)
        return

    # Check if there are too many GitAuto commits (prevent infinite retry loops)
    pr_commits = get_pull_request_commits(
        owner=owner_name, repo=repo_name, pr_number=pr_number, token=token
    )
    gitauto_commit_count = sum(
        1
        for c in pr_commits
        if c["commit"]["author"]
        and GITHUB_APP_USER_NAME in c["commit"]["author"]["name"]
    )

    if gitauto_commit_count >= MAX_GITAUTO_COMMITS_PER_PR:
        comment_msg = f"I've made {gitauto_commit_count} commits trying to fix this, but the tests keep failing with slightly different errors. I'm going to stop here to avoid an infinite loop. Could you take a look?"
        msg = f"Stopped after {gitauto_commit_count} commits in PR #{pr_number} - preventing infinite loop"
        logger.info(msg)
        create_comment(body=comment_msg, base_args=base_args)
        slack_notify(f"{msg} in `{owner_name}/{repo_name}`", thread_ts)
        return

    # Create the first comment
    p = 0
    log_messages = []
    msg = CHECK_RUN_FAILED_MESSAGE
    add_log_message(msg, log_messages)
    body = create_progress_bar(p=p, msg="\n".join(log_messages))
    comment_url = create_comment(body=body, base_args=base_args)
    base_args["comment_url"] = comment_url

    # Create a usage record
    usage_id = create_user_request(
        user_id=sender_id,
        user_name=sender_name,
        installation_id=installation_id,
        owner_id=owner_id,
        owner_type=owner_type,
        owner_name=owner_name,
        repo_id=repo_id,
        repo_name=repo_name,
        pr_number=pr_number,
        source="github",
        trigger="test_failure",
        email=sender_info.email,
        display_name=sender_info.display_name,
        lambda_info=lambda_info,
    )
    base_args["usage_id"] = usage_id

    # Cancel other in_progress check runs before proceeding with the fix
    cancel_workflow_runs(
        owner=owner_name, repo=repo_name, branch=head_branch, token=token
    )

    # Get changed files in the PR
    changed_files = get_pull_request_files(
        owner=owner_name, repo=repo_name, pr_number=pr_number, token=token
    )

    p += 5
    add_log_message(
        "Checked out the pull request title and changed files.", log_messages
    )
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    # Validate files for syntax issues before editing
    files_to_validate = [
        f["filename"] for f in changed_files if f["status"] != "removed"
    ]
    validation_result = await verify_task_is_ready(
        base_args=base_args,
        file_paths=files_to_validate,
        run_phpunit=False,
    )
    base_args["baseline_tsc_errors"] = set(validation_result.tsc_errors)
    pre_existing_errors = ""
    if validation_result.errors:
        pre_existing_errors = "\n".join(validation_result.errors)
        pre_existing_errors = label_log_source(
            pre_existing_errors,
            "ours",
            "GitAuto validation (AWS Lambda, Amazon Linux 2023)",
        )
        logger.warning(
            "Pre-existing validation errors on PR #%s before edits begin (%d):\n%s",
            pr_number,
            len(validation_result.errors),
            pre_existing_errors,
        )
    fixes_applied = validation_result.fixes_applied

    # Get the error log from the workflow run.
    ci_log_source = ""
    if is_circleci:
        ci_log_source = f"CircleCI for {owner_name}/{repo_name}"
        circleci_token = get_circleci_token(owner_id)

        if not circleci_token:
            logger.warning(
                "CircleCI token missing for owner_id=%s (workflow=%s); aborting",
                owner_id,
                circleci_workflow_id,
            )
            comment_body = "CircleCI token not configured. Please add your CircleCI token in GitAuto repository settings to enable automatic test failure fixes."
            update_comment(body=comment_body, base_args=base_args)
            slack_notify(
                f"CircleCI token not configured for {owner_name}/{repo_name}", thread_ts
            )
            return

        # Use the project slug extracted from the URL
        # Get failed jobs from workflow and collect their logs
        logger.info(
            "Fetching CircleCI workflow jobs for workflow_id=%s", circleci_workflow_id
        )
        workflow_jobs = get_circleci_workflow_jobs(circleci_workflow_id, circleci_token)
        failed_job_logs = []

        for job in workflow_jobs:
            if job.get("status") not in ("failed", "infrastructure_fail", "timedout"):
                logger.info(
                    "Skipping CircleCI job %s with status=%s (not a failure)",
                    job.get("job_number"),
                    job.get("status"),
                )
                continue

            job_number = job.get("job_number")
            if not job_number:
                logger.info(
                    "Skipping CircleCI job with missing job_number (status=%s)",
                    job.get("status"),
                )
                continue

            job_logs = get_circleci_build_logs(
                circleci_project_slug, job_number, circleci_token
            )
            if isinstance(job_logs, str) and job_logs:
                logger.info(
                    "Collected CircleCI logs for job %s (%d chars)",
                    job_number,
                    len(job_logs),
                )
                failed_job_logs.append(job_logs)

        error_log = (
            "\n\n".join(failed_job_logs)
            if failed_job_logs
            else "No failed job logs found"
        )
    elif is_codecov:
        logger.info("check_suite using Codecov path for check_run=%s", check_run_name)
        ci_log_source = f"Codecov coverage report for {owner_name}/{repo_name}"  # still "theirs" — coverage for the customer's repo
        # See payloads/github/check_run/codecov_check_run_output.json
        output = check_run.get("output", {})
        title = output.get("title", "")
        summary = output.get("summary", "")
        text = output.get("text", "")

        error_log = f"Codecov Check Failed: {check_run_name}\n\n"
        error_log += f"Title: {title}\n\n"
        error_log += f"Summary:\n{summary}\n\n"
        error_log += f"Details:\n{text}\n\n"

        # Fetch file-level coverage from Codecov API
        codecov_token = get_codecov_token(owner_id)
        if codecov_token:
            logger.info(
                "Codecov token present; fetching file-level coverage details for owner_id=%s",
                owner_id,
            )
            # Extract service from details_url (e.g., "gh" from https://app.codecov.io/gh/owner/repo)
            parts = details_url.split("codecov.io/")[1].split("/")
            service_map = {
                "gh": "github",  # Confirmed from Codecov documentation
                "ghe": "github_enterprise",  # Inferred
                "gl": "gitlab",  # Inferred
                "bb": "bitbucket",  # Inferred
            }
            codecov_service = service_map.get(parts[0], "github")

            codecov_data = get_codecov_commit_coverage(
                owner=owner_name,
                repo=repo_name,
                commit_sha=check_run["head_sha"],
                codecov_token=codecov_token,
                service=codecov_service,
            )
            if codecov_data:
                logger.info(
                    "Codecov returned coverage for %d files; appending to error_log",
                    len(codecov_data),
                )
                error_log += "\n\nFile-level Coverage Details:\n"
                for file in codecov_data:
                    error_log += f"\n{file['name']}: {file['coverage']}%\n"
                    if file.get("uncovered_lines"):
                        logger.info("Codecov file %s has uncovered lines", file["name"])
                        lines = ", ".join(
                            str(line_num) for line_num in file["uncovered_lines"]
                        )
                        error_log += f"  Uncovered lines: {lines}\n"
                    if file.get("partially_covered_lines"):
                        logger.info(
                            "Codecov file %s has partially covered lines", file["name"]
                        )
                        lines = ", ".join(
                            str(line_num)
                            for line_num in file["partially_covered_lines"]
                        )
                        error_log += f"  Partially covered lines: {lines}\n"
    else:
        logger.info(
            "check_suite using GitHub Actions path for run_id=%s", github_run_id
        )
        ci_log_source = f"GitHub Actions for {owner_name}/{repo_name}"
        # GitHub Actions log retrieval (existing logic)
        error_log = get_workflow_run_logs(
            owner=owner_name, repo=repo_name, run_id=github_run_id, token=token
        )

    if error_log == 404:
        permission_url = create_permission_url(
            owner_type=owner_type,
            owner_name=owner_name,
            installation_id=installation_id,
        )
        comment_body = f"{PERMISSION_DENIED_MESSAGE} {permission_url}"
        add_log_message(comment_body, log_messages)
        update_comment(body="\n".join(log_messages), base_args=base_args)

        # Get installation permissions via API
        permissions = get_installation_permissions(installation_id)

        # Early return notification
        msg = f"Skipped - permission denied for workflow run id `{circleci_workflow_id if is_circleci else github_run_id}` - Permissions: `{permissions}`"
        logger.error(msg)
        slack_notify(f"{msg} in `{owner_name}/{repo_name}`", thread_ts)
        return

    if error_log is None or not isinstance(error_log, str):
        comment_body = f"I couldn't find the error log. Contact {EMAIL_LINK} if the issue persists."
        add_log_message(comment_body, log_messages)
        update_comment(body="\n".join(log_messages), base_args=base_args)

        # Early return notification
        msg = "Skipped - error log not found"
        logger.warning(
            "%s for PR #%s (error_log type=%s)",
            msg,
            pr_number,
            type(error_log).__name__,
        )
        slack_notify(f"{msg} for `{owner_name}/{repo_name}`", thread_ts)
        return

    # Detect infrastructure failures (segfaults, OOM, etc.) - skip LLM and retry CI
    infra_failure = detect_infra_failure(error_log)
    if infra_failure:
        logger.info(
            "Detected infrastructure failure=%s on PR #%s; using CI-retry path instead of LLM fix",
            infra_failure,
            pr_number,
        )
        # Count previous infra retries from commit messages (pr_commits already fetched above)
        infra_retry_msg = "Infrastructure failure retry"
        infra_retry_count = sum(
            1 for c in pr_commits if infra_retry_msg in c["commit"]["message"]
        )

        if infra_retry_count >= MAX_INFRA_RETRIES:
            logger.warning(
                "Infra-retry ceiling hit on PR #%s: %d previous retries for %s, giving up on retriggers",
                pr_number,
                infra_retry_count,
                infra_failure,
            )
            msg = f"Infrastructure failure (`{infra_failure}`) persists after {infra_retry_count} retries. Skipping."
            add_log_message(msg, log_messages)
            update_comment(body="\n".join(log_messages), base_args=base_args)
            if usage_id:
                logger.info(
                    "Finalizing usage_id=%s after infra-retry ceiling hit", usage_id
                )
                update_usage(
                    usage_id=usage_id,
                    token_input=0,
                    token_output=0,
                    total_seconds=int(time.time() - current_time),
                    is_completed=True,
                    pr_number=pr_number,
                    original_error_log=error_log,
                    minimized_error_log=clean_logs(error_log),
                )
            logger.info(msg)
            slack_notify(f"{msg} in `{owner_name}/{repo_name}`", thread_ts)
            logger.info(
                "returning early because infra_retry_count >= MAX_INFRA_RETRIES"
            )
            return

        # Re-trigger CI with empty commit instead of calling LLM
        msg = f"Detected `{infra_failure}` (not a code issue). Re-triggering CI (retry {infra_retry_count + 1}/{MAX_INFRA_RETRIES})..."
        add_log_message(msg, log_messages)
        update_comment(body="\n".join(log_messages), base_args=base_args)
        pushed = create_empty_commit(base_args=base_args, message=infra_retry_msg)
        if not pushed:
            logger.warning(
                "Infra-retry empty commit skipped on %s: concurrent push detected; their push will trigger CI on its own",
                head_branch,
            )
            add_log_message(
                f"Another commit landed on `{head_branch}` while I was working. Their push triggers CI on its own, so no empty commit needed.",
                log_messages,
            )
            update_comment(body="\n".join(log_messages), base_args=base_args)

        if usage_id:
            logger.info(
                "Finalizing usage_id=%s after infra-retry empty commit", usage_id
            )
            update_usage(
                usage_id=usage_id,
                token_input=0,
                token_output=0,
                total_seconds=int(time.time() - current_time),
                is_completed=True,
                pr_number=pr_number,
                original_error_log=error_log,
                minimized_error_log=clean_logs(error_log),
            )
        logger.info("Infra-retry empty commit on PR #%s: %s", pr_number, msg)
        slack_notify(f"{msg} in `{owner_name}/{repo_name}`", thread_ts)
        return

    # Hash the normalized error log to detect duplicate errors across CI runs (raw logs contain commit SHAs that change with each empty commit)
    normalized_log = normalize_log_for_hashing(error_log)
    error_log_hash = hashlib.sha256(normalized_log.encode(encoding=UTF8)).hexdigest()
    logger.info(
        "Error log for PR #%s hash=%s:\n%s", pr_number, error_log_hash, error_log
    )

    # Clean logs using the complete pipeline
    minimized_log = clean_logs(error_log)

    # Check if this error hash has been attempted before (scoped to this PR). Compare by error hash only - workflow_id changes every CI run but the error is the same.
    existing_hashes = get_retry_error_hashes(
        owner_id=owner_id, repo_id=repo_id, pr_number=pr_number
    )
    if error_log_hash in existing_hashes:
        msg = f"Skipping `{check_run_name}` because GitAuto has already tried to fix this error before."
        add_log_message(msg, log_messages)
        update_comment(body="\n".join(log_messages), base_args=base_args)

        # Update usage record for skipped duplicate
        if usage_id:
            logger.info("Finalizing usage_id=%s on duplicate-error skip", usage_id)
            update_usage(
                usage_id=usage_id,
                token_input=0,
                token_output=0,
                total_seconds=int(time.time() - current_time),
                is_completed=True,
                pr_number=pr_number,
                retry_error_hashes=existing_hashes,
                original_error_log=error_log,
                minimized_error_log=minimized_log,
            )

        logger.info(
            "Duplicate error hash=%s on PR #%s: %s", error_log_hash, pr_number, msg
        )
        slack_notify(f"{msg} in `{owner_name}/{repo_name}`", thread_ts)
        return

    # Save the error hash to avoid retrying the same error
    existing_hashes.append(error_log_hash)
    update_retry_error_hashes(
        owner_id=owner_id, repo_id=repo_id, pr_number=pr_number, hashes=existing_hashes
    )

    p += 5
    add_log_message("Checked out the error log from the workflow run.", log_messages)
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    # Plan how to fix the error
    today = datetime.now().strftime("%Y-%m-%d")

    root_files = get_local_file_tree(base_args=base_args, dir_path="")
    target_dir: str | None = None
    target_dir_files: list[str] = []
    if changed_files:
        logger.info(
            "Building parent-dir set from %d changed files to narrow agent context",
            len(changed_files),
        )
        parents: set[str] = set()
        for file_change in changed_files:
            parent = str(Path(file_change["filename"]).parent)
            if parent != ".":
                logger.info("Adding parent dir %s to target scope", parent)
                parents.add(parent)
        if len(parents) == 1:
            logger.info(
                "All changed files share parent dir %s; narrowing agent scope to that dir",
                next(iter(parents)),
            )
            target_dir = parents.pop()
            target_dir_files = get_local_file_tree(
                base_args=base_args, dir_path=target_dir
            )

    # For large logs, save to file and reference it instead of embedding in the message
    if len(minimized_log) > MAX_INLINE_LOG_CHARS:
        save_ci_log_to_file(clone_dir, minimized_log)
        logger.info(
            "CI log too large (%d chars > %d); saved to %s",
            len(minimized_log),
            MAX_INLINE_LOG_CHARS,
            CI_LOG_PATH,
        )
        preview_chars = 5_000
        preview = minimized_log[:preview_chars]
        ci_log_value = (
            f"CI error log preview (first {preview_chars:,} of {len(minimized_log):,} chars):\n{preview}\n\n"
            f"Full log saved at: {CI_LOG_PATH}\n"
            f"Use get_local_file_content to read the full file, or search_local_file_contents to grep for specific errors."
        )
    else:
        logger.info(
            "Minimized CI log fits inline (%d chars); passing directly to agent",
            len(minimized_log),
        )
        ci_log_value = minimized_log

    # Tag the customer CI log with its source so the agent doesn't confuse it with errors produced inside our own Lambda.
    ci_log_value = label_log_source(ci_log_value, "theirs", ci_log_source)

    # Truncate patch — it sits in the first message and repeats in every LLM call
    max_patch_chars = 1000
    for f in changed_files:
        patch = f.get("patch")
        if patch and len(patch) > max_patch_chars:
            logger.info(
                "Truncating patch for %s from %d to %d chars to reduce per-call input tokens",
                f.get("filename"),
                len(patch),
                max_patch_chars,
            )
            f["patch"] = (
                patch[:max_patch_chars]
                + f"\n... [truncated, {len(patch):,} chars total]"
            )

    input_message: dict[str, str | list[str] | None] = {
        "pull_request_title": pr_title,
        "changed_files": json.dumps(obj=changed_files),
        "step_1_ci_error_log": ci_log_value,
        "today": today,
        "root_files": root_files,
        "target_dir": target_dir,
        "target_dir_files": target_dir_files,
    }
    if fixes_applied or pre_existing_errors:
        logger.info(
            "Prettier/ESLint auto-fix ran before agent; attaching note to input_message"
        )
        input_message["step_2_prettier_eslint_note"] = (
            "After the CI failure, we ran Prettier/ESLint --fix. "
            "Files may have changed. Read the latest content."
        )
    if fixes_applied:
        logger.info("Attaching step_2a auto-fixed list to input_message")
        input_message["step_2a_auto_fixed_and_committed"] = fixes_applied
    if pre_existing_errors:
        logger.info("Attaching step_2b pre-existing unfixable errors to input_message")
        input_message["step_2b_remaining_unfixable_errors"] = pre_existing_errors
    user_input = json.dumps(obj=input_message)

    # Create messages
    messages: list[MessageParam] = [{"role": "user", "content": user_input}]

    # Loop a process explore repo and commit changes until the ticket is resolved
    total_token_input = 0
    total_token_output = 0
    is_completed = False
    completion_reason = ""

    system_message = create_system_message(
        trigger=trigger, repo_settings=repo_settings, clone_dir=clone_dir
    )

    cost_cap_usd = get_credit_price(model_id) * COST_CAP_RATIO
    initial_head_sha = base_args["latest_commit_sha"]
    concurrent_push_detected = False

    for iteration in range(MAX_ITERATIONS):
        logger.info(
            "Agent loop iteration %d/%d on PR #%s",
            iteration + 1,
            MAX_ITERATIONS,
            pr_number,
        )
        if should_bail(
            current_time=current_time,
            phase="execution",
            base_args=base_args,
            slack_thread_ts=thread_ts,
        ):
            logger.info(
                "Agent loop bailed via should_bail on iteration %d/%d on PR #%s",
                iteration + 1,
                MAX_ITERATIONS,
                pr_number,
            )
            break

        model_id = maybe_switch_to_free_model(
            owner=owner_name,
            repo=repo_name,
            pr_number=pr_number,
            cost_cap_usd=cost_cap_usd,
            model_id=model_id,
            slack_thread_ts=thread_ts,
        )

        # Re-check trigger_on_test_failure in case it was disabled during execution
        refreshed_settings = get_repository(owner_id=owner_id, repo_id=repo_id)
        if not refreshed_settings or not refreshed_settings.get(
            "trigger_on_test_failure"
        ):
            is_completed = True
            completion_reason = "Stopped because the test failure trigger was disabled during execution."
            logger.info(
                "trigger_on_test_failure disabled mid-execution: %s", completion_reason
            )
            break

        # Safety check: Stop if older active request exists (race condition prevention)
        older_active_request = (
            check_older_active_test_failure_request(
                owner_id=owner_id,
                repo_id=repo_id,
                pr_number=pr_number,
                current_usage_id=usage_id,
            )
            if usage_id
            else None
        )
        if older_active_request:
            body = f"Stopped - older active test failure request found for PR #{pr_number}. Avoiding race condition."
            logger.info(
                "Older active test-failure request wins on PR #%s (usage_id=%s): %s",
                pr_number,
                usage_id,
                body,
            )
            if comment_url:
                logger.info("Updating existing comment with race-condition stop")
                update_comment(body=body, base_args=base_args)
            slack_notify(f"{body} in `{owner_name}/{repo_name}`", thread_ts)
            break

        # Call the agent to explore the codebase and commit changes
        result = await chat_with_agent(
            messages=messages,
            system_message=system_message,
            base_args=base_args,
            p=p,
            log_messages=log_messages,
            usage_id=usage_id,
            tools=TOOLS_FOR_PRS,
            model_id=model_id,
        )
        messages = result.messages
        is_completed = result.is_completed
        p = result.p
        total_token_input += result.token_input
        total_token_output += result.token_output

        if result.concurrent_push_detected:
            logger.warning(
                "check_suite: concurrent push on PR #%s; breaking agent loop",
                pr_number,
            )
            concurrent_push_detected = True
            break

        if is_completed:
            logger.info(
                "Agent signaled completion via verify_task_is_complete, breaking loop"
            )
            break

        # Force GC between rounds to free temporary objects (messages, diffs) and reduce Lambda OOM risk
        gc_collect_and_log()

    # Force verification unless concurrent push was detected (verifying on stale state would re-trigger the same bail).
    # verify_task_is_complete is kept even after a should_bail break because it runs Prettier/ESLint fixes that may produce new commits — those commits then qualify the PR for the CI retrigger path below.
    if not is_completed and not concurrent_push_detected:
        logger.info("Forcing verify_task_is_complete on PR #%s", pr_number)
        final_result = await verify_task_is_complete(base_args=base_args)
        is_completed = final_result.success

    # Decide whether to create the retrigger empty commit.
    # If the agent made no code changes on this run AND we're at/over the PR's cost cap, creating an empty commit would retrigger CI on the same failing code, fire this handler again, re-bail on cost cap (cost is PR-cumulative), commit again, loop forever.
    # When commits were pushed this run, retrigger CI — those changes might fix it.
    final_head_sha = get_local_head_sha(clone_dir=clone_dir)
    has_change_commits = bool(final_head_sha) and final_head_sha != initial_head_sha
    total_cost_usd = get_total_cost_for_pr(
        owner_name=owner_name, repo_name=repo_name, pr_number=pr_number
    )
    cost_cap_reached = total_cost_usd >= cost_cap_usd
    logger.info(
        "Retrigger decision on PR #%s: initial_head=%s final_head=%s has_change_commits=%s total_cost=$%.4f cost_cap=$%.4f cost_cap_reached=%s",
        pr_number,
        initial_head_sha,
        final_head_sha,
        has_change_commits,
        total_cost_usd,
        cost_cap_usd,
        cost_cap_reached,
    )

    # Concurrent push bail: skip final empty commit (racer's push already triggers CI), post accurate message
    if concurrent_push_detected:
        logger.info(
            "check_suite: posting concurrent-push bail message on PR #%s and skipping final empty commit",
            pr_number,
        )
        bail_msg = f"Another commit landed on `{head_branch}` while I was working on `{check_run_name}`. Their push triggers CI on its own, so I'm stopping here — your push stands."
        update_comment(body=bail_msg, base_args=base_args)
    elif cost_cap_reached and not has_change_commits:
        logger.info(
            "check_suite: cost cap reached with no change commits on PR #%s; skipping final empty commit to prevent infinite retry loop",
            pr_number,
        )
    # If stopped due to trigger being disabled, post reason and skip empty commit
    elif completion_reason:
        logger.info(
            "Posting early-stop reason to PR #%s and skipping final empty commit: %s",
            pr_number,
            completion_reason,
        )
        update_comment(body=completion_reason, base_args=base_args)
    else:
        logger.info(
            "Creating final empty commit on PR #%s to release concurrency lock and retrigger CI",
            pr_number,
        )
        # Trigger final test workflows with an empty commit
        comment_body = "Creating final empty commit to trigger workflows..."
        update_comment(body=comment_body, base_args=base_args)
        pushed = create_empty_commit(base_args=base_args)

        # Update final comment. Do NOT include CHECK_RUN_FAILED_MESSAGE here — that marker is a concurrency lock set at line 317 when processing starts.
        # Clearing it here releases the lock so the next check_suite webhook can proceed.
        # The error hash dedup at line 557 prevents re-attempting the same error.
        if not pushed:
            logger.warning(
                "Final empty commit skipped on %s: concurrent push detected; posting respect-the-push message",
                head_branch,
            )
            final_msg = f"Another commit landed on `{head_branch}` while I was working on `{check_run_name}`. Their push triggers CI on its own, so no empty commit needed."
        elif is_completed:
            logger.info(
                "Final empty commit pushed and agent reports completion; posting waiting-for-CI message on PR #%s",
                pr_number,
            )
            final_msg = f"Created an empty commit to re-trigger the `{check_run_name}` CI. Waiting for results."
        else:
            logger.warning(
                "Final empty commit pushed but agent did not complete; posting review-changes message on PR #%s",
                pr_number,
            )
            final_msg = f"I tried to fix `{check_run_name}` but verification still shows errors. Please review the changes."
        update_comment(body=final_msg, base_args=base_args)

    # Update usage record
    end_time = time.time()
    if usage_id:
        logger.info(
            "Finalizing usage_id=%s for PR #%s: tokens_in=%d tokens_out=%d",
            usage_id,
            pr_number,
            total_token_input,
            total_token_output,
        )
        update_usage(
            usage_id=usage_id,
            token_input=total_token_input,
            token_output=total_token_output,
            total_seconds=int(end_time - current_time),
            pr_number=pr_number,
            is_completed=True,
            retry_error_hashes=existing_hashes,
            original_error_log=error_log,
            minimized_error_log=minimized_log,
        )

    # End notification
    slack_notify("Completed", thread_ts)
