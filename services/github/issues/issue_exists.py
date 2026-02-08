import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def issue_exists(*, owner: str, repo: str, token: str, title: str):
    """https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#search-issues-and-pull-requests"""
    query = f'repo:{owner}/{repo} is:issue is:open "{title}" in:title'
    response = requests.get(
        url=f"{GITHUB_API_URL}/search/issues",
        headers=create_headers(token=token),
        params={"q": query},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    data: dict[str, int] = response.json()
    return data.get("total_count", 0) > 0
