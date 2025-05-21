# Standard imports
from typing import TypedDict, Literal

# Local imports
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


class CoverageItem(TypedDict):
    package_name: str
    level: Literal["repository", "directory", "file"]
    full_path: str
    line_coverage: float
    statement_coverage: float
    function_coverage: float
    branch_coverage: float
    path_coverage: float
    uncovered_lines: str
    uncovered_functions: str
    uncovered_branches: str


@handle_exceptions(default_return_value=None, raise_on_error=False)
def create_or_update_coverages(
    coverages_list: list[CoverageItem],
    owner_id: int,
    repo_id: int,
    branch_name: str,
    primary_language: str,
    user_name: str,
):
    """Bulk process multiple coverage records with common metadata"""
    if not coverages_list:
        return None

    # Check for duplicates
    seen = {}
    for coverage in coverages_list:
        key = (repo_id, coverage["full_path"])
        if key in seen:
            print(
                f"Duplicate found for repo_id={repo_id}, full_path={coverage['full_path']}"
            )
            print(f"First occurrence: {seen[key]}")
            print(f"Duplicate: {coverage}")
        seen[key] = coverage

    # Get current file paths
    current_paths = [coverage["full_path"] for coverage in seen.values()]

    # Delete records for files that no longer exist
    if current_paths:
        supabase.table("coverages").delete().eq("repo_id", repo_id).not_.in_(
            "full_path", current_paths
        ).execute()
    else:
        # If no files, delete all records for this repo
        supabase.table("coverages").delete().eq("repo_id", repo_id).execute()

    # Prepare data for upsert by adding common fields to each coverage item
    upsert_data = [
        {
            "owner_id": owner_id,
            "repo_id": repo_id,
            "branch_name": branch_name,
            "primary_language": primary_language,
            "path_coverage": 0,
            **coverage,
            "created_by": user_name,
            "updated_by": user_name,
        }
        for coverage in seen.values()
    ]

    # Set uncovered fields to None when the coverage is 100%
    for item in upsert_data:
        if item["line_coverage"] == 100:
            item["uncovered_lines"] = None
        if item["function_coverage"] == 100:
            item["uncovered_functions"] = None
        if item["branch_coverage"] == 100:
            item["uncovered_branches"] = None

    # Upsert data (insert if not exists, update if exists)
    result = (
        supabase.table("coverages")
        .upsert(upsert_data, on_conflict="repo_id,full_path")
        .execute()
    )

    return result.data
