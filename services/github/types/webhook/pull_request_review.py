from typing import NotRequired, TypedDict

from services.github.types.installation import Installation
from services.github.types.organization import Organization
from services.github.types.pull_request import PullRequest
from services.github.types.repository import Repository
from services.github.types.sender import Sender
from services.github.types.user import User


class Review(TypedDict):
    id: int
    node_id: str
    body: str | None
    user: User
    state: str


class PullRequestReviewPayload(TypedDict):
    """https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request_review"""

    action: str
    review: Review
    pull_request: PullRequest
    repository: Repository
    organization: NotRequired[Organization]
    sender: Sender
    installation: Installation
