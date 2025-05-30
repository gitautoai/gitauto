from datetime import datetime
import json
from typing import Any

# Local imports
from config import (
    EXCEPTION_OWNERS,
    GITHUB_APP_USER_NAME,
    STRIPE_PRODUCT_ID_FREE,
)
from services.chat_with_agent import chat_with_agent
from services.github.comment_manager import reply_to_comment
from services.github.comments.update_comment import update_comment
from services.github.github_manager import get_remote_file_content, get_remote_file_tree
from services.github.pulls_manager import (
    get_pull_request_file_contents,
    get_review_thread_comments,
)
from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.owner import Owner
from services.github.types.pull_request import PullRequest
from services.github.types.repository import Repository
from services.stripe.subscriptions import get_stripe_product_id
from services.supabase.owners_manager import get_stripe_customer_id
from utils.colors.colorize_log import colorize
from utils.progress_bar.progress_bar import create_progress_bar


def handle_review_run(payload: dict[str, Any]) -> None:
    print("handle_review_run was called")

    # Extract review comment etc
    review: dict[str, Any] = payload["comment"]
    review_id: int = review["id"]
    review_node_id: str = review["node_id"]
    review_path: str = review["path"]
    review_subject_type: str = review["subject_type"]
    review_line: int = review["line"]
    review_side: str = review["side"]
    # review_position: int = review["position"]
    review_body: str = review["body"]

    # Extract repository related variables
    repo: Repository = payload["repository"]
    repo_name: str = repo["name"]
    is_fork: bool = repo["fork"]

    # Extract owner related variables
    owner: Owner = repo["owner"]
    owner_type: str = owner["type"]
    owner_id: int = owner["id"]
    owner_name: str = owner["login"]

    # Extract PR related variables
    pull_request: PullRequest = payload["pull_request"]
    pull_number: int = pull_request["number"]
    pull_title: str = pull_request["title"]
    pull_body: str = pull_request["body"]
    pull_url: str = pull_request["url"]
    pull_file_url: str = f"{pull_url}/files"
    head_branch: str = pull_request["head"]["ref"]  # gitauto/issue-167-20250101-155924
    pull_user: str = pull_request["user"]["login"]
    if pull_user != GITHUB_APP_USER_NAME:
        print(
            f"Skipping because pull_user is not GitAuto. pull_user: {pull_user} for owner_id: {owner_id}"
        )
        return  # Prevent GitAuto from jumping into others' PRs

    # Extract sender related variables and return if sender is GitAuto itself
    sender_id: int = payload["sender"]["id"]
    sender_name: str = payload["sender"]["login"]
    if sender_name == GITHUB_APP_USER_NAME:
        print(
            f"Skipping because sender is GitAuto itself. sender_name: {sender_name} for owner_id: {owner_id}"
        )
        return  # Prevent infinite loops by self-triggering

    print(f"Payload: {json.dumps(payload, indent=2)}")

    # Extract other information
    installation_id: int = payload["installation"]["id"]
    token: str = get_installation_access_token(installation_id=installation_id)

    # Get all comments in the review thread
    thread_comments = get_review_thread_comments(
        owner=owner_name,
        repo=repo_name,
        pull_number=pull_number,
        comment_node_id=review_node_id,
        token=token,
    )

    # Combine all comments in chronological order for context
    review_comment = f"## Review thread on {review_path} Line: {review_line}\n"
    if thread_comments:
        for comment in thread_comments:
            author = comment["author"]["login"]
            body = comment["body"]
            created_at = comment["createdAt"]
            review_comment += f"{author} commented at {created_at}: {body}\n"
    else:
        # Fallback to single comment if thread fetch fails
        review_comment += f"{review_body}"
    # print(f"review_comment: {review_comment}")

    base_args: dict[str, str | int | bool] = {
        "owner_type": owner_type,
        "owner_id": owner_id,
        "owner": owner_name,
        "repo": repo_name,
        "is_fork": is_fork,
        "issue_number": pull_number,
        "pull_number": pull_number,
        "pull_title": pull_title,
        "pull_body": pull_body,
        "pull_url": pull_url,
        "pull_file_url": pull_file_url,
        "new_branch": head_branch,
        "base_branch": head_branch,  # Yes, intentionally set head_branch to base_branch because get_remote_file_tree requires the base branch
        "review_id": review_id,
        "review_path": review_path,
        "review_subject_type": review_subject_type,
        "review_line": review_line,
        "review_side": review_side,
        # "review_position": review_position,
        "review_body": review_body,
        "review_comment": review_comment,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "token": token,
    }

    # Return here if stripe_customer_id is not found
    stripe_customer_id: str | None = get_stripe_customer_id(owner_id=owner_id)
    if stripe_customer_id is None:
        print(f"Skipping because stripe_customer_id is not found. owner_id: {owner_id}")
        return

    # Return here if product_id is not found or is in free tier
    product_id: str | None = get_stripe_product_id(customer_id=stripe_customer_id)
    is_paid = product_id is not None and product_id != STRIPE_PRODUCT_ID_FREE
    is_exception = owner_name in EXCEPTION_OWNERS
    if not is_paid and not is_exception:
        msg = f"Skipping because product_id is not found or is in free tier. product_id: '{product_id}' for owner_id: {owner_id}"
        print(colorize(text=msg, color="yellow"))
        return

    # Greeting
    p = 0
    log_messages = []
    msg = "Thanks for the review! I'm on it."
    log_messages.append(msg)
    comment_body = create_progress_bar(p=0, msg="\n".join(log_messages))
    comment_url = reply_to_comment(base_args=base_args, body=comment_body)
    base_args["comment_url"] = comment_url

    # Get a review commented file
    review_file = get_remote_file_content(file_path=review_path, base_args=base_args)
    p += 5
    log_messages.append(f"Read the file `{review_path}` you commented on.")
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    # Get changed files in the PR
    pull_files = get_pull_request_file_contents(url=pull_file_url, base_args=base_args)
    p += 5
    log_messages.append(f"Read {len(pull_files)} changed files in the PR.")
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    # Get the file tree in the root of the repo
    file_tree, tree_comment = get_remote_file_tree(base_args=base_args)
    p += 5
    log_messages.append(tree_comment)
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    # Plan how to fix the error
    today = datetime.now().strftime("%Y-%m-%d")
    input_message: dict[str, str] = {
        "pull_request_title": pull_title,
        "pull_request_body": pull_body,
        "review_comment": review_comment,
        "review_file": review_file,
        "pull_files": pull_files,
        "file_tree": file_tree,
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
    msg = "Resolved your feedback! Looks good?"
    update_comment(body=msg, base_args=base_args)
    return
