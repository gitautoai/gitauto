# Standard imports
import json
import logging
import time
from uuid import uuid4

# Third-party imports
import tiktoken

# Local imports
from config import (
    GITHUB_APP_USER_ID,
    OPENAI_MODEL_ID,
    PRODUCT_ID,
    PRODUCT_NAME,
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
    get_remote_file_content_by_url,
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
from utils.extract_urls import extract_urls
from utils.progress_bar import create_progress_bar
from utils.text_copy import (
    UPDATE_COMMENT_FOR_RAISED_ERRORS_BODY,
    git_command,
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
    issue_number: int = issue["number"]
    issue_body: str = issue["body"] or ""
    github_urls, other_urls = extract_urls(text=issue_body)
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
    print(f"Issue Title: {issue_title}\n")
    print(f"Issue Body:\n{issue_body}\n")
    if github_urls:
        print(f"\nGitHub URLs: {json.dumps(github_urls, indent=2)}")
    if other_urls:
        print(f"\nOther URLs: {json.dumps(other_urls, indent=2)}")

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
    msg = "Reading this issue body, comments, and file tree..."
    comment_url: str = create_comment(
        owner=owner,
        repo=repo_name,
        issue_number=issue_number,
        body=create_progress_bar(p=0, msg=msg),
        token=token,
    )
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

    # Prepare contents for Agent
    file_paths: list[str] = get_remote_file_tree(
        owner=owner,
        repo=repo_name,
        ref=base_branch,
        comment_url=comment_url,
        token=token,
    )
    file_paths_json = json.dumps(file_paths)
    print(f"{len(file_paths)} file paths found in the repository.")
    print(f"File Paths Characters: {len(file_paths_json)}")
    print(f"File Paths Tokens: {len(tiktoken.encoding_for_model(OPENAI_MODEL_ID).encode(file_paths_json))}\n")
    issue_comments: list[str] = get_issue_comments(
        owner=owner, repo=repo_name, issue_number=issue_number, token=token
    )
    reference_contents: list[str] = []
    for url in github_urls:
        content = get_remote_file_content_by_url(url=url, token=token)
        print(f"```{url}\n{content}```\n")
        reference_contents.append(content)

    # Prepare PR body
    comment_body = create_progress_bar(p=10, msg="Writing a pull request body...")
    update_comment(comment_url=comment_url, token=token, body=comment_body)
    pr_body: str = write_pr_body(
        input_message=json.dumps(
            obj={
                "issue_title": issue_title,
                "issue_body": issue_body,
                "reference_contents": reference_contents,
                "issue_comments": issue_comments,
                "file_paths": file_paths,
            }
        )
    )

    # Create a remote branch
    comment_body = create_progress_bar(p=20, msg="Creating a remote branch...")
    update_comment(comment_url=comment_url, token=token, body=comment_body)
    uuid: str = str(object=uuid4())
    branch: str = f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}{issue['number']}-{uuid}"
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
        branch_name=branch,
        owner=owner,
        repo=repo_name,
        sha=latest_commit_sha,
        comment_url=comment_url,
        token=token,
    )
    comment_body = create_progress_bar(p=30, msg="Thinking about how to code...")
    update_comment(comment_url=comment_url, token=token, body=comment_body)
    token_input, token_output = run_assistant(
        file_paths=file_paths,
        issue_title=issue_title,
        issue_body=issue_body,
        reference_contents=reference_contents,
        issue_comments=issue_comments,
        owner=owner,
        pr_body=pr_body,
        ref=base_branch,
        repo=repo_name,
        comment_url=comment_url,
        branch=branch,
        token=token,
    )

    # Create a pull request to the base branch
    comment_body = create_progress_bar(p=90, msg="Creating a pull request...")
    update_comment(comment_url=comment_url, token=token, body=comment_body)
    issue_link: str = f"{PR_BODY_STARTS_WITH}{issue_number}]({issue['html_url']})\n\n"
    pr_url: str | None = create_pull_request(
        base=base_branch,
        body=issue_link + pr_body + git_command(new_branch_name=branch),
        head=branch,
        owner=owner,
        repo=repo_name,
        title=f"{PRODUCT_NAME}: {issue_title}",
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
