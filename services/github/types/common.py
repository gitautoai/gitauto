"""Common type definitions used across GitHub API types."""

from typing import Literal, TypedDict


# Common type aliases
OwnerType = Literal["User", "Organization"]
IssueState = Literal["open", "closed"]
PullRequestState = Literal["open", "closed", "merged"]
CheckRunStatus = Literal["queued", "in_progress", "completed"]
CheckRunConclusion = Literal["success", "failure", "neutral", "cancelled", "skipped", "timed_out", "action_required"]


class BaseGitHubEntity(TypedDict):
    """Base type for GitHub entities with common fields."""
    id: int
    node_id: str
    url: str