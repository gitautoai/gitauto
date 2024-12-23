import requests
from constants.settings import DEFAULT_BRANCH_NAME
from config import GITHUB_API_URL, TIMEOUT
from services.github.create_headers import create_headers
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="main", raise_on_error=False)
def get_default_branch(owner: str, repo: str, token: str):
    """https://docs.github.com/en/rest/branches/branches?apiVersion=2022-11-28#list-branches"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/branches"
    headers = create_headers(token=token)
    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    data = response.json()
    default_branch_name: str = DEFAULT_BRANCH_NAME
    latest_commit_sha: str = data[0]["commit"]["sha"]
    return default_branch_name, latest_commit_sha
