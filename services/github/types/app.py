from datetime import datetime
from typing import TypedDict

from services.github.types.owner import Owner


class App(TypedDict):
    id: int
    client_id: str
    slug: str
    node_id: str
    owner: Owner
    name: str
    description: str
    external_url: str
    html_url: str
    created_at: datetime
    updated_at: datetime
    permissions: dict
    events: list[str]
