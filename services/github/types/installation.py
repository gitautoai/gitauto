from typing import TypedDict

from services.github.types.common import BaseGitHubEntity


class Installation(BaseGitHubEntity):
    """GitHub App installation type
    
    This is a minimal version of InstallationDetails used for basic installation info
    """
    pass