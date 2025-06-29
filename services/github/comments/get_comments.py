# Standard imports
from typing import Any

# Third party imports
import requests

# Local imports
from config import GITHUB_API_URL, GITHUB_APP_IDS, TIMEOUT
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_comments(
    issue_number: int, base_args: BaseArgs, includes_me: bool = False
) -> list[str]:
    """https://docs.github.com/en/rest/issues/comments#list-issue-comments"""
    owner, repo, token = base_args["owner"], base_args["repo"], base_args["token"]
    response = requests.get(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments",
        headers=create_headers(token=token),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    comments: list[dict[str, Any]] = response.json()
    if not includes_me:
        filtered_comments: list[dict[str, Any]] = [
            comment
            for comment in comments
            if comment.get("performed_via_github_app") is None
            or comment["performed_via_github_app"].get("id") not in GITHUB_APP_IDS
        ]
    else:
        filtered_comments = comments
    comment_texts: list[str] = [comment["body"] for comment in filtered_comments]
    return comment_texts
