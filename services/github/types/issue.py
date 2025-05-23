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
    assignee: Optional[User]
    assignees: list[User]
    milestone: Optional[str]
    comments: int
    created_at: str
    updated_at: str
    closed_at: Optional[str]
    author_association: str
    active_lock_reason: Optional[str]
    body: Optional[str]
    reactions: dict[str, int]
    timeline_url: str
    performed_via_github_app: Optional[str]
    state_reason: Optional[str]
