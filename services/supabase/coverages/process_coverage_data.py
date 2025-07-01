# Standard imports
from typing import TypedDict, Literal
import json

# Local imports
from services.supabase.coverages.get_coverages import get_coverages
from services.supabase.coverages.upsert_coverages import upsert_coverages
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
def process_coverage_data(
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

    # Get existing records before deleting
    existing_records = get_coverages(repo_id=repo_id, filenames=current_paths)

    # Prepare data for upsert
    upsert_data = []
    for coverage in seen.values():
        try:
            existing_record = existing_records.get(coverage["full_path"]) or {}
            item = {
                **existing_record,
                # System fields are always updated
                "owner_id": owner_id,
                "repo_id": repo_id,
                "branch_name": branch_name,
                "primary_language": primary_language,
                "path_coverage": 0,
                "updated_by": user_name,
                # Override with coverage data
                **coverage,
            }

            # Set default values for new records
            if not existing_record:
                item["created_by"] = user_name
                item["is_excluded_from_testing"] = False

            # Set uncovered fields to None when the coverage is 100%
            if item.get("line_coverage") == 100:
                item["uncovered_lines"] = None
            if item.get("function_coverage") == 100:
                item["uncovered_functions"] = None
            if item.get("branch_coverage") == 100:
                item["uncovered_branches"] = None

            # Remove id, created_at, and updated_at fields to avoid upsert conflicts
            item.pop("id", None)
            item.pop("created_at", None)
            item.pop("updated_at", None)

            # Test if item is JSON serializable
            json.dumps(item)
            upsert_data.append(item)
        except (TypeError, ValueError, OverflowError) as e:
            print(f"Skipping non-serializable item: {str(e)}\nItem data: {coverage}")
            continue

    if not upsert_data:
        print("No valid items to upsert after filtering")
        return None

    # Use new bulk upsert function
    return upsert_coverages(upsert_data)
