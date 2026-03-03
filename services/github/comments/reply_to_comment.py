import requests

from anthropic.types import ToolUnionParam

from config import GITHUB_API_URL, TIMEOUT
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions

REPLY_TO_REVIEW_COMMENT: ToolUnionParam = {
    "name": "reply_to_review_comment",
    "description": "Replies in the review comment thread on the pull request. Use this to respond to the reviewer's feedback - explain what you changed and why, or explain why you chose not to apply a suggestion.",
    "input_schema": {
        "type": "object",
        "properties": {
            "body": {
                "type": "string",
                "description": "The reply text to post in the review thread.",
            },
        },
        "required": ["body"],
        "additionalProperties": False,
    },
    "strict": True,
}


@handle_exceptions(default_return_value=None, raise_on_error=False)
def reply_to_comment(base_args: BaseArgs, body: str, **_kwargs):
    """https://docs.github.com/en/rest/pulls/comments?apiVersion=2022-11-28#create-a-reply-for-a-review-comment"""
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    pr_number = base_args.get("pr_number")
    comment_id = base_args.get("review_id")

    if not pr_number:
        raise ValueError(
            f"pr_number is required for reply_to_comment but got: {pr_number}"
        )

    if not comment_id:
        raise ValueError(
            f"review_id is required for reply_to_comment but got: {comment_id}"
        )

    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies"
    headers: dict[str, str] = create_headers(token=token)
    response = requests.post(
        url=url, headers=headers, json={"body": body}, timeout=TIMEOUT
    )
    response.raise_for_status()
    return response.json()["url"]
