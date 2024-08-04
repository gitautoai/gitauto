# Standard imports
import json
import logging
import time
from uuid import uuid4

# Local imports
from config import (
    GITHUB_APP_USER_ID,
    PRODUCT_ID,
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
    PR_BODY_STARTS_WITH,
    ISSUE_NUMBER_FORMAT,
)
from services.github.github_manager import (
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
from utils.progress_bar import generate_progress_bar
from utils.text_copy import (
    UPDATE_COMMENT_FOR_RAISED_ERRORS_BODY,
    pull_request_completed,
    request_limit_reached,
)

supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)


async def handle_gitauto(payload: GitHubLabeledPayload, trigger_type: str) -> None:
    """Core functionality to create comments on issue, create PRs, and update progress."""
    current_time: float = time.time()

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
    owner_type: str = repo["owner"]["type"]
    owner: str = repo["owner"]["login"]
    owner_id: int = repo["owner"]["id"]
    repo_name: str = repo["name"]
    base_branch: str = repo["default_branch"]
    sender_id: int = payload["sender"]["id"]
    is_automation: bool = sender_id == GITHUB_APP_USER_ID
    sender_name: str = payload["sender"]["login"]
    issuer_name: str = issue["user"]["login"]
    token: str = get_installation_access_token(installation_id=installation_id)

    requests_left, request_count, end_date = (
        supabase_manager.get_how_many_requests_left_and_cycle(
            user_id=sender_id,
            installation_id=installation_id,
            user_name=sender_name,
            owner_id=owner_id,
            owner_name=owner,
        )
    )
    if requests_left <= 0:
        logging.info("\nRequest limit reached for user %s.", sender_name)
        create_comment(
            owner=owner,
            repo=repo_name,
            issue_number=issue_number,
            body=request_limit_reached(
                user_name=sender_name,
                request_count=request_count,
                end_date=end_date,
            ),
            token=token,
        )
        return
    unique_issue_id = f"{owner_type}/{owner}/{repo_name}#{issue_number}"
    usage_record_id = supabase_manager.create_user_request(
        user_id=sender_id,
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

    comment_url: str = create_comment(
        owner=owner,
        repo=repo_name,
        issue_number=issue_number,
        body=generate_progress_bar(p=0),
        token=token,
    )
    # Prepare contents for Agent
    file_paths: list[str] = get_remote_file_tree(
        owner=owner,
        repo=repo_name,
        ref=base_branch,
        comment_url=comment_url,
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

    print(
        f"{time.strftime('%H:%M:%S', time.localtime())} Installation token received.\n"
    )

    update_comment(
        comment_url=comment_url,
        token=token,
        body=generate_progress_bar(p=20),
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
        clone_url=repo["clone_url"],
        token=token,
    )
    create_remote_branch(
        branch_name=new_branch,
        owner=owner,
        repo=repo_name,
        sha=latest_commit_sha,
        comment_url=comment_url,
        token=token,
    )
    print(
        f"{time.strftime('%H:%M:%S', time.localtime())} Remote branch created: {new_branch}.\n"
    )

    token_input, token_output = run_assistant(
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

    update_comment(
        comment_url=comment_url,
        token=token,
        body=generate_progress_bar(p=90),
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
    pr_url: str | None = create_pull_request(
        base=base_branch,
        body=issue_link + pr_body + git_commands,
        head=new_branch,
        owner=owner,
        repo=repo_name,
        title=f"Fix {issue_title} with {PRODUCT_ID} model",
        token=token,
    )

    # Update the issue comment based on if the PR was created or not
    if pr_url is not None:
        body_after_pr = pull_request_completed(
            issuer_name=issuer_name,
            sender_name=sender_name,
            pr_url=pr_url,
            is_automation=is_automation,
        )
    else:
        body_after_pr = UPDATE_COMMENT_FOR_RAISED_ERRORS_BODY
    update_comment(comment_url=comment_url, token=token, body=body_after_pr)

    end_time = time.time()
    supabase_manager.complete_and_update_usage_record(
        usage_record_id=usage_record_id,
        token_input=token_input,
        token_output=token_output,
        total_seconds=int(end_time - current_time),
    )
    return
