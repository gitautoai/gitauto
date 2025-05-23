from typing import TypedDict


class Permissions(TypedDict):
    actions: str
    contents: str
    metadata: str
    workflows: str
    repository_hooks: str
