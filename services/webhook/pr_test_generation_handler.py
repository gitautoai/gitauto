# Standard imports
import json
from datetime import datetime
import time
from typing import Any

# Local imports
from config import PRODUCT_ID, GITHUB_APP_USER_NAME
from services.chat_with_agent import chat_with_agent

# Local imports (GitHub)
from services.github.branches.check_branch_exists import check_branch_exists
from services.github.comments.create_comment import create_comment
from services.github.comments.update_comment import update_comment
from services.github.commits.create_empty_commit import create_empty_commit
from services.github.pulls.get_pull_request import get_pull_request
from services.github.pulls.is_pull_request_open import is_pull_request_open
from services.github.token.get_installation_token import get_installation_access_token
from services.github.trees.get_file_tree import get_file_tree
from services.github.workflow_runs.cancel_workflow_runs import cancel_workflow_runs

# Local imports (Supabase & Webhook)
from services.supabase.repositories.get_repository import get_repository_settings
from services.supabase.usage.is_request_limit_reached import is_request_limit_reached
from services.webhook.utils.create_system_messages import create_system_messages
from services.webhook.utils.extract_selected_files import extract_selected_files

# Local imports (Utils)
from utils.error.handle_exceptions import handle_exceptions
from utils.progress_bar.progress_bar import create_progress_bar
from utils.prompts.push_trigger import PUSH_TRIGGER_SYSTEM_PROMPT
from utils.text.text_copy import request_limit_reached
from utils.time.is_lambda_timeout_approaching import is_lambda_timeout_approaching
from utils.time.get_timeout_message import get_timeout_message


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def handle_pr_test_generation(payload: dict[str, Any]) -> None:
    current_time = time.time()

    # Skip if the comment editor is a bot
    sender = payload["sender"]
    sender_id = sender["id"]
    sender_name = sender["login"]
    if sender_name.endswith("[bot]"):
        return

    # Skip if the comment author is not GitAuto
    comment = payload["comment"]
    if comment["user"]["login"] != GITHUB_APP_USER_NAME:
        return

    search_text = "- [x] Generate Tests"
    if PRODUCT_ID != "gitauto":
        search_text += f" - {PRODUCT_ID}"

    # Skip if the comment body does not contain the search text
    comment_body = comment["body"]
    if search_text not in comment_body:
        return

    # Skip if no files are selected
    selected_files = extract_selected_files(comment_body)
    if not selected_files:
        return

    repository = payload["repository"]
    repo_id = repository["id"]
    repo_name = repository["name"]
    owner_name = repository["owner"]["login"]
    owner_type = repository["owner"]["type"]
    owner_id = repository["owner"]["id"]
    installation_id = payload["installation"]["id"]
    token = get_installation_access_token(installation_id=installation_id)

    issue_number = payload["issue"]["number"]

    # Check if the user has reached the request limit
    is_limit_reached, _requests_left, request_limit, end_date = (
        is_request_limit_reached(
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
            owner_type=owner_type,
            repo_name=repo_name,
            issue_number=issue_number,
        )
    )

    # If request limit is reached, create a comment and return early
    if is_limit_reached:
        body = request_limit_reached(
            user_name=sender_name, request_count=request_limit, end_date=end_date
        )

        base_args = {
            "owner": owner_name,
            "repo": repo_name,
            "issue_number": issue_number,
            "token": token,
        }

        create_comment(body=body, base_args=base_args)
        return

    pr_data = get_pull_request(
        owner=owner_name, repo=repo_name, pull_number=issue_number, token=token
    )
    branch_name = pr_data["head"]["ref"]  # Set the source branch (from)

    # Cancel existing workflow runs since we'll be making new commits
    cancel_workflow_runs(
        owner=owner_name, repo=repo_name, branch=branch_name, token=token
    )

    repo_settings = get_repository_settings(repo_id=repo_id)

    base_args = {
        "owner_type": owner_type,
        "owner_id": owner_id,
        "owner": owner_name,
        "repo": repo_name,
        "repo_id": repo_id,
        "is_fork": repository.get("fork", False),
        "issue_number": issue_number,
        "pull_number": issue_number,
        "new_branch": branch_name,
        "base_branch": branch_name,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "token": token,
        "skip_ci": True,
    }

    p = 0
    log_messages = []
    msg = f"Generating tests for {len(selected_files)} selected files."
    log_messages.append(msg)

    comment_body = create_progress_bar(p=0, msg="\n".join(log_messages))
    comment_url = create_comment(body=comment_body, base_args=base_args)
    base_args["comment_url"] = comment_url

    p += 10
    log_messages.append("Getting repository file tree.")
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    file_tree, tree_comment = get_file_tree(base_args=base_args)
    p += 10
    log_messages.append(tree_comment)
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    today = datetime.now().strftime("%Y-%m-%d")

    input_message = {
        "selected_files": selected_files,
        "file_tree": file_tree,
        "today": today,
    }

    system_messages = create_system_messages(repo_settings=repo_settings)
    system_messages = [
        {"role": "system", "content": PUSH_TRIGGER_SYSTEM_PROMPT}
    ] + system_messages

    messages = [{"role": "user", "content": json.dumps(input_message)}]

    previous_calls = []
    retry_count = 0
    while True:
        # Timeout check: Stop if we're approaching Lambda limit
        is_timeout_approaching, elapsed_time = is_lambda_timeout_approaching(
            current_time
        )
        if is_timeout_approaching:
            timeout_msg = get_timeout_message(
                elapsed_time, "PR test generation processing"
            )
            update_comment(body=timeout_msg, base_args=base_args)
            break

        # Safety check: Stop if PR is closed or branch is deleted
        if not is_pull_request_open(
            owner=owner_name, repo=repo_name, pull_number=issue_number, token=token
        ):
            body = f"Process stopped: Pull request #{issue_number} was closed during execution."
            print(body)
            update_comment(body=body, base_args=base_args)
            break

        if not check_branch_exists(
            owner=owner_name, repo=repo_name, branch_name=branch_name, token=token
        ):
            body = f"Process stopped: Branch '{branch_name}' has been deleted"
            print(body)
            update_comment(body=body, base_args=base_args)
            break

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
            mode="get",
            previous_calls=previous_calls,
            p=p,
            log_messages=log_messages,
        )

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

        if not is_explored and not is_committed:
            break

        if not is_explored and is_committed:
            retry_count += 1
            if retry_count > 3:
                break
            continue

        if is_explored and not is_committed:
            retry_count += 1
            if retry_count > 3:
                break
            continue

        retry_count = 0

    body = "Creating final empty commit to trigger workflows..."
    update_comment(body=body, base_args=base_args)
    create_empty_commit(base_args)

    final_msg = "Finished generating tests for selected files!"
    update_comment(body=final_msg, base_args=base_args)
