from typing import TypedDict
from services.github.types.user import User
from services.github.types.repository import Repository


class Ref(TypedDict):
    """GitHub Git reference object (used in PRs, branches, comparisons, etc.)"""

    label: str  # e.g. "octocat:main"
    ref: str  # e.g. "main"
    sha: str  # e.g. "1234567890"
    user: User
    repo: Repository
