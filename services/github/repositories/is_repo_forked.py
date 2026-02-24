import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_repo_forked(owner: str, repo: str, token: str):
    """https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#get-a-repository"""
    response = requests.get(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}",
        headers=create_headers(token=token),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    data: dict[str, bool] = response.json()
    return data.get("fork", False)
