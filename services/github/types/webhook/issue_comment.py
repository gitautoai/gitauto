from typing import Literal, NotRequired, TypedDict

from services.github.types.installation import Installation
from services.github.types.issue import Issue, PrIssue
from services.github.types.organization import Organization
from services.github.types.repository import Repository
from services.github.types.sender import Sender
from services.github.types.user import User


class Comment(TypedDict):
    id: int
    node_id: str
    user: User
    body: str
    created_at: str
    updated_at: str


BodyChange = TypedDict("BodyChange", {"from": str})
Changes = TypedDict("Changes", {"body": BodyChange}, total=False)


class IssueCommentWebhookPayload(TypedDict):
    """https://docs.github.com/en/webhooks/webhook-events-and-payloads#issue_comment"""

    action: Literal["created", "edited", "labeled", "unlabeled", "deleted"]
    comment: Comment
    issue: Issue
    repository: Repository
    organization: NotRequired[Organization]  # Personal repos don't have this key
    sender: Sender
    installation: Installation
    changes: Changes


# Can't inherit from IssueCommentWebhookPayload because pyright rejects narrowing TypedDict fields (action and issue) in subclasses due to invariance.
class PrCommentWebhookPayload(TypedDict):
    action: Literal["created", "edited"]
    comment: Comment
    issue: PrIssue
    repository: Repository
    organization: NotRequired[Organization]  # Personal repos don't have this key
    sender: Sender
    installation: Installation
    changes: Changes
