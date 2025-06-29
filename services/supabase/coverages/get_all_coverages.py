from typing import cast
from schemas.supabase.fastapi.schema_public_latest import CoveragesBaseSchema
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_all_coverages(repo_id: int):
    result = (
        supabase.table("coverages")
        .select("*")
        .eq("repo_id", repo_id)
        .eq("level", "file")
        .order("statement_coverage", desc=False)  # Lowest coverage first
        .order("file_size", desc=False)  # Smallest files first for ties
        .order("full_path", desc=False)  # Alphabetical order for final ties
        .execute()
    )

    return cast(list[CoveragesBaseSchema], result.data or [])
