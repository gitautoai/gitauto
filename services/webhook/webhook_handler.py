# Standard imports
from typing import Any, cast

# Local imports
from config import (
    GITHUB_APP_USER_ID,
    GITHUB_APP_USER_NAME,
    GITHUB_CHECK_RUN_FAILURES,
    PRODUCT_ID,
)
from constants.triggers import NewPrTrigger
from services.github.types.webhook.review_run_payload import ReviewRunPayload
from services.github.types.github_types import (
    CheckSuiteCompletedPayload,
    InstallationPayload,
    InstallationRepositoriesPayload,
    PrClosedPayload,
    PrLabeledPayload,
)
from services.github.types.webhook.issue_comment import IssueCommentWebhookPayload
from services.github.types.webhook.pull_request_review import PullRequestReviewPayload
from services.github.types.webhook.push import PushWebhookPayload
from services.slack.slack_notify import slack_notify
from services.supabase.installations.unsuspend_installation import (
    unsuspend_installation,
)
from services.supabase.usage.get_usage_by_pr import get_usage_by_pr
from services.supabase.usage.update_usage import update_usage
from services.webhook.check_suite_handler import handle_check_suite
from services.webhook.handle_coverage_report import handle_coverage_report
from services.webhook.handle_installation import handle_installation_created
from services.webhook.handle_installation_deleted_or_suspended import (
    handle_installation_deleted_or_suspended,
)
from services.webhook.handle_installation_repos_added import (
    handle_installation_repos_added,
)
from services.webhook.handle_installation_repos_removed import (
    handle_installation_repos_removed,
)
from services.webhook.new_pr_handler import handle_new_pr
from services.webhook.pr_body_handler import write_pr_description
from services.webhook.push_handler import handle_push
from services.github.pulls.get_pull_request import get_pull_request
from services.github.pulls.get_review_inline_comments import get_review_inline_comments
from services.github.token.get_installation_token import get_installation_access_token
from services.webhook.review_run_handler import handle_review_run
from services.webhook.utils.adapt_pr_comment_to_review_payload import (
    adapt_pr_comment_to_review_payload,
)
from services.webhook.utils.adapt_pr_review_to_review_payload import (
    adapt_pr_review_to_review_payload,
)
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
    # https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=suspend#installation
    if event_name == "installation" and action in ("deleted", "suspend"):
        typed_payload = cast(InstallationPayload, payload)
        handle_installation_deleted_or_suspended(payload=typed_payload, action=action)
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
            handle_installation_repos_added(payload=typed_payload)
            return

        if action == "removed":
            handle_installation_repos_removed(payload=typed_payload)
            return

    # Handle PR labeled events (triggered by dashboard or schedule adding gitauto label to a PR)
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request
    if event_name == "pull_request" and action == "labeled":
        typed_payload = cast(PrLabeledPayload, payload)

        # Only process when the "gitauto" label is specifically added
        label_name = typed_payload["label"]["name"]
        if label_name != PRODUCT_ID:
            logger.info("Ignoring non-gitauto label: %s", label_name)
            return

        # Reject bot senders (except GitAuto's own app for schedule triggers)
        sender = typed_payload["sender"]
        sender_login = sender["login"]
        if sender_login.endswith("[bot]") and sender["id"] != GITHUB_APP_USER_ID:
            logger.info("Ignoring label event from bot: %s", sender_login)
            return

        # Determine trigger from branch name: {PRODUCT_ID}/schedule-* vs {PRODUCT_ID}/dashboard-*
        head_ref = typed_payload["pull_request"]["head"]["ref"]
        prefix = f"{PRODUCT_ID}/"
        if not head_ref.startswith(prefix):
            logger.info("Ignoring non-gitauto branch: %s", head_ref)
            return

        suffix = head_ref[len(prefix) :]
        trigger = cast(NewPrTrigger, suffix.split("-")[0])
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
        typed_payload = cast(ReviewRunPayload, payload)
        await handle_review_run(
            payload=typed_payload,
            trigger="pr_file_review",
            lambda_info=lambda_info,
        )
        return

    # https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request_review
    if event_name == "pull_request_review" and action in ("submitted", "edited"):
        typed_payload = cast(PullRequestReviewPayload, payload)
        sender_login = typed_payload["sender"]["login"]
        if sender_login == GITHUB_APP_USER_NAME:
            logger.info("Ignoring PR review from GitAuto itself")
            return

        head_ref = typed_payload["pull_request"]["head"]["ref"]
        if not head_ref.startswith(PRODUCT_ID + "/"):
            logger.info("Ignoring PR review on non-GitAuto PR (branch: %s)", head_ref)
            return

        review = typed_payload["review"]
        state = review["state"]
        owner_name = typed_payload["repository"]["owner"]["login"]
        repo_name = typed_payload["repository"]["name"]
        pr_number = typed_payload["pull_request"]["number"]
        body = review["body"] or ""

        if state == "approved":
            logger.info(
                "PR #%d approved by %s for %s/%s",
                pr_number,
                sender_login,
                owner_name,
                repo_name,
            )
            return

        if state in ("changes_requested", "commented") and body.strip():
            # Skip if this review also has inline comments, which trigger separately via pull_request_review_comment with better file/line metadata
            review_id = review["id"]
            installation_id = typed_payload["installation"]["id"]
            token = get_installation_access_token(installation_id=installation_id)
            inline_comments = get_review_inline_comments(
                owner=owner_name,
                repo=repo_name,
                pr_number=pr_number,
                review_id=review_id,
                token=token,
            )
            if inline_comments:
                logger.info(
                    "PR #%d review (%s) by %s for %s/%s - has %d inline comments, skipping summary (inline events handle it)",
                    pr_number,
                    state,
                    sender_login,
                    owner_name,
                    repo_name,
                    len(inline_comments),
                )
                return

            adapted_payload = adapt_pr_review_to_review_payload(payload=typed_payload)
            if not adapted_payload:
                logger.info("Failed to adapt PR review payload, skipping")
                return
            await handle_review_run(
                payload=adapted_payload,
                trigger="pr_review",
                lambda_info=lambda_info,
            )
            return

        if state in ("changes_requested", "commented"):
            logger.info(
                "PR #%d review (%s) by %s for %s/%s - no review summary, skipping",
                pr_number,
                state,
                sender_login,
                owner_name,
                repo_name,
            )
            return

        logger.info("Ignoring PR review with state: %s", state)
        return

    # https://docs.github.com/en/webhooks/webhook-events-and-payloads#issue_comment
    # Handle general PR comments (not inline review comments)
    if event_name == "issue_comment" and action in ("created", "edited"):
        typed_payload = cast(IssueCommentWebhookPayload, payload)

        # Only handle PR comments, not issue comments
        if not typed_payload["issue"].get("pull_request"):
            logger.info("Ignoring issue comment (not a PR comment)")
            return

        # Skip if sender is GitAuto itself
        if typed_payload["sender"]["login"] == GITHUB_APP_USER_NAME:
            logger.info("Ignoring PR comment from GitAuto itself")
            return

        # Fetch full PR object since issue_comment payload only has a stub
        issue = typed_payload["issue"]
        repo_payload = typed_payload["repository"]
        owner_name = repo_payload["owner"]["login"]
        repo_name = repo_payload["name"]
        pr_number = issue["number"]
        installation_id = typed_payload["installation"]["id"]
        token = get_installation_access_token(installation_id=installation_id)
        pr = get_pull_request(
            owner=owner_name, repo=repo_name, pr_number=pr_number, token=token
        )
        if not pr:
            logger.info("Failed to fetch PR #%d, skipping", pr_number)
            return

        # Only handle comments on GitAuto PRs
        head_ref = pr["head"]["ref"]
        if not head_ref.startswith(PRODUCT_ID + "/"):
            logger.info("Ignoring PR comment on non-GitAuto PR (branch: %s)", head_ref)
            return

        adapted_payload = adapt_pr_comment_to_review_payload(
            payload=typed_payload, pull_request=pr
        )
        if not adapted_payload:
            logger.info("Failed to adapt issue comment payload, skipping")
            return
        await handle_review_run(
            payload=adapted_payload,
            trigger="pr_comment",
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
