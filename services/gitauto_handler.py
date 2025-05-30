# Standard imports
from asyncio import create_task
from datetime import datetime
from json import dumps
import time
from typing import Literal

# Local imports
from config import EXCEPTION_OWNERS, PRODUCT_ID, PRODUCT_NAME, PR_BODY_STARTS_WITH
from services.chat_with_agent import chat_with_agent
from services.github.asset_manager import get_base64, render_text
from services.github.comment_manager import delete_my_comments
from services.github.comments.create_comment import create_comment
from services.github.comments.get_comments import get_comments
from services.github.comments.update_comment import update_comment
from services.github.file_manager import find_config_files
from services.github.github_manager import (
    create_pull_request,
    create_remote_branch,
    get_latest_remote_commit_sha,
    get_remote_file_content,
    get_remote_file_content_by_url,
    get_remote_file_tree,
    add_reaction_to_issue,
)
from services.github.github_types import GitHubLabeledPayload
from services.github.github_utils import deconstruct_github_payload
from services.jira.jira_manager import deconstruct_jira_payload
from services.openai.vision import describe_image
from services.slack.slack import slack
from services.supabase.gitauto_manager import create_user_request
from services.supabase.usage.update_usage import update_usage
from services.supabase.users_manager import get_how_many_requests_left_and_cycle
from utils.progress_bar.progress_bar import create_progress_bar
from utils.text.text_copy import (
    UPDATE_COMMENT_FOR_422,
    git_command,
    pull_request_completed,
    request_limit_reached,
)
from utils.urls.extract_urls import extract_image_urls


async def handle_gitauto(
    payload: GitHubLabeledPayload,
    trigger_type: Literal["label", "comment", "review_comment"],
    input_from: Literal["github", "jira"],
) -> None:
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

    # Delete all comments made by GitAuto except the one with the checkbox to clean up the issue
    if input_from == "github":
        delete_my_comments(base_args=base_args)

    # Create a comment to track progress
    p = 0
    log_messages = []
    msg = "Got your request."
    log_messages.append(msg)
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    comment_url: str | None = create_comment(body=comment_body, base_args=base_args)
    base_args["comment_url"] = comment_url

    # Get some base args
    installation_id = base_args["installation_id"]
    owner_id = base_args["owner_id"]
    owner_name = base_args["owner"]
    owner_type = base_args["owner_type"]
    repo_id = base_args["repo_id"]
    repo_name = base_args["repo"]
    issue_number = base_args["issue_number"]
    issue_title = base_args["issue_title"]
    issue_body = base_args["issue_body"]
    issue_body_rendered = render_text(base_args=base_args, text=issue_body)
    issuer_name = base_args["issuer_name"]
    parent_issue_number = base_args["parent_issue_number"]
    parent_issue_title = base_args["parent_issue_title"]
    parent_issue_body = base_args["parent_issue_body"]
    new_branch_name = base_args["new_branch"]
    sender_id = base_args["sender_id"]
    sender_name = base_args["sender_name"]
    sender_email = base_args["sender_email"]
    github_urls = base_args["github_urls"]
    # other_urls = base_args["other_urls"]
    token = base_args["token"]
    is_automation = base_args["is_automation"]

    # Print who, what, and where
    print(
        f"`{sender_id}:{sender_name}` wants to create a PR for `{issue_number}:{issue_title}` in `{owner_name}/{repo_name}`"
    )

    # Notify Slack
    trigger = (
        "Labeled"
        if trigger_type == "label"
        else "Triggered" if trigger_type == "comment" else "Review-commented"
    )
    msg = f"{trigger} by `{sender_name}` for `{issue_title}` in `{owner_name}/{repo_name}`"
    slack(msg)

    p += 5
    log_messages.append("Extracted metadata.")
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)), base_args=base_args
    )

    # Check if the user has reached the request limit
    requests_left, request_count, end_date, is_retried = (
        get_how_many_requests_left_and_cycle(
            installation_id=installation_id,
            owner_id=owner_id,
            owner_name=owner_name,
            owner_type=owner_type,
            repo_name=repo_name,
            issue_number=issue_number,
        )
    )
    p += 5
    log_messages.append(f"Checked request limit. {requests_left} requests left.")
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)), base_args=base_args
    )

    # Notify the user if the request limit is reached and early return
    if requests_left <= 0 and not is_retried and owner_name not in EXCEPTION_OWNERS:
        body = request_limit_reached(
            user_name=sender_name, request_count=request_count, end_date=end_date
        )
        update_comment(body=body, base_args=base_args)
        print(body)
        return

    # Create a usage record
    usage_record_task = create_task(
        create_user_request(
            user_id=sender_id if input_from == "github" else 0,
            user_name=sender_name,
            installation_id=installation_id,
            owner_id=owner_id,
            owner_type=owner_type,
            owner_name=owner_name,
            repo_id=repo_id,
            repo_name=repo_name,
            issue_number=issue_number,
            source=input_from,
            email=sender_email,
        )
    )
    if input_from == "github":
        create_task(
            add_reaction_to_issue(
                issue_number=issue_number, content="eyes", base_args=base_args
            )
        )

    # Check out the issue comments, and file tree
    file_tree, tree_comment = get_remote_file_tree(base_args=base_args)
    p += 5
    log_messages.append(tree_comment)
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)), base_args=base_args
    )

    config_files: list[str] = find_config_files(file_tree=file_tree)
    comment_body = f"Found {len(config_files)} configuration files."
    if len(config_files) > 0:
        comment_body += "\n- " + "\n- ".join(config_files) + "\n"
    p += 5
    log_messages.append(comment_body)
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)), base_args=base_args
    )

    config_contents: list[str] = []
    for config_file in config_files:
        content = get_remote_file_content(file_path=config_file, base_args=base_args)
        config_contents.append(content)
    comment_body = f"Read {len(config_files)} configuration files."
    p += 5
    log_messages.append(comment_body)
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)), base_args=base_args
    )

    # Check out the issue comments
    issue_comments: list[str] = []
    if input_from == "github":
        issue_comments = get_comments(issue_number=issue_number, base_args=base_args)
    elif input_from == "jira":
        issue_comments = base_args["issue_comments"]
    comment_body = f"Found {len(issue_comments)} issue comments."
    p += 5
    log_messages.append(comment_body)
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)), base_args=base_args
    )

    # Check out the image URLs in the issue body and comments
    image_urls = extract_image_urls(text=issue_body_rendered)
    if image_urls:
        comment_body = f"Found {len(image_urls)} images in the issue body."
        p += 5
        log_messages.append(comment_body)
        update_comment(
            body=create_progress_bar(p=p, msg="\n".join(log_messages)),
            base_args=base_args,
        )

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
        comment_body = "Also checking out the URLs in the issue body."
        p += 5
        log_messages.append(comment_body)
        update_comment(
            body=create_progress_bar(p=p, msg="\n".join(log_messages)),
            base_args=base_args,
        )
        content = get_remote_file_content_by_url(url=url, token=token)
        print(f"```{url}\n{content}```\n")
        reference_contents.append(content)

    today = datetime.now().strftime("%Y-%m-%d")

    # Ask for help if needed like a human would do
    # comment_body = "Checking if I can solve it or if I should just hit you up."
    # p = min(p + 5, 95)
    # update_comment(body=comment_body, base_args=base_args, p=p)
    user_input = dumps(
        {
            "today": today,
            "metadata": base_args,
            "issue_title": issue_title,
            "issue_body": issue_body,
            "reference_contents": reference_contents,
            "issue_comments": issue_comments,
            "parent_issue_number": parent_issue_number,
            "parent_issue_title": parent_issue_title,
            "parent_issue_body": parent_issue_body,
            "file_tree": file_tree,
            "config_contents": config_contents,
        }
    )
    messages = [{"role": "user", "content": user_input}]

    # Create a remote branch
    latest_commit_sha: str = ""
    if input_from == "github":
        latest_commit_sha = get_latest_remote_commit_sha(
            clone_url=base_args["clone_url"], base_args=base_args
        )
    elif input_from == "jira":
        latest_commit_sha = base_args["latest_commit_sha"]
    create_remote_branch(sha=latest_commit_sha, base_args=base_args)
    comment_body = f"Created a branch: `{new_branch_name}`"
    p += 5
    log_messages.append(comment_body)
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)), base_args=base_args
    )

    # Loop a process explore repo and commit changes until the ticket is resolved
    previous_calls = []
    retry_count = 0
    while True:
        # Explore repo
        (
            messages,
            previous_calls,
            _tool_name,
            _tool_args,
            token_input,
            token_output,
            is_explored,
            p,
        ) = chat_with_agent(
            messages=messages,
            base_args=base_args,
            mode="explore",
            previous_calls=previous_calls,
            p=p,
            log_messages=log_messages,
        )

        # Search Google
        # (
        #     messages,
        #     previous_calls,
        #     _tool_name,
        #     _tool_args,
        #     token_input,
        #     token_output,
        #     _is_searched,
        #     p,
        # ) = chat_with_agent(
        #     messages=messages,
        #     base_args=base_args,
        #     mode="search",
        #     previous_calls=previous_calls,
        #     p=p,
        #     log_messages=log_messages,
        # )

        # Commit changes based on the exploration information
        (
            messages,
            previous_calls,
            _tool_name,
            _tool_args,
            token_input,
            token_output,
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
    comment_body = "Creating a pull request."
    p += 5
    log_messages.append(comment_body)
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)), base_args=base_args
    )
    title = f"{PRODUCT_NAME}: {issue_title}"
    issue_link: str = f"{PR_BODY_STARTS_WITH}{issue_number}\n\n"
    pr_body = issue_link + git_command(new_branch_name=new_branch_name)
    pr_url = create_pull_request(body=pr_body, title=title, base_args=base_args)

    # Update the issue comment based on if the PR was created or not
    pr_number = None
    if pr_url is not None:
        is_completed = True
        pr_number = int(pr_url.split("/")[-1])
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
    usage_record_id = await usage_record_task
    update_usage(
        usage_record_id=usage_record_id,
        is_completed=is_completed,
        pr_number=pr_number,
        token_input=token_input,
        token_output=token_output,
        total_seconds=int(end_time - current_time),
    )
    return
