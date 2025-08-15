# Standard imports
from datetime import datetime
import hashlib
import json
import time

# Local imports
from config import EMAIL_LINK, GITHUB_APP_USER_NAME, UTF8
from constants.messages import PERMISSION_DENIED_MESSAGE, CHECK_RUN_STUMBLED_MESSAGE
from services.chat_with_agent import chat_with_agent

# Local imports (CircleCI)
from services.circleci.get_build_logs import get_circleci_build_logs
from services.circleci.get_workflow_jobs import get_circleci_workflow_jobs

# Local imports (GitHub)
from services.github.branches.check_branch_exists import check_branch_exists
from services.github.comments.create_comment import create_comment
from services.github.comments.has_comment_with_text import has_comment_with_text
from services.github.comments.update_comment import update_comment
from services.github.commits.create_empty_commit import create_empty_commit
from services.github.github_manager import get_remote_file_content
from services.github.installations.get_installation_permissions import (
    get_installation_permissions,
)
from services.github.pulls.get_pull_request import get_pull_request
from services.github.pulls.get_pull_request_file_changes import (
    get_pull_request_file_changes,
)
from services.github.pulls.is_pull_request_open import is_pull_request_open
from services.github.types.github_types import BaseArgs, CheckRunCompletedPayload
from services.github.utils.create_permission_url import create_permission_url
from services.github.token.get_installation_token import get_installation_access_token
from services.github.trees.get_file_tree_list import get_file_tree_list
from services.github.types.check_run import CheckRun
from services.github.types.check_suite import CheckSuite
from services.github.types.pull_request import PullRequest
from services.github.types.repository import Repository
from services.github.workflow_runs.cancel_workflow_runs import cancel_workflow_runs
from services.github.workflow_runs.get_workflow_run_logs import get_workflow_run_logs
from services.github.workflow_runs.get_workflow_run_path import get_workflow_run_path

# Local imports (Slack)
from services.slack.slack_notify import slack_notify

# Local imports (Supabase)
from services.supabase.create_user_request import create_user_request
from services.supabase.repositories.get_repository import get_repository
from services.supabase.usage.get_retry_pairs import get_retry_workflow_id_hash_pairs
from services.supabase.usage.update_retry_pairs import (
    update_retry_workflow_id_hash_pairs,
)
from services.supabase.usage.update_usage import update_usage

# Local imports (Others)
from utils.progress_bar.progress_bar import create_progress_bar
from utils.time.is_lambda_timeout_approaching import is_lambda_timeout_approaching
from utils.time.get_timeout_message import get_timeout_message


