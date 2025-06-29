from requests import delete
from config import GITHUB_API_URL, TIMEOUT
from services.github.create_headers import create_headers
from services.github.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def delete_comment(base_args: BaseArgs, comment_id: int):
    """https://docs.github.com/en/rest/issues/comments?apiVersion=2022-11-28#delete-an-issue-comment"""
    owner, repo, token = (base_args["owner"], base_args["repo"], base_args["token"])
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/comments/{comment_id}"
    headers: dict[str, str] = create_headers(token=token)
    response = delete(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
