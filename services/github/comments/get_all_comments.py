from requests import get
from config import GITHUB_API_URL, TIMEOUT
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_all_comments(base_args: BaseArgs):
    """https://docs.github.com/en/rest/issues/comments?apiVersion=2022-11-28#list-issue-comments"""
    owner, repo, issue_number, token = (
        base_args["owner"],
        base_args["repo"],
        base_args["issue_number"],
        base_args["token"],
    )
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments"
    headers: dict[str, str] = create_headers(token=token)
    response = get(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    comments: list[dict] = response.json()
    return comments
