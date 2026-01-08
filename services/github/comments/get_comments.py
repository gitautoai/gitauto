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
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    response = requests.get(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments",
        headers=create_headers(token=token),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    comments: list[dict[str, object]] = response.json()
    if not includes_me:
        filtered_comments: list[dict[str, object]] = []
        for comment in comments:
            app = comment.get("performed_via_github_app")
            if app is None:
                filtered_comments.append(comment)
            elif isinstance(app, dict) and app.get("id") not in GITHUB_APP_IDS:
                filtered_comments.append(comment)
    else:
        filtered_comments = comments
    comment_texts: list[str] = [str(comment["body"]) for comment in filtered_comments]
    return comment_texts
