# Standard imports
from typing import Any, cast

# Local imports
from config import (
    GITHUB_CHECK_RUN_FAILURES,
    PRODUCT_ID,
    PR_BODY_STARTS_WITH,
    ISSUE_NUMBER_FORMAT,
)
from services.coverages.coverage_analyzer import handle_workflow_coverage
from services.github.comments.create_gitauto_button_comment import (
    create_gitauto_button_comment,
)
from services.slack.slack import slack

# Local imports (Supabase)
from services.supabase.installations.delete_installation import delete_installation
from services.supabase.installations.unsuspend_installation import (
    unsuspend_installation,
)
from services.supabase.issues.update_issue_merged import update_issue_merged

# Local imports (Webhooks)
from services.webhook.check_run_handler import handle_check_run
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
    #     print("Marketplace purchase is triggered")
    #     await handle_installation_created(payload=payload)

    # https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=created#installation
    if event_name == "installation" and action in ("created"):
        msg = f"🎉 New installation by `{payload['sender']['login']}` for `{payload['installation']['account']['login']}`"
        slack(msg)
        await handle_installation_created(payload=payload)
        return

    # https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=deleted#installation
    if event_name == "installation" and action in ("deleted"):
        msg = f":skull: Installation deleted by `{payload['sender']['login']}` for `{payload['installation']['account']['login']}`"
        slack(msg)
        delete_installation(
            installation_id=payload["installation"]["id"],
            user_id=payload["sender"]["id"],
            user_name=payload["sender"]["login"],
        )
        return

    # https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=suspend#installation
    if event_name == "installation" and action in ("suspend"):
        msg = f":skull: Installation suspended by `{payload['sender']['login']}` for `{payload['installation']['account']['login']}`"
        slack(msg)
        delete_installation(
            installation_id=payload["installation"]["id"],
            user_id=payload["sender"]["id"],
            user_name=payload["sender"]["login"],
        )
        return

    # https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=unsuspend#installation
    if event_name == "installation" and action in ("unsuspend"):
        msg = f"🎉 Installation unsuspended by `{payload['sender']['login']}` for `{payload['installation']['account']['login']}`"
        slack(msg)
        unsuspend_installation(installation_id=payload["installation"]["id"])
        return

    # Add issue templates to the repositories when GitAuto is added to a repository
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#installation_repositories
    if event_name == "installation_repositories" and action in ("added"):
        await handle_installation_repos_added(payload=payload)
        return

    # Handle issue events
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#issues
    if event_name == "issues":
        if action == "labeled":
            await create_pr_from_issue(
                payload=payload, trigger="issue_label", input_from="github"
            )
            return
        if action == "opened":
            create_gitauto_button_comment(payload=payload)
            return

    # Run GitAuto when checkbox is checked (edited)
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#issue_comment
    if event_name == "issue_comment" and action == "edited":
        await handle_pr_checkbox_trigger(payload=payload)

        search_text = "- [x] Generate PR"
        comment_body = payload["comment"]["body"]

        # For dev environment, require "- [x] Generate PR - dev" checkbox
        if (
            PRODUCT_ID != "gitauto"
            and (search_text + " - " + PRODUCT_ID) in comment_body
        ):
            await create_pr_from_issue(
                payload=payload, trigger="issue_comment", input_from="github"
            )
            return

        # For production environment, ensure it's just "- [x] Generate PR" without any suffix
        # This prevents both prod and dev from triggering on prod checkbox
        if search_text in comment_body and (search_text + " - ") not in comment_body:
            await create_pr_from_issue(
                payload=payload, trigger="issue_comment", input_from="github"
            )
        return

    # Monitor check_run failure and re-run agent with failure reason
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#check_run
    if event_name == "check_run" and action in ("completed"):
        conclusion: str = payload["check_run"]["conclusion"]
        if conclusion in GITHUB_CHECK_RUN_FAILURES:
            handle_check_run(payload=payload)
        return

    # Write a PR description to the issue when GitAuto opened the PR
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request
    if event_name == "pull_request" and action == "opened":
        create_pr_checkbox_comment(payload=payload)
        write_pr_description(payload=payload)
        await handle_screenshot_comparison(payload=payload)
        return

    # Compare screenshots when the PR is synchronized
    if event_name == "pull_request" and action in ("synchronize"):
        create_pr_checkbox_comment(payload=payload)
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
            handle_pr_merged(payload=payload)
            return

        # Get issue number from PR body
        body: str = pull_request["body"]
        if not body or not body.startswith(PR_BODY_STARTS_WITH):
            print(f"PR body does not start with {PR_BODY_STARTS_WITH}")
            return

        issue_ref = body.split()[1]  # "Resolves #714" -> ["Resolves", "#714"]
        if not issue_ref.startswith("#"):
            print(f"Unexpected PR body format: {body}")
            return

        issue_number = int(issue_ref[1:])  # "#714" -> 714
        repository = payload["repository"]
        owner_type = repository["owner"]["type"]
        owner_name = repository["owner"]["login"]
        repo_name = repository["name"]
        update_issue_merged(
            owner_type=owner_type,
            owner_name=owner_name,
            repo_name=repo_name,
            issue_number=issue_number,
            merged=True,
        )

        msg = f"🎉 PR merged by `{payload['sender']['login']}` for `{payload['repository']['name']}`"
        slack(msg)
        return

    # https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request_review_comment
    # Do nothing when action is "deleted"
    if event_name == "pull_request_review_comment" and action in ("created", "edited"):
        handle_review_run(payload=payload)
        return

    # Add workflow_run event handler
    if event_name == "workflow_run" and action == "completed":
        if payload["workflow_run"]["conclusion"] == "success":
            await handle_workflow_coverage(
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
