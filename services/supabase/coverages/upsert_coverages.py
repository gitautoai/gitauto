# Local imports
from schemas.supabase.types import CoveragesInsert
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def upsert_coverages(coverage_records: list[CoveragesInsert]):
    if not coverage_records:
        return None

    result = (
        supabase.table("coverages")
        .upsert(
            coverage_records,
            on_conflict="repo_id,full_path",
            default_to_null=False,
        )
        .execute()
    )

    return result.data
