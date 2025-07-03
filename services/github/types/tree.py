from typing import TypedDict


class Tree(TypedDict):
    path: str  # "filename.ext"
    mode: str  # "100644"
    type: str  # "blob"
    size: int  # 100
    sha: str  # "7c258a9869f33c1e1e1f74fbb32f07c86cb5a75b"
    url: str  # "https://api.github.com/repos/owner/repo/git/blobs/7c258a9869f33c1e1e1f74fbb32f07c86cb5a75b"
