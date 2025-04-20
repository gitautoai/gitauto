from typing import TypedDict, Optional, cast
from services.supabase.client import supabase
from utils.handle_exceptions import handle_exceptions


class RepositoryRules(TypedDict, total=False):
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

    # Other columns
    created_at: str
    created_by: str
    updated_at: str
    updated_by: str


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_repository_rules(repo_id: int):
    """Get the rules for a repository from Supabase."""
    result = supabase.table("repositories").select("*").eq("repo_id", repo_id).execute()

    if result.data and result.data[0]:
        return cast(RepositoryRules, result.data[0])

    return None
