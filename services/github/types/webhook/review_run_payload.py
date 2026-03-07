from typing import TypedDict

from services.github.types.installation import Installation
from services.github.types.organization import Organization
from services.github.types.pull_request import PullRequest
from services.github.types.repository import Repository
from services.github.types.user import User


class ReviewRunComment(TypedDict):
    id: int
    node_id: str
    body: str
    user: User
    path: str
    subject_type: str
    line: int
    side: str


class ReviewRunPayload(TypedDict):
    action: str
    comment: ReviewRunComment
    pull_request: PullRequest
    repository: Repository
    organization: Organization
    sender: User
    installation: Installation
