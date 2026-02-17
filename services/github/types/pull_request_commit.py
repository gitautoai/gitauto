# https://docs.github.com/en/rest/pulls/pulls#list-commits-on-a-pull-request
from typing import TypedDict

from services.github.types.user import User


class GitUser(TypedDict):
    name: str
    email: str
    date: str


class GitCommitInfo(TypedDict):
    url: str
    author: GitUser | None
    committer: GitUser | None
    message: str
    comment_count: int


class PullRequestCommit(TypedDict):
    url: str
    sha: str
    node_id: str
    html_url: str
    comments_url: str
    commit: GitCommitInfo
    author: User | None
    committer: User | None
