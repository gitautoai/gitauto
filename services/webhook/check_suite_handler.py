# Standard imports
import asyncio
from datetime import datetime
import hashlib
import json
from pathlib import Path
import time

# Third-party imports
from anthropic.types import MessageParam

# Local imports
from config import EMAIL_LINK, GITHUB_APP_USER_NAME, PRODUCT_ID, UTF8
from constants.agent import MAX_ITERATIONS
from constants.general import MAX_GITAUTO_COMMITS_PER_PR
from constants.messages import PERMISSION_DENIED_MESSAGE, CHECK_RUN_STUMBLED_MESSAGE
from services.agents.verify_task_is_ready import verify_task_is_ready
from services.agents.verify_task_is_complete import verify_task_is_complete
from services.chat_with_agent import chat_with_agent
from services.circleci.get_build_logs import get_circleci_build_logs
from services.circleci.get_workflow_jobs import get_circleci_workflow_jobs
from services.codecov.get_commit_coverage import get_codecov_commit_coverage
from services.efs.get_efs_dir import get_efs_dir
from services.node.ensure_node_packages import ensure_node_packages
from services.node.set_npm_token_env import set_npm_token_env
from services.git.get_clone_dir import get_clone_dir
from services.git.get_clone_url import get_clone_url
from services.git.git_clone_to_efs import clone_tasks, git_clone_to_efs
from services.git.prepare_repo_for_work import prepare_repo_for_work
from services.github.check_suites.get_failed_check_runs import (
    get_failed_check_runs_from_check_suite,
)
from services.github.comments.create_comment import create_comment
from services.github.comments.has_comment_with_text import has_comment_with_text
from services.github.comments.update_comment import update_comment
from services.github.commits.create_empty_commit import create_empty_commit
from services.github.installations.get_installation_permissions import (
    get_installation_permissions,
)
from services.github.pulls.get_pull_request import get_pull_request
from services.github.pulls.get_pull_request_commits import get_pull_request_commits
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.types.github_types import BaseArgs, CheckSuiteCompletedPayload
from services.github.utils.create_permission_url import create_permission_url
from services.github.token.get_installation_token import get_installation_access_token
from services.github.trees.get_file_tree_list import get_file_tree_list
from services.github.workflow_runs.cancel_workflow_runs import cancel_workflow_runs
from services.github.workflow_runs.get_workflow_run_logs import get_workflow_run_logs
from services.claude.tools.tools import TOOLS_FOR_PRS
from services.slack.slack_notify import slack_notify
from services.supabase.check_suites.insert_check_suite import insert_check_suite
from services.supabase.codecov_tokens.get_codecov_token import get_codecov_token
from services.supabase.create_user_request import create_user_request
from services.supabase.circleci_tokens.get_circleci_token import get_circleci_token
from services.supabase.repositories.get_repository import get_repository
from services.supabase.usage.get_retry_pairs import get_retry_workflow_id_hash_pairs
from services.supabase.usage.update_retry_pairs import (
    update_retry_workflow_id_hash_pairs,
)
from services.supabase.usage.update_usage import update_usage
from services.supabase.usage.check_older_active_test_failure import (
    check_older_active_test_failure_request,
)
from services.webhook.utils.create_system_message import create_system_message
from services.webhook.utils.should_bail import should_bail
from utils.logging.add_log_message import add_log_message
from utils.logging.logging_config import logger, set_pr_number, set_trigger
from utils.logs.clean_logs import clean_logs
from utils.progress_bar.progress_bar import create_progress_bar


