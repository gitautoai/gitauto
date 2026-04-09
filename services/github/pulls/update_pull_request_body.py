import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def update_pull_request_body(
    owner_name: str, repo_name: str, pr_number: int, token: str, body: str
):
    """https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#update-a-pull-request"""
    url = f"{GITHUB_API_URL}/repos/{owner_name}/{repo_name}/pulls/{pr_number}"
    headers = create_headers(token=token)
    data = {"body": body}
    response = requests.patch(url=url, headers=headers, json=data, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()
