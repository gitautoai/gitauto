# Standard imports
from typing import Literal, NotRequired, TypedDict

Status = Literal["added", "modified", "removed"]


# https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#list-pull-requests-files
class PullRequestFile(TypedDict):
    sha: str
    filename: str
    status: Status
    additions: int
    deletions: int
    changes: int
    blob_url: str
    raw_url: str
    contents_url: str
    patch: NotRequired[str]
