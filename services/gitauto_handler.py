# Standard imports
import json
import logging
import time
from uuid import uuid4

# Local imports
from config import (
    EXCEPTION_OWNERS,
    GITHUB_APP_USER_ID,
    IS_PRD,
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
    get_user_public_email,
)
from services.github.github_types import (
    BaseArgs,
    GitHubLabeledPayload,
    IssueInfo,
    RepositoryInfo,
)
from services.openai.commit_changes import chat_with_agent
from services.openai.instructions.write_pr_body import WRITE_PR_BODY
from services.openai.chat import chat_with_ai
from services.supabase import SupabaseManager
from utils.extract_urls import extract_urls
from utils.progress_bar import create_progress_bar
from utils.text_copy import (
    UPDATE_COMMENT_FOR_422,
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

    # Extract issue related variables
    issue: IssueInfo = payload["issue"]
    issue_title: str = issue["title"]
    issue_number: int = issue["number"]
    issue_body: str = issue["body"] or ""
    issuer_name: str = issue["user"]["login"]

    # Extract repository related variables
    repo: RepositoryInfo = payload["repository"]
    repo_name: str = repo["name"]
    is_fork: bool = repo.get("fork", False)

    # Extract owner related variables
    owner_type: str = repo["owner"]["type"]
    owner_name: str = repo["owner"]["login"]
    owner_id: int = repo["owner"]["id"]

    # Extract branch related variables
    base_branch_name: str = repo["default_branch"]
    uuid: str = str(object=uuid4())
    new_branch_name: str = f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}{issue['number']}-{uuid}"

    # Extract sender related variables
    sender_id: int = payload["sender"]["id"]
    is_automation: bool = sender_id == GITHUB_APP_USER_ID
    sender_name: str = payload["sender"]["login"]
    reviewers: list[str] = list(
        set(name for name in (sender_name, issuer_name) if "[bot]" not in name)
    )

    # Extract other information
    github_urls, other_urls = extract_urls(text=issue_body)
    installation_id: int = payload["installation"]["id"]
    token: str = get_installation_access_token(installation_id=installation_id)
    sender_email = get_user_public_email(username=sender_name, token=token)

    base_args: BaseArgs = {
        "owner": owner_name,
        "repo": repo_name,
        "is_fork": is_fork,
        "base_branch": base_branch_name,
        "new_branch": new_branch_name,
        "token": token,
        "reviewers": reviewers,
    }

    # Check if the user has reached the request limit
    requests_left, request_count, end_date = (
        supabase_manager.get_how_many_requests_left_and_cycle(
            user_id=sender_id,
            installation_id=installation_id,
            user_name=sender_name,
            owner_id=owner_id,
            owner_name=owner_name,
        )
    )
    print(f"{requests_left=}")

    # Notify the user if the request limit is reached and early return
    if requests_left <= 0 and IS_PRD and owner_name not in EXCEPTION_OWNERS:
        logging.info("\nRequest limit reached for user %s.", sender_name)
        body = request_limit_reached(
            user_name=sender_name, request_count=request_count, end_date=end_date
        )
        create_comment(issue_number=issue_number, body=body, base_args=base_args)
        return

    msg = "Got your request. Alright, let's get to it..."
    comment_body = create_progress_bar(p=0, msg=msg)
    comment_url = create_comment(
        issue_number=issue_number, body=comment_body, base_args=base_args
    )
    base_args["comment_url"] = comment_url
    unique_issue_id = f"{owner_type}/{owner_name}/{repo_name}#{issue_number}"
    usage_record_id = supabase_manager.create_user_request(
        user_id=sender_id,
        user_name=sender_name,
        installation_id=installation_id,
        unique_issue_id=unique_issue_id,
        email=sender_email,
    )
    add_reaction_to_issue(
        issue_number=issue_number, content="eyes", base_args=base_args
    )

    # Check out the issue comments, and root files/directories list
    comment_body = "Checking the issue title, body, comments, and root files list..."
    update_comment(body=comment_body, base_args=base_args, p=10)
    root_files_and_dirs: list[str] = get_remote_file_tree(base_args=base_args)
    issue_comments = get_issue_comments(issue_number=issue_number, base_args=base_args)

    # Check out the URLs in the issue body
    reference_contents: list[str] = []
    for url in github_urls:
        comment_body = "Also checking out the URLs in the issue body..."
        update_comment(body=comment_body, base_args=base_args, p=15)
        content = get_remote_file_content_by_url(url=url, token=token)
        print(f"```{url}\n{content}```\n")
        reference_contents.append(content)

    # Write a pull request body
    comment_body = "Writing up the pull request body..."
    update_comment(body=comment_body, base_args=base_args, p=20)
    pr_body: str = chat_with_ai(
        system_input=WRITE_PR_BODY,
        user_input=json.dumps(
            obj={
                "issue_title": issue_title,
                "issue_body": issue_body,
                "reference_contents": reference_contents,
                "issue_comments": issue_comments,
                "root_files_and_dirs": root_files_and_dirs,
            }
        ),
    )
    base_args["pr_body"] = pr_body

    # Ask for help if needed like a human would do
    comment_body = "Checking if I can solve it or if I should just hit you up..."
    update_comment(body=comment_body, base_args=base_args, p=25)
    messages = [{"role": "user", "content": pr_body}]
    (*_, token_input, token_output, is_commented) = chat_with_agent(
        messages=messages, base_args=base_args, mode="comment"
    )
    if is_commented:
        return

    # Create a remote branch
    comment_body = "Looks like it's doable. Creating the remote branch..."
    update_comment(body=comment_body, base_args=base_args, p=30)
    latest_commit_sha: str = get_latest_remote_commit_sha(
        clone_url=repo["clone_url"],
        base_args=base_args,
    )
    create_remote_branch(sha=latest_commit_sha, base_args=base_args)

    # Loop a process explore repo and commit changes until the ticket is resolved
    previous_calls = []
    retry_count = 0
    p = 35
    while True:
        # Explore repo
        (
            messages,
            previous_calls,
            tool_name,
            tool_args,
            token_input,
            token_output,
            is_explored,
        ) = chat_with_agent(
            messages=messages,
            base_args=base_args,
            mode="explore",
            previous_calls=previous_calls,
        )
        if tool_name is not None and tool_args is not None:
            comment_body = f"Calling `{tool_name}()` with `{tool_args}`..."
            update_comment(body=comment_body, base_args=base_args, p=p)
            p = min(p + 5, 85)

        # Commit changes based on the exploration information
        (
            messages,
            previous_calls,
            tool_name,
            tool_args,
            token_input,
            token_output,
            is_committed,
        ) = chat_with_agent(
            messages=messages,
            base_args=base_args,
            mode="commit",
            previous_calls=previous_calls,
        )
        if tool_name is not None and tool_args is not None:
            comment_body = f"Calling `{tool_name}()` with `{tool_args}`..."
            update_comment(body=comment_body, base_args=base_args, p=p)
            p = min(p + 5, 85)

        # If no new file is found and no changes are made, it means that the agent has completed the ticket or got stuck for some reason
        if not is_explored and not is_committed:
            break

        # If no files are found but changes are made, it might fall into an infinite loop (e.g., repeatedly making and reverting similar changes with slight variations)
        if not is_explored and is_committed:
            retry_count += 1
            if retry_count > 10:
                break

        # If files are found but no changes are made, it means that the agent found files but didn't think it's necessary to commit changes or fell into an infinite-like loop (e.g. slightly different searches)
        if is_explored and not is_committed:
            retry_count += 1
            if retry_count > 10:
                break

        # Because the agent is committing changes, keep doing the loop
        retry_count = 0

    # Create a pull request to the base branch
    comment_body = "Creating a pull request..."
    update_comment(body=comment_body, base_args=base_args, p=90)
    title = f"{PRODUCT_NAME}: {issue_title}"
    issue_link: str = f"{PR_BODY_STARTS_WITH}{issue_number}\n\n"
    pr_body = issue_link + pr_body + git_command(new_branch_name=new_branch_name)
    pr_url = create_pull_request(body=pr_body, title=title, base_args=base_args)

    # Update the issue comment based on if the PR was created or not
    if pr_url is not None:
        is_completed = True
        body_after_pr = pull_request_completed(
            issuer_name=issuer_name,
            sender_name=sender_name,
            pr_url=pr_url,
            is_automation=is_automation,
        )
    else:
        is_completed = False
        body_after_pr = UPDATE_COMMENT_FOR_422
    update_comment(body=body_after_pr, base_args=base_args)

    end_time = time.time()
    supabase_manager.complete_and_update_usage_record(
        usage_record_id=usage_record_id,
        is_completed=is_completed,
        token_input=token_input,
        token_output=token_output,
        total_seconds=int(end_time - current_time),
    )
    return
