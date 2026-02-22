import requests
from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_all_comments(*, owner: str, repo: str, pr_number: int, token: str):
    """https://docs.github.com/en/rest/issues/comments?apiVersion=2022-11-28#list-issue-comments"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers: dict[str, str] = create_headers(token=token)
    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    comments: list[dict] = response.json()
    return comments
