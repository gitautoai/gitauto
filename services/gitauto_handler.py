# Standard imports
import json
import time
from uuid import uuid4

# Local imports
from config import (
    PRODUCT_ID,
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
    PR_BODY_STARTS_WITH,
    ISSUE_NUMBER_FORMAT,
)
from services.github.github_manager import (
    commit_changes_to_remote_branch,
    create_pull_request,
    create_remote_branch,
    get_installation_access_token,
    get_issue_comments,
    get_latest_remote_commit_sha,
    get_remote_file_tree,
    create_comment,
    update_comment,
    add_reaction_to_issue,
)
from services.github.github_types import (
    GitHubLabeledPayload,
    IssueInfo,
    RepositoryInfo,
)
from services.openai.chat import write_pr_body
from services.openai.agent import run_assistant
from services.supabase import SupabaseManager
from utils.file_manager import extract_file_name
from utils.text_copy import pull_request_completed, request_limit_reached

supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)


async def handle_gitauto(payload: GitHubLabeledPayload, trigger_type: str) -> None:
    """Core functionality to create comments on issue, create PRs, and update progress."""
    # Extract label and validate it
    if trigger_type == "label" and payload["label"]["name"] != PRODUCT_ID:
        return

    # Extract information from the payload
    issue: IssueInfo = payload["issue"]
    issue_title: str = issue["title"]
    issue_body: str = issue["body"] or ""
    issue_number: int = issue["number"]
    installation_id: int = payload["installation"]["id"]
    repo: RepositoryInfo = payload["repository"]
    owner_type = payload["repository"]["owner"]["type"][0]
    owner: str = repo["owner"]["login"]
    repo_name: str = repo["name"]
    base_branch: str = repo["default_branch"]
    user_id: int = payload["sender"]["id"]
    user_name: str = payload["sender"]["login"]
    token: str = get_installation_access_token(installation_id=installation_id)

    requests_left, request_count, end_date = (
        supabase_manager.get_how_many_requests_left_and_cycle(
            user_id=user_id, installation_id=installation_id
        )
    )
    if requests_left <= 0:
        create_comment(
            owner=owner,
            repo=repo_name,
            issue_number=issue_number,
            body=request_limit_reached(
                user_name=user_name,
                request_count=request_count,
                end_date=end_date,
            ),
            token=token,
        )
        return
    unique_issue_id = f"{owner_type}/{owner}/{repo_name}#{issue_number}"
    supabase_manager.create_user_request(
        user_id=user_id,
        installation_id=installation_id,
        unique_issue_id=unique_issue_id,
    )
    add_reaction_to_issue(
        owner=owner,
        repo=repo_name,
        issue_number=issue_number,
        content="eyes",
        token=token,
    )

    # Start progress and check if current issue is already in progress from another invocation
    if supabase_manager.is_issue_in_progress(unique_issue_id=unique_issue_id):
        return
    comment_url = create_comment(
        owner=owner,
        repo=repo_name,
        issue_number=issue_number,
        body="![X](https://progress-bar.dev/0/?title=Progress&width=800)\nGitAuto just started crafting a pull request.",
        token=token,
    )
    # Prepare contents for Agent
    file_paths: list[str] = get_remote_file_tree(
        owner=owner,
        repo=repo_name,
        ref=base_branch,
        comment_url=comment_url,
        unique_issue_id=unique_issue_id,
        token=token,
    )
    issue_comments: list[str] = get_issue_comments(
        owner=owner, repo=repo_name, issue_number=issue_number, token=token
    )

    pr_body: str = write_pr_body(
        input_message=json.dumps(
            obj={
                "issue_title": issue_title,
                "issue_body": issue_body,
                "issue_comments": issue_comments,
                "file_paths": file_paths,
            }
        )
    )
    supabase_manager.update_progress(unique_issue_id=unique_issue_id, progress=5)
    print(
        f"{time.strftime('%H:%M:%S', time.localtime())} Installation token received.\n"
    )

    # Create a remote branch
    uuid: str = str(object=uuid4())
    new_branch: str = f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}{issue['number']}-{uuid}"
    latest_commit_sha: str = get_latest_remote_commit_sha(
        owner=owner,
        repo=repo_name,
        branch=base_branch,
        comment_url=comment_url,
        unique_issue_id=unique_issue_id,
        token=token,
    )
    create_remote_branch(
        branch_name=new_branch,
        owner=owner,
        repo=repo_name,
        sha=latest_commit_sha,
        comment_url=comment_url,
        unique_issue_id=unique_issue_id,
        token=token,
    )
    print(
        f"{time.strftime('%H:%M:%S', time.localtime())} Remote branch created: {new_branch}.\n"
    )

    diffs: list[str] = run_assistant(
        file_paths=file_paths,
        issue_title=issue_title,
        issue_body=issue_body,
        issue_comments=issue_comments,
        owner=owner,
        pr_body=pr_body,
        ref=base_branch,
        repo=repo_name,
        comment_url=comment_url,
        new_branch=new_branch,
        token=token,
    )

    supabase_manager.update_progress(unique_issue_id=unique_issue_id, progress=90)
    update_comment(
        comment_url=comment_url,
        token=token,
        body="![X](https://progress-bar.dev/50/?title=Progress&width=800)\nHalf way there!",
    )

    # Commit the changes to the new remote branch
    for diff in diffs:
        file_path: str = extract_file_name(diff_text=diff)
        print(
            f"{time.strftime('%H:%M:%S', time.localtime())} File path: {file_path}.\n"
        )
        commit_changes_to_remote_branch(
            branch=new_branch,
            commit_message=f"Update {file_path}",
            diff_text=diff,
            file_path=file_path,
            owner=owner,
            repo=repo_name,
            token=token,
        )
        print(
            f"{time.strftime('%H:%M:%S', time.localtime())} Changes committed to {new_branch}.\n"
        )

    # Create a pull request to the base branch
    issue_link: str = f"{PR_BODY_STARTS_WITH}{issue_number}]({issue['html_url']})\n\n"
    git_commands = (
        f"\n\n## Test these changes locally\n\n"
        f"```\n"
        f"git checkout -b {new_branch}\n"
        f"git pull origin {new_branch}\n"
        f"```"
    )
    pull_request_url = create_pull_request(
        base=base_branch,
        body=issue_link + pr_body + git_commands,
        head=new_branch,
        owner=owner,
        repo=repo_name,
        title=f"Fix {issue_title} with {PRODUCT_ID} model",
        comment_url=comment_url,
        unique_issue_id=unique_issue_id,
        token=token,
    )
    print(f"{time.strftime('%H:%M:%S', time.localtime())} Pull request created.\n")

    update_comment(
        comment_url=comment_url,
        token=token,
        body=pull_request_completed(pull_request_url=pull_request_url),
    )

    supabase_manager.complete_user_request(
        user_id=user_id, installation_id=installation_id
    )
    supabase_manager.update_progress(unique_issue_id=unique_issue_id, progress=100)
    return
