from typing import Optional, TypedDict

from services.github.types.app import App


class SimplifiedRepo(TypedDict):
    id: int
    url: str
    name: str


class SimplifiedRef(TypedDict):
    ref: str
    sha: str
    repo: SimplifiedRepo


class SimplifiedPullRequest(TypedDict):
    url: str
    id: int
    number: int
    head: SimplifiedRef
    base: SimplifiedRef


class HeadCommit(TypedDict):
    id: str
    tree_id: str
    message: str
    timestamp: str
    author: dict
    committer: dict


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
    pull_requests: list[SimplifiedPullRequest]
    app: App
    created_at: str
    updated_at: str
    rerequestable: bool
    runs_rerequestable: bool
    latest_check_runs_count: int
    check_runs_url: str
    head_commit: HeadCommit
