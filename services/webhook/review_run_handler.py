# Standard imports
import asyncio
from datetime import datetime
import json
from pathlib import Path
import time

# Third-party imports
from anthropic.types import MessageParam

# Local imports
from config import GITHUB_APP_USER_NAME
from constants.agent import MAX_ITERATIONS
from constants.triggers import ReviewTrigger
from payloads.github.pull_request_review_comment.types import (
    PullRequestReviewCommentPayload,
)
from services.agents.verify_task_is_complete import verify_task_is_complete
from services.agents.verify_task_is_ready import verify_task_is_ready
from services.chat_with_agent import chat_with_agent
from services.efs.get_efs_dir import get_efs_dir
from services.node.ensure_node_packages import ensure_node_packages
from services.node.set_npm_token_env import set_npm_token_env
from services.php.ensure_php_packages import ensure_php_packages
from services.git.get_clone_dir import get_clone_dir
from services.git.get_clone_url import get_clone_url
from services.git.git_clone_to_efs import clone_tasks, git_clone_to_efs
from services.git.prepare_repo_for_work import prepare_repo_for_work
from services.github.comments.reply_to_comment import reply_to_comment
from services.github.comments.update_comment import update_comment
from services.github.commits.create_empty_commit import create_empty_commit
from services.github.files.get_local_file_content import get_local_file_content
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.pulls.get_review_thread_comments import get_review_thread_comments
from services.github.token.get_installation_token import get_installation_access_token
from services.github.users.get_email_from_commits import get_email_from_commits
from services.github.users.get_user_public_email import get_user_public_info
from services.github.trees.get_local_file_tree import get_local_file_tree
from services.github.types.github_types import ReviewBaseArgs
from services.claude.tools.tools import TOOLS_FOR_PRS
from services.supabase.create_user_request import create_user_request
from services.supabase.repositories.get_repository import get_repository
from services.supabase.usage.update_usage import update_usage
from services.webhook.utils.create_system_message import create_system_message
from services.webhook.utils.should_bail import should_bail
from utils.logging.add_log_message import add_log_message
from utils.logging.logging_config import logger, set_pr_number, set_trigger
from utils.memory.gc_collect_and_log import gc_collect_and_log
from utils.progress_bar.progress_bar import create_progress_bar


