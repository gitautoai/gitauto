# Standard imports
from typing import cast

# Third-party imports
from schemas.supabase.types import Coverages

# Local imports
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_all_coverages(repo_id: int):
    result = (
        supabase.table("coverages")
        .select("*")
        .eq("repo_id", repo_id)
        .eq("level", "file")
        .order("statement_coverage,file_size,full_path", desc=False)
        .execute()
    )

    if not result.data:
        return []

    return [cast(Coverages, item) for item in result.data]
