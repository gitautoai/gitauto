# Local imports
from config import LABEL, GITHUB_APP_ID, GITHUB_PRIVATE_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from ..supabase.supabase_manager import InstallationTokenManager
from .github_manager import GitHubManager
from jwt import JWT, jwk_from_pem
import git

import time
import sys
import uuid
import requests

import openai
from agent.models import Model
from agent.coders import Coder
import os
from agent.inputoutput import InputOutput
from pathlib import Path

# Initialize managers
github_manager = GitHubManager(GITHUB_APP_ID, GITHUB_PRIVATE_KEY)
supabase_manager = InstallationTokenManager(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


async def handle_installation_created(payload):
    installation_id = payload["installation"]["id"]
    account_login = payload["installation"]["account"]["login"]
    html_url = payload["installation"]["account"]["html_url"]
    action = payload.get("action")
    repositories = []
    repository_ids = []
    if action == 'created':
        repositories = [obj.get('full_name') for obj in payload["repositories"]]
        repository_ids = [obj.get('id') for obj in payload["repositories"]]
    if action == 'added':
        repositories = [obj.get('full_name') for obj in payload["repositories_added"]]
        repository_ids = [obj.get('id') for obj in payload["repositories_added"]]

    supabase_manager.save_installation_token(installation_id, account_login, html_url, repositories, repository_ids)


async def handle_installation_deleted(payload: GitHubInstallationPayload) -> None:
    installation_id: int = payload["installation"]["id"]
    supabase_manager.delete_installation_token(installation_id=installation_id)


# Handle the issue labeled event
async def handle_issue_labeled(payload):
    label = payload["label"]["name"]
    if label != LABEL:
        return
    issue = payload["issue"]
    url = issue["html_url"]
    repository_id = payload["repository"]["id"]

    installation_id = supabase_manager.get_installation_id(repository_id)
    print("Installation ID: ", installation_id)

    with open('privateKey.pem', 'rb') as pem_file:
        signing_key = pem_file.read()

    new_uuid = uuid.uuid4()
    print("UUID: ", new_uuid)
    payload = {
        'iat': int(time.time()),
        'exp': int(time.time()) + 600,
        'iss': GITHUB_APP_ID
    }

    jwt_instance = JWT()
    encoded_jwt = jwt_instance.encode(payload, jwk_from_pem(signing_key), alg='RS256')

    print(f"JWT:  {encoded_jwt}")

    headers = {
        "Authorization": f"Bearer {encoded_jwt}",
        "Content-Type": "application/json"
    }   

    response = requests.post(f'https://api.github.com/app/installations/{installation_id}/access_tokens', headers=headers)
    token = response.json().get('token')

    git.Repo.clone_from(f'https://x-access-token:{token}@github.com/nikitamalinov/lalager', f'./tmp/{new_uuid}')
    
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
    io.tool_output(*sys.argv, log_only=True)

    git_dname = str(Path.cwd() / f'tmp/{new_uuid}')

    openai_api_key = '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'

    kwargs = dict()
    client = openai.OpenAI(api_key=openai_api_key, **kwargs)

    main_model = Model.create('gpt-4-1106-preview', client)

    try:
        coder = Coder.create(
            main_model=main_model,
            edit_format=None,
            skip_model_availabily_check=False,
            client=client,
            io=None,
            fnames=None,
            git_dname=git_dname,
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
    io.tool_output("Use /help to see in-chat commands, run with --help to see cmd line args")

    io.add_to_input_history("add header with tag 'Hello World' to homepage")
    io.tool_output()
    coder.run(with_message="add header with tag 'Hello World' to homepage")

    repo_path = Path.cwd() / f'tmp/{new_uuid}'
    original_path = os.getcwd()
    os.chdir(repo_path)

    str_uuid = str(new_uuid)
    # Create a new branch and push to it
    repo = git.Repo(repo_path)
    branch = str_uuid
    repo.create_head(branch)
    repo.git.push('origin', branch)

    # Push to branch to create PR
    remote_url = repo.remotes.origin.url
    repo_name = remote_url.split('/')[-1].replace('.git', '')
    repo_owner = remote_url.split('/')[-2]
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = {
        "title": issue['title'],
        "body": "World",
        "head": f"nikitamalinov:{str_uuid}",
        "base": 'main',
    }
    response = requests.post(url, headers=headers, json=data)

    os.chdir(original_path)

    # TODO delete tmp folder


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
