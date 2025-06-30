# Standard imports
from datetime import datetime
import hashlib
import json
import time

# Local imports
from config import EMAIL_LINK, GITHUB_APP_USER_NAME, UTF8
from constants.urls import PRICING_URL
from services.chat_with_agent import chat_with_agent

# Local imports (GitHub)
from services.github.branches.check_branch_exists import check_branch_exists
from services.github.comments.create_comment import create_comment
from services.github.comments.update_comment import update_comment
from services.github.commits.create_empty_commit import create_empty_commit
from services.github.github_manager import get_remote_file_content
from services.github.pulls.get_pull_request import get_pull_request
from services.github.pulls.get_pull_request_file_changes import (
    get_pull_request_file_changes,
)
from services.github.pulls.is_pull_request_open import is_pull_request_open
from services.github.types.github_types import CheckRunCompletedPayload
from services.github.utils.create_permission_url import create_permission_url
from services.github.token.get_installation_token import get_installation_access_token
from services.github.trees.get_file_tree import get_file_tree
from services.github.types.check_run import CheckRun
from services.github.types.check_suite import CheckSuite
from services.github.types.pull_request import PullRequest
from services.github.types.repository import Repository
from services.github.workflow_runs.cancel_workflow_runs import cancel_workflow_runs
from services.github.workflow_runs.get_workflow_run_logs import get_workflow_run_logs
from services.github.workflow_runs.get_workflow_run_path import get_workflow_run_path

# Local imports (Supabase)
from services.supabase.owners_manager import get_stripe_customer_id
from services.supabase.repositories.get_repository import get_repository_settings
from services.supabase.usage.get_retry_pairs import get_retry_workflow_id_hash_pairs
from services.supabase.usage.update_retry_pairs import (
    update_retry_workflow_id_hash_pairs,
)

# Local imports (Others)
from services.webhook.utils.create_system_messages import create_system_messages
from utils.progress_bar.progress_bar import create_progress_bar
from utils.time.is_lambda_timeout_approaching import is_lambda_timeout_approaching
from utils.time.get_timeout_message import get_timeout_message


def handle_check_run(payload: CheckRunCompletedPayload) -> None:
    current_time = time.time()

    # Extract workflow run id
    check_run: CheckRun = payload["check_run"]
    details_url = check_run["details_url"]
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
    base_args: dict[str, str | int | bool] = {
        "owner_type": owner_type,
        "owner_id": owner_id,
        "owner": owner_name,
        "repo": repo_name,
        "repo_id": repo_id,
        "is_fork": is_fork,
        "issue_number": pull_number,
        "new_branch": head_branch,
        "base_branch": head_branch,  # Yes, intentionally set head_branch to base_branch because get_file_tree requires the base branch
        "sender_id": sender_id,
        "sender_name": sender_name,
        "pull_number": pull_number,
        "workflow_id": workflow_id,
        "check_run_name": check_run_name,
        "token": token,
        "skip_ci": True,
    }
    # Print who, what, and where
    print(
        f"`GitAuto is fixing a Check Run error for `#{pull_number}` in `{owner_name}/{repo_name}`"
    )

    # Create the first comment
    p = 0
    log_messages = []
    msg = "Oops! Check run stumbled."
    log_messages.append(msg)
    body = create_progress_bar(p=p, msg="\n".join(log_messages))
    comment_url = create_comment(body=body, base_args=base_args)
    base_args["comment_url"] = comment_url

    # Return here if stripe_customer_id is not found
    stripe_customer_id = get_stripe_customer_id(owner_id=owner_id)
    if stripe_customer_id is None:
        msg = f"Subscribe [here]({PRICING_URL}) to get GitAuto to self-correct check run errors."
        log_messages.append(msg)
        update_comment(body="\n".join(log_messages), base_args=base_args)
        return

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

    # Get the GitHub workflow file content
    workflow_path = get_workflow_run_path(
        owner=owner_name, repo=repo_name, run_id=workflow_id, token=token
    )
    permission_url = create_permission_url(
        owner_type=owner_type, owner_name=owner_name, installation_id=installation_id
    )
    if workflow_path == 404:
        comment_body = f"Approve permission(s) to allow GitAuto to access the check run logs here: {permission_url}"
        log_messages.append(comment_body)
        update_comment(body="\n".join(log_messages), base_args=base_args)
        return

    workflow_content = get_remote_file_content(
        file_path=workflow_path, base_args=base_args
    )
    p += 5
    log_messages.append(
        f"Checked out the GitHub Action workflow file. `{workflow_path}`"
    )
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    # Get the file tree in the root of the repo
    file_tree: str = get_file_tree(base_args=base_args)
    p += 5
    log_messages.append("Checked out the file tree in the repo.")
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    # Get the error log from the workflow run
    error_log: str | int | None = get_workflow_run_logs(
        owner=owner_name, repo=repo_name, run_id=workflow_id, token=token
    )
    if error_log == 404:
        comment_body = f"Approve permission(s) to allow GitAuto to access the check run logs here: {permission_url}"
        log_messages.append(comment_body)
        update_comment(body="\n".join(log_messages), base_args=base_args)
        return
    if error_log is None:
        comment_body = f"I couldn't find the error log. Contact {EMAIL_LINK} if the issue persists."
        log_messages.append(comment_body)
        update_comment(body="\n".join(log_messages), base_args=base_args)
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

    # Get repository settings
    repo_settings = get_repository_settings(repo_id=repo_id)

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
    system_messages = create_system_messages(repo_settings=repo_settings)
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
            system_messages=system_messages,
            base_args=base_args,
            mode="get",  # explore can not be used here because "search_remote_file_contents" can search files only in the default branch NOT in the branch that is merged into the default branch
            previous_calls=previous_calls,
            p=p,
            log_messages=log_messages,
        )

        # Search Google
        # (
        #     messages,
        #     previous_calls,
        #     _tool_name,
        #     _tool_args,
        #     _token_input,
        #     _token_output,
        #     _is_searched,
        #     p,
        # ) = chat_with_agent(
        #     messages=messages,
        #     system_messages=system_messages,
        #     base_args=base_args,
        #     mode="search",
        #     previous_calls=previous_calls,
        #     p=p,
        #     log_messages=log_messages,
        # )

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
            system_messages=system_messages,
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
    body = "Creating final empty commit to trigger workflows..."
    update_comment(body=body, base_args=base_args)
    create_empty_commit(base_args)

    # Create a pull request to the base branch
    msg = f"Committed the Check Run `{check_run_name}` error fix! Running it again."
    update_comment(body=msg, base_args=base_args)
    return
