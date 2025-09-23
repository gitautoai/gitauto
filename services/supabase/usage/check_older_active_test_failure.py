from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def check_older_active_test_failure_request(
    owner_id: int, repo_id: int, pr_number: int, current_usage_id: int
):
    result = (
        supabase.table("usage")
        .select("id, created_at")
        .eq("owner_id", owner_id)
        .eq("repo_id", repo_id)
        .eq("pr_number", pr_number)
        .eq("trigger", "test_failure")
        .eq("is_completed", False)
        .lt("id", current_usage_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None
