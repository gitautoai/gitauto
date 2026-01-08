import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.pulls.add_reviewers import add_reviewers
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def create_pull_request(body: str, title: str, base_args: BaseArgs):
    """https://docs.github.com/en/rest/pulls/pulls#create-a-pull-request"""
    owner, repo, base, head, token = (
        base_args["owner"],
        base_args["repo"],
        base_args["base_branch"],
        base_args["new_branch"],
        base_args["token"],
    )
    response: requests.Response = requests.post(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls",
        headers=create_headers(token=token),
        json={"title": title, "body": body, "head": head, "base": base},
        timeout=TIMEOUT,
    )
    if response.status_code == 422:
        msg = f"{create_pull_request.__name__} encountered an HTTPError: 422 Client Error: Unprocessable Entity for url: {response.url}, which is because no commits between the base branch and the working branch."
        raise requests.exceptions.HTTPError(msg)

    response.raise_for_status()
    pr_data = response.json()
    pr_url: str = pr_data["html_url"]
    pr_number: int = pr_data["number"]

    # Add reviewers to the pull request
    base_args["pr_number"] = pr_number
    add_reviewers(base_args=base_args)

    return pr_url, pr_number
