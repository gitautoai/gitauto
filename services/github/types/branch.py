from typing import TypedDict

from services.github.types.user import User


class Commit(TypedDict):
    sha: str
    node_id: str
    url: str
    html_url: str
    author: User
    committer: User


class Branch(TypedDict):
    name: str
    commit: Commit