async def handle_review_run(
    payload: PullRequestReviewCommentPayload,
    trigger: ReviewTrigger,
    lambda_info: dict[str, str | None] | None = None,
):
    current_time = time.time()
    set_trigger(trigger)

    # Extract review comment etc
    review = payload["comment"]
    review_id = review["id"]
    review_node_id = review["node_id"]
    review_path = review["path"]
    review_subject_type = review["subject_type"]
    review_line = review["line"]
    review_side = review["side"]
    # review_position: int = review["position"]
    review_body = review["body"]

    comment_author = review["user"]
    comment_author_type = comment_author["type"]
    if comment_author_type == "Bot":
        return

    # Extract repository related variables
    repo = payload["repository"]
    repo_id = repo["id"]
    repo_name = repo["name"]
    is_fork = repo["fork"]

    # Extract owner related variables
    owner = repo["owner"]
    owner_type = owner["type"]
    owner_id = owner["id"]
    owner_name = owner["login"]
    set_npm_token_env(owner_id)

    # Extract PR related variables
    pull_request = payload["pull_request"]
    pr_number = pull_request["number"]
    set_pr_number(pr_number)
    pr_title = pull_request["title"]
    pr_body = pull_request["body"]
    pr_url = pull_request["url"]
    pr_file_url = f"{pr_url}/files"
    head_branch = pull_request["head"]["ref"]  # gitauto/dashboard-20250101-155924-Ab1C
    base_branch = pull_request["base"]["ref"]  # main, master, etc.
    pr_creator = pull_request["user"]["login"]
    if pr_creator != GITHUB_APP_USER_NAME:
        return

    # Extract sender related variables and return if sender is GitAuto itself
    sender_id: int = payload["sender"]["id"]
    sender_name: str = payload["sender"]["login"]
    if sender_name == GITHUB_APP_USER_NAME:
        return

    # Extract other information
    installation_id: int = payload["installation"]["id"]
    token = get_installation_access_token(installation_id=installation_id)
    sender_info = get_user_public_info(username=sender_name, token=token)
    if not sender_info.email:
        email = get_email_from_commits(
            owner=owner_name, repo=repo_name, username=sender_name, token=token
        )
        if email:
            sender_info.email = email

    # Get all comments in the review thread
    thread_comments = get_review_thread_comments(
        owner=owner_name,
        repo=repo_name,
        pr_number=pr_number,
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

    clone_dir = get_clone_dir(owner_name, repo_name, pr_number)
    base_args: ReviewBaseArgs = {
        # Required fields
        "owner_type": owner_type,
        "owner_id": owner_id,
        "owner": owner_name,
        "repo_id": repo_id,
        "repo": repo_name,
        "clone_url": repo["clone_url"],
        "is_fork": is_fork,
        "pr_number": pr_number,
        "pr_comments": [],
        "latest_commit_sha": pull_request["head"]["sha"],
        "base_branch": head_branch,  # Yes, intentionally set head_branch to base_branch because get_file_tree requires the base branch
        "new_branch": head_branch,
        "installation_id": installation_id,
        "token": token,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "sender_email": sender_info.email,
        "sender_display_name": sender_info.display_name,
        "is_automation": False,
        "reviewers": [],
        "github_urls": [],
        "other_urls": [],
        "clone_dir": clone_dir,
        "pr_title": pr_title,
        "pr_body": pr_body or "",
        "pr_creator": pr_creator,
        "pr_url": pr_url,
        "pr_file_url": pr_file_url,
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
        git_clone_to_efs(efs_dir, clone_url, base_branch)
    )
    node_ready = await ensure_node_packages(
        owner_name, owner_id, repo_name, base_branch, token, efs_dir
    )
    logger.info("node: ready=%s", node_ready)

    php_ready = await ensure_php_packages(
        owner_name, owner_id, repo_name, base_branch, token, efs_dir
    )
    logger.info("php: ready=%s", php_ready)

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
        trigger="review_comment",
        email=sender_info.email,
        display_name=sender_info.display_name,
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
    review_file = get_local_file_content(file_path=review_path, base_args=base_args)
    p += 5
    add_log_message(f"Read the file `{review_path}` you commented on.", log_messages)
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    # Get list of changed files in the PR (filenames only, not contents)
    pr_files = get_pull_request_files(
        owner=owner_name, repo=repo_name, pr_number=pr_number, token=token
    )
    p += 5
    add_log_message(f"Found {len(pr_files)} changed files in the PR.", log_messages)
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    # Validate files for syntax issues before editing
    files_to_validate = [f["filename"] for f in pr_files if f["status"] != "removed"]
    validation_result = await verify_task_is_ready(
        base_args=base_args,
        file_paths=files_to_validate,
        run_tsc=True,
        run_jest=True,
        run_phpunit=True,
    )
    base_args["baseline_tsc_errors"] = set(validation_result.tsc_errors)
    pre_existing_errors = ""
    if validation_result.errors:
        pre_existing_errors = "\n".join(validation_result.errors)
        logger.warning("Remaining errors:\n%s", pre_existing_errors)
    fixes_applied = validation_result.fixes_applied

    # Build allowed_to_edit_files from PR changed files and validation errors
    allowed_to_edit_files = set(validation_result.files_with_errors)
    for file_change in pr_files:
        allowed_to_edit_files.add(file_change["filename"])

    # Get repository settings
    repo_settings = get_repository(owner_id=owner_id, repo_id=repo_id)

    # Plan how to fix the error
    today = datetime.now().strftime("%Y-%m-%d")

    root_files = get_local_file_tree(base_args=base_args, dir_path="")
    target_dir: str | None = None
    target_dir_files: list[str] = []
    if review_path:
        parent = str(Path(review_path).parent)
        if parent != ".":
            target_dir = parent
            target_dir_files = get_local_file_tree(base_args=base_args, dir_path=parent)

    input_message = {
        "step_1_review_comment": review_comment,
        "pull_request_title": pr_title,
        "pull_request_body": pr_body,
        "review_file": review_file,
        "pr_files": pr_files,
        "today": today,
        "root_files": root_files,
        "target_dir": target_dir,
        "target_dir_files": target_dir_files,
    }
    if fixes_applied or pre_existing_errors:
        input_message["step_2_prettier_eslint_note"] = (
            "Before you start, we ran Prettier/ESLint --fix. "
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
            slack_thread_ts=None,
        ):
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
            allowed_to_edit_files=allowed_to_edit_files,
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

        # Force GC between rounds to free temporary objects (messages, diffs) and reduce Lambda OOM risk
        gc_collect_and_log()

    # Log if loop exhausted without completion and force verification
    if not is_completed:
        logger.warning(
            "Agent loop hit MAX_ITERATIONS (%d) without calling verify_task_is_complete. Forcing verification.",
            MAX_ITERATIONS,
        )
        final_result = await verify_task_is_complete(base_args=base_args)
        is_completed = final_result.success

    # Trigger final test workflows with an empty commit
    body = "Creating final empty commit to trigger workflows..."
    update_comment(body=body, base_args=base_args)
    create_empty_commit(base_args=base_args)

    # Create final message based on verification result
    if is_completed:
        msg = "Resolved your feedback! Looks good?"
    else:
        msg = "I tried to address your feedback but verification still shows errors. Please review the changes."
    update_comment(body=msg, base_args=base_args)

    # Update usage record
    end_time = time.time()
    if usage_id:
        update_usage(
            usage_id=usage_id,
            token_input=total_token_input,
            token_output=total_token_output,
            total_seconds=int(end_time - current_time),
            pr_number=pr_number,
            is_completed=True,
        )
    return
