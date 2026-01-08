from requests import post

from config import GITHUB_API_URL, TIMEOUT
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def reply_to_comment(base_args: BaseArgs, body: str):
    """https://docs.github.com/en/rest/pulls/comments?apiVersion=2022-11-28#create-a-reply-for-a-review-comment"""
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    pull_number = base_args.get("pull_number")
    comment_id = base_args.get("review_id")

    if not pull_number or not comment_id:
        raise ValueError("pull_number and review_id are required for reply_to_comment")
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pull_number}/comments/{comment_id}/replies"
    headers: dict[str, str] = create_headers(token=token)
    response = post(url=url, headers=headers, json={"body": body}, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()["url"]
