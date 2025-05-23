from typing import TypedDict, Optional, cast
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


class RepositorySettings(TypedDict):
    """https://supabase.com/dashboard/project/dkrxtcbaqzrodvsagwwn/editor/202072?schema=public&sort=created_at%3Adesc&view=definition"""

    # Primary keys
    # id: int
    # owner_id: int
    # repo_id: int
    # repo_name: str

    # Repository rules
    repo_rules: Optional[str]
    target_branch: str

    # Repository references
    web_urls: Optional[list[str]]
    file_paths: Optional[list[str]]

    # Screenshot settings
    use_screenshots: Optional[bool]
    production_url: Optional[str]
    local_port: Optional[int]
    startup_commands: Optional[list[str]]

    # Repository metrics
    file_count: Optional[int]
    blank_lines: Optional[int]
    comment_lines: Optional[int]
    code_lines: Optional[int]

    # Trigger settings
    trigger_on_review_comment: bool
    trigger_on_test_failure: bool
    trigger_on_commit: bool
    trigger_on_merged: bool
    trigger_on_schedule: bool

    # Schedule settings
    schedule_frequency: Optional[str]
    schedule_minute: Optional[int]
    schedule_time: Optional[str]
    schedule_day_of_week: Optional[str]
    schedule_include_weekends: bool

    # Timestamps
    # created_at: str  # "2025-05-23T12:00:00.000Z"
    # created_by: str  # "1234567:John Doe"
    # updated_at: str  # "2025-05-23T12:00:00.000Z"
    # updated_by: str  # "1234567:John Doe"


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_repository_settings(repo_id: int):
    """Get the rules for a repository from Supabase."""
    fields = "repo_rules, target_branch, web_urls, file_paths, use_screenshots, production_url, local_port, startup_commands, file_count, blank_lines, comment_lines, code_lines, trigger_on_review_comment, trigger_on_test_failure, trigger_on_commit, trigger_on_merged, trigger_on_schedule, schedule_frequency, schedule_minute, schedule_time, schedule_day_of_week, schedule_include_weekends"

    result = (
        supabase.table("repositories").select(fields).eq("repo_id", repo_id).execute()
    )

    if result.data and result.data[0]:
        return cast(RepositorySettings, result.data[0])

    return None
