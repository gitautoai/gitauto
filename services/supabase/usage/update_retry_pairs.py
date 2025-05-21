from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def update_retry_workflow_id_hash_pairs(
    owner_id: int, repo_id: int, pr_number: int, pairs: list[str]
):
    (
        supabase.table("usage")
        .update(
            {
                "retry_workflow_id_hash_pairs": pairs,
                "is_completed": True,
            }
        )
        .eq("owner_id", owner_id)
        .eq("repo_id", repo_id)
        .eq("pr_number", pr_number)
        .execute()
    )
