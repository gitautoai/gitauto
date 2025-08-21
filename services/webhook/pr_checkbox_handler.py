# Standard imports
import json
from datetime import datetime
import time

# Local imports
from config import PRODUCT_ID, GITHUB_APP_USER_NAME
from constants.messages import SETTINGS_LINKS
from services.chat_with_agent import chat_with_agent
from services.resend.send_email import send_email
from services.resend.text.credits_depleted_email import get_credits_depleted_email_text

# Local imports (GitHub)
from services.github.branches.check_branch_exists import check_branch_exists
from services.github.comments.create_comment import create_comment
from services.github.comments.update_comment import update_comment
from services.github.commits.create_empty_commit import create_empty_commit
from services.github.pulls.get_pull_request import get_pull_request
from services.github.pulls.is_pull_request_open import is_pull_request_open
from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.github_types import BaseArgs
from services.github.types.webhook.issue_comment import IssueCommentWebhookPayload
from services.github.workflow_runs.cancel_workflow_runs import cancel_workflow_runs

# Local imports (Slack)
from services.slack.slack_notify import slack_notify

# Local imports (Supabase & Webhook)
from services.supabase.create_user_request import create_user_request
from services.supabase.credits.insert_credit import insert_credit
from services.supabase.repositories.get_repository import get_repository
from services.supabase.usage.is_request_limit_reached import is_request_limit_reached
from services.supabase.usage.update_usage import update_usage
from services.supabase.users.get_user import get_user
from services.supabase.owners.get_owner import get_owner
from services.webhook.utils.extract_selected_files import extract_selected_files

