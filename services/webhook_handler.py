# Standard imports
import time
from uuid import uuid4

# Local imports
from config import PRODUCT_ID, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from services.github.github_manager import (
    commit_changes_to_remote_branch,
    create_pull_request,
    create_remote_branch,
    get_installation_access_token,
    get_latest_remote_commit_sha,
    get_remote_file_tree
)
from services.github.github_types import (
    GitHubEventPayload,
    GitHubInstallationPayload,
    GitHubLabeledPayload,
    IssueInfo,
    RepositoryInfo
)
from services.openai.openai_agent import run_assistant
from services.supabase.supabase_manager import InstallationTokenManager
from utils.file_manager import extract_file_name

# Initialize managers
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

    supabase_manager.save_installation_token(
        installation_id=installation_id,
        account_login=account_login,
        html_url=html_url,
        repositories=repositories,
        repository_ids=repository_ids
    )


async def handle_installation_deleted(payload: GitHubInstallationPayload) -> None:
    installation_id: int = payload["installation"]["id"]
    supabase_manager.delete_installation_token(installation_id=installation_id)


async def handle_issue_labeled(payload: GitHubLabeledPayload):
    # Extract label and validate it
    label: str = payload["label"]["name"]
    if label != PRODUCT_ID:
        return

    # Extract information from the payload
    issue: IssueInfo = payload["issue"]
    issue_title: str = issue["title"]
    issue_body: str = issue["body"] or ""
    issue_comments: list[str] = [""]
    installation_id: int = payload["installation"]["id"]
    repo: RepositoryInfo = payload["repository"]
    owner: str = repo["owner"]["login"]
    repo_name: str = repo["name"]
    base_branch: str = repo["default_branch"]

    # Clone the repository
    token: str = get_installation_access_token(installation_id=installation_id)
    file_paths: list[str] = get_remote_file_tree(
        owner=owner, repo=repo_name, ref=base_branch, token=token
    )
    print(f"{time.strftime('%H:%M:%S', time.localtime())} Installation token received.\n")

    diffs: list[str] = run_assistant(
        file_paths=file_paths,
        issue_title=issue_title,
        issue_body=issue_body,
        issue_comments=issue_comments,
        owner=owner,
        ref=base_branch,
        repo=repo_name,
        token=token
    )

    # Create a remote branch
    uuid: str = str(object=uuid4())
    new_branch: str = f"{PRODUCT_ID}/issue-#{issue['number']}-{uuid}"
    latest_commit_sha = get_latest_remote_commit_sha(
        owner=owner, repo=repo_name, branch=base_branch, token=token
    )
    create_remote_branch(
        branch_name=new_branch,
        owner=owner,
        repo=repo_name,
        sha=latest_commit_sha,
        token=token
    )
    print(f"{time.strftime('%H:%M:%S', time.localtime())} Remote branch created: {new_branch}.\n")

    # Commit the changes to the new remote branch
    for diff in diffs:
        file_path: str = extract_file_name(diff_text=diff)
        print(f"{time.strftime('%H:%M:%S', time.localtime())} File path: {file_path}.\n")
        commit_changes_to_remote_branch(
            branch=new_branch,
            commit_message=f"Update {file_path}",
            diff_text=diff,
            file_path=file_path,
            owner=owner,
            repo=repo_name,
            token=token
        )
        print(f"{time.strftime('%H:%M:%S', time.localtime())} Changes committed to {new_branch}.\n")

    # Create a pull request to the base branch
    create_pull_request(
        base=base_branch,
        body=issue_body,
        head=new_branch,
        owner=owner,
        repo=repo_name,
        title=f"Fix {issue_title} with {PRODUCT_ID} model",
        token=token
    )
    print(f"{time.strftime('%H:%M:%S', time.localtime())} Pull request created.\n")

    return


async def handle_webhook_event(payload: GitHubEventPayload) -> None:
    """ Determine the event type and call the appropriate handler """
    action = payload.get("action")
    if not action:
        return

    # Check the type of webhook event and handle accordingly
    if action in ("created", "added") and "installation" in payload:
        print("Installaton is created")
        await handle_installation_created(payload=payload)

    elif action in ("deleted", "removed") and "installation" in payload:
        print("Installaton is deleted")
        await handle_installation_deleted(payload=payload)

    elif action == "labeled" and "issue" in payload:
        print("Issue is labeled")
        await handle_issue_labeled(payload=payload)