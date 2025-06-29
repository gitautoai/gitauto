from requests import post
from config import GITHUB_API_URL, TIMEOUT
from services.github.create_headers import create_headers
from services.github.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def reply_to_comment(base_args: BaseArgs, body: str):
    """https://docs.github.com/en/rest/pulls/comments?apiVersion=2022-11-28#create-a-reply-for-a-review-comment"""
    owner, repo, token = base_args["owner"], base_args["repo"], base_args["token"]
    pull_number = base_args["pull_number"]
    comment_id = base_args["review_id"]
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pull_number}/comments/{comment_id}/replies"
    headers: dict[str, str] = create_headers(token=token)
    response = post(url=url, headers=headers, json={"body": body}, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()["url"]
