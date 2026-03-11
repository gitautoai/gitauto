import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def close_pull_request(pr_number: int, base_args: BaseArgs):
    """https://docs.github.com/en/rest/pulls/pulls#update-a-pull-request"""
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    response = requests.patch(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}",
        headers=create_headers(token=token),
        json={"state": "closed"},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
