# Third party imports
import requests

# Local imports
from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_review_summary_comment(
    owner: str, repo: str, pr_number: int, review_id: int, token: str
):
    """https://docs.github.com/en/rest/pulls/reviews#get-a-review-for-a-pull-request"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}/reviews/{review_id}"
    headers = create_headers(token=token)
    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    data: dict[str, str | int | None] = response.json()
    body = data.get("body") or ""
    return str(body)
