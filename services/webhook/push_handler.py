# pylint: disable=too-many-locals, too-many-statements, too-many-branches

from datetime import datetime
import json
import time
from typing import Any

# Local imports
from services.chat_with_agent import chat_with_agent

# Local imports (GitHub)
from services.github.branches.check_branch_exists import check_branch_exists
from services.github.comments.create_comment import create_comment
from services.github.comments.update_comment import update_comment
from services.github.commits.create_empty_commit import create_empty_commit
from services.github.commits.get_commit_diff import get_commit_diff
from services.github.pulls.find_pull_request_by_branch import (
    find_pull_request_by_branch,
)
from services.github.pulls.is_pull_request_open import is_pull_request_open
from services.github.token.get_installation_token import get_installation_access_token
from services.github.trees.get_file_tree import get_file_tree
from services.github.types.owner import Owner
from services.github.types.repository import Repository

# Local imports (Supabase)
from services.supabase.coverages.get_coverages import get_coverages
from services.supabase.owners_manager import get_stripe_customer_id
from services.supabase.repositories.get_repository import get_repository_settings
from services.webhook.utils.create_system_messages import create_system_messages

# Local imports (Utils)
from utils.files.is_code_file import is_code_file
from utils.files.is_excluded_from_testing import is_excluded_from_testing
from utils.files.is_test_file import is_test_file
from utils.progress_bar.progress_bar import create_progress_bar
from utils.prompts.push_trigger import PUSH_TRIGGER_SYSTEM_PROMPT
from utils.time.is_lambda_timeout_approaching import is_lambda_timeout_approaching
from utils.time.get_timeout_message import get_timeout_message


def handle_push_event(payload: dict[str, Any]) -> None:
    current_time = time.time()  # Add this early in the function

    # Skip if it's any bot
    sender_id: int = payload["sender"]["id"]
    sender_name: str = payload["sender"]["login"]
    if sender_name.endswith("[bot]"):
        return

    # Skip merge commits - base_ref is set when it's a merge
    base_ref = payload.get("base_ref")
    if base_ref is not None:
        return

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

    # Extract owner related variables
    owner: Owner = repo["owner"]
    owner_type: str = owner["type"]
    owner_id: int = owner["id"]
    owner_name: str = owner["login"]

    # Extract push related variables
    ref: str = payload["ref"]  # refs/heads/branch-name
    branch_name: str = ref.replace("refs/heads/", "")
    default_branch = repo["default_branch"]
    commits: list[dict[str, Any]] = payload["commits"]
    head_commit: dict[str, Any] = payload["head_commit"]

    # Skip if push is to default branch
    if branch_name == default_branch:
        print(f"Skipping push to default branch: {default_branch}")
        return

    # Skip if no commits
    if not commits:
        return

    print(
        f"Push event from {sender_name} to {owner_name}/{repo_name} on branch {branch_name}"
    )

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

        # Get coverage data for all files in this commit
        all_files_in_commit = [file["filename"] for file in commit_diff["files"]]
        coverage_data = get_coverages(repo_id=repo_id, filenames=all_files_in_commit)

        # Filter out test files, non-code files, and excluded files
        filtered_files = []
        for file in commit_diff["files"]:
            filename = file["filename"]
            if (
                is_code_file(filename)
                and not is_test_file(filename)
                and not is_excluded_from_testing(
                    filename=filename, coverage_data=coverage_data
                )
            ):
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
        "skip_ci": True,
    }

    # Return here if stripe_customer_id is not found
    stripe_customer_id: str | None = get_stripe_customer_id(owner_id=owner_id)
    if stripe_customer_id is None:
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
    file_tree, tree_comment = get_file_tree(base_args=base_args)
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

    # Prepare system messages
    system_messages = create_system_messages(repo_settings=repo_settings)
    system_messages = [
        {"role": "system", "content": PUSH_TRIGGER_SYSTEM_PROMPT}
    ] + system_messages

    # Create user messages only
    messages = [{"role": "user", "content": json.dumps(input_message)}]

    # Loop a process explore repo and commit changes until tests are added
    previous_calls = []
    retry_count = 0
    while True:
        # Timeout check: Stop if we're approaching Lambda limit
        is_timeout_approaching, elapsed_time = is_lambda_timeout_approaching(
            current_time
        )
        if is_timeout_approaching:
            timeout_msg = get_timeout_message(elapsed_time, "Push event processing")
            if comment_url:
                update_comment(body=timeout_msg, base_args=base_args)
            break

        # Safety check: Stop if PR is closed or branch is deleted
        if pull_number > 0:
            # Check if PR is still open
            if not is_pull_request_open(
                owner=owner_name, repo=repo_name, pull_number=pull_number, token=token
            ):
                body = f"Process stopped: Pull request #{pull_number} was closed during execution."
                print(body)
                if comment_url:
                    update_comment(body=body, base_args=base_args)
                break

        # Check if branch still exists
        if not check_branch_exists(
            owner=owner_name, repo=repo_name, branch_name=branch_name, token=token
        ):
            body = f"Process stopped: Branch '{branch_name}' has been deleted"
            print(body)
            if comment_url:
                update_comment(body=body, base_args=base_args)
            break

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
            system_messages=system_messages,
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
            system_messages=system_messages,
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

    # Trigger final test workflows with an empty commit
    body = "Creating final empty commit to trigger workflows..."
    if comment_url:
        update_comment(body=body, base_args=base_args)
    else:
        print(body)
    create_empty_commit(base_args)

    # Final message
    final_msg = "Finished analyzing commits and adding missing tests!"
    if comment_url:
        update_comment(body=final_msg, base_args=base_args)
    else:
        print(final_msg)

    return
