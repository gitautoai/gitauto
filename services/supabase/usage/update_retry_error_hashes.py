from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def update_retry_error_hashes(
    *,
    platform: Platform,
    owner_id: int,
    repo_id: int,
    pr_number: int,
    hashes: list[str],
):
    (
        supabase.table("usage")
        .update(
            {
                "retry_error_hashes": hashes,
                "is_completed": True,
            }
        )
        .eq("platform", platform)
        .eq("owner_id", owner_id)
        .eq("repo_id", repo_id)
        .eq("pr_number", pr_number)
        .execute()
    )