def handle_check_run(payload: CheckRunCompletedPayload):
    current_time = time.time()
    trigger = "test_failure"

    # Extract workflow run id
    check_run: CheckRun = payload["check_run"]
    details_url = check_run["details_url"]

    is_circleci = "circleci.com" in details_url if details_url else False
    if is_circleci:
        # URL: https://app.circleci.com/pipelines/circleci/J2wtzLah5rmzRnx6qn4RyQ/UUb5FLNgQCnif8mB6mQn7s/7/workflows/772ddda7-d6b7-49ad-9123-108d9f8164b5
        workflow_id = details_url.split("/workflows/")[1].split("?")[0]
        url_parts = details_url.split("/pipelines/")[1].split("/")
        circleci_project_slug = f"{url_parts[0]}/{url_parts[1]}/{url_parts[2]}"
    else:
        workflow_id = details_url.split(sep="/")[-3]

    check_run_name = check_run["name"]

    # Extract repository related variables
    repo: Repository = payload["repository"]
    repo_name = repo["name"]
    repo_id = repo["id"]
    is_fork = repo.get("fork", False)

    # Extract owner related variables
    owner = repo.get("owner", None)
    if owner is None:
        return
    owner_type = owner["type"]
    owner_id = owner["id"]
    owner_name = owner["login"]

    # Extract branch related variables
    check_suite: CheckSuite = check_run["check_suite"]
    head_branch = check_suite["head_branch"]

    # Extract sender related variables and return if sender is GitAuto itself
    sender_id = payload["sender"]["id"]
    sender_name = payload["sender"]["login"]
    if sender_name != GITHUB_APP_USER_NAME:
        return

    # Extract PR related variables and return if no PR is associated with this check run
    pull_requests: list[PullRequest] = check_run.get("pull_requests", [])
    if not pull_requests:
        return

    pull_request: PullRequest = pull_requests[0]
    pull_number = pull_request["number"]
    pull_url = pull_request["url"]

    # Extract other information
    installation_id = payload["installation"]["id"]
    token: str = get_installation_access_token(installation_id=installation_id)

    # Get repository settings - check if trigger_on_test_failure is enabled
    repo_settings = get_repository(repo_id=repo_id)
    if not repo_settings or not repo_settings.get("trigger_on_test_failure"):
        return

    # Start notification
    start_msg = f"Check run handler started for `{check_run_name}` in PR #{pull_number} in `{owner_name}/{repo_name}`"
    thread_ts = slack_notify(start_msg)

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
        "issue_title": f"Check run failure: {check_run_name}",
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
        # Extra fields for backward compatibility
        "pull_number": pull_number,
        "workflow_id": workflow_id,
        "check_run_name": check_run_name,
        "skip_ci": True,
    }

    # Check if permission comment or stumbled comment already exists
    if has_comment_with_text(
        base_args, [PERMISSION_DENIED_MESSAGE, CHECK_RUN_STUMBLED_MESSAGE]
    ):
        slack_notify(
            f"Permission request has already been made or another check run has already been working on this PR for `{owner_name}/{repo_name}`",
            thread_ts,
        )
        return

    # Create the first comment
    p = 0
    log_messages = []
    msg = CHECK_RUN_STUMBLED_MESSAGE
    log_messages.append(msg)
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
    )

    # Cancel other in_progress check runs before proceeding with the fix
    cancel_workflow_runs(
        owner=owner_name, repo=repo_name, branch=head_branch, token=token
    )

    # Get title, body, and code changes in the PR
    pr_data = get_pull_request(
        owner=owner_name, repo=repo_name, pull_number=pull_number, token=token
    )
    pull_title = pr_data["title"]
    pull_body = pr_data["body"]
    pull_file_url = f"{pull_url}/files"
    pull_changes = get_pull_request_file_changes(url=pull_file_url, token=token)
    p += 5
    log_messages.append("Checked out the pull request title, body, and code changes.")
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    # Get the CI/CD workflow file content
    if is_circleci:
        # CircleCI uses .circleci/config.yml
        workflow_path = ".circleci/config.yml"
        workflow_content = get_remote_file_content(
            file_path=workflow_path, base_args=base_args
        )
    else:
        # GitHub Actions workflow
        workflow_path = get_workflow_run_path(
            owner=owner_name, repo=repo_name, run_id=workflow_id, token=token
        )

        workflow_content = ""
        if workflow_path != 404:
            workflow_content = get_remote_file_content(
                file_path=workflow_path, base_args=base_args
            )

    p += 5
    log_messages.append(
        f"Checked out the {'CircleCI' if is_circleci else 'GitHub Action'} workflow file. `{workflow_path}`"
    )
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    # Get the file tree in the root of the repo
    file_tree, _ = get_file_tree_list(base_args=base_args, max_files=100)
    p += 5
    log_messages.append("Checked out the file tree in the repo.")
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    # Get the error log from the workflow run
    if is_circleci:
        circleci_token = repo_settings.get("circleci_token") if repo_settings else None

        if not circleci_token:
            comment_body = "CircleCI token not configured. Please add your CircleCI token in GitAuto repository settings to enable automatic test failure fixes."
            update_comment(body=comment_body, base_args=base_args)
            slack_notify(
                f"CircleCI token not configured for {owner_name}/{repo_name}", thread_ts
            )
            return

        # Use the project slug extracted from the URL
        # Get failed jobs from workflow and collect their logs
        workflow_jobs = get_circleci_workflow_jobs(workflow_id, circleci_token)
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
    else:
        # GitHub Actions log retrieval (existing logic)
        error_log = get_workflow_run_logs(
            owner=owner_name, repo=repo_name, run_id=workflow_id, token=token
        )

    if error_log == 404:
        permission_url = create_permission_url(
            owner_type=owner_type,
            owner_name=owner_name,
            installation_id=installation_id,
        )
        comment_body = f"{PERMISSION_DENIED_MESSAGE} {permission_url}"
        log_messages.append(comment_body)
        update_comment(body="\n".join(log_messages), base_args=base_args)

        # Get installation permissions via API
        permissions = get_installation_permissions(installation_id)

        # Early return notification
        early_return_msg = f"error_log is 404. Permission denied for workflow run id `{workflow_id}` in `{owner_name}/{repo_name}` - Permissions: `{permissions}`"
        slack_notify(early_return_msg, thread_ts)
        return

    if error_log is None:
        comment_body = f"I couldn't find the error log. Contact {EMAIL_LINK} if the issue persists."
        log_messages.append(comment_body)
        update_comment(body="\n".join(log_messages), base_args=base_args)

        # Early return notification
        early_return_msg = f"Error log not found for {owner_name}/{repo_name}"
        slack_notify(early_return_msg, thread_ts)
        return

    # Create a pair of workflow ID and error log hash
    error_log_hash = hashlib.sha256(error_log.encode(encoding=UTF8)).hexdigest()
    current_pair = f"{workflow_id}:{error_log_hash}"
    print(f"Workflow ID and error log hash pair: {current_pair}")

    # Check if this exact pair exists
    existing_pairs = get_retry_workflow_id_hash_pairs(
        owner_id=owner_id, repo_id=repo_id, pr_number=pull_number
    )
    if existing_pairs and current_pair in existing_pairs:
        msg = f"Skipping `{check_run_name}` because GitAuto has already tried to fix this exact error before `{current_pair}`."
        log_messages.append(msg)
        update_comment(body="\n".join(log_messages), base_args=base_args)

        # Early return notification
        early_return_msg = (
            f"Already attempted fix for {owner_name}/{repo_name} - {check_run_name}"
        )
        slack_notify(early_return_msg, thread_ts)
        return

    # Save the pair to avoid infinite loops
    existing_pairs.append(current_pair)
    update_retry_workflow_id_hash_pairs(
        owner_id=owner_id, repo_id=repo_id, pr_number=pull_number, pairs=existing_pairs
    )

    p += 5
    log_messages.append("Checked out the error log from the workflow run.")
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    # Plan how to fix the error
    today = datetime.now().strftime("%Y-%m-%d")
    input_message: dict[str, str] = {
        "pull_request_title": pull_title,
        "pull_request_body": pull_body,
        "pull_request_changes": json.dumps(obj=pull_changes),
        "workflow_content": workflow_content,
        "file_tree": file_tree,
        "error_log": error_log,
        "today": today,
    }
    user_input = json.dumps(obj=input_message)

    # Create messages
    messages = [{"role": "user", "content": user_input}]

    # Loop a process explore repo and commit changes until the ticket is resolved
    previous_calls = []
    retry_count = 0
    while True:
        # Timeout check: Stop if we're approaching Lambda limit
        is_timeout_approaching, elapsed_time = is_lambda_timeout_approaching(
            current_time
        )
        if is_timeout_approaching:
            timeout_msg = get_timeout_message(elapsed_time, "Check run processing")
            if comment_url:
                update_comment(body=timeout_msg, base_args=base_args)
            break

        # Safety check: Stop if PR is closed or branch is deleted
        if not is_pull_request_open(
            owner=owner_name, repo=repo_name, pull_number=pull_number, token=token
        ):
            body = f"Process stopped: Pull request #{pull_number} was closed during execution."
            print(body)
            if comment_url:
                update_comment(body=body, base_args=base_args)
            break

        if not check_branch_exists(
            owner=owner_name, repo=repo_name, branch_name=head_branch, token=token
        ):
            body = f"Process stopped: Branch '{head_branch}' has been deleted"
            print(body)
            if comment_url:
                update_comment(body=body, base_args=base_args)
            break

        # Explore repo
        (
            messages,
            previous_calls,
            _tool_name,
            _tool_args,
            _token_input,
            _token_output,
            is_explored,
            p,
        ) = chat_with_agent(
            messages=messages,
            trigger=trigger,
            repo_settings=repo_settings,
            base_args=base_args,
            mode="get",  # explore can not be used here because "search_remote_file_contents" can search files only in the default branch NOT in the branch that is merged into the default branch
            previous_calls=previous_calls,
            p=p,
            log_messages=log_messages,
        )

        # Commit changes based on the exploration information
        (
            messages,
            previous_calls,
            _tool_name,
            _tool_args,
            _token_input,
            _token_output,
            is_committed,
            p,
        ) = chat_with_agent(
            messages=messages,
            trigger=trigger,
            repo_settings=repo_settings,
            base_args=base_args,
            mode="commit",
            previous_calls=previous_calls,
            p=p,
            log_messages=log_messages,
        )

        # If no new file is found and no changes are made, it means that the agent has completed the ticket or got stuck for some reason
        if not is_explored and not is_committed:
            break

        # If no files are found but changes are made, it might fall into an infinite loop (e.g., repeatedly making and reverting similar changes with slight variations)
        if not is_explored and is_committed:
            retry_count += 1
            if retry_count > 3:
                break
            continue

        # If files are found but no changes are made, it means that the agent found files but didn't think it's necessary to commit changes or fell into an infinite-like loop (e.g. slightly different searches)
        if is_explored and not is_committed:
            retry_count += 1
            if retry_count > 3:
                break
            continue

        # Because the agent is committing changes, keep doing the loop
        retry_count = 0

    # Trigger final test workflows with an empty commit
    comment_body = "Creating final empty commit to trigger workflows..."
    update_comment(body=comment_body, base_args=base_args)
    create_empty_commit(base_args=base_args)

    # Create final message
    final_msg = f"Finished fixing the `{check_run_name}` check run error!"
    update_comment(body=final_msg, base_args=base_args)

    # Update usage record
    end_time = time.time()
    update_usage(
        usage_id=usage_id,
        token_input=0,
        token_output=0,
        total_seconds=int(end_time - current_time),
        pr_number=pull_number,
        is_completed=True,
    )

    # End notification
    slack_notify("Completed", thread_ts)
