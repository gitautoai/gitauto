import requests

from anthropic.types import ToolUnionParam

from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from services.types.base_args import ReviewBaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

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
def reply_to_comment(base_args: ReviewBaseArgs, body: str, **_kwargs):
    """https://docs.github.com/en/rest/pulls/comments?apiVersion=2022-11-28#create-a-reply-for-a-review-comment"""
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    pr_number = base_args.get("pr_number")
    comment_id = base_args.get("review_id")

    if not pr_number:
        logger.error("reply_to_comment: missing pr_number")
        raise ValueError(
            f"pr_number is required for reply_to_comment but got: {pr_number}"
        )

    # PR-level comments (no file path) use the issue comments API, not the inline comment reply API.
    # "pr_review" = PR-level review, "pr_comment" = general PR comment (adapted from issue_comment).
    review_subject_type = base_args.get("review_subject_type")
    if review_subject_type in ("pr_review", "pr_comment"):
        logger.info("reply_to_comment: PR-level comment, using issue comments endpoint")
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{pr_number}/comments"
    else:
        logger.info("reply_to_comment: inline review reply endpoint")
        if not comment_id:
            logger.error("reply_to_comment: missing review_id for inline reply")
            raise ValueError(
                f"review_id is required for reply_to_comment but got: {comment_id}"
            )
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies"

    headers: dict[str, str] = create_headers(token=token)
    response = requests.post(
        url=url, headers=headers, json={"body": body}, timeout=TIMEOUT
    )
    # Parent comment is deleted. GitHub returns 404 on the replies endpoint. resolved-but-still-existing threads return 2xx, so 404 specifically means deletion. Sentry AGENT-303/304 (Foxquilt/foxden-shared-lib PR 629 comment 3093714165 deleted before GitAuto could reply).
    if response.status_code == 404:
        logger.info(
            "reply_to_comment: parent comment gone (404), skipping reply on %s",
            url,
        )
        return None
    response.raise_for_status()
    logger.info("reply_to_comment: replied at %s", url)
    return response.json()["url"]
