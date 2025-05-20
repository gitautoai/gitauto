# Local imports
from datetime import datetime
import json
from config import (
    EMAIL_LINK,
    EXCEPTION_OWNERS,
    GITHUB_APP_USER_NAME,
    PRICING_URL,
    STRIPE_PRODUCT_ID_FREE,
)
from services.chat_with_agent import chat_with_agent
from services.github.actions_manager import get_workflow_run_logs, get_workflow_run_path
from services.github.comments.create_comment import create_comment
from services.github.comments.get_comments import get_comments
from services.github.comments.update_comment import update_comment
from services.github.github_manager import get_remote_file_content, get_remote_file_tree
from services.github.github_types import (
    CheckRun,
    CheckRunCompletedPayload,
    CheckSuite,
    Owner,
    PullRequest,
    Repository,
)
from services.github.pulls_manager import (
    get_pull_request,
    get_pull_request_file_changes,
)
from services.github.github_utils import create_permission_url
from services.github.token.get_installation_token import get_installation_access_token
from services.stripe.subscriptions import get_stripe_product_id
from services.supabase.owners_manager import get_stripe_customer_id
from utils.colors.colorize_log import colorize
from utils.progress_bar.progress_bar import create_progress_bar


def handle_check_run(payload: CheckRunCompletedPayload) -> None:
    # Extract workflow run id
    check_run: CheckRun = payload["check_run"]
    details_url: str = check_run["details_url"]
    workflow_run_id: str = details_url.split(sep="/")[-3]
    check_run_name: str = check_run["name"]

    # Extract repository related variables
    repo: Repository = payload["repository"]
    repo_name: str = repo["name"]
    is_fork: bool = repo.get("fork", False)

    # Extract owner related variables
    owner: Owner = repo.get("owner", {})
    if owner is None:
        msg = "Skipping because owner is not found"
        print(colorize(text=msg, color="yellow"))
        return
    owner_type: str = owner["type"]
    owner_id: int = owner["id"]
    owner_name: str = owner["login"]

    # Extract branch related variables
    check_suite: CheckSuite = check_run["check_suite"]
    head_branch: str = check_suite["head_branch"]

    # Extract sender related variables and return if sender is GitAuto itself
    sender_id: int = payload["sender"]["id"]
    sender_name: str = payload["sender"]["login"]
    if sender_name != GITHUB_APP_USER_NAME:
        msg = f"Skipping because sender is not GitAuto. sender_name: '{sender_name}' and GITHUB_APP_USER_NAME: '{GITHUB_APP_USER_NAME}'"
        print(colorize(text=msg, color="yellow"))
        return

    # Extract PR related variables and return if no PR is associated with this check run
    pull_requests: list[PullRequest] = check_run.get("pull_requests", [])
    if not pull_requests:
        msg = "Skipping because no pull request is associated with this check run"
        print(colorize(text=msg, color="yellow"))
        return
    pull_request: PullRequest = pull_requests[0]
    pull_number: int = pull_request["number"]
    pull_url: str = pull_request["url"]

    # Extract other information
    installation_id: int = payload["installation"]["id"]
    token: str = get_installation_access_token(installation_id=installation_id)
    base_args: dict[str, str | int | bool] = {
        "owner_type": owner_type,
        "owner_id": owner_id,
        "owner": owner_name,
        "repo": repo_name,
        "is_fork": is_fork,
        "issue_number": pull_number,
        "new_branch": head_branch,
        "base_branch": head_branch,  # Yes, intentionally set head_branch to base_branch because get_remote_file_tree requires the base branch
        "sender_id": sender_id,
        "sender_name": sender_name,
        "pull_number": pull_number,
        "workflow_run_id": workflow_run_id,
        "check_run_name": check_run_name,
        "token": token,
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

    # Return here if product_id is not found or is in free tier
    product_id = get_stripe_product_id(customer_id=stripe_customer_id)
    is_paid = product_id is not None and product_id != STRIPE_PRODUCT_ID_FREE
    is_exception = owner_name in EXCEPTION_OWNERS
    if not is_paid and not is_exception:
        msg = f"Subscribe [here]({PRICING_URL}) to get GitAuto to self-correct check run errors."
        log_messages.append(msg)
        update_comment(body="\n".join(log_messages), base_args=base_args)
        return

    # Return here if GitAuto has tried to fix this Check Run error before because we need to avoid infinite loops
    pr_comments = get_comments(
        issue_number=pull_number, base_args=base_args, includes_me=True
    )
    print(f"Check run name: {check_run_name}")
    if any(check_run_name in comment for comment in pr_comments):
        msg = f"Skipping `{check_run_name}` because GitAuto has tried to fix this Check Run error before"
        log_messages.append(msg)
        update_comment(body="\n".join(log_messages), base_args=base_args)
        return

    # Get title, body, and code changes in the PR
    pull_title, pull_body = get_pull_request(url=pull_url, token=token)
    pull_file_url = f"{pull_url}/files"
    pull_changes = get_pull_request_file_changes(url=pull_file_url, token=token)
    p += 5
    log_messages.append("Checked out the pull request title, body, and code changes.")
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    # Get the GitHub workflow file content
    workflow_path = get_workflow_run_path(
        owner=owner_name, repo=repo_name, run_id=workflow_run_id, token=token
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
    file_tree: str = get_remote_file_tree(base_args=base_args)
    p += 5
    log_messages.append("Checked out the file tree in the repo.")
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    # Get the error log from the workflow run
    error_log: str | int | None = get_workflow_run_logs(
        owner=owner_name, repo=repo_name, run_id=workflow_run_id, token=token
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
    messages = [{"role": "user", "content": user_input}]

    # Loop a process explore repo and commit changes until the ticket is resolved
    previous_calls = []
    retry_count = 0
    while True:
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

    # Create a pull request to the base branch
    msg = f"Committed the Check Run `{check_run_name}` error fix! Running it again."
    update_comment(body=msg, base_args=base_args)
    return
