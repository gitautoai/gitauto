# pylint: disable=too-many-locals, too-many-statements, too-many-branches

from datetime import datetime
import json
from typing import Any

# Local imports
from config import EXCEPTION_OWNERS, STRIPE_PRODUCT_ID_FREE
from services.chat_with_agent import chat_with_agent
from services.github.comments.create_comment import create_comment
from services.github.comments.update_comment import update_comment
from services.github.commits.get_commit_diff import get_commit_diff
from services.github.github_manager import get_remote_file_tree
from services.github.pull_requests.find_pull_request_by_branch import (
    find_pull_request_by_branch,
)
from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.owner import Owner
from services.github.types.repository import Repository
from services.stripe.subscriptions import get_stripe_product_id
from services.supabase.owners_manager import get_stripe_customer_id
from services.supabase.repositories.get_repository import get_repository_settings
from utils.colors.colorize_log import colorize
from utils.files.is_code_file import is_code_file
from utils.files.is_test_file import is_test_file
from utils.progress_bar.progress_bar import create_progress_bar
from utils.prompts.push_trigger import PUSH_TRIGGER_SYSTEM_PROMPT


def handle_push_event(payload: dict[str, Any]) -> None:
    print("handle_push_event was called")

    # Extract repository related variables
    repo: Repository = payload["repository"]
    repo_name: str = repo["name"]
    repo_id: int = repo["id"]
    is_fork: bool = repo["fork"]

    # Check repository settings for trigger_on_commit and rules
    repo_settings = get_repository_settings(repo_id=repo_id)
    if repo_settings and not repo_settings.get("trigger_on_commit", False):
        print(f"Skipping push event for {repo_name} - trigger_on_commit is disabled")
        return

    repo_rules = None
    if repo_settings and repo_settings.get("repo_rules", ""):
        repo_rules = repo_settings.get("repo_rules", "")

    # Extract owner related variables
    owner: Owner = repo["owner"]
    owner_type: str = owner["type"]
    owner_id: int = owner["id"]
    owner_name: str = owner["login"]

    # Extract push related variables
    ref: str = payload["ref"]  # refs/heads/branch-name
    branch_name: str = ref.replace("refs/heads/", "")
    commits: list[dict[str, Any]] = payload["commits"]
    head_commit: dict[str, Any] = payload["head_commit"]

    # Skip if no commits
    if not commits:
        print("Skipping because no commits found")
        return

    # Extract other information
    installation_id: int = payload["installation"]["id"]
    token: str = get_installation_access_token(installation_id=installation_id)

    # Get detailed commit changes with actual diffs
    commit_changes = []
    has_code_files = False
    for commit in commits:
        commit_diff = get_commit_diff(
            owner=owner_name, repo=repo_name, commit_sha=commit["id"], token=token
        )

        if not commit_diff:
            continue

        # Filter out test files and non-code files
        filtered_files = []
        for file in commit_diff["files"]:
            filename = file["filename"]
            if is_code_file(filename) and not is_test_file(filename):
                filtered_files.append(file)
                has_code_files = True

        if filtered_files:
            commit_info = {
                "commit_id": commit["id"],
                "commit_message": commit_diff["message"],
                "author": commit_diff["author"],
                "timestamp": commit.get("timestamp", ""),
                "files": filtered_files,  # Contains actual diff patches
            }
            commit_changes.append(commit_info)

    # If no code files after filtering, skip processing
    if not has_code_files:
        print("No non-test code files found in commits. Skipping test generation.")
        return

    print(f"Found {len(commit_changes)} commits with code changes that may need tests")

    # Extract sender related variables
    sender_id: int = payload["sender"]["id"]
    sender_name: str = payload["sender"]["login"]

    print(
        f"Push event from {sender_name} to {owner_name}/{repo_name} on branch {branch_name}"
    )

    # Find associated PR for this branch using GraphQL
    pull_request = find_pull_request_by_branch(
        owner=owner_name, repo=repo_name, branch_name=branch_name, token=token
    )
    pull_number = pull_request["number"] if pull_request else 0

    base_args: dict[str, str | int | bool] = {
        "owner_type": owner_type,
        "owner_id": owner_id,
        "owner": owner_name,
        "repo": repo_name,
        "repo_id": repo_id,
        "is_fork": is_fork,
        "issue_number": pull_number,
        "pull_number": pull_number,
        "new_branch": branch_name,
        "base_branch": branch_name,
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

    # Create initial comment (if we have a PR)
    p = 0
    log_messages = []
    msg = "New commits detected! Analyzing changes to add missing tests."
    log_messages.append(msg)

    # Only create comment if we have a valid PR
    comment_url = None
    if pull_number > 0:
        comment_body = create_progress_bar(p=0, msg="\n".join(log_messages))
        comment_url = create_comment(body=comment_body, base_args=base_args)
        base_args["comment_url"] = comment_url

    p += 10
    log_messages.append(f"Analyzed {len(commits)} commits with detailed changes.")
    if comment_url:
        comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
        update_comment(body=comment_body, base_args=base_args)

    # Get the file tree in the root of the repo
    file_tree, tree_comment = get_remote_file_tree(base_args=base_args)
    p += 10
    log_messages.append(tree_comment)
    if comment_url:
        comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
        update_comment(body=comment_body, base_args=base_args)

    # Prepare input for AI agent
    today = datetime.now().strftime("%Y-%m-%d")

    input_message = {
        "commit_changes": commit_changes,
        "head_commit": head_commit,
        "file_tree": file_tree,
        "today": today,
    }

    messages = [
        {"role": "system", "content": PUSH_TRIGGER_SYSTEM_PROMPT},
        {"role": "system", "content": f"## Repository rules:\n\n{repo_rules}"},
        {"role": "user", "content": json.dumps(input_message)},
    ]

    # Loop a process explore repo and commit changes until tests are added
    previous_calls = []
    retry_count = 0
    return
    while True:
        # Explore repo to understand the codebase and identify missing tests
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
            mode="get",
            previous_calls=previous_calls,
            p=p,
            log_messages=log_messages,
        )

        # Commit test changes based on the exploration information
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

        # If no new file is found and no changes are made, it means that the agent has completed the task or got stuck
        if not is_explored and not is_committed:
            break

        # If no files are found but changes are made, it might fall into an infinite loop
        if not is_explored and is_committed:
            retry_count += 1
            if retry_count > 3:
                break
            continue

        # If files are found but no changes are made, it means that the agent found files but didn't think it's necessary to commit changes
        if is_explored and not is_committed:
            retry_count += 1
            if retry_count > 3:
                break
            continue

        # Because the agent is committing changes, keep doing the loop
        retry_count = 0

    # Final message
    final_msg = "Finished analyzing commits and adding missing tests!"
    if comment_url:
        update_comment(body=final_msg, base_args=base_args)
    else:
        print(final_msg)

    return
