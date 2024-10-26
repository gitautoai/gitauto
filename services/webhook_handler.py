    # Ensure all changes are committed and pushed
    # Update README and other relevant documentation
    # Document new functions and changes
    # Review and refactor code for clarity and efficiency
    # Ensure all new code is covered by tests
    # Add unit tests for new functions
    # Add error handling for API requests
    # Log the response from the GitHub API when posting comments
    # Add logging for issue assessment and clarification requests
    # Ensure backward compatibility by maintaining existing processes
    # Terminate further processing if clarification is requested
def handle_issue_event(issue_details, issue_number, token):
    try:
        # Existing logic
    except Exception as e:
    if not assess_issue_details(issue_details):
        print(f"Error handling issue event: {e}")
        return None
        request_clarification(issue_number, token)
from services.github.github_manager import assess_issue_details, request_clarification
from services.github.github_manager import comment_on_issue
def comment_on_issue(issue_number, comment, token):
    """Post a comment on a GitHub issue."""
    url = f"https://api.github.com/repos/{{owner}}/{{repo}}/issues/{{issue_number}}/comments"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": comment}
    response = requests.post(url, headers=headers, json=data)
    return response.status_code, response.json()
# Standard imports
import re
from typing import Any

# Local imports
from config import (
    GITHUB_CHECK_RUN_FAILURES,
    PRODUCT_ID,
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
    PR_BODY_STARTS_WITH,
    ISSUE_NUMBER_FORMAT,
)
from services.check_run_handler import handle_check_run
from services.github.github_manager import (
    add_issue_templates,
    create_comment_on_issue_with_gitauto_button,
    get_installation_access_token,
    # turn_on_issue,
)
from services.github.github_types import GitHubInstallationPayload
from services.supabase import SupabaseManager
from services.gitauto_handler import handle_gitauto
from utils.handle_exceptions import handle_exceptions

# Initialize managers
supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def handle_installation_created(payload: GitHubInstallationPayload) -> None:
    """Creates installation records on GitAuto APP installation"""
    installation_id: int = payload["installation"]["id"]
    owner_type: str = payload["installation"]["account"]["type"]
    owner_name: str = payload["installation"]["account"]["login"]
    owner_id: int = payload["installation"]["account"]["id"]
    repo_full_names: list[str] = [repo["full_name"] for repo in payload["repositories"]]
    user_id: int = payload["sender"]["id"]
    user_name: str = payload["sender"]["login"]
    token: str = get_installation_access_token(installation_id=installation_id)

    # Create installation record in Supabase
    supabase_manager.create_installation(
        installation_id=installation_id,
        owner_type=owner_type,
        owner_name=owner_name,
        owner_id=owner_id,
        user_id=user_id,
        user_name=user_name,
    )

    # Add issue templates to the repositories
    for i, full_name in enumerate(iterable=repo_full_names, start=1):
        print(f"\nAdding issue templates ({i}/{len(repo_full_names)}): {full_name}")
        # turn_on_issue(full_name=full_name, token=token)
        add_issue_templates(full_name=full_name, installer_name=user_name, token=token)


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def handle_installation_deleted(payload: GitHubInstallationPayload) -> None:
    """Soft deletes installation record on GitAuto APP installation"""
    installation_id: int = payload["installation"]["id"]
    supabase_manager.delete_installation(installation_id=installation_id)


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def handle_installation_repos_added(payload) -> None:
    installation_id: int = payload["installation"]["id"]
    repo_full_names: list[str] = [
        repo["full_name"] for repo in payload["repositories_added"]
    ]
    sender_name: str = payload["sender"]["login"]
    token: str = get_installation_access_token(installation_id=installation_id)
    for full_name in repo_full_names:
        # turn_on_issue(full_name=full_name, token=token)
        add_issue_templates(
            full_name=full_name, installer_name=sender_name, token=token
        )


@handle_exceptions(default_return_value=None, raise_on_error=True)
async def handle_webhook_event(event_name: str, payload: dict[str, Any]) -> None:
    """
    Determine the event type and call the appropriate handler.
    Check the type of webhook event and handle accordingly.
    https://docs.github.com/en/apps/github-marketplace/using-the-github-marketplace-api-in-your-app/handling-new-purchases-and-free-trials
    https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=purchased#marketplace_purchase
    """
    action: str = payload.get("action")
    if not action:
        return

    # if event_name == "marketplace_purchase" and action in ("purchased"):
    #     print("Marketplace purchase is triggered")
    #     await handle_installation_created(payload=payload)

    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#installation
    if event_name == "installation" and action in ("created"):
        print("Installation is created")
        await handle_installation_created(payload=payload)
        return
    if event_name == "installation" and action in ("deleted"):
        print("Installation is deleted")
        await handle_installation_deleted(payload=payload)
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
            await handle_gitauto(payload=payload, trigger_type="label")
            return
        if action == "opened":
            create_comment_on_issue_with_gitauto_button(payload=payload)
            return

    # Run GitAuto when checkbox is checked (edited)
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#issue_comment
    if event_name == "issue_comment" and action == "edited":
        issue_handled = False
        search_text = "- [x] Generate PR"
        if PRODUCT_ID != "gitauto":
            search_text += " - " + PRODUCT_ID
            if payload["comment"]["body"].find(search_text) != -1:
                issue_handled = True
                await handle_gitauto(payload=payload, trigger_type="comment")
        else:
            if (
                payload["comment"]["body"].find(search_text) != -1
                and payload["comment"]["body"].find(search_text + " - ") == -1
            ):
                issue_handled = True
                await handle_gitauto(payload=payload, trigger_type="comment")
        if not issue_handled:
            print("Edit is not an activated GitAtuo trigger.")
        return

    # Monitor check_run failure and re-run agent with failure reason
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#check_run
    if event_name == "check_run" and action in ("completed"):
        conclusion: str = payload["check_run"]["conclusion"]
        if conclusion in GITHUB_CHECK_RUN_FAILURES:
            handle_check_run(payload=payload)
        return

    # Track merged PRs as this is also our success status
    # See https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request
    if event_name == "pull_request" and action == "closed":
        pull_request = payload.get("pull_request")
        if not pull_request:
            return

        # Check PR is merged and this is correct GitAuto environment
        if pull_request["merged_at"] is not None and pull_request["head"][
            "ref"
        ].startswith(PRODUCT_ID + ISSUE_NUMBER_FORMAT):
            # Create unique_issue_id to update merged status
            body: str = pull_request["body"]
            if not body.startswith(PR_BODY_STARTS_WITH):
                return
            pattern = re.compile(r"/issues/(\d+)")
            match = re.search(pattern, body)
            if not match:
                return
            issue_number = match.group(1)
            owner_type = payload["repository"]["owner"]["type"]
            unique_issue_id = f"{owner_type}/{payload['repository']['owner']['login']}/{payload['repository']['name']}#{issue_number}"
            supabase_manager.set_issue_to_merged(unique_issue_id=unique_issue_id)
        return

    # Unhandled events are captured here
    print(f"Event '{event_name}' with action '{action}' was received but skipped.")
