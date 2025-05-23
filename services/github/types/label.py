from typing import Optional, TypedDict


class Label(TypedDict):
    id: int
    node_id: str
    url: str
    name: str
    color: str
    default: bool
    description: Optional[str]
