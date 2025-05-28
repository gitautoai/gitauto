import requests
from config import GITHUB_API_URL, PRODUCT_ID, TIMEOUT
from services.github.create_headers import create_headers
from services.github.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def create_issue(title: str, body: str, assignees: list[str], base_args: BaseArgs):
    """https://docs.github.com/en/rest/issues/issues?apiVersion=2022-11-28#create-an-issue"""
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    labels = [PRODUCT_ID]

    payload = {
        "title": title,
        "body": body,
        "labels": labels,
    }

    if assignees:
        payload["assignees"] = assignees

    response = requests.post(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues",
        headers=create_headers(token=token),
        json=payload,
        timeout=TIMEOUT,
    )
    response.raise_for_status()

    return None
