import requests
from config import GITHUB_API_URL, TIMEOUT
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def add_reaction_to_issue(issue_number: int, content: str, base_args: BaseArgs) -> None:
    """https://docs.github.com/en/rest/reactions/reactions?apiVersion=2022-11-28#create-reaction-for-an-issue"""
    owner, repo, token = base_args["owner"], base_args["repo"], base_args["token"]
    response: requests.Response = requests.post(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}/reactions",
        headers=create_headers(token=token),
        json={"content": content},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    response.json()
