# Standard imports
import asyncio
from datetime import datetime
import json
from pathlib import Path
import time
from typing import Any

# Local imports
from config import GITHUB_APP_USER_NAME
from constants.agent import MAX_ITERATIONS
from services.chat_with_agent import chat_with_agent
from services.efs.start_async_install_on_efs import start_async_install_on_efs
from services.github.branches.check_branch_exists import check_branch_exists
from services.github.comments.reply_to_comment import reply_to_comment
from services.github.comments.update_comment import update_comment
from services.github.commits.create_empty_commit import create_empty_commit
from services.github.files.get_remote_file_content import get_remote_file_content
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.pulls.get_review_thread_comments import get_review_thread_comments
from services.github.pulls.is_pull_request_open import is_pull_request_open
from services.github.token.get_installation_token import get_installation_access_token
from services.github.trees.get_file_tree_list import get_file_tree_list
from services.github.types.github_types import ReviewBaseArgs
from services.github.types.owner import Owner
from services.github.types.pull_request import PullRequest
from services.github.types.repository import Repository
from services.git.clone_repo import clone_repo
from services.git.get_clone_dir import get_clone_dir
from services.openai.functions.functions import TOOLS_FOR_PRS
from services.supabase.create_user_request import create_user_request
from services.supabase.repositories.get_repository import get_repository
from services.supabase.usage.update_usage import update_usage
from utils.logging.add_log_message import add_log_message
from utils.logging.logging_config import logger, set_pr_number, set_trigger
from utils.progress_bar.progress_bar import create_progress_bar
from utils.time.is_lambda_timeout_approaching import is_lambda_timeout_approaching
from utils.time.get_timeout_message import get_timeout_message


async def handle_review_run(
    payload: dict[str, Any], lambda_info: dict[str, str | None] | None = None
):
    current_time = time.time()
    trigger = "review_comment"
    set_trigger(trigger)

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
    set_pr_number(pull_number)
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

    # Clone repo to tmp and install dependencies to efs (both fire-and-forget, run in parallel)
    base_args["clone_dir"] = get_clone_dir(owner_name, repo_name, pull_number)
    asyncio.create_task(
        clone_repo(owner_name, repo_name, pull_number, head_branch, token)
    )
    start_async_install_on_efs(base_args)

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
    add_log_message(msg, log_messages)
    comment_body = create_progress_bar(p=0, msg="\n".join(log_messages))
    comment_url = reply_to_comment(base_args=base_args, body=comment_body)
    base_args["comment_url"] = comment_url

    # Get a review commented file
    review_file = get_remote_file_content(file_path=review_path, base_args=base_args)
    p += 5
    add_log_message(f"Read the file `{review_path}` you commented on.", log_messages)
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    # Get list of changed files in the PR (filenames only, not contents)
    pull_files = get_pull_request_files(
        owner=owner_name, repo=repo_name, pull_number=pull_number, token=token
    )
    p += 5
    add_log_message(f"Found {len(pull_files)} changed files in the PR.", log_messages)
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    # Get repository settings
    repo_settings = get_repository(owner_id=owner_id, repo_id=repo_id)

    # Plan how to fix the error
    today = datetime.now().strftime("%Y-%m-%d")

    root_files = get_file_tree_list(base_args=base_args, dir_path="")
    target_dir: str | None = None
    target_dir_files: list[str] = []
    if review_path:
        parent = str(Path(review_path).parent)
        if parent != ".":
            target_dir = parent
            target_dir_files = get_file_tree_list(base_args=base_args, dir_path=parent)

    input_message = {
        "pull_request_title": pull_title,
        "pull_request_body": pull_body,
        "review_comment": review_comment,
        "review_file": review_file,
        "pull_files": pull_files,
        "today": today,
        "root_files": root_files,
        "target_dir": target_dir,
        "target_dir_files": target_dir_files,
    }
    user_input = json.dumps(obj=input_message)

    # Create messages
    messages = [{"role": "user", "content": user_input}]

    # Loop a process explore repo and commit changes until the ticket is resolved
    total_token_input = 0
    total_token_output = 0
    is_completed = False

    for _iteration in range(MAX_ITERATIONS):
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
            logger.info(body)
            if comment_url:
                update_comment(body=body, base_args=base_args)
            break

        if not check_branch_exists(
            owner=owner_name, repo=repo_name, branch_name=head_branch, token=token
        ):
            body = f"Process stopped: Branch '{head_branch}' has been deleted"
            logger.info(body)
            if comment_url:
                update_comment(body=body, base_args=base_args)
            break

        # Call the agent to explore the codebase and commit changes
        (
            messages,
            token_input,
            token_output,
            is_completed,
            p,
        ) = await chat_with_agent(
            messages=messages,
            trigger=trigger,
            repo_settings=repo_settings,
            base_args=base_args,
            p=p,
            log_messages=log_messages,
            usage_id=usage_id,
            tools=TOOLS_FOR_PRS,
        )
        total_token_input += token_input
        total_token_output += token_output

        if is_completed:
            logger.info(
                "Agent signaled completion via verify_task_is_complete, breaking loop"
            )
            break

    # Log if loop exhausted without completion
    if not is_completed:
        logger.warning("Agent loop ended without calling verify_task_is_complete")

    # Trigger final test workflows with an empty commit
    body = "Creating final empty commit to trigger workflows..."
    update_comment(body=body, base_args=base_args)
    create_empty_commit(base_args=base_args)

    # Create a pull request to the base branch
    msg = "Resolved your feedback! Looks good?"
    update_comment(body=msg, base_args=base_args)

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
        )
    return
