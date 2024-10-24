# Local imports
import json
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from services.github.actions_manager import get_workflow_run_logs, get_workflow_run_path
from services.github.github_manager import (
    get_installation_access_token,
    create_comment,
    get_issue_comments,
    get_remote_file_content,
    get_remote_file_tree,
    update_comment,
)
from services.github.github_types import (
    CheckRun,
    CheckRunCompletedPayload,
    CheckSuite,
    PullRequest,
    Repository,
)
from services.github.pulls_manager import get_pull_request, get_pull_request_files
from services.openai.commit_changes import explore_repo_or_commit_changes
from services.openai.chat import chat_with_ai
from services.openai.instructions.identify_cause import IDENTIFY_CAUSE
from services.supabase import SupabaseManager
from utils.progress_bar import create_progress_bar

supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)


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
    owner_type: str = repo["owner"]["type"]
    owner_id: int = repo["owner"]["id"]
    owner_name: str = repo["owner"]["login"]

    # Extract branch related variables
    check_suite: CheckSuite = check_run["check_suite"]
    head_branch: str = check_suite["head_branch"]

    # Extract sender related variables
    sender_id: int = payload["sender"]["id"]
    sender_name: str = payload["sender"]["login"]

    # Extract PR related variables
    pull_request: PullRequest = check_run["pull_requests"][0]
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
        "new_branch": head_branch,
        "base_branch": head_branch,  # Yes, intentionally set head_branch to base_branch because get_remote_file_tree requires the base branch
        "sender_id": sender_id,
        "sender_name": sender_name,
        "pull_number": pull_number,
        "workflow_run_id": workflow_run_id,
        "check_run_name": check_run_name,
        "token": token,
    }

    # Return here if GitAuto has tried to fix this Check Run error before because we need to avoid infinite loops
    pr_comments = get_issue_comments(
        issue_number=pull_number, base_args=base_args, includes_me=True
    )
    print(f"pr_comments: {json.dumps(obj=pr_comments, indent=2)}")
    if any(check_run_name in comment for comment in pr_comments):
        print("Skipping because GitAuto has tried to fix this Check Run error before")
        return

    # Create a first comment to inform the user that GitAuto is trying to fix the Check Run error
    msg = "Oops! Check run stumbled. Digging into logs... 🕵️"
    comment_body = create_progress_bar(p=0, msg=msg)
    comment_url = create_comment(
        issue_number=pull_number, body=comment_body, base_args=base_args
    )
    base_args["comment_url"] = comment_url

    # Get title, body, and code changes in the PR
    pull_title, pull_body = get_pull_request(url=pull_url, token=token)
    pull_file_url = pull_url + "/files"
    pull_changes = get_pull_request_files(url=pull_file_url, token=token)

    # Get the GitHub workflow file content
    workflow_path = get_workflow_run_path(
        owner=owner_name, repo=repo_name, run_id=workflow_run_id, token=token
    )
    workflow_content = get_remote_file_content(
        file_path=workflow_path, base_args=base_args
    )

    # Get the file tree in the root of the repo
    file_tree: str = get_remote_file_tree(base_args=base_args)

    # Get the error log from the workflow run
    error_log: str | None = get_workflow_run_logs(
        owner=owner_name, repo=repo_name, run_id=workflow_run_id, token=token
    )
    if error_log is None:
        return

    # Plan how to fix the error
    comment_body = create_progress_bar(p=30, msg="Planning how to fix the error...")
    update_comment(comment_url=comment_url, token=token, body=comment_body)
    input_message: dict[str, str] = {
        "pull_request_title": pull_title,
        "pull_request_body": pull_body,
        "pull_request_changes": json.dumps(obj=pull_changes),
        "workflow_content": workflow_content,
        "file_tree": file_tree,
        "error_log": error_log,
    }
    user_input = json.dumps(obj=input_message)
    how_to_fix: str = chat_with_ai(system_input=IDENTIFY_CAUSE, user_input=user_input)
    print(f"how_to_fix:\n{how_to_fix}")
    content = {
        "pull_request_title": pull_title,
        "file_tree": file_tree,
        "workflow_content": workflow_content,
        "error_log": error_log,
        "how_to_fix": how_to_fix,
    }
    messages = [{"role": "user", "content": json.dumps(obj=content)}]

    # Loop a process explore repo and commit changes until the ticket is resolved
    previous_calls = []
    retry_count = 0
    while True:
        # Explore repo
        messages, previous_calls, _token_input, _token_output, is_explored = (
            explore_repo_or_commit_changes(
                messages=messages,
                base_args=base_args,
                mode="get",  # explore can not be used here because "search_remote_file_contents" can search files only in the default branch NOT in the branch that is merged into the default branch
                previous_calls=previous_calls,
            )
        )

        # Commit changes based on the exploration information
        messages, previous_calls, _token_input, _token_output, is_committed = (
            explore_repo_or_commit_changes(
                messages=messages,
                base_args=base_args,
                mode="commit",
                previous_calls=previous_calls,
            )
        )

        # If no new file is found and no changes are made, it means that the agent has completed the ticket or got stuck for some reason
        if not is_explored and not is_committed:
            break

        # If files are found but no changes are made, it means that the agent found files but didn't think it's necessary to commit changes or fell into an infinite-like loop (e.g. slightly different searches)
        if is_explored and not is_committed:
            retry_count += 1
            if retry_count > 3:
                break

        # Because the agent is committing changes, keep doing the loop
        retry_count = 0

    # Create a pull request to the base branch
    msg = f"Committed the Check Run `{check_run_name}` error fix! Running it again..."
    update_comment(comment_url=comment_url, token=token, body=msg)
    return
