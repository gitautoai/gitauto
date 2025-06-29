# Standard imports
from typing import cast

# Third party imports
import requests

# Local imports
from config import GITHUB_API_URL, TIMEOUT
from services.github.types.pull_request import PullRequest
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_pull_request(owner: str, repo: str, pull_number: int, token: str):
    """https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#get-a-pull-request"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pull_number}"
    headers = create_headers(token=token)
    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    return cast(PullRequest, response.json())
