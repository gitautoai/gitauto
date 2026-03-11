import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_repo_archived(owner: str, repo: str, token: str):
    """GitHub API only - the 'archived' flag has no git CLI equivalent.
    https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#get-a-repository
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}"
    headers = create_headers(token=token)
    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    data: dict[str, bool] = response.json()
    return data.get("archived", False)
