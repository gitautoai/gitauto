from typing import Optional, TypedDict

from services.github.types.label import Label
from services.github.types.ref import Ref
from services.github.types.user import User


class WebhookPullRequest(TypedDict):
    """PR object from webhook payloads (e.g. pull_request_review_comment). Missing REST API-only
    fields like mergeable_state, merged, mergeable, commits, additions, deletions, changed_files.
    """

    url: str
    id: int
    node_id: str
    number: int
    head: Ref
    base: Ref
    html_url: str
    diff_url: str
    patch_url: str
    issue_url: str
    state: str
    locked: bool
    title: str
    user: User
    body: str | None
    created_at: str
    updated_at: str
    closed_at: Optional[str]
    merged_at: Optional[str]
    merge_commit_sha: Optional[str]
    assignee: Optional[User]
    assignees: list[User]
    requested_reviewers: list[User]
    requested_teams: list[dict]
    labels: list[Label]
    milestone: Optional[dict]
    draft: bool
    commits_url: str
    review_comments_url: str
    review_comment_url: str
    comments_url: str
    statuses_url: str
    _links: dict
    author_association: str
    auto_merge: Optional[dict]
    active_lock_reason: Optional[str]
