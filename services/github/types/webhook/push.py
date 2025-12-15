from typing import TypedDict
from services.github.types.installation import Installation
from services.github.types.repository import Repository
from services.github.types.sender import Sender


class PushWebhookPayload(TypedDict):
    ref: str
    repository: Repository
    sender: Sender
    installation: Installation
