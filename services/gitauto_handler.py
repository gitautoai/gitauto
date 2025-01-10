# Standard imports
from datetime import datetime
import json
import time
from typing import Literal

# Local imports
from config import (
    EXCEPTION_OWNERS,
    IS_PRD,
    PRODUCT_ID,
    PRODUCT_NAME,
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
    PR_BODY_STARTS_WITH,
)
from services.github.asset_manager import get_base64, render_text
from services.github.comment_manager import delete_my_comments
from services.github.file_manager import find_config_files
from services.github.github_manager import (
    create_pull_request,
    create_remote_branch,
    get_issue_comments,
    get_latest_remote_commit_sha,
    get_remote_file_content,
    get_remote_file_content_by_url,
    get_remote_file_tree,
    create_comment,
    update_comment,
    add_reaction_to_issue,
)
from services.github.github_types import GitHubLabeledPayload
from services.github.github_utils import deconstruct_github_payload
from services.jira.jira_manager import deconstruct_jira_payload
from services.openai.commit_changes import chat_with_agent
from services.openai.instructions.write_pr_body import WRITE_PR_BODY
from services.openai.chat import chat_with_ai
from services.openai.vision import describe_image
from services.supabase import SupabaseManager
from utils.extract_urls import extract_image_urls
from utils.progress_bar import create_progress_bar
from utils.text_copy import (
    UPDATE_COMMENT_FOR_422,
    git_command,
    pull_request_completed,
    request_limit_reached,
)

supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)


