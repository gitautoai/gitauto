# Local imports
from ..supabase.supabase_manager import InstallationTokenManager
from .github_manager import GitHubManager
from config import LABEL, GITHUB_APP_ID, GITHUB_PRIVATE_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

# Initialize managers
github_manager = GitHubManager(GITHUB_APP_ID, GITHUB_PRIVATE_KEY)
supabase_manager = InstallationTokenManager(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


# Handle the installation created event
async def handle_installation_event(payload):
    installation_target_type = payload["installation"]["target_type"]
    installation_target_id = payload["installation"]["target_id"]
    installation_id = payload["installation"]["id"]
    installation_status = payload["action"]
    created_by_id = payload["sender"]["id"]
    created_by_name = payload["sender"]["login"]

    # Get the installation access token if the installation was not deleted
    access_token, expires_at = (github_manager.get_installation_access_token(installation_id) if installation_status != "deleted" else (None, None))

    # Determine the installation target name
    if installation_target_type == "User":
        installation_target_name = payload["installation"]["account"]["login"]
    elif installation_target_type == "Organization":
        installation_target_name = payload["installation"]["account"]["login"]
    elif installation_target_type == "Repository":
        installation_target_name = payload["repository"]["name"]
    else:
        installation_target_name = "Unknown"

    # Print the installation event based on the action
    if installation_status == "created":
        print(f"\nGitHub App installed on {installation_target_type}: {installation_target_name}")
    elif installation_status == "deleted":
        print(f"\nGitHub App uninstalled from {installation_target_type}: {installation_target_name}")

    # Save the installation details to the database
    supabase_manager.save_installation_token(
        installation_target_type, installation_target_id, installation_target_name, installation_id, installation_status, created_by_id, created_by_name
    )

    return access_token, expires_at


# Handle the issue labeled event
async def handle_issue_labeled(payload):
    issue = payload["issue"]
    label = payload["label"]["name"]
    if label == LABEL:
        print(f"Issue with label '{label}' detected.")
        print(f"Title: {issue['title']}")
        print(f"Content: {issue['body']}")


# Determine the event type and call the appropriate handler
async def handle_webhook_event(payload):
    action = payload.get("action")

    # Check the type of webhook event and handle accordingly
    if action == "created" and "installation" in payload:
        await handle_installation_event(payload)

    elif action == "updated" and "installation" in payload:
        await handle_installation_event(payload)

    elif action == "deleted" and "installation" in payload:
        await handle_installation_event(payload)

    elif action == "labeled" and "issue" in payload:
        await handle_issue_labeled(payload)
