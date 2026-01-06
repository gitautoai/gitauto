from datetime import datetime
import json
import time
from typing import Any

# Local imports
from config import GITHUB_APP_USER_NAME
from services.chat_with_agent import chat_with_agent
from services.github.types.github_types import ReviewBaseArgs

# Local imports (GitHub)
from services.github.branches.check_branch_exists import check_branch_exists
from services.github.comments.reply_to_comment import reply_to_comment
from services.github.comments.update_comment import update_comment
from services.github.commits.create_empty_commit import create_empty_commit
from services.github.files.get_remote_file_content import get_remote_file_content
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.pulls.get_review_thread_comments import get_review_thread_comments
from services.github.pulls.is_pull_request_open import is_pull_request_open
from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.owner import Owner
from services.github.types.pull_request import PullRequest
from services.github.types.repository import Repository

# Local imports (Supabase)
from services.supabase.create_user_request import create_user_request
from services.supabase.repositories.get_repository import get_repository
from services.supabase.usage.update_usage import update_usage

# Local imports (Utils)
from utils.progress_bar.progress_bar import create_progress_bar
from utils.time.is_lambda_timeout_approaching import is_lambda_timeout_approaching
from utils.time.get_timeout_message import get_timeout_message


def handle_review_run(
    payload: dict[str, Any], lambda_info: dict[str, str | None] | None = None
):
    current_time = time.time()
    trigger = "review_comment"

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

    comment_author: dict[str, Any] = review["user"]
    comment_author_type: str = comment_author["type"]
    if comment_author_type == "Bot":
        return

    # Extract repository related variables
    repo: Repository = payload["repository"]
    repo_id: int = repo["id"]
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
        return

    # Extract sender related variables and return if sender is GitAuto itself
    sender_id: int = payload["sender"]["id"]
    sender_name: str = payload["sender"]["login"]
    if sender_name == GITHUB_APP_USER_NAME:
        return

    # Extract other information
    installation_id: int = payload["installation"]["id"]
    token = get_installation_access_token(installation_id=installation_id)
    if not token:
        raise ValueError(
            f"No token for installation {installation_id} ({owner_name}/{repo_name})"
        )

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

    base_args: ReviewBaseArgs = {
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
        "issue_body": pull_body or "",
        "issue_comments": [],
        "latest_commit_sha": pull_request["head"]["sha"],
        "issuer_name": sender_name,
        "base_branch": head_branch,  # Yes, intentionally set head_branch to base_branch because get_file_tree requires the base branch
        "new_branch": head_branch,
        "installation_id": installation_id,
        "token": token,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "sender_email": f"{sender_name}@users.noreply.github.com",
        "is_automation": False,
        "reviewers": [],
        "github_urls": [],
        "other_urls": [],
        # Extra fields for backward compatibility
        "pull_number": pull_number,
        "pull_title": pull_title,
        "pull_body": pull_body,
        "pull_url": pull_url,
        "pull_file_url": pull_file_url,
        "review_id": review_id,
        "review_path": review_path,
        "review_subject_type": review_subject_type,
        "review_line": review_line,
        "review_side": review_side,
        # "review_position": review_position,
        "review_body": review_body,
        "review_comment": review_comment,
        "skip_ci": True,
    }

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
        trigger="review_comment",
        email=None,
        lambda_info=lambda_info,
    )

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

    # Get list of changed files in the PR (filenames only, not contents)
    pull_files = get_pull_request_files(url=pull_file_url, token=token)
    p += 5
    log_messages.append(f"Found {len(pull_files)} changed files in the PR.")
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    # Get repository settings
    repo_settings = get_repository(owner_id=owner_id, repo_id=repo_id)

    # Plan how to fix the error
    today = datetime.now().strftime("%Y-%m-%d")
    input_message = {
        "pull_request_title": pull_title,
        "pull_request_body": pull_body,
        "review_comment": review_comment,
        "review_file": review_file,
        "pull_files": pull_files,
        "today": today,
    }
    user_input = json.dumps(obj=input_message)

    # Create messages
    messages = [{"role": "user", "content": user_input}]

    # Loop a process explore repo and commit changes until the ticket is resolved
    previous_calls = []
    retry_count = 0
    total_token_input = 0
    total_token_output = 0
    while True:
        # Timeout check: Stop if we're approaching Lambda limit
        is_timeout_approaching, elapsed_time = is_lambda_timeout_approaching(
            current_time
        )
        if is_timeout_approaching:
            timeout_msg = get_timeout_message(elapsed_time, "Review run processing")
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
            token_input,
            token_output,
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
            usage_id=usage_id,
        )
        total_token_input += token_input
        total_token_output += token_output

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
        #     trigger=trigger,
        #     repo_settings=repo_settings,
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
            token_input,
            token_output,
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
            usage_id=usage_id,
        )
        total_token_input += token_input
        total_token_output += token_output

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
    create_empty_commit(base_args=base_args)

    # Create a pull request to the base branch
    msg = "Resolved your feedback! Looks good?"
    update_comment(body=msg, base_args=base_args)

    # Update usage record
    end_time = time.time()
    update_usage(
        usage_id=usage_id,
        token_input=total_token_input,
        token_output=total_token_output,
        total_seconds=int(end_time - current_time),
        pr_number=pull_number,
        is_completed=True,
    )
    return
