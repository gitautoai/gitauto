from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_credit_records_by_owner(owner_id, start, end):
    """Get credit deduction records for an owner in date range."""
    result = (
        supabase.table("credits")
        .select("id, usage_id, amount_usd, transaction_type, created_at")
        .eq("owner_id", owner_id)
        .eq("transaction_type", "usage")
        .gte("created_at", start)
        .lt("created_at", end)
        .order("created_at")
        .execute()
    )
    return result.data
