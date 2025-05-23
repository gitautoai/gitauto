from typing import TypedDict, Optional, cast
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


class RepositorySettings(TypedDict, total=False):
    id: int
    owner_id: int
    repo_id: int
    repo_name: str

    # Rules
    repo_rules: Optional[str]
    target_branch: str

    # References
    web_urls: Optional[list[str]]
    file_paths: Optional[list[str]]

    # Screenshots
    use_screenshots: Optional[bool]
    production_url: Optional[str]
    local_port: Optional[int]
    startup_commands: Optional[list[str]]

    # Metrics
    file_count: Optional[int]
    blank_lines: Optional[int]
    comment_lines: Optional[int]
    code_lines: Optional[int]

    # Triggers
    trigger_on_review_comment: bool
    trigger_on_test_failure: bool
    trigger_on_commit: bool
    trigger_on_merged: bool
    trigger_on_schedule: bool

    # Schedule
    schedule_frequency: Optional[str]
    schedule_minute: Optional[int]
    schedule_time: Optional[str]
    schedule_day_of_week: Optional[str]
    schedule_include_weekends: bool

    # Other columns
    created_at: str  # "2025-05-23T12:00:00.000Z"
    created_by: str  # "1234567:John Doe"
    updated_at: str  # "2025-05-23T12:00:00.000Z"
    updated_by: str  # "1234567:John Doe"


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_repository_settings(repo_id: int):
    """Get the rules for a repository from Supabase."""
    result = supabase.table("repositories").select("*").eq("repo_id", repo_id).execute()

    if result.data and result.data[0]:
        return cast(RepositorySettings, result.data[0])

    return None
