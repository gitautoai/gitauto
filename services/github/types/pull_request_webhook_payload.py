from typing import Literal, TypedDict

from services.github.types.installation import Installation
from services.github.types.organization import Organization
from services.github.types.pull_request import PullRequest
from services.github.types.repository import Repository
from services.github.types.user import User


class PullRequestWebhookPayload(TypedDict):
    action: Literal[
        "opened",
        "closed",
        "synchronize",
        "edited",
        "reopened",
        "ready_for_review",
        "converted_to_draft",
        "assigned",
        "unassigned",
        "review_requested",
        "review_request_removed",
        "labeled",
        "unlabeled",
        "locked",
        "unlocked",
    ]
    number: int
    pull_request: PullRequest
    repository: Repository
    organization: Organization
    sender: User
    installation: Installation
