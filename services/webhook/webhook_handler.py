# Standard imports
import logging
from typing import Any, cast

# Local imports
from config import (
    GITHUB_CHECK_RUN_FAILURES,
    ISSUE_NUMBER_FORMAT,
    PR_BODY_STARTS_WITH,
    PRODUCT_ID,
)

# Local imports (AWS)
from services.aws.delete_scheduler import delete_scheduler
from services.aws.get_schedulers import get_schedulers_by_owner_id

# Local imports (GitHub)
from services.github.comments.create_gitauto_button_comment import (
    create_gitauto_button_comment,
)

# Local imports (Resend)
from services.github.types.github_types import (
    CheckRunCompletedPayload,
    GitHubInstallationPayload,
    GitHubLabeledPayload,
    GitHubPullRequestClosedPayload,
)
from services.github.types.owner import OwnerType
from services.github.types.pull_request_webhook_payload import PullRequestWebhookPayload
from services.github.types.webhook.issue_comment import IssueCommentWebhookPayload
from services.resend.get_first_name import get_first_name
from services.resend.send_email import send_email
from services.resend.text.suspend_email import get_suspend_email_text
from services.resend.text.uninstall_email import get_uninstall_email_text

# Local imports (Slack)
from services.slack.slack_notify import slack_notify

# Local imports (Supabase)
from services.supabase.installations.delete_installation import delete_installation
from services.supabase.installations.unsuspend_installation import (
    unsuspend_installation,
)
from services.supabase.issues.update_issue_merged import update_issue_merged
from services.supabase.users.get_user import get_user

# Local imports (Webhooks)
from services.webhook.check_run_handler import handle_check_run
from services.webhook.handle_coverage_report import handle_coverage_report
from services.webhook.issue_handler import create_pr_from_issue
from services.webhook.pr_body_handler import write_pr_description
from services.webhook.review_run_handler import handle_review_run
from services.webhook.screenshot_handler import handle_screenshot_comparison
from services.webhook.handle_installation import handle_installation_created
from services.webhook.handle_installation_repos import handle_installation_repos_added
from services.webhook.merge_handler import handle_pr_merged
from services.webhook.pr_checkbox_handler import handle_pr_checkbox_trigger
from services.webhook.utils.create_pr_checkbox_comment import create_pr_checkbox_comment

