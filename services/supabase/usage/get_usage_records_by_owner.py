from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_usage_records_by_owner(owner, start, end):
    """Get usage records for an owner in date range."""
    result = (
        supabase.table("usage")
        .select("id, repo_name, pr_number, trigger, is_completed, created_at")
        .eq("owner_name", owner)
        .gte("created_at", start)
        .lt("created_at", end)
        .order("created_at")
        .execute()
    )
    return result.data
