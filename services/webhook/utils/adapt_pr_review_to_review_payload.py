from services.github.types.webhook.pull_request_review import PullRequestReviewPayload
from services.github.types.webhook.review_run_payload import ReviewRunPayload
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def adapt_pr_review_to_review_payload(payload: PullRequestReviewPayload):
    review = payload["review"]
    result: ReviewRunPayload = {
        "action": payload["action"],
        "comment": {
            "id": review["id"],
            "node_id": review["node_id"],
            "body": review["body"] or "",
            "user": review["user"],
            "path": "",
            "subject_type": "pr_review",
            "line": 0,
            "side": "",
        },
        "pull_request": payload["pull_request"],
        "repository": payload["repository"],
        "sender": payload["sender"],
        "installation": payload["installation"],
    }
    organization = payload.get("organization")
    if organization is not None:
        result["organization"] = organization

    return result
