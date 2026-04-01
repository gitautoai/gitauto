from typing import Literal, TypedDict

from schemas.supabase.types import OwnerType


class SetupInstalledRepositoryEvent(TypedDict):
    triggerType: Literal["setup_installed_repository"]
    owner_id: int
    owner_name: str
    owner_type: OwnerType
    repo_id: int
    repo_name: str
    installation_id: int
    user_id: int
    user_name: str
    sender_email: str | None
    sender_display_name: str
