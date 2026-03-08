from dataclasses import dataclass

import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@dataclass
class RepoInfo:
    default_branch: str
    is_empty: bool
    is_archived: bool


@handle_exceptions(
    default_return_value=RepoInfo("main", False, False), raise_on_error=True
)
def get_default_branch(owner: str, repo: str, token: str):
    # https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#get-a-repository
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}"
    headers = create_headers(token=token)
    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    data = response.json()
    return RepoInfo(
        default_branch=data["default_branch"],
        is_empty=data["size"] == 0,
        is_archived=data.get("archived", False),
    )
