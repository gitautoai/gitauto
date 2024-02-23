# Standard imports
import os
import requests
import sys
import time
import uuid
from pathlib import Path

# Third-party imports
import git
import jwt
import openai

# Local imports
from agent.coders import Coder
from agent.inputoutput import InputOutput
from agent.models import Model
from config import LABEL, GITHUB_APP_ID, GITHUB_PRIVATE_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, ENV
from services.github.github_manager import GitHubManager
from services.github.github_types import GitHubInstallationPayload, GitHubLabeledPayload, IssueInfo
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
    label: str = payload["label"]["name"]
    if label != LABEL:
        return

    issue: IssueInfo = payload["issue"]

    installation_id: str = payload["installation"]["id"]


    # Create a JWT token for authentication
    now = int(time.time())
    payload = {
        'iat': now,
        'exp': now + 600,  # JWT expires in 10 minutes
        'iss': GITHUB_APP_ID
    }
    print("decoding")
    print('key: ', GITHUB_PRIVATE_KEY)
    encoded_jwt: str = jwt.encode(payload=payload, key=GITHUB_PRIVATE_KEY, algorithm='RS256')
    headers: dict[str, str] = {
        "Authorization": f"Bearer {encoded_jwt}",
        "Content-Type": "application/json"
    }
    print("decoded, getting authenticated with gh")
    # TODO 47287862 should be {installation_id}
    response = requests.post(url=f'https://api.github.com/app/installations/47287862/access_tokens', headers=headers)
    token: str = response.json().get('token')
    print("got response")
    new_uuid = uuid.uuid4()
    
    # Create and get into tmp folder
    original_path: str = os.getcwd()
    tmp_folder = '/tmp'
    if(ENV == "local"):
        tmp_folder = original_path + '/tmp'
    if not os.path.exists(tmp_folder):
        os.makedirs(tmp_folder)
    os.chdir(tmp_folder)
    
    try:
        print("creating folder")
        # os.system(f'mkdir {new_uuid}')
        # os.system(f'cd {new_uuid}')
        print('listing: ')
        os.system(f'ls')
        print('current dir: ')
        os.system(f'pwd')
        print("created folder")
        os.system(f'git init')
        print("git inited")
        
        # os.system(f'git config --global user.email "nikita@malinovsky.net')
        

        print("cloned!!!")
        print(f'git clone https://x-access-token:{token}@github.com/nikitamalinov/lalager.git')
        print('listing: ')
        os.system(f'ls')
        os.system(f'git clone https://x-access-token:{token}@github.com/nikitamalinov/lalager.git')
        print("LITING: ")
        os.system(f'ls')
        # git.Repo.clone_from(url=f'https://x-access-token:{token}@github.com/nikitamalinov/lalager.git', to_path=f'./{new_uuid}')
    except Exception as e:
        print(e)
    print("Repo cloned")
    
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


    git_dname = str(Path.cwd() / f'{new_uuid}')

    openai_api_key = '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'

    kwargs = dict()
    client = openai.OpenAI(api_key=openai_api_key, **kwargs)

    main_model = Model.create('gpt-4-1106-preview', client)

    # Create a new coder instance
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

    # Run the coder
    io.tool_output("Use /help to see in-chat commands, run with --help to see cmd line args")
    io.add_to_input_history(inp="add header with tag 'Hello World' to homepage")
    io.tool_output()
    coder.run(with_message="add header with tag 'Hello World' to homepage")

    # Create a new branch and push to it
    repo_path: Path = Path.cwd() / f'{new_uuid}'
    os.chdir(path=repo_path)

    str_uuid = str(object=new_uuid)
    # Create a new branch and push to it
    repo = git.Repo(path=repo_path)
    branch: str = str_uuid
    repo.create_head(path=branch)
    repo.git.push('origin', branch)

    # Push to branch to create PR
    remote_url: str = repo.remotes.origin.url
    repo_name: str = remote_url.split(sep='/')[-1].replace('.git', '')
    repo_owner: str = remote_url.split(sep='/')[-2]
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data: dict[str, str] = {
        "title": issue['title'],
        "body": "World",
        "head": f"nikitamalinov:{str_uuid}",
        "base": 'main',
    }
    response = requests.post(url=url, headers=headers, json=data)

    os.chdir(original_path)
    print("Created PR")
    
    
    # TODO delete tmp folder


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
