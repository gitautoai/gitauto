import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def change_pr_base_branch(base_args: BaseArgs, new_base_branch: str):
    """A PR's base branch is GitHub metadata (not stored in git). There's no git command to change it - must use the GitHub API.
    https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#update-a-pull-request
    """
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    pr_number = base_args["pr_number"]

    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
    headers: dict[str, str] = create_headers(token=token)
    response = requests.patch(
        url=url, headers=headers, json={"base": new_base_branch}, timeout=TIMEOUT
    )
    response.raise_for_status()
    return f"Changed base branch of PR #{pr_number} to '{new_base_branch}'"
