# Standard imports
from typing import cast

# Third-party imports
from schemas.supabase.types import Coverages

# Local imports
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions

PAGE_SIZE = 1000


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_all_coverages(owner_id: int, repo_id: int):
    all_records: list[Coverages] = []
    offset = 0

    while True:
        result = (
            supabase.table("coverages")
            .select("*")
            .eq("owner_id", owner_id)
            .eq("repo_id", repo_id)
            .eq("level", "file")
            .order("statement_coverage,file_size,full_path", desc=False)
            .range(offset, offset + PAGE_SIZE - 1)
            .execute()
        )

        if not result.data:
            break

        all_records.extend(cast(Coverages, item) for item in result.data)

        if len(result.data) < PAGE_SIZE:
            break

        offset += PAGE_SIZE

    return all_records
