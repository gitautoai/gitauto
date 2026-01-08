from schemas.supabase.types import RepoCoverageInsert
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def upsert_repo_coverage(coverage_data: RepoCoverageInsert):
    # Convert from TypedDict to regular dict for Supabase
    result = supabase.table("repo_coverage").insert(dict(coverage_data)).execute()
    return result.data
