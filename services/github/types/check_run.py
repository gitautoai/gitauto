from datetime import datetime
from typing import TypedDict

from services.github.types.app import App
from services.github.types.check_suite import CheckSuite
from services.github.types.output import Output
from services.github.types.pull_request import PullRequest


class CheckRun(TypedDict):
    id: int
    name: str
    node_id: str
    head_sha: str
    html_url: str
    details_url: str
    status: str
    conclusion: str
    started_at: datetime
    completed_at: datetime
    output: Output
    check_suite: CheckSuite
    app: App
    pull_requests: list[PullRequest]
