# Standard imports
from typing import Any, cast

# Local imports
from config import (
    GITHUB_CHECK_RUN_FAILURES,
    PRODUCT_ID,
)
from constants.triggers import Trigger
from payloads.github.pull_request_review_comment.types import (
    PullRequestReviewCommentPayload,
)
from services.aws.delete_scheduler import delete_scheduler
from services.aws.get_schedulers import get_schedulers_by_owner_id
from services.github.types.github_types import (
    CheckSuiteCompletedPayload,
    InstallationPayload,
    InstallationRepositoriesPayload,
    PrClosedPayload,
    PrLabeledPayload,
)
from services.github.types.webhook.push import PushWebhookPayload
from services.resend.get_first_name import get_first_name
from services.resend.send_email import send_email
from services.resend.text.suspend_email import get_suspend_email_text
from services.resend.text.uninstall_email import get_uninstall_email_text
from services.slack.slack_notify import slack_notify
from services.supabase.installations.delete_installation import delete_installation
from services.supabase.installations.unsuspend_installation import (
    unsuspend_installation,
)
from services.supabase.usage.get_usage_by_pr import get_usage_by_pr
from services.supabase.usage.update_usage import update_usage
from services.supabase.users.get_user import get_user
from services.webhook.check_suite_handler import handle_check_suite
from services.webhook.handle_coverage_report import handle_coverage_report
from services.webhook.handle_installation import handle_installation_created
from services.webhook.handle_installation_repos_added import (
    handle_installation_repos_added,
)
from services.webhook.handle_installation_repos_removed import (
    handle_installation_repos_removed,
)
from services.webhook.new_pr_handler import handle_new_pr
from services.webhook.pr_body_handler import write_pr_description
from services.webhook.push_handler import handle_push
from services.webhook.review_run_handler import handle_review_run
from services.webhook.successful_check_suite_handler import (
    handle_successful_check_suite,
)
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import (
    logger,
    set_event_action,
    set_pr_number,
    set_trigger,
)


