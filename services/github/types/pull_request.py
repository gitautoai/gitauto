from typing import TypedDict


class PullRequest(TypedDict):
    url: str
    id: int
    number: int
    head: dict
    base: dict
