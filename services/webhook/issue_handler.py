# Standard imports
from datetime import datetime
from json import dumps
import logging
import time
from typing import Literal, cast

# Local imports
from config import GITHUB_API_URL, PRODUCT_ID, PR_BODY_STARTS_WITH
from constants.messages import COMPLETED_PR, SETTINGS_LINKS
from services.chat_with_agent import chat_with_agent
from services.efs.start_async_install_on_efs import start_async_install_on_efs
from services.resend.send_email import send_email
from services.resend.text.credits_depleted_email import get_credits_depleted_email_text

# Local imports (GitHub)
from services.github.branches.check_branch_exists import check_branch_exists
from services.github.branches.create_remote_branch import create_remote_branch
from services.github.comments.create_comment import create_comment
from services.github.comments.delete_comments_by_identifiers import (
    delete_comments_by_identifiers,
)
from services.github.comments.get_comments import get_comments
from services.github.comments.update_comment import update_comment
from services.github.commits.create_empty_commit import create_empty_commit
from services.github.commits.get_latest_remote_commit_sha import (
    get_latest_remote_commit_sha,
)
from services.github.commits.replace_remote_file import replace_remote_file_content
from services.github.files.get_raw_content import get_raw_content
from services.github.files.get_remote_file_content_by_url import (
    get_remote_file_content_by_url,
)
from services.github.markdown.render_text import render_text
from services.github.pulls.create_pull_request import create_pull_request
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.reactions.add_reaction_to_issue import add_reaction_to_issue
from services.github.types.github_types import GitHubLabeledPayload
from services.github.utils.deconstruct_github_payload import deconstruct_github_payload
from services.jira.types import JiraPayload

# Local imports (Jira, OpenAI, Slack)
from services.jira.deconstruct_jira_payload import deconstruct_jira_payload
from services.openai.vision import describe_image
from services.slack.slack_notify import slack_notify

# Local imports (Supabase, Webhook)
from services.supabase.create_user_request import create_user_request
from services.supabase.credits.insert_credit import insert_credit
from services.supabase.owners.get_owner import get_owner
from services.supabase.owners.get_stripe_customer_id import get_stripe_customer_id
from services.supabase.owners.update_stripe_customer_id import update_stripe_customer_id
from services.supabase.repository_features.get_repository_features import (
    get_repository_features,
)
from services.supabase.usage.insert_usage import Trigger
from services.supabase.usage.update_usage import update_usage
from services.supabase.users.get_user import get_user
from services.stripe.check_availability import check_availability
from services.stripe.create_stripe_customer import create_stripe_customer

# Local imports (Utils)
from utils.files.is_test_file import is_test_file
from utils.files.merge_test_file_headers import merge_test_file_headers
from utils.images.get_base64 import get_base64
from utils.progress_bar.progress_bar import create_progress_bar
from utils.text.comment_identifiers import PROGRESS_BAR_EMPTY, PROGRESS_BAR_FILLED
from utils.text.text_copy import (
    UPDATE_COMMENT_FOR_422,
    git_command,
    pull_request_completed,
)
from utils.time.get_timeout_message import get_timeout_message
from utils.time.is_lambda_timeout_approaching import is_lambda_timeout_approaching
from utils.urls.extract_urls import extract_image_urls


