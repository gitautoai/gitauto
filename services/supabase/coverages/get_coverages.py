from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value={}, raise_on_error=False)
def get_coverages(repo_id: int, filenames: list[str]):
    if not filenames:
        return {}

    result = (
        supabase.table("coverages")
        .select("*")
        .eq("repo_id", repo_id)
        .in_("full_path", filenames)
        .execute()
    )

    if not result.data:
        return {}

    # Create a dictionary mapping file paths to their coverage data
    coverage_dict = {}
    for item in result.data:
        coverage_dict[item["full_path"]] = item

    return coverage_dict
