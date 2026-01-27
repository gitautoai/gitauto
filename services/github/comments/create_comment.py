import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def create_comment(body: str, base_args: BaseArgs, **_kwargs):
    # https://docs.github.com/en/rest/issues/comments?apiVersion=2022-11-28#create-an-issue-comment
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    issue_number = base_args["issue_number"]

    response = requests.post(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments",
        headers=create_headers(token=token),
        json={"body": body},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    url: str = response.json()["url"]
    return url