# Local imports (Utils)
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=True)
async def handle_webhook_event(event_name: str, payload: dict[str, Any]):
    """
    Determine the event type and call the appropriate handler.
    Check the type of webhook event and handle accordingly.
    https://docs.github.com/en/apps/github-marketplace/using-the-github-marketplace-api-in-your-app/handling-new-purchases-and-free-trials
    https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=purchased#marketplace_purchase
    """
    action: str | None = payload.get("action")

    # Handle push events from non-bot users
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#push
    # if event_name == "push":
    # return

    # For other events, we need to check the action
    if not action:
        return

    # if event_name == "marketplace_purchase" and action in ("purchased"):
    #     logging.info("Marketplace purchase is triggered")
    #     await handle_installation_created(payload=payload)

    # https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=created#installation
    if event_name == "installation" and action in ("created"):
        owner_name = payload["installation"]["account"]["login"]
        sender_name = payload["sender"]["login"]
        msg = f"🎉 New installation by `{sender_name}` for `{owner_name}`"
        slack_notify(msg)
        handle_installation_created(payload=cast(GitHubInstallationPayload, payload))
        return

    # https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=deleted#installation
    if event_name == "installation" and action in ("deleted"):
        owner_id = payload["installation"]["account"]["id"]
        owner_name = payload["installation"]["account"]["login"]
        sender_name = payload["sender"]["login"]
        msg = f":skull: Installation deleted by `{sender_name}` for `{owner_name}`"
        slack_notify(msg)

        delete_installation(
            installation_id=payload["installation"]["id"],
            user_id=payload["sender"]["id"],
            user_name=payload["sender"]["login"],
        )

        # Send uninstall email
        user = get_user(payload["sender"]["id"])
        if user and user.get("email"):
            first_name = get_first_name(user.get("user_name", ""))
            subject, text = get_uninstall_email_text(first_name)
            send_email(to=user["email"], subject=subject, text=text)

        # Delete AWS schedulers for this owner
        schedulers_to_delete = get_schedulers_by_owner_id(owner_id)
        for schedule_name in schedulers_to_delete:
            delete_scheduler(schedule_name)

        return

    # https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=suspend#installation
    if event_name == "installation" and action in ("suspend"):
        owner_id = payload["installation"]["account"]["id"]
        owner_name = payload["installation"]["account"]["login"]
        sender_name = payload["sender"]["login"]
        msg = f":skull: Installation suspended by `{sender_name}` for `{owner_name}`"
        slack_notify(msg)

        delete_installation(
            installation_id=payload["installation"]["id"],
            user_id=payload["sender"]["id"],
            user_name=payload["sender"]["login"],
        )

        # Send suspend email
        user = get_user(payload["sender"]["id"])
        if user and user.get("email"):
            first_name = get_first_name(user.get("user_name", ""))
            subject, text = get_suspend_email_text(first_name)
            send_email(to=user["email"], subject=subject, text=text)

        # Delete AWS schedulers for this owner
        schedulers_to_delete = get_schedulers_by_owner_id(owner_id)
        for schedule_name in schedulers_to_delete:
            delete_scheduler(schedule_name)

        return

    # https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=unsuspend#installation
    if event_name == "installation" and action in ("unsuspend"):
        owner_name = payload["installation"]["account"]["login"]
        sender_name = payload["sender"]["login"]
        msg = f"🎉 Installation unsuspended by `{sender_name}` for `{owner_name}`"
        slack_notify(msg)
        unsuspend_installation(installation_id=payload["installation"]["id"])
        return

    # Add issue templates to the repositories when GitAuto is added to a repository
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#installation_repositories
    if event_name == "installation_repositories" and action in ("added"):
        handle_installation_repos_added(payload=payload)
        return

    # Handle issue events
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#issues
    if event_name == "issues":
        if action == "labeled":
            create_pr_from_issue(
                payload=cast(GitHubLabeledPayload, payload),
                trigger="issue_label",
                input_from="github",
            )
            return
        if action == "opened":
            create_gitauto_button_comment(payload=cast(GitHubLabeledPayload, payload))
            return

    # Run GitAuto when checkbox is checked (edited)
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#issue_comment
    if event_name == "issue_comment" and action == "edited":
        await handle_pr_checkbox_trigger(
            payload=cast(IssueCommentWebhookPayload, payload)
        )

        search_text = "- [x] Generate PR"
        comment_body = payload["comment"]["body"]

        # For dev environment, require "- [x] Generate PR - dev" checkbox
        if (
            PRODUCT_ID != "gitauto"
            and (search_text + " - " + PRODUCT_ID) in comment_body
        ):
            create_pr_from_issue(
                payload=cast(GitHubLabeledPayload, payload),
                trigger="issue_comment",
                input_from="github",
            )
            return

        # For production environment, ensure it's just "- [x] Generate PR" without any suffix
        # This prevents both prod and dev from triggering on prod checkbox
        if search_text in comment_body and (search_text + " - ") not in comment_body:
            create_pr_from_issue(
                payload=cast(GitHubLabeledPayload, payload),
                trigger="issue_comment",
                input_from="github",
            )
        return

    # Monitor check_run failure and re-run agent with failure reason
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#check_run
    if event_name == "check_run" and action in ("completed"):
        conclusion: str = payload["check_run"]["conclusion"]
        if conclusion in GITHUB_CHECK_RUN_FAILURES:
            handle_check_run(payload=cast(CheckRunCompletedPayload, payload))
        return

    # Write a PR description to the issue when GitAuto opened the PR
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request
    if event_name == "pull_request" and action == "opened":
        create_pr_checkbox_comment(payload=cast(PullRequestWebhookPayload, payload))
        write_pr_description(payload=payload)
        await handle_screenshot_comparison(payload=payload)
        return

    # Compare screenshots when the PR is synchronized
    if event_name == "pull_request" and action in ("synchronize"):
        create_pr_checkbox_comment(payload=cast(PullRequestWebhookPayload, payload))
        await handle_screenshot_comparison(payload=payload)
        return

    # Track merged PRs as this is also our success status
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request
    if event_name == "pull_request" and action == "closed":
        pull_request = payload.get("pull_request")
        if not pull_request:
            return

        # Check PR is merged and this is correct GitAuto environment
        merged_at = cast(str, pull_request.get("merged_at", ""))
        ref = cast(str, pull_request.get("head", {}).get("ref", ""))

        if not merged_at or not ref:
            return

        if not ref.startswith(PRODUCT_ID + ISSUE_NUMBER_FORMAT):
            handle_pr_merged(payload=cast(GitHubPullRequestClosedPayload, payload))
            return

        # Get issue number from PR body
        body: str = pull_request["body"]
        if not body or not body.startswith(PR_BODY_STARTS_WITH):
            return

        issue_ref = body.split()[1]  # "Resolves #714" -> ["Resolves", "#714"]
        if not issue_ref.startswith("#"):
            return

        issue_number = int(issue_ref[1:])  # "#714" -> 714
        repository: dict[str, Any] = payload["repository"]
        owner_type: OwnerType = repository["owner"]["type"]
        owner_name: str = repository["owner"]["login"]
        repo_name: str = repository["name"]
        update_issue_merged(
            owner_type=owner_type,
            owner_name=owner_name,
            repo_name=repo_name,
            issue_number=issue_number,
            merged=True,
        )

        # Notify Slack
        sender_name: str = payload["sender"]["login"]
        author_name: str = payload["pull_request"]["user"]["login"]
        msg = f"🎉 PR created by `{author_name}` was merged by `{sender_name}` for `{owner_name}/{repo_name}`"
        slack_notify(msg)
        return

    # https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request_review_comment
    # Do nothing when action is "deleted"
    if event_name == "pull_request_review_comment" and action in ("created", "edited"):
        handle_review_run(payload=payload)
        return

    # Add workflow_run event handler (GitHub Actions)
    if event_name == "workflow_run" and action == "completed":
        if payload["workflow_run"]["conclusion"] == "success":
            handle_coverage_report(
                owner_id=payload["repository"]["owner"]["id"],
                owner_name=payload["repository"]["owner"]["login"],
                repo_id=payload["repository"]["id"],
                repo_name=payload["repository"]["name"],
                installation_id=payload["installation"]["id"],
                run_id=payload["workflow_run"]["id"],
                head_branch=payload["workflow_run"]["head_branch"],
                user_name=payload["sender"]["login"],
            )
        return

    # Add check_suite event handler (CircleCI only)
    if (
        event_name == "check_suite"
        and action == "completed"
        and payload["check_suite"]["app"]["slug"] == "circleci-checks"
    ):
        if payload["check_suite"]["conclusion"] == "success":
            repository = payload["repository"]
            owner_id = repository["owner"]["id"]
            owner_name = repository["owner"]["login"]
            repo_name = repository["name"]
            check_suite = payload["check_suite"]
            logging.info(
                "Processing CircleCI check_suite completion for %s/%s (run_id: %s)",
                owner_name,
                repo_name,
                check_suite["id"],
            )
            handle_coverage_report(
                owner_id=owner_id,
                owner_name=owner_name,
                repo_id=repository["id"],
                repo_name=repo_name,
                installation_id=payload["installation"]["id"],
                run_id=check_suite["id"],
                head_branch=check_suite["head_branch"],
                user_name=payload["sender"]["login"],
                source="circleci",
            )
        return
