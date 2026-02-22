import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def add_labels(owner: str, repo: str, pr_number: int, token: str, labels: list[str]):
    """https://docs.github.com/en/rest/issues/labels?apiVersion=2022-11-28#add-labels-to-an-issue"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{pr_number}/labels"
    headers = create_headers(token=token)
    response = requests.post(
        url=url, headers=headers, json={"labels": labels}, timeout=TIMEOUT
    )
    response.raise_for_status()
