from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_usage_by_pr(owner_id: int, repo_id: int, pr_number: int):
    result = (
        supabase.table("usage")
        .select("id")
        .eq("owner_id", owner_id)
        .eq("repo_id", repo_id)
        .eq("pr_number", pr_number)
        .execute()
    )
    return result.data
