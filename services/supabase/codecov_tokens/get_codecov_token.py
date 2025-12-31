from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_codecov_token(owner_id: int):
    response = (
        supabase.table("codecov_tokens")
        .select("token")
        .eq("owner_id", owner_id)
        .maybe_single()
        .execute()
    )

    if response and response.data:
        return response.data["token"]

    return None
