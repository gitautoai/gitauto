from typing import cast
from requests import get

from config import GITHUB_API_URL, TIMEOUT
from services.github.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value={}, raise_on_error=False)
def get_repository_languages(owner: str, repo: str, token: str):
    """https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#list-repository-languages"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/languages"
    headers = create_headers(token=token)
    response = get(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    return cast(dict[str, int], response.json())