async def handle_gitauto(
    payload: GitHubLabeledPayload,
    trigger_type: Literal["label", "comment", "review_comment"],
    input_from: Literal["github", "jira"],
) -> None:
    """Core functionality to create comments on issue, create PRs, and update progress."""
    current_time: float = time.time()

    # Extract label and validate it
    if trigger_type == "label" and payload["label"]["name"] != PRODUCT_ID:
        return

    # Deconstruct payload based on input_from
    base_args = None
    if input_from == "github":
        base_args = deconstruct_github_payload(payload=payload)
    elif input_from == "jira":
        base_args = deconstruct_jira_payload(payload=payload)

    # Get some base args
    installation_id = base_args["installation_id"]
    owner_id = base_args["owner_id"]
    owner_name = base_args["owner"]
    owner_type = base_args["owner_type"]
    repo_name = base_args["repo"]
    issue_number = base_args["issue_number"]
    issue_title = base_args["issue_title"]
    issue_body = base_args["issue_body"]
    issue_body_rendered = render_text(base_args=base_args, text=issue_body)
    issuer_name = base_args["issuer_name"]
    new_branch_name = base_args["new_branch"]
    sender_id = base_args["sender_id"]
    sender_name = base_args["sender_name"]
    sender_email = base_args["sender_email"]
    github_urls = base_args["github_urls"]
    # other_urls = base_args["other_urls"]
    token = base_args["token"]
    is_automation = base_args["is_automation"]
    # Check if the user has reached the request limit
    requests_left, request_count, end_date = (
        supabase_manager.get_how_many_requests_left_and_cycle(
            installation_id=installation_id, owner_id=owner_id, owner_name=owner_name
        )
    )

    # Delete all comments made by GitAuto except the one with the checkbox to clean up the issue
    delete_my_comments(base_args=base_args)

    # Notify the user if the request limit is reached and early return
    if requests_left <= 0 and IS_PRD and owner_name not in EXCEPTION_OWNERS:
        body = request_limit_reached(
            user_name=sender_name, request_count=request_count, end_date=end_date
        )
        create_comment(body=body, base_args=base_args)
        return

    msg = "Got your request. Alright, let's get to it..."
    comment_body = create_progress_bar(p=0, msg=msg)
    comment_url: str | None = create_comment(body=comment_body, base_args=base_args)
    base_args["comment_url"] = comment_url
    unique_issue_id = f"{owner_type}/{owner_name}/{repo_name}"
    if input_from == "github":
        unique_issue_id = unique_issue_id + f"#{issue_number}"
    elif input_from == "jira":
        unique_issue_id = unique_issue_id + f"#jira-{issue_number}"
    usage_record_id = supabase_manager.create_user_request(
        user_id=sender_id if input_from == "github" else 0,
        user_name=sender_name,
        installation_id=installation_id,
        unique_issue_id=unique_issue_id,
        email=sender_email,
    )
    if input_from == "github":
        add_reaction_to_issue(
            issue_number=issue_number, content="eyes", base_args=base_args
        )

    # Check out the issue comments, and file tree
    comment_body = "Checking the issue title, body, comments, and file tree..."
    update_comment(body=comment_body, base_args=base_args, p=10)
    file_tree: list[str] = get_remote_file_tree(base_args=base_args)
    config_files: list[str] = find_config_files(file_tree=file_tree)
    config_contents: list[str] = []
    for config_file in config_files:
        content = get_remote_file_content(file_path=config_file, base_args=base_args)
        config_contents.append(content)

    # Check out the issue comments
    issue_comments: list[str] = []
    if input_from == "github":
        issue_comments = get_issue_comments(
            issue_number=issue_number, base_args=base_args
        )
    elif input_from == "jira":
        issue_comments = base_args["issue_comments"]

    # Check out the image URLs in the issue body and comments
    image_urls = extract_image_urls(text=issue_body_rendered)
    for issue_comment in issue_comments:
        issue_comment_rendered = render_text(base_args=base_args, text=issue_comment)
        image_urls.extend(extract_image_urls(text=issue_comment_rendered))
    for url in image_urls:
        base64_image = get_base64(url=url["url"])
        context = f"## Issue:\n{issue_title}\n\n## Issue Body:\n{issue_body}\n\n## Issue Comments:\n{'\n'.join(issue_comments)}"
        description = describe_image(base64_image=base64_image, context=context)
        description = f"## {url['alt']}\n\n{description}"
        issue_comments.append(description)
        create_comment(body=description, base_args=base_args)

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
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"Today's date: {today}")
    pr_body: str = chat_with_ai(
        system_input=WRITE_PR_BODY,
        user_input=json.dumps(
            obj={
                "issue_title": issue_title,
                "issue_body": issue_body,
                "reference_contents": reference_contents,
                "issue_comments": issue_comments,
                "file_tree": file_tree,
                "config_contents": config_contents,
                "metadata": base_args,
                "today": today,
            }
        ),
    )
    base_args["pr_body"] = pr_body

    # Ask for help if needed like a human would do
    comment_body = "Checking if I can solve it or if I should just hit you up..."
    update_comment(body=comment_body, base_args=base_args, p=25)
    messages = [
        {"role": "user", "content": pr_body},
        {"role": "user", "content": f"File tree:\n{file_tree}"},
        {"role": "user", "content": f"Config contents:\n{config_contents}"},
        {"role": "user", "content": f"Metadata:\n{base_args}"},
        {"role": "user", "content": f"Today's date:\n{today}"},
    ]
    # (*_, token_input, token_output, is_commented) = chat_with_agent(
    #     messages=messages, base_args=base_args, mode="comment"
    # )
    # if is_commented:
    #     end_time = time.time()
    #     supabase_manager.complete_and_update_usage_record(
    #         usage_record_id=usage_record_id,
    #         is_completed=True,  # False is only for GitAuto's failure
    #         token_input=token_input,
    #         token_output=token_output,
    #         total_seconds=int(end_time - current_time),
    #     )
    #     return

    # Create a remote branch
    comment_body = "Looks like it's doable. Creating the remote branch..."
    update_comment(body=comment_body, base_args=base_args, p=30)
    latest_commit_sha: str = ""
    if input_from == "github":
        latest_commit_sha = get_latest_remote_commit_sha(
            clone_url=base_args["clone_url"], base_args=base_args
        )
    elif input_from == "jira":
        latest_commit_sha = base_args["latest_commit_sha"]
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

        # Search Google
        (
            messages,
            previous_calls,
            tool_name,
            tool_args,
            token_input,
            token_output,
            _is_searched,
        ) = chat_with_agent(
            messages=messages,
            base_args=base_args,
            mode="search",
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
