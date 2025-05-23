from typing import TypedDict

from services.github.types.common import BaseGitHubEntity


class Organization(BaseGitHubEntity):
    """GitHub organization type"""
    login: str
    repos_url: str
    events_url: str
    hooks_url: str
    issues_url: str
    members_url: str
    public_members_url: str
    avatar_url: str
    description: str | None