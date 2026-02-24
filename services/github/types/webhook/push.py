from typing import TypedDict

from services.github.types.installation import Installation
from services.github.types.repository import Repository
from services.github.types.sender import Sender


class PushCommit(TypedDict):
    added: list[str]
    modified: list[str]
    removed: list[str]


class PushWebhookPayload(TypedDict):
    ref: str
    commits: list[PushCommit]
    repository: Repository
    sender: Sender
    installation: Installation
