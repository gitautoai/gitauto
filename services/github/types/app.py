from datetime import datetime
from typing import TypedDict

from services.github.types.owner import Owner
from services.github.types.common import BaseGitHubEntity


class App(BaseGitHubEntity):
    client_id: str
    slug: str
    owner: Owner
    name: str
    description: str
    external_url: str
    html_url: str
    created_at: datetime
    updated_at: datetime
    permissions: dict
    events: list[str]