import os
import requests
import sys
import time
import uuid

from pathlib import Path
import git
import jwt
import openai

# Local imports
from agent.coders import Coder
from agent.inputoutput import InputOutput
from agent.models import Model
from services.github.github_types import GitHubLabeledPayload, IssueInfo
from config import OPEN_API_KEY, ENV
from .github_manager import github_access_token




async def handle_issue_labeled(payload: GitHubLabeledPayload):
    label: str = payload["label"]["name"]
    model = ''
    if label == 'pragent':
        model = 'gpt-4-1106-preview'
    elif label == 'pragent-2':
        model = 'gemini'
    else:
        return

    issue: IssueInfo = payload["issue"]
    installation_id: str = payload["installation"]["id"]

    token = github_access_token(installation_id)
    
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
        print('listing: ')
        os.system(f'ls')
        print('current dir: ')
        os.system(f'pwd')
        print("created folder")

        print(f'git clone https://x-access-token:{token}@github.com/nikitamalinov/lalager.git')
        print('listing: ')
        os.system(f'ls')
        # os.system('rm -rf lalager')
        os.system(f'git clone https://x-access-token:{token}@github.com/nikitamalinov/lalager.git')
        print("LINING: ")
        os.system(f'ls')
    except Exception as e:
        print(e)

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

    kwargs = dict()
    client = openai.OpenAI(api_key=OPEN_API_KEY, **kwargs)

    main_model = Model.create('gpt-4-1106-preview', client)
    return
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