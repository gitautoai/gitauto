from config import LABEL, GITHUB_APP_ID, GITHUB_PRIVATE_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from ..supabase.supabase_manager import InstallationTokenManager
from .github_manager import GitHubManager

# Initialize managers
github_manager = GitHubManager(GITHUB_APP_ID, GITHUB_PRIVATE_KEY)
supabase_manager = InstallationTokenManager(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


async def handle_installation_created(payload):
    installation_id = payload["installation"]["id"]
    account_login = payload["installation"]["account"]["login"]
    html_url = payload["installation"]["account"]["html_url"]
    # Github access token will expire, so no need for this
    # access_token = github_manager.get_installation_access_token(installation_id)
    # print(f"Access token for installation ID: {installation_id} is {access_token}")
    supabase_manager.save_installation_token(installation_id, account_login, html_url)


# Handle the installation deleted event
async def handle_installation_deleted(payload):
    installation_id = payload["installation"]["id"]
    supabase_manager.delete_installation_token(installation_id)
    print(f"GitHub App uninstalled from installation ID: {installation_id}")


# Handle the issue labeled event
async def handle_issue_labeled(payload):
    issue = payload["issue"]
    label = payload["label"]["name"]
    if label == LABEL:
        print(f"Issue with label '{label}' detected.")
        print(f"Title: {issue['title']}")
        print(f"Content: {issue['body']}")
    # Run our functionality


async def handle_webhook_event(payload):
    if('action' in payload):
        action = payload.get("action")
        if action == "created" and "installation" in payload:
            await handle_installation_created(payload)
        elif action == "deleted" and "installation" in payload:
            await handle_installation_deleted(payload)
    elif('payload' in payload):       
        action = payload.get("payload").get('action')
        if action == "labeled" and "issue" in action:
            await handle_issue_labeled(payload)
