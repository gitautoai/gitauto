from typing import TypedDict


class Permissions(TypedDict):
    """GitHub App permissions type
    
    Values can be: "read", "write", or "none"
    """
    actions: str
    contents: str
    metadata: str
    workflows: str
    repository_hooks: str