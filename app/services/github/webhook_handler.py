from config import LABEL, GITHUB_APP_ID, GITHUB_PRIVATE_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from ..supabase.supabase_manager import InstallationTokenManager
from .github_manager import GitHubManager

# Initialize managers
github_manager = GitHubManager(GITHUB_APP_ID, GITHUB_PRIVATE_KEY)
supabase_manager = InstallationTokenManager(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

from jwt import JWT, jwk_from_pem
import time
import sys

async def handle_installation_created(payload):
    installation_id = payload["installation"]["id"]
    account_login = payload["installation"]["account"]["login"]
    html_url = payload["installation"]["account"]["html_url"]
    repositories = [obj.get('full_name') for obj in payload["repositories"]]
    # Github access token will expire, so no need for this
    # access_token = github_manager.get_installation_access_token(installation_id)
    # print(f"Access token for installation ID: {installation_id} is {access_token}")
    supabase_manager.save_installation_token(installation_id, account_login, html_url, repositories)


# Handle the installation deleted event
async def handle_installation_deleted(payload):
    installation_id = payload["installation"]["id"]
    supabase_manager.delete_installation_token(installation_id)


# Handle the issue labeled event
async def handle_issue_labeled(payload):
    issue = payload["issue"]
    label = payload["label"]["name"]
    url = issue["html_url"]
    installation_id = payload["installation"]["id"]
    if label == LABEL:
        print(f"Issue with label '{label}' detected.")
        print(f"Title: {issue['title']}")
        print(f"Content: {issue['body']}")
    # Run our functionality


async def handle_webhook_event(payload):
    if('action' in payload):
        action = payload.get("action")
        if action == "created" and "installation" in payload:
            print("CREATED")
            await handle_installation_created(payload)
        elif (action == "deleted" or  action == "removed") and "installation" in payload:
            print("DELETED")
            await handle_installation_deleted(payload)
        elif action == "labeled" and "issue" in payload:
            print("LABELED")
            await handle_issue_labeled(payload)