# Local imports (Utils)
from utils.error.handle_exceptions import handle_exceptions
from utils.progress_bar.progress_bar import create_progress_bar
from utils.text.reset_command import create_reset_command_message
from utils.text.text_copy import request_limit_reached
from utils.time.is_lambda_timeout_approaching import is_lambda_timeout_approaching
from utils.time.get_timeout_message import get_timeout_message


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def handle_pr_checkbox_trigger(payload: IssueCommentWebhookPayload):
    current_time = time.time()
    trigger = "pr_checkbox"

    # Skip if the comment editor is a bot
    sender = payload["sender"]
    sender_id = sender["id"]
    sender_name = sender["login"]
    if sender_name.endswith("[bot]"):
        return

    # Skip if the comment author is not GitAuto
    comment = payload["comment"]
    if comment["user"]["login"] != GITHUB_APP_USER_NAME:
        return

    search_text = "- [x] Generate Tests"
    if PRODUCT_ID != "gitauto":
        search_text += f" - {PRODUCT_ID}"

    # Skip if the comment body does not contain the search text
    comment_body = comment["body"].replace(SETTINGS_LINKS, "").strip()
    if search_text not in comment_body:
        return

    # Skip if no files are selected
    selected_files = extract_selected_files(comment_body)
    if not selected_files:
        return

    repository = payload["repository"]
    repo_id = repository["id"]
    repo_name = repository["name"]
    owner_name = repository["owner"]["login"]
    owner_type = repository["owner"]["type"]
    owner_id = repository["owner"]["id"]
    installation_id = payload["installation"]["id"]
    token = get_installation_access_token(installation_id=installation_id)

    issue_number = payload["issue"]["number"]

    # Start notification
    start_msg = f"PR checkbox handler started by `{sender_name}` for PR #{issue_number} in `{owner_name}/{repo_name}`"
    thread_ts = slack_notify(start_msg)

    # Check if the user has reached the request limit
    limit_result = is_request_limit_reached(
        installation_id=installation_id,
        owner_id=owner_id,
        owner_name=owner_name,
        owner_type=owner_type,
        repo_name=repo_name,
        issue_number=issue_number,
    )
    is_limit_reached = limit_result["is_limit_reached"]
    # _requests_left = limit_result["requests_left"]
    request_limit = limit_result["request_limit"]
    end_date = limit_result["end_date"]
    is_credit_user = limit_result["is_credit_user"]

    # Get PR info for base_args
    pr_data = get_pull_request(
        owner=owner_name, repo=repo_name, pull_number=issue_number, token=token
    )
    head_branch = pr_data["head"]["ref"]

    base_args: BaseArgs = {
        "input_from": "github",
        "owner_type": owner_type,
        "owner_id": owner_id,
        "owner": owner_name,
        "repo_id": repo_id,
        "repo": repo_name,
        "clone_url": repository.get("clone_url", ""),
        "is_fork": repository.get("fork", False),
        "issue_number": issue_number,
        "issue_title": pr_data.get("title", ""),
        "issue_body": pr_data.get("body", ""),
        "issue_comments": [],
        "latest_commit_sha": "",
        "issuer_name": sender_name,
        "base_branch": head_branch,
        "new_branch": head_branch,
        "installation_id": installation_id,
        "token": token,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "sender_email": "",
        "is_automation": False,
        "reviewers": [],
        "github_urls": [],
        "other_urls": [],
    }

    # If request limit is reached, create a comment and return early
    if is_limit_reached:
        body = request_limit_reached(
            user_name=sender_name, request_count=request_limit, end_date=end_date
        )

        create_comment(body=body, base_args=base_args)

        # Send email notification if user is a credit user and has zero credits
        # Disabled: This would send emails every time schedule trigger runs, annoying users
        # if is_credit_user and sender_id:
        #     user = get_user(user_id=sender_id)
        #     if user and user.get("email"):
        #         subject, text = get_no_credits_email_text(sender_name)
        #         send_email(to=user["email"], subject=subject, text=text)

        # Early return notification
        early_return_msg = f"Request limit reached for {owner_name}/{repo_name} - {request_limit} requests used"
        slack_notify(early_return_msg, thread_ts)
        return

    # Create a usage record
    usage_id = create_user_request(
        user_id=sender_id,
        user_name=sender_name,
        installation_id=installation_id,
        owner_id=owner_id,
        owner_type=owner_type,
        owner_name=owner_name,
        repo_id=repo_id,
        repo_name=repo_name,
        issue_number=issue_number,
        source="github",
        trigger="pr_checkbox",
        email=None,
    )

    # Cancel existing workflow runs since we'll be making new commits
    cancel_workflow_runs(
        owner=owner_name, repo=repo_name, branch=head_branch, token=token
    )

    repo_settings = get_repository(repo_id=repo_id)

    p = 0
    log_messages = []
    msg = f"Generating tests for {len(selected_files)} selected files."
    log_messages.append(msg)

    comment_body = create_progress_bar(p=0, msg="\n".join(log_messages))
    comment_url = create_comment(body=comment_body, base_args=base_args)
    base_args["comment_url"] = comment_url

    p += 10
    log_messages.append("Getting repository file tree.")
    comment_body = create_progress_bar(p=p, msg="\n".join(log_messages))
    update_comment(body=comment_body, base_args=base_args)

    today = datetime.now().strftime("%Y-%m-%d")

    input_message = {
        "selected_files": selected_files,
        "today": today,
    }

    messages = [{"role": "user", "content": json.dumps(input_message)}]

    previous_calls = []
    retry_count = 0
    while True:
        # Timeout check: Stop if we're approaching Lambda limit
        is_timeout_approaching, elapsed_time = is_lambda_timeout_approaching(
            current_time
        )
        if is_timeout_approaching:
            timeout_msg = get_timeout_message(
                elapsed_time, "PR test generation processing"
            )
            update_comment(body=timeout_msg, base_args=base_args)
            break

        # Safety check: Stop if PR is closed or branch is deleted
        if not is_pull_request_open(
            owner=owner_name, repo=repo_name, pull_number=issue_number, token=token
        ):
            body = f"Process stopped: Pull request #{issue_number} was closed during execution."
            print(body)
            update_comment(body=body, base_args=base_args)
            break

        if not check_branch_exists(
            owner=owner_name, repo=repo_name, branch_name=head_branch, token=token
        ):
            body = f"Process stopped: Branch '{head_branch}' has been deleted"
            print(body)
            update_comment(body=body, base_args=base_args)
            break

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
            trigger=trigger,
            repo_settings=repo_settings,
            base_args=base_args,
            mode="get",
            previous_calls=previous_calls,
            p=p,
            log_messages=log_messages,
        )

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
            trigger=trigger,
            repo_settings=repo_settings,
            base_args=base_args,
            mode="commit",
            previous_calls=previous_calls,
            p=p,
            log_messages=log_messages,
        )

        if not is_explored and not is_committed:
            break

        if not is_explored and is_committed:
            retry_count += 1
            if retry_count > 3:
                break
            continue

        if is_explored and not is_committed:
            retry_count += 1
            if retry_count > 3:
                break
            continue

        retry_count = 0

    body = "Creating final empty commit to trigger workflows..."
    update_comment(body=body, base_args=base_args)
    create_empty_commit(base_args=base_args)

    # Create final message with reset command
    final_msg = (
        "Finished generating tests for selected files!"
        + create_reset_command_message(head_branch)
    )
    update_comment(body=final_msg, base_args=base_args)

    # Update usage record
    end_time = time.time()
    update_usage(
        usage_id=usage_id,
        token_input=0,
        token_output=0,
        total_seconds=int(end_time - current_time),
        pr_number=issue_number,
        is_completed=True,
    )

    # Insert credit usage if user is using credits (not paid subscription)
    if is_credit_user:
        insert_credit(owner_id=owner_id, transaction_type="usage", usage_id=usage_id)

        # Check if user just ran out of credits and send casual notification
        owner = get_owner(owner_id=owner_id)
        if owner and owner["credit_balance_usd"] <= 0 and sender_id:
            user = get_user(user_id=sender_id)
            if user and user.get("email"):
                subject, text = get_credits_depleted_email_text(sender_name)
                send_email(to=user["email"], subject=subject, text=text)

    # End notification
    slack_notify("Completed", thread_ts)