def create_pr_from_issue(
    payload: GitHubLabeledPayload | JiraPayload,
    trigger: Trigger,
    input_from: Literal["github", "jira"],
    lambda_info: dict[str, str | None] | None = None,
) -> None:
    current_time: float = time.time()

    # Extract label and validate it
    if (
        trigger == "issue_label"
        and input_from == "github"
        and "label" in payload
        and payload["label"]["name"] != PRODUCT_ID
    ):
        return

    # Deconstruct payload based on input_from
    base_args = None
    repo_settings = None
    if input_from == "github":
        base_args, repo_settings = deconstruct_github_payload(
            payload=cast(GitHubLabeledPayload, payload)
        )
    elif input_from == "jira":
        base_args, repo_settings = deconstruct_jira_payload(
            payload=cast(JiraPayload, payload)
        )

    # Ensure skip_ci is set to True for development commits
    base_args["skip_ci"] = True

    # Get some base args for early notifications
    owner_name = base_args["owner"]
    repo_name = base_args["repo"]
    issue_number = base_args["issue_number"]
    issue_title = base_args["issue_title"]
    sender_name = base_args["sender_name"]

    # Start notification
    start_msg = f"Issue handler started: `{trigger}` by `{sender_name}` for `{issue_number}:{issue_title}` in `{owner_name}/{repo_name}`"
    thread_ts = slack_notify(start_msg)

    # Delete all comments made by GitAuto except the one with the checkbox to clean up the issue
    if input_from == "github":
        gitauto_identifiers = [
            COMPLETED_PR,
            UPDATE_COMMENT_FOR_422,
            PROGRESS_BAR_FILLED,
            PROGRESS_BAR_EMPTY,
        ]
        delete_comments_by_identifiers(
            base_args=base_args, identifiers=gitauto_identifiers
        )

    # Create a comment to track progress
    p = 0
    log_messages = []
    msg = "Got your request."
    log_messages.append(msg)
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    comment_url = create_comment(
        owner=owner_name,
        repo=repo_name,
        token=base_args["token"],
        issue_number=issue_number,
        body=comment_body,
    )
    base_args["comment_url"] = comment_url

    # Get some base args
    installation_id = base_args["installation_id"]
    owner_id = base_args["owner_id"]
    owner_type = base_args["owner_type"]
    repo_id = base_args["repo_id"]
    issue_body = base_args["issue_body"].replace(SETTINGS_LINKS, "").strip()
    issue_body_rendered = render_text(base_args=base_args, text=issue_body)
    issuer_name = base_args["issuer_name"]
    parent_issue_number = base_args.get("parent_issue_number")
    parent_issue_title = base_args.get("parent_issue_title")
    parent_issue_body = base_args.get("parent_issue_body")
    new_branch_name = base_args["new_branch"]
    sender_id = base_args["sender_id"]
    sender_email = base_args["sender_email"]
    github_urls = base_args["github_urls"]
    # other_urls = base_args["other_urls"]
    token = base_args["token"]
    is_automation = base_args["is_automation"]

    repo_features = get_repository_features(repo_id=repo_id)
    restrict_edit_to_target_test_file_only = (
        repo_features["restrict_edit_to_target_test_file_only"]
        if repo_features
        else True
    )
    allow_edit_any_file = (
        repo_features["allow_edit_any_file"] if repo_features else False
    )

    p += 5
    log_messages.append("Extracted metadata.")
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)), base_args=base_args
    )

    # Ensure stripe customer exists (create if needed)
    stripe_customer_id = get_stripe_customer_id(owner_id)
    if not stripe_customer_id:
        stripe_customer_id = create_stripe_customer(
            owner_id=owner_id,
            owner_name=owner_name,
            installation_id=installation_id,
            user_id=sender_id if sender_id else 0,
            user_name=sender_name if sender_name else "unknown",
        )
        if stripe_customer_id:
            update_stripe_customer_id(owner_id, stripe_customer_id)

    # Now check availability (stripe_customer_id will exist or be None if creation failed)
    availability_status = check_availability(
        owner_id=owner_id,
        owner_name=owner_name,
        repo_name=repo_name,
        installation_id=installation_id,
        sender_name=sender_name,
    )

    can_proceed = availability_status["can_proceed"]
    user_message = availability_status["user_message"]
    billing_type = availability_status["billing_type"]

    if availability_status["log_message"] and can_proceed:
        log_messages.append(availability_status["log_message"])

    p += 5
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)), base_args=base_args
    )

    # Notify the user if access is denied and early return
    if not can_proceed:
        body = user_message
        update_comment(body=body, base_args=base_args)
        print(body)

        # Send email notification if user is a credit user and has zero credits
        # Disabled: This would send emails every time schedule trigger runs, annoying users
        # if is_credit_user and sender_id:
        #     user = get_user(user_id=sender_id)
        #     if user and user.get("email"):
        #         subject, text = get_no_credits_email_text(sender_name)
        #         send_email(to=user["email"], subject=subject, text=text)

        # Early return notification
        slack_notify(availability_status["log_message"], thread_ts)
        return

    # Start async package installation early to run in parallel with LLM processing (returns immediately if already installed on EFS)
    start_async_install_on_efs(base_args)

    # Create a usage record
    usage_id = create_user_request(
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
        trigger=trigger,
        email=sender_email,
        lambda_info=lambda_info,
    )

    if input_from == "github":
        add_reaction_to_issue(
            issue_number=issue_number, content="eyes", base_args=base_args
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
        # Check if URL has a valid image extension (OpenAI only supports: png, jpeg, gif, webp)
        image_extensions = (".png", ".jpg", ".jpeg", ".gif", ".webp")
        if not any(url["url"].lower().endswith(ext) for ext in image_extensions):
            logging.warning(
                "Skipping non-image URL or unsupported format: %s", url["url"]
            )
            continue

        base64_image = get_base64(url=url["url"])

        if not base64_image:
            logging.warning("Failed to fetch image from URL: %s", url["url"])
            continue

        context = f"## Issue:\n{issue_title}\n\n## Issue Body:\n{issue_body}\n\n## Issue Comments:\n{'\n'.join(issue_comments)}"
        description = describe_image(base64_image=base64_image, context=context)
        description = f"## {url['alt']}\n\n{description}"
        issue_comments.append(description)
        create_comment(
            owner=owner_name,
            repo=repo_name,
            token=token,
            issue_number=issue_number,
            body=description,
        )

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
        }
    )

    # Create messages
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

    # Create initial empty commit and PR early in the process
    comment_body = "Creating initial PR..."
    p += 5
    log_messages.append(comment_body)
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)), base_args=base_args
    )
    create_empty_commit(
        base_args=base_args, message="Initial empty commit to create PR"
    )

    issue_link: str = f"{PR_BODY_STARTS_WITH}{issue_number}\n\n"
    pr_body = issue_link + git_command(new_branch_name=new_branch_name)
    pr_url, pr_number = create_pull_request(
        body=pr_body, title=issue_title, base_args=base_args
    )

    comment_body = f"Created pull request: {pr_url}"
    p += 5
    log_messages.append(comment_body)
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)),
        base_args=base_args,
    )

    # Loop a process explore repo and commit changes until the ticket is resolved
    previous_calls = []
    retry_count = 0
    total_token_input = 0
    total_token_output = 0
    while True:
        # Timeout check: Stop if we're approaching Lambda limit
        is_timeout_approaching, elapsed_time = is_lambda_timeout_approaching(
            current_time
        )
        if is_timeout_approaching:
            timeout_msg = get_timeout_message(elapsed_time, "Issue processing")
            log_messages.append(timeout_msg)
            update_comment(
                body=create_progress_bar(p=p, msg="\n".join(log_messages)),
                base_args=base_args,
            )
            break

        # Safety check: Stop if branch is deleted
        if not check_branch_exists(
            owner=owner_name, repo=repo_name, branch_name=new_branch_name, token=token
        ):
            body = f"Process stopped: Branch '{new_branch_name}' has been deleted"
            print(body)
            if comment_url:
                update_comment(body=body, base_args=base_args)
            break

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
            trigger=trigger,
            repo_settings=repo_settings,
            base_args=base_args,
            mode="explore",
            previous_calls=previous_calls,
            p=p,
            log_messages=log_messages,
            usage_id=usage_id,
            allow_edit_any_file=allow_edit_any_file,
            restrict_edit_to_target_test_file_only=restrict_edit_to_target_test_file_only,
        )
        total_token_input += token_input
        total_token_output += token_output

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
        #     trigger=trigger,
        #     repo_settings=repo_settings,
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
            trigger=trigger,
            repo_settings=repo_settings,
            base_args=base_args,
            mode="commit",
            previous_calls=previous_calls,
            p=p,
            log_messages=log_messages,
            usage_id=usage_id,
            allow_edit_any_file=allow_edit_any_file,
            restrict_edit_to_target_test_file_only=restrict_edit_to_target_test_file_only,
        )
        total_token_input += token_input
        total_token_output += token_output

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

    # Add headers to test files before triggering CI
    files_url = (
        f"{GITHUB_API_URL}/repos/{owner_name}/{repo_name}/pulls/{pr_number}/files"
    )
    changed_files = get_pull_request_files(url=files_url, token=token)

    for file_change in changed_files:
        file_path = file_change["filename"]
        if not is_test_file(file_path):
            continue

        file_content = get_raw_content(
            owner=owner_name,
            repo=repo_name,
            file_path=file_path,
            ref=new_branch_name,
            token=token,
        )
        if not file_content:
            continue

        updated_content = merge_test_file_headers(file_content, file_path)
        if not updated_content or updated_content == file_content:
            continue

        replace_remote_file_content(
            file_content=updated_content,
            file_path=file_path,
            base_args=base_args,
        )

    # Trigger final test workflows with an empty commit
    comment_body = "Triggering workflows..."
    p += 5
    log_messages.append(comment_body)
    update_comment(
        body=create_progress_bar(p=p, msg="\n".join(log_messages)), base_args=base_args
    )
    create_empty_commit(base_args=base_args)

    # Update the issue comment
    is_completed = True
    body_after_pr = pull_request_completed(
        issuer_name=issuer_name,
        sender_name=sender_name,
        pr_url=pr_url,
        is_automation=is_automation,
    )
    update_comment(body=body_after_pr, base_args=base_args)

    # Success notification
    success_msg = f"Work completed for {owner_name}/{repo_name} PR: {pr_url}"
    slack_notify(success_msg, thread_ts)

    end_time = time.time()
    update_usage(
        usage_id=usage_id,
        is_completed=is_completed,
        pr_number=pr_number,
        token_input=total_token_input,
        token_output=total_token_output,
        total_seconds=int(end_time - current_time),
    )

    # Insert credit usage if user is using credits (not paid subscription)
    if is_completed and billing_type == "credit":
        insert_credit(owner_id=owner_id, transaction_type="usage", usage_id=usage_id)

        # Check if user just ran out of credits and send casual notification
        owner = get_owner(owner_id=owner_id)
        if owner and owner["credit_balance_usd"] <= 0 and sender_id:
            user = get_user(user_id=sender_id)
            email = user.get("email") if user else None
            if email:
                subject, text = get_credits_depleted_email_text(sender_name)
                send_email(to=email, subject=subject, text=text)

    # End notification
    end_msg = "Completed" if is_completed else "@channel Failed"
    slack_notify(end_msg, thread_ts)
    return
