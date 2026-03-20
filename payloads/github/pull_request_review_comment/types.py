from typing import Literal, Optional, TypedDict

from services.github.types.installation import Installation
from services.github.types.organization import Organization
from services.github.types.pull_request import PullRequest
from services.github.types.repository import Repository
from services.github.types.user import User


class ReviewCommentReactions(TypedDict):
    url: str
    total_count: int


class ReviewCommentLinks(TypedDict):
    self: dict
    html: dict
    pull_request: dict


class ReviewComment(TypedDict):
    url: str
    pull_request_review_id: int
    id: int
    node_id: str
    diff_hunk: str
    path: str
    commit_id: str
    original_commit_id: str
    user: User
    body: str
    created_at: str
    updated_at: str
    html_url: str
    pull_request_url: str
    author_association: str
    _links: ReviewCommentLinks
    reactions: ReviewCommentReactions
    start_line: Optional[int]
    original_start_line: Optional[int]
    start_side: Optional[str]
    line: int
    original_line: int
    side: str
    original_position: int
    position: int
    subject_type: Literal["line", "file"]


class PullRequestReviewCommentPayload(TypedDict):
    action: Literal["created", "edited", "deleted"]
    comment: ReviewComment
    pull_request: PullRequest
    repository: Repository
    organization: Organization
    sender: User
    installation: Installation
