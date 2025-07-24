# Local imports
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def check_grant_exists(owner_id: int) -> bool:
    result = (
        supabase.table("credits")
        .select("id")
        .eq("owner_id", owner_id)
        .eq("transaction_type", "grant")
        .execute()
    )
    return len(result.data) > 0