@handle_exceptions(default_return_value=None, raise_on_error=True)
async def handle_webhook_event(
    event_name: str,
    payload: dict[str, Any],
    lambda_info: dict[str, str | None] | None = None,
):
    """
    Determine the event type and call the appropriate handler.
    Check the type of webhook event and handle accordingly.
    https://docs.github.com/en/apps/github-marketplace/using-the-github-marketplace-api-in-your-app/handling-new-purchases-and-free-trials
    https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=purchased#marketplace_purchase
    """
    action: str | None = payload.get("action")
    set_event_action(event_name, action or "")

    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#push
    if event_name == "push":
        handle_push(payload=cast(PushWebhookPayload, payload))
        return

    # For other events, we need to check the action
    if not action:
        return

    # if event_name == "marketplace_purchase" and action in ("purchased"):
    #     logger.info("Marketplace purchase is triggered")
    #     await handle_installation_created(payload=payload)

    # https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=created#installation
    if event_name == "installation" and action in ("created"):
        typed_payload = cast(InstallationPayload, payload)
        owner_name = typed_payload["installation"]["account"]["login"]
        sender_name = typed_payload["sender"]["login"]
        msg = f"🎉 New installation by `{sender_name}` for `{owner_name}`"
        slack_notify(msg)
        await handle_installation_created(payload=typed_payload)
        return

    # https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=deleted#installation
    if event_name == "installation" and action in ("deleted"):
        typed_payload = cast(InstallationPayload, payload)
        owner_id = typed_payload["installation"]["account"]["id"]
        owner_name = typed_payload["installation"]["account"]["login"]
        sender_name = typed_payload["sender"]["login"]
        msg = f":skull: Installation deleted by `{sender_name}` for `{owner_name}`"
        slack_notify(msg)

        delete_installation(
            installation_id=typed_payload["installation"]["id"],
            user_id=typed_payload["sender"]["id"],
            user_name=typed_payload["sender"]["login"],
        )

        # Send uninstall email
        user = get_user(typed_payload["sender"]["id"])
        email = user.get("email") if user else None
        user_name = user.get("user_name", "") if user else ""
        if email:
            first_name = get_first_name(user_name)
            subject, text = get_uninstall_email_text(first_name)
            send_email(to=email, subject=subject, text=text)

        # Delete AWS schedulers for this owner
        schedulers_to_delete = get_schedulers_by_owner_id(owner_id)
        for schedule_name in schedulers_to_delete:
            delete_scheduler(schedule_name)

        return

    # https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=suspend#installation
    if event_name == "installation" and action in ("suspend"):
        typed_payload = cast(InstallationPayload, payload)
        owner_id = typed_payload["installation"]["account"]["id"]
        owner_name = typed_payload["installation"]["account"]["login"]
        sender_name = typed_payload["sender"]["login"]
        msg = f":skull: Installation suspended by `{sender_name}` for `{owner_name}`"
        slack_notify(msg)

        delete_installation(
            installation_id=typed_payload["installation"]["id"],
            user_id=typed_payload["sender"]["id"],
            user_name=typed_payload["sender"]["login"],
        )

        # Send suspend email
        user = get_user(typed_payload["sender"]["id"])
        email = user.get("email") if user else None
        user_name = user.get("user_name", "") if user else ""
        if email:
            first_name = get_first_name(user_name)
            subject, text = get_suspend_email_text(first_name)
            send_email(to=email, subject=subject, text=text)

        # Delete AWS schedulers for this owner
        schedulers_to_delete = get_schedulers_by_owner_id(owner_id)
        for schedule_name in schedulers_to_delete:
            delete_scheduler(schedule_name)

        return

    # https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=unsuspend#installation
    if event_name == "installation" and action in ("unsuspend"):
        typed_payload = cast(InstallationPayload, payload)
        owner_name = typed_payload["installation"]["account"]["login"]
        sender_name = typed_payload["sender"]["login"]
        msg = f"🎉 Installation unsuspended by `{sender_name}` for `{owner_name}`"
        slack_notify(msg)
        unsuspend_installation(installation_id=typed_payload["installation"]["id"])
        return

    # Handle repository additions/removals when GitAuto is added to a repository
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#installation_repositories
    if event_name == "installation_repositories":
        typed_payload = cast(InstallationRepositoriesPayload, payload)
        if action == "added":
            await handle_installation_repos_added(payload=typed_payload)
            return

        if action == "removed":
            handle_installation_repos_removed(payload=typed_payload)
            return

    # Handle PR labeled events (triggered by dashboard or schedule adding gitauto label to a PR)
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request
    if event_name == "pull_request" and action == "labeled":
        typed_payload = cast(PrLabeledPayload, payload)
        # Determine trigger from branch name: {PRODUCT_ID}/schedule-* vs {PRODUCT_ID}/dashboard-*
        head_ref = typed_payload["pull_request"]["head"]["ref"]
        prefix = f"{PRODUCT_ID}/"
        suffix = head_ref[len(prefix) :] if head_ref.startswith(prefix) else ""
        trigger = cast(Trigger, suffix.split("-")[0] if suffix else "dashboard")
        await handle_new_pr(
            payload=typed_payload,
            trigger=trigger,
            lambda_info=lambda_info,
        )
        return

    # Write a PR description when GitAuto opened the PR
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request
    if event_name == "pull_request" and action == "opened":
        write_pr_description(payload=payload)
        return

    # Track merged PRs as this is also our success status
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request
    if event_name == "pull_request" and action == "closed":
        typed_payload = cast(PrClosedPayload, payload)
        pull_request = typed_payload["pull_request"]

        # Check PR is merged and this is correct GitAuto environment
        merged_at = pull_request.get("merged_at")
        ref = pull_request["head"]["ref"]

        if not merged_at or not ref:
            return

        if not ref.startswith(PRODUCT_ID + "/"):
            return

        set_trigger("pr_merged")
        repository = typed_payload["repository"]
        owner_name = repository["owner"]["login"]
        repo_name = repository["name"]

        # Update usage records for this PR to mark as merged
        pr_number = pull_request["number"]
        set_pr_number(pr_number)
        repo_id = repository["id"]
        owner_id = repository["owner"]["id"]

        usage_records = get_usage_by_pr(owner_id, repo_id, pr_number)
        for record in usage_records:
            update_usage(usage_id=record["id"], is_merged=True)

        # Notify Slack
        sender_name = typed_payload["sender"]["login"]
        pr_title = pull_request["title"]
        msg = f"🎉 PR #{pr_number} merged by `{sender_name}` for `{owner_name}/{repo_name}`: {pr_title}"
        slack_notify(msg)
        return

    # https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request_review_comment
    # Do nothing when action is "deleted"
    if event_name == "pull_request_review_comment" and action in ("created", "edited"):
        typed_payload = cast(PullRequestReviewCommentPayload, payload)
        await handle_review_run(
            payload=typed_payload,
            trigger="review_comment",
            lambda_info=lambda_info,
        )
        return

    # Add workflow_run event handler (GitHub Actions)
    if event_name == "workflow_run" and action == "completed":
        set_trigger("workflow_run_completed")
        if payload["workflow_run"]["conclusion"] == "success":
            handle_coverage_report(
                owner_id=payload["repository"]["owner"]["id"],
                owner_name=payload["repository"]["owner"]["login"],
                repo_id=payload["repository"]["id"],
                repo_name=payload["repository"]["name"],
                installation_id=payload["installation"]["id"],
                run_id=payload["workflow_run"]["id"],
                head_branch=payload["workflow_run"]["head_branch"],
                head_sha=payload["workflow_run"]["head_sha"],
                user_name=payload["sender"]["login"],
            )
        return

    # Handle check_suite events
    if event_name == "check_suite" and action == "completed":
        typed_payload = cast(CheckSuiteCompletedPayload, payload)
        check_suite = typed_payload["check_suite"]
        app_slug = check_suite["app"]["slug"]
        conclusion = check_suite["conclusion"]

        # Handle failures (test failures)
        if conclusion in GITHUB_CHECK_RUN_FAILURES:
            await handle_check_suite(payload=typed_payload, lambda_info=lambda_info)
            return

        # Skip non-success conclusions
        if conclusion != "success":
            return

        # Handle successful check for all CI systems
        handle_successful_check_suite(payload=typed_payload)

        # CircleCI: Handle coverage report
        if app_slug == "circleci-checks":
            set_trigger("check_suite_completed")
            repo = typed_payload["repository"]
            logger.info(
                "Processing CircleCI check_suite completion (run_id: %s)",
                check_suite["id"],
            )
            handle_coverage_report(
                owner_id=repo["owner"]["id"],
                owner_name=repo["owner"]["login"],
                repo_id=repo["id"],
                repo_name=repo["name"],
                installation_id=typed_payload["installation"]["id"],
                run_id=check_suite["id"],
                head_branch=check_suite["head_branch"],
                head_sha=check_suite["head_sha"],
                user_name=typed_payload["sender"]["login"],
                source="circleci",
            )

        return