async def handle_check_suite(
    payload: CheckSuiteCompletedPayload,
    lambda_info: dict[str, str | None] | None = None,
):
    current_time = time.time()
    trigger = "test_failure"
    set_trigger(trigger)

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

    # Check if this is a GitAuto PR by branch name (early return)
    # head_branch can be None when:
    # - Check suite runs on a tag push (tags don't have branches)
    # - Check suite runs on a deleted branch
    # - Check suite runs on a direct commit without PR
    # - Orphan commits or detached HEAD state
    check_suite = payload["check_suite"]
    head_branch = check_suite["head_branch"]
    if not head_branch or not head_branch.startswith(PRODUCT_ID):
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
    codecov_check_run_id = ""
    github_run_id = 0

    if is_circleci:
        # URL: https://app.circleci.com/pipelines/circleci/J2wtzLah5rmzRnx6qn4RyQ/UUb5FLNgQCnif8mB6mQn7s/7/workflows/772ddda7-d6b7-49ad-9123-108d9f8164b5
        circleci_workflow_id = details_url.split("/workflows/")[1].split("?")[0]
        url_parts = details_url.split("/pipelines/")[1].split("/")
        circleci_project_slug = f"{url_parts[0]}/{url_parts[1]}/{url_parts[2]}"
    elif is_codecov:
        codecov_check_run_id = str(check_run.get("id", ""))
    elif is_deepsource:
        # DeepSource: https://app.deepsource.com/gh/guibranco/projects-monitor-ui/
        return
    elif is_side8:
        # Side8: https://admin.pipeline.side8.io
        return
    else:
        # Check if this is a GitHub Actions URL with run ID
        if details_url and "/actions/runs/" in details_url:
            # https://github.com/hiroshinishio/tetris/actions/runs/11393174689/job/31710113401
            github_run_id = int(details_url.split(sep="/")[-3])
        else:
            # Other CI/CD services or external apps - skip processing
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

    # Extract PR related variables and return if no PR is associated with this check suite
    pull_requests = check_suite["pull_requests"]
    if not pull_requests:
        return

    pull_request = pull_requests[0]
    pull_number = pull_request["number"]
    set_pr_number(pull_number)

    full_pr = get_pull_request(
        owner=owner_name, repo=repo_name, pull_number=pull_number, token=token
    )
    pull_title = full_pr["title"]
    target_branch = full_pr["base"]["ref"]

    # Get repository settings - check if trigger_on_test_failure is enabled
    repo_settings = get_repository(owner_id=owner_id, repo_id=repo_id)
    if not repo_settings or not repo_settings.get("trigger_on_test_failure"):
        return

    # Start notification
    start_msg = f"Check run handler started for `{check_run_name}` in PR #{pull_number} in `{owner_name}/{repo_name}`"
    thread_ts = slack_notify(start_msg)

    clone_dir = get_clone_dir(owner_name, repo_name, pull_number)
    base_args: BaseArgs = {
        # Required fields
        "input_from": "github",
        "owner_type": owner_type,
        "owner_id": owner_id,
        "owner": owner_name,
        "repo_id": repo_id,
        "repo": repo_name,
        "clone_url": repo["clone_url"],
        "is_fork": is_fork,
        "issue_number": pull_number,
        "issue_title": pull_title,
        "issue_body": f"Automated fix for failed check run: {check_run_name}",
        "issue_comments": [],
        "latest_commit_sha": check_run["head_sha"],
        "issuer_name": sender_name,
        "base_branch": head_branch,
        "new_branch": head_branch,  # Yes, intentionally set head_branch to base_branch because get_file_tree requires the base branch
        "installation_id": installation_id,
        "token": token,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "sender_email": f"{sender_name}@users.noreply.github.com",
        "is_automation": True,
        "reviewers": [],
        "github_urls": [],
        "other_urls": [],
        "clone_dir": clone_dir,
        # Extra fields for backward compatibility
        "pull_number": pull_number,
        "workflow_id": circleci_workflow_id if is_circleci else github_run_id,
        "check_run_name": check_run_name,
        "skip_ci": True,
    }

    # Clone repo to tmp
    await prepare_repo_for_work(
        owner=owner_name,
        repo=repo_name,
        pr_branch=head_branch,
        token=token,
        clone_dir=clone_dir,
    )

    # Start clone and install tasks
    efs_dir = get_efs_dir(owner_name, repo_name)
    clone_url = get_clone_url(owner_name, repo_name, token)
    clone_tasks[efs_dir] = asyncio.create_task(
        git_clone_to_efs(efs_dir, clone_url, target_branch)
    )
    node_ready = await ensure_node_packages(
        owner_name, owner_id, repo_name, target_branch, token, efs_dir
    )
    logger.info("node: ready=%s", node_ready)

    # Check if permission comment or stumbled comment already exists
    if has_comment_with_text(
        owner=owner_name,
        repo=repo_name,
        issue_number=pull_number,
        token=token,
        texts=[CHECK_RUN_STUMBLED_MESSAGE],
    ):
        msg = f"Skipped - stumbled comment exists for PR #{pull_number}"
        logger.info(msg)
        slack_notify(f"{msg} in `{owner_name}/{repo_name}`", thread_ts)
        return

    if has_comment_with_text(
        owner=owner_name,
        repo=repo_name,
        issue_number=pull_number,
        token=token,
        texts=[PERMISSION_DENIED_MESSAGE],
    ):
        msg = f"Skipped - permission request pending for PR #{pull_number}"
        logger.error(msg)
        slack_notify(f"{msg} in `{owner_name}/{repo_name}`", thread_ts)
        return

    # Check if there are too many GitAuto commits (prevent infinite retry loops)
    pr_commits = get_pull_request_commits(
        owner=owner_name, repo=repo_name, pull_number=pull_number, token=token
    )
    gitauto_commit_count = 0
    for commit in pr_commits:
        commit_author = commit.get("commit", {}).get("author", {})
        commit_name = commit_author.get("name", "")
        if GITHUB_APP_USER_NAME in commit_name:
            gitauto_commit_count += 1

    if gitauto_commit_count >= MAX_GITAUTO_COMMITS_PER_PR:
        comment_msg = f"I've made {gitauto_commit_count} commits trying to fix this, but the tests keep failing with slightly different errors. I'm going to stop here to avoid an infinite loop. Could you take a look?"
        msg = f"Stopped after {gitauto_commit_count} commits in PR #{pull_number} - preventing infinite loop"
        logger.info(msg)
        create_comment(body=comment_msg, base_args=base_args)
        slack_notify(f"{msg} in `{owner_name}/{repo_name}`", thread_ts)
        return

    # Create the first comment
    p = 0
    log_messages = []
    msg = CHECK_RUN_STUMBLED_MESSAGE
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
        issue_number=pull_number,
        source="github",
        trigger="test_failure",
        email=None,
        pr_number=pull_number,
        lambda_info=lambda_info,
    )

    # Cancel other in_progress check runs before proceeding with the fix
    cancel_workflow_runs(
        owner=owner_name, repo=repo_name, branch=head_branch, token=token
    )

    # Get changed files in the PR
    changed_files = get_pull_request_files(
        owner=owner_name, repo=repo_name, pull_number=pull_number, token=token
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
        base_args=base_args, file_paths=files_to_validate, run_tsc=True, run_jest=True
    )
    base_args["baseline_tsc_errors"] = set(validation_result.tsc_errors)
    pre_existing_errors = ""
    if validation_result.errors:
        pre_existing_errors = "\n".join(validation_result.errors)
        logger.warning("Remaining errors:\n%s", pre_existing_errors)
    fixes_applied = validation_result.fixes_applied

    # Get the error log from the workflow run
    if is_circleci:
        circleci_token = get_circleci_token(owner_id)

        if not circleci_token:
            comment_body = "CircleCI token not configured. Please add your CircleCI token in GitAuto repository settings to enable automatic test failure fixes."
            update_comment(body=comment_body, base_args=base_args)
            slack_notify(
                f"CircleCI token not configured for {owner_name}/{repo_name}", thread_ts
            )
            return

        # Use the project slug extracted from the URL
        # Get failed jobs from workflow and collect their logs
        workflow_jobs = get_circleci_workflow_jobs(circleci_workflow_id, circleci_token)
        failed_job_logs = []

        for job in workflow_jobs:
            if job.get("status") != "failed":
                continue

            job_number = job.get("job_number")
            if not job_number:
                continue

            job_logs = get_circleci_build_logs(
                circleci_project_slug, job_number, circleci_token
            )
            if job_logs and job_logs != 404:
                failed_job_logs.append(job_logs)

        error_log = (
            "\n\n".join(failed_job_logs)
            if failed_job_logs
            else "No failed job logs found"
        )
    elif is_codecov:
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
                error_log += "\n\nFile-level Coverage Details:\n"
                for file in codecov_data:
                    error_log += f"\n{file['name']}: {file['coverage']}%\n"
                    if file.get("uncovered_lines"):
                        lines = ", ".join(
                            str(line_num) for line_num in file["uncovered_lines"]
                        )
                        error_log += f"  Uncovered lines: {lines}\n"
                    if file.get("partially_covered_lines"):
                        lines = ", ".join(
                            str(line_num)
                            for line_num in file["partially_covered_lines"]
                        )
                        error_log += f"  Partially covered lines: {lines}\n"
    else:
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
        logger.error(msg)
        slack_notify(f"{msg} for `{owner_name}/{repo_name}`", thread_ts)
        return

    # Create a pair of workflow ID and error log hash
    error_log_hash = hashlib.sha256(error_log.encode(encoding=UTF8)).hexdigest()
    if is_circleci:
        workflow_id = circleci_workflow_id
    elif is_codecov:
        workflow_id = codecov_check_run_id
    else:
        workflow_id = str(github_run_id)
    current_pair = f"{workflow_id}:{error_log_hash}"
    logger.info("Workflow ID and error log hash pair: %s", current_pair)
    logger.info("Error log content for PR #%s:", pull_number)
    logger.info(error_log)

    # Clean logs using the complete pipeline
    minimized_log = clean_logs(error_log)

    # Check if this exact pair exists
    existing_pairs = get_retry_workflow_id_hash_pairs(
        owner_id=owner_id, repo_id=repo_id, pr_number=pull_number
    )
    if existing_pairs and current_pair in existing_pairs:
        msg = f"Skipping `{check_run_name}` because GitAuto has already tried to fix this exact error before `{current_pair}`."
        add_log_message(msg, log_messages)
        update_comment(body="\n".join(log_messages), base_args=base_args)

        # Update usage record for skipped duplicate
        if usage_id:
            update_usage(
                usage_id=usage_id,
                token_input=0,
                token_output=0,
                total_seconds=int(time.time() - current_time),
                is_completed=True,
                pr_number=pull_number,
                retry_workflow_id_hash_pairs=existing_pairs,
                original_error_log=error_log,
                minimized_error_log=minimized_log,
            )

        # Early return notification
        logger.info(msg)
        slack_notify(f"{msg} in `{owner_name}/{repo_name}`", thread_ts)
        return

    # Save the pair to avoid infinite loops
    existing_pairs.append(current_pair)
    update_retry_workflow_id_hash_pairs(
        owner_id=owner_id, repo_id=repo_id, pr_number=pull_number, pairs=existing_pairs
    )

    p += 5
    add_log_message("Checked out the error log from the workflow run.", log_messages)
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    # Plan how to fix the error
    today = datetime.now().strftime("%Y-%m-%d")

    root_files = get_file_tree_list(base_args=base_args, dir_path="")
    target_dir: str | None = None
    target_dir_files: list[str] = []
    if changed_files:
        parents: set[str] = set()
        for file_change in changed_files:
            parent = str(Path(file_change["filename"]).parent)
            if parent != ".":
                parents.add(parent)
        if len(parents) == 1:
            target_dir = parents.pop()
            target_dir_files = get_file_tree_list(
                base_args=base_args, dir_path=target_dir
            )

    input_message: dict[str, str | list[str] | None] = {
        "pull_request_title": pull_title,
        "changed_files": json.dumps(obj=changed_files),
        "step_1_ci_error_log": minimized_log,
        "today": today,
        "root_files": root_files,
        "target_dir": target_dir,
        "target_dir_files": target_dir_files,
    }
    if fixes_applied or pre_existing_errors:
        input_message["step_2_prettier_eslint_note"] = (
            "After the CI failure, we ran Prettier/ESLint --fix. "
            "Files may have changed. Read the latest content."
        )
    if fixes_applied:
        input_message["step_2a_auto_fixed_and_committed"] = fixes_applied
    if pre_existing_errors:
        input_message["step_2b_remaining_unfixable_errors"] = pre_existing_errors
    user_input = json.dumps(obj=input_message)

    # Create messages
    messages: list[MessageParam] = [{"role": "user", "content": user_input}]

    # Loop a process explore repo and commit changes until the ticket is resolved
    total_token_input = 0
    total_token_output = 0
    is_completed = False

    system_message = create_system_message(trigger=trigger, repo_settings=repo_settings)

    for _iteration in range(MAX_ITERATIONS):
        if should_bail(
            current_time=current_time,
            phase="execution",
            base_args=base_args,
            slack_thread_ts=thread_ts,
        ):
            break

        # Safety check: Stop if older active request exists (race condition prevention)
        older_active_request = (
            check_older_active_test_failure_request(
                owner_id=owner_id,
                repo_id=repo_id,
                pr_number=pull_number,
                current_usage_id=usage_id,
            )
            if usage_id
            else None
        )
        if older_active_request:
            body = f"Stopped - older active test failure request found for PR #{pull_number}. Avoiding race condition."
            logger.info(body)
            if comment_url:
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
            model_id=None,
        )
        messages = result.messages
        is_completed = result.is_completed
        p = result.p
        total_token_input += result.token_input
        total_token_output += result.token_output

        if is_completed:
            logger.info(
                "Agent signaled completion via verify_task_is_complete, breaking loop"
            )
            break

    # Log if loop exhausted without completion and force verification
    if not is_completed:
        logger.warning(
            "Agent loop hit MAX_ITERATIONS (%d) without calling verify_task_is_complete. Forcing verification.",
            MAX_ITERATIONS,
        )
        final_result = await verify_task_is_complete(base_args=base_args)
        is_completed = final_result.success

    # Trigger final test workflows with an empty commit
    comment_body = "Creating final empty commit to trigger workflows..."
    update_comment(body=comment_body, base_args=base_args)
    create_empty_commit(base_args=base_args)

    # Create final message based on verification result
    if is_completed:
        final_msg = f"Finished fixing the `{check_run_name}` check run error!"
    else:
        final_msg = f"I tried to fix `{check_run_name}` but verification still shows errors. Please review the changes."
    update_comment(body=final_msg, base_args=base_args)

    # Update usage record
    end_time = time.time()
    if usage_id:
        update_usage(
            usage_id=usage_id,
            token_input=total_token_input,
            token_output=total_token_output,
            total_seconds=int(end_time - current_time),
            pr_number=pull_number,
            is_completed=True,
            retry_workflow_id_hash_pairs=existing_pairs,
            original_error_log=error_log,
            minimized_error_log=minimized_log,
        )

    # End notification
    slack_notify("Completed", thread_ts)
