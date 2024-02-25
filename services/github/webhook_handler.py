# Standard imports
import os
import shutil
import sys
import time
from pathlib import Path
from uuid import UUID, uuid4

# Third-party imports
import git
import openai
import requests

# Local imports
from agent.coders import Coder
from agent.inputoutput import InputOutput
from agent.models import Model
from config import GITHUB_APP_ID, GITHUB_PRIVATE_KEY, LABEL, OPENAI_API_KEY, OPENAI_MODEL_ID, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from services.github.github_manager import GitHubManager
from services.github.github_types import GitHubInstallationPayload, GitHubLabeledPayload, IssueInfo, RepositoryInfo
from services.supabase.supabase_manager import InstallationTokenManager

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


async def handle_issue_labeled(payload: GitHubLabeledPayload):
    # Extract label and validate it
    label: str = payload["label"]["name"]
    if label != LABEL:
        return

    # Extract information from the payload
    issue: IssueInfo = payload["issue"]
    installation_id: int = payload["installation"]["id"]
    repo: RepositoryInfo = payload["repository"]
    repo_url: str = repo["html_url"]

    # Clone the repository
    new_uuid: UUID = uuid4()
    token: str = github_manager.get_installation_access_token(installation_id=installation_id)
    github_manager.clone_repository(token=token, repo_url=repo_url, uuid=new_uuid)

    # Initialize the OpenAI API
    io = InputOutput(
      pretty=True,
      yes=True,
      input_history_file=None,
      chat_history_file=None,
      input=input,
      output=None,
      user_input_color="blue",
      tool_output_color=None,
      tool_error_color="red",
      encoding="utf-8",
      dry_run=False,
    )

    # Print the tool output
    io.tool_output(*sys.argv, log_only=True)

    # Define the directory for the cloned repository
    root_path: str = os.getcwd()
    cloned_repo_path_instance: Path = Path.cwd() / f'tmp/{new_uuid}'
    cloned_repo_path_str = str(object=Path.cwd() / f'tmp/{new_uuid}')

    # Configure the OpenAI client
    kwargs = {}
    client = openai.OpenAI(api_key=OPENAI_API_KEY, **kwargs)
    main_model = Model.create(name=OPENAI_MODEL_ID, client=client)

    # Create a new coder instance
    try:
        coder = Coder.create(
            main_model=main_model,
            edit_format=None,
            skip_model_availabily_check=False,
            client=client,
            io=None,
            fnames=None,
            git_dname=cloned_repo_path_str,
            pretty=True,
            show_diffs=False,
            auto_commits=True,
            dirty_commits=True,
            dry_run=False,
            map_tokens=1024,
            verbose=True,
            assistant_output_color="blue",
            code_theme="default",
            stream=True,
            use_git=True,
            voice_language=None,
            aider_ignore_file=None,
        )
    except ValueError as err:
        print(err)
        return 1

    # Run the coder with a specific command
    issue_title: str = issue.get('title')
    issue_body: str = issue.get('body') or ""
    message: str = f"Issue Title: {issue_title}\n\nIssue Body: {issue_body}"
    coder.run(with_message=message)

    # Create a new branch (head) in local repo and push it to the remote repo
    os.chdir(path=cloned_repo_path_instance)
    str_uuid = str(object=new_uuid)
    repo_instance = git.Repo(path=cloned_repo_path_instance)
    branch_name: str = str_uuid
    repo_instance.create_head(path=branch_name)
    repo_instance.git.push('origin', branch_name)


    # Create a Pull Request
    response: requests.Response = github_manager.create_pull_request(repo=repo, branch_name=branch_name, issue=issue, token=token)

    os.chdir(path=root_path)

    # Delete the cloned repository
    shutil.rmtree(path=cloned_repo_path_instance)


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
