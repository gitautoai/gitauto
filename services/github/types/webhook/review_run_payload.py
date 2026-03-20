from typing import Literal, NotRequired, TypedDict

from services.github.types.installation import Installation
from services.github.types.organization import Organization
from services.github.types.pull_request import PullRequest
from services.github.types.repository import Repository
from services.github.types.user import User

ReviewSubjectType = Literal["line", "pr_comment", "pr_review"]


class ReviewRunComment(TypedDict):
    body: str
    id: int
    line: int
    node_id: str
    path: str
    # Present in pull_request_review_comment events
    pull_request_review_id: NotRequired[int]
    side: str
    subject_type: ReviewSubjectType
    user: User


class ReviewRunPayload(TypedDict):
    action: str
    comment: ReviewRunComment
    installation: Installation
    organization: NotRequired[Organization]  # Personal repos don't have this key
    pull_request: PullRequest
    repository: Repository
    sender: User
