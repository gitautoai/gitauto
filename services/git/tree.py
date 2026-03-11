from typing import TypedDict

from typing_extensions import NotRequired


class Tree(TypedDict):
    path: str  # "filename.ext"
    mode: str  # "100644"
    type: str  # "blob"
    sha: str  # "7c258a9869f33c1e1e1f74fbb32f07c86cb5a75b"
    size: NotRequired[int]  # Only for blobs, not for trees (directories)
