from typing import Literal, TypedDict
from services.github.types.installation import Installation
from services.github.types.repository import Repository
from services.github.types.sender import Sender
from services.github.types.issue import Issue
from services.github.types.organization import Organization

Comment = TypedDict("Comment", {"id": int, "user": dict, "body": str})
BodyChange = TypedDict("BodyChange", {"from": str})
Changes = TypedDict("Changes", {"body": BodyChange}, total=False)


class IssueCommentWebhookPayload(TypedDict):
    action: Literal["created", "edited", "labeled", "unlabeled", "deleted"]
    comment: Comment
    issue: Issue
    repository: Repository
    organization: Organization
    sender: Sender
    installation: Installation
    changes: Changes
