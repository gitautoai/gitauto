# Standard imports
from typing import cast

# Third-party imports
from schemas.supabase.types import Coverages

# Local imports
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value={}, raise_on_error=False)
def get_coverages(owner_id: int, repo_id: int, filenames: list[str]):
    coverage_dict: dict[str, Coverages] = {}
    if not filenames:
        return coverage_dict

    # Dynamic batching based on character count
    # Empirically tested exact limit: 25,036 characters
    # Using 20,000 as safe limit (80% of max)
    max_chars = 20000
    overhead = 100  # Query structure overhead

    batch = []
    current_chars = overhead

    for filename in filenames:
        # Each filename needs quotes and comma: "filename",
        filename_chars = len(filename) + 3

        if current_chars + filename_chars > max_chars and batch:
            # Process current batch
            result = (
                supabase.table("coverages")
                .select("*")
                .eq("owner_id", owner_id)
                .eq("repo_id", repo_id)
                .in_("full_path", batch)
                .execute()
            )

            if result.data:
                for item in result.data:
                    coverage_dict[item["full_path"]] = cast(Coverages, item)

            # Start new batch
            batch = [filename]
            current_chars = overhead + filename_chars
        else:
            batch.append(filename)
            current_chars += filename_chars

    # Process final batch
    if batch:
        result = (
            supabase.table("coverages")
            .select("*")
            .eq("owner_id", owner_id)
            .eq("repo_id", repo_id)
            .in_("full_path", batch)
            .execute()
        )

        if result.data:
            for item in result.data:
                coverage_dict[item["full_path"]] = cast(Coverages, item)

    return coverage_dict
