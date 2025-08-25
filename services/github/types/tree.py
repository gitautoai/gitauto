from typing import TypedDict
from typing_extensions import NotRequired


class Tree(TypedDict):
    """https://docs.github.com/en/rest/git/trees#get-a-tree"""

    # Required fields
    path: str  # "filename.ext"
    mode: str  # "100644"
    type: str  # "blob"
    sha: str  # "7c258a9869f33c1e1e1f74fbb32f07c86cb5a75b"
    url: str  # "https://api.github.com/repos/owner/repo/git/blobs/7c258a9869f33c1e1e1f74fbb32f07c86cb5a75b"

    # Optional fields
    size: NotRequired[int]  # 100 (optional, only for blobs)
