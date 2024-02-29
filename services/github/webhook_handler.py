# Standard imports
import time

# Local imports
from config import GITHUB_APP_ID, GITHUB_PRIVATE_KEY, LABEL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from services.github.github_manager import GitHubManager
from services.github.github_types import GitHubInstallationPayload, GitHubLabeledPayload, IssueInfo, RepositoryInfo
from services.openai.openai_agent import OpenAIAgent
from services.supabase.supabase_manager import InstallationTokenManager

# Initialize managers
github_manager = GitHubManager(app_id=GITHUB_APP_ID, private_key=GITHUB_PRIVATE_KEY)
openai_agent = OpenAIAgent()
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


async def handle_issue_labeled(payload: GitHubLabeledPayload):
    # Extract label and validate it
    label: str = payload["label"]["name"]
    if label != LABEL:
        return

    # Extract information from the payload
    issue: IssueInfo = payload["issue"]
    issue_title: str = issue["title"]
    issue_body: str = issue["body"] or ""
    issue_comments: list[str] = [""]
    installation_id: int = payload["installation"]["id"]
    repo: RepositoryInfo = payload["repository"]
    repo_url: str = repo["html_url"]
    owner: str = repo["owner"]["login"]
    repo_name: str = repo["name"]

    # Clone the repository
    token: str = github_manager.get_installation_access_token(installation_id=installation_id)
    file_paths: list[str] = github_manager.get_remote_file_tree(owner=owner, repo=repo_name, ref="main", token=token)
    print(f"{time.strftime('%H:%M:%S', time.localtime())} Repository cloned: {repo_url}.\n")

    openai_agent.run_assistant(
        file_paths=file_paths,
        issue_title=issue_title,
        issue_body=issue_body,
        issue_comments=issue_comments,
        owner=owner,
        ref="main",
        repo=repo_name
        )
    return


# Determine the event type and call the appropriate handler
async def handle_webhook_event(payload) -> None:
    # TODO Verify webhook using webhoo.verify from octokit
    if ('action' in payload):
        action = payload.get("action")

        # Check the type of webhook event and handle accordingly
        if (action == "created" or action == "added") and "installation" in payload:
            print("Installaton is created")
            await handle_installation_created(payload=payload)

        elif (action == "deleted" or action == "removed") and "installation" in payload:
            print("Installaton is deleted")
            await handle_installation_deleted(payload=payload)

        elif action == "labeled" and "issue" in payload:
            print("Issue is labeled")
            await handle_issue_labeled(payload=payload)
