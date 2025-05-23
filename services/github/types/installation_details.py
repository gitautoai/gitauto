from typing import Optional, TypedDict

from services.github.types.permission import Permissions
from services.github.types.user import User


class InstallationDetails(TypedDict):
    id: int
    account: User
    repository_selection: str
    access_tokens_url: str
    repositories_url: str
    html_url: str
    app_id: int
    app_slug: str
    target_id: int
    target_type: str
    permissions: Permissions
    events: list[str]
    created_at: str
    updated_at: str
    single_file_name: Optional[str]
    has_multiple_single_files: bool
    single_file_paths: list[str]
    suspended_by: Optional[str]
    suspended_at: Optional[str]
