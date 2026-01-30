import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def delete_remote_branch(base_args: BaseArgs):
    # https://docs.github.com/en/rest/git/refs?apiVersion=2022-11-28#delete-a-reference
    owner = base_args["owner"]
    repo = base_args["repo"]
    branch_name = base_args["new_branch"]
    token = base_args["token"]
    response = requests.delete(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/refs/heads/{branch_name}",
        headers=create_headers(token=token),
        timeout=TIMEOUT,
    )
    return response.status_code == 204
