from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_owner(owner_id: int) -> dict | None:
    result = supabase.table("owners").select("*").eq("owner_id", owner_id).execute()
    return result.data[0] if result.data else None
