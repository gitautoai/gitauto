from requests import delete
from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def delete_comment(*, owner: str, repo: str, token: str, comment_id: int):
    """https://docs.github.com/en/rest/issues/comments?apiVersion=2022-11-28#delete-an-issue-comment"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/comments/{comment_id}"
    headers: dict[str, str] = create_headers(token=token)
    response = delete(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
