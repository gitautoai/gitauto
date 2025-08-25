# Standard imports
from typing import cast

# Third-party imports
from schemas.supabase.types import Coverages

# Local imports
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value={}, raise_on_error=False)
def get_coverages(repo_id: int, filenames: list[str]):
    coverage_dict: dict[str, Coverages] = {}
    if not filenames:
        return coverage_dict

    result = (
        supabase.table("coverages")
        .select("*")
        .eq("repo_id", repo_id)
        .in_("full_path", filenames)
        .execute()
    )

    if not result.data:
        return coverage_dict

    # Create a dictionary mapping file paths to their coverage data
    for item in result.data:
        coverage_dict[item["full_path"]] = cast(Coverages, item)

    return coverage_dict
