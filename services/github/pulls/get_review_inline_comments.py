# Third party imports
import requests

# Local imports
from config import GITHUB_API_URL, PER_PAGE, TIMEOUT
from payloads.github.pull_request_review_comment.types import ReviewComment
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_review_inline_comments(
    owner: str, repo: str, pr_number: int, review_id: int, token: str
):
    """https://docs.github.com/en/rest/pulls/reviews#list-comments-for-a-pull-request-review"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}/reviews/{review_id}/comments"
    headers = create_headers(token=token)
    all_comments: list[ReviewComment] = []
    page = 1
    while True:
        response = requests.get(
            url=url,
            headers=headers,
            timeout=TIMEOUT,
            params={"per_page": PER_PAGE, "page": page},
        )
        response.raise_for_status()
        batch: list[ReviewComment] = response.json()
        all_comments.extend(batch)
        if len(batch) < PER_PAGE:
            break
        page += 1
    return all_comments
