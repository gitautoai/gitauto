from typing import TypedDict

from services.github.trees.get_file_tree import get_file_tree
from services.website.verify_api_key import verify_api_key


class RepositoryFile(TypedDict):
    path: str
    sha: str
    size: int


def get_repository_files(
    owner: str,
    repo: str,
    branch: str,
    token: str,
    api_key: str,
):
    """Fetch all files from a GitHub repository. Used by website for coverage dashboard."""
    verify_api_key(api_key)

    tree_items = get_file_tree(owner=owner, repo=repo, ref=branch, token=token)

    return [
        RepositoryFile(path=item["path"], sha=item["sha"], size=item.get("size", 0))
        for item in tree_items
        if item["type"] == "blob"
    ]
