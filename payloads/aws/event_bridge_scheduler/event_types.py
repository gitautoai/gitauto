from typing import Literal, TypedDict

from schemas.supabase.types import OwnerType


class EventBridgeSchedulerEvent(TypedDict):
    """Event payload structure from AWS EventBridge Scheduler"""

    ownerId: int
    ownerType: OwnerType
    ownerName: str
    repoId: int
    repoName: str
    userId: int
    userName: str
    installationId: int
    triggerType: Literal["schedule"]
