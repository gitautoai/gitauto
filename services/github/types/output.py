from typing import TypedDict


class Output(TypedDict):
    """GitHub check run output type"""
    title: str | None
    summary: str | None
    text: str | None
    annotations_count: int
    annotations_url: str