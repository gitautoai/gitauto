import datetime
from typing import Optional, TypedDict

from services.github.types.app import App
from services.github.types.pull_request import PullRequest


class CheckSuite(TypedDict):
    id: int
    node_id: str
    head_branch: str
    head_sha: str
    status: str
    conclusion: Optional[str]
    url: str
    before: str
    after: str
    pull_requests: list[PullRequest]
    app: App
    created_at: datetime
    updated_at: datetime
