from typing import TypedDict

from services.github.types.label import Label
from services.github.types.user import User


class Issue(TypedDict):
    url: str
    repository_url: str
    labels_url: str
    comments_url: str
    events_url: str
    html_url: str
    id: int
    node_id: str
    number: int
    title: str
    user: User
    labels: list[Label]
    state: str
    locked: bool
    assignee: User | None
    assignees: list[User]
    milestone: str | None
    comments: int
    created_at: str
    updated_at: str
    closed_at: str | None
    author_association: str
    active_lock_reason: str | None
    body: str | None
    reactions: dict[str, int]
    timeline_url: str
    performed_via_github_app: str | None
    state_reason: str | None
