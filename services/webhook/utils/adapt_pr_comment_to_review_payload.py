from services.github.types.pull_request import PullRequest
from services.github.types.webhook.issue_comment import IssueCommentWebhookPayload
from services.github.types.webhook.review_run_payload import ReviewRunPayload
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def adapt_pr_comment_to_review_payload(
    payload: IssueCommentWebhookPayload,
    pull_request: PullRequest,
):
    comment = payload["comment"]
    result: ReviewRunPayload = {
        "action": payload["action"],
        "comment": {
            "id": comment["id"],
            "node_id": comment["node_id"],
            "body": comment["body"],
            "user": comment["user"],
            "path": "",
            "subject_type": "pr_comment",
            "line": 0,
            "side": "",
        },
        "pull_request": pull_request,
        "repository": payload["repository"],
        "sender": payload["sender"],
        "installation": payload["installation"],
    }
    organization = payload.get("organization")  # Personal repos don't have this key
    if organization is not None:
        result["organization"] = organization

    return result
