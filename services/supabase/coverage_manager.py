# Standard imports
from typing import TypedDict, Literal

# Local imports
from services.supabase.client import supabase
from utils.handle_exceptions import handle_exceptions


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

    # Prepare data for upsert by adding common fields to each coverage item
    upsert_data = [
        {
            "owner_id": owner_id,
            "repo_id": repo_id,
            "branch_name": branch_name,
            "primary_language": primary_language,
            "path_coverage": 0,
            **coverage,
            "updated_by": user_name,
            "created_by": user_name,  # Will only be used for new records
        }
        for coverage in seen.values()
    ]

    # Use upsert to handle both inserts and updates in a single operation
    result = (
        supabase.table("coverages")
        .upsert(
            upsert_data,
            on_conflict="repo_id,full_path",
        )
        .execute()
    )

    return result.data
