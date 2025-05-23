from typing import TypedDict

from services.github.types.common import BaseGitHubEntity


class Sender(BaseGitHubEntity):
    """GitHub sender type - represents the user who triggered an event"""
    login: str
    avatar_url: str
    gravatar_id: str
    html_url: str
    followers_url: str
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: str
    organizations_url: str
    repos_url: str
    events_url: str
    received_events_url: str
    type: str
    user_view_type: str
    site_admin: bool