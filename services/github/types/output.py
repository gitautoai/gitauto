from typing import Optional, TypedDict


class Output(TypedDict):
    title: Optional[str]
    summary: Optional[str]
    text: Optional[str]
    annotations_count: int
    annotations_url: str
