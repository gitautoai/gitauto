from typing import TypedDict

from services.github.types.label import Label
from services.github.types.user import User


class PullRequest(TypedDict):
    url: str
    id: int
    node_id: str
    number: int
    head: dict
    base: dict
    html_url: str
    diff_url: str
    patch_url: str
    issue_url: str
    state: str
    locked: bool
    title: str
    user: User
    body: str
    created_at: str
    updated_at: str
    closed_at: str | None
    merged_at: str | None
    merge_commit_sha: str | None
    assignee: User | None
    assignees: list[User]
    requested_reviewers: list[User]
    requested_teams: list[dict]
    labels: list[Label]
    milestone: dict | None
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
    merged: bool
    mergeable: Optional[bool]
    rebaseable: Optional[bool]
    mergeable_state: str
    merged_by: Optional[User]
    comments: int
    review_comments: int
    maintainer_can_modify: bool
    commits: int
    additions: int
    deletions: int
    changed_files: int
