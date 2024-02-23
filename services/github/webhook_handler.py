from pathlib import Path

# Local imports
from agent.coders import Coder
from agent.inputoutput import InputOutput
from agent.models import Model
from config import  GITHUB_APP_ID, GITHUB_PRIVATE_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, ENV
from services.github.github_manager import GitHubManager
from services.github.github_types import GitHubInstallationPayload
from services.supabase.supabase_manager import InstallationTokenManager
from .labeled_issue import handle_issue_labeled

# Initialize managers
github_manager = GitHubManager(app_id=GITHUB_APP_ID, private_key=GITHUB_PRIVATE_KEY)
supabase_manager = InstallationTokenManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)


async def handle_installation_created(payload: GitHubInstallationPayload) -> None:
    installation_id: int = payload["installation"]["id"]
    account_login: str = payload["installation"]["account"]["login"]
    html_url: str = payload["installation"]["account"]["html_url"]
    action: str = payload.get("action")
    repositories = []
    repository_ids = []
    if action == 'created':
        repositories: list[str] = [obj.get('full_name') for obj in payload["repositories"]]
        repository_ids: list[int] = [obj.get('id') for obj in payload["repositories"]]
    if action == 'added':
        repositories = [obj.get('full_name') for obj in payload["repositories_added"]]
        repository_ids = [obj.get('id') for obj in payload["repositories_added"]]

    supabase_manager.save_installation_token(installation_id=installation_id, account_login=account_login, html_url=html_url, repositories=repositories, repository_ids=repository_ids)


async def handle_installation_deleted(payload: GitHubInstallationPayload) -> None:
    installation_id: int = payload["installation"]["id"]
    supabase_manager.delete_installation_token(installation_id=installation_id)




async def handle_webhook_event(payload) -> None:
    if ('action' in payload):
        action = payload.get("action")
        if (action == "created" or action == "added") and "installation" in payload:
            print("Installaton is created/added")
            await handle_installation_created(payload=payload)

        elif (action == "deleted" or action == "removed") and "installation" in payload:
            print("Installaton is deleted/removed")
            await handle_installation_deleted(payload=payload)

        elif action == "labeled" and "issue" in payload:
            print("Issue is labeled")
            await handle_issue_labeled(payload=payload)
