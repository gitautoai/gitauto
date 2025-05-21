from typing import cast

from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_retry_workflow_id_hash_pairs(owner_id: int, repo_id: int, pr_number: int):
    response = (
        supabase.table("usage")
        .select("retry_workflow_id_hash_pairs")
        .eq("owner_id", owner_id)
        .eq("repo_id", repo_id)
        .eq("pr_number", pr_number)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not response.data:
        return cast(list[str], [])

    retry_pairs = response.data[0].get("retry_workflow_id_hash_pairs", [])
    if retry_pairs is None:
        return cast(list[str], [])

    return cast(list[str], retry_pairs)
