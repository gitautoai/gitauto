import requests

from config import GITHUB_API_URL, GITHUB_APP_IDS, TIMEOUT
from services.github.types.webhook.pr_comment import Comment
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_pr_comments(
    *, owner: str, repo: str, pr_number: int, token: str, exclude_self: bool
):
    """https://docs.github.com/en/rest/issues/comments#list-issue-comments"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = create_headers(token=token)
    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    comments: list[Comment] = response.json()
    if exclude_self:
        filtered: list[Comment] = []
        for comment in comments:
            app = comment.get("performed_via_github_app")
            if app is None or app.get("id") not in GITHUB_APP_IDS:
                filtered.append(comment)
        logger.info(
            "Filtered %d → %d PR comments (excluded self)", len(comments), len(filtered)
        )
        return filtered

    logger.info("Returning all %d PR comments", len(comments))
    return comments
