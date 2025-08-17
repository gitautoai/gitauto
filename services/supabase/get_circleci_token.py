from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_circleci_token(owner_id: int):
    """Get CircleCI token for the given owner from the circleci_tokens table."""
    response = (
        supabase.table("circleci_tokens")
        .select("token")
        .eq("owner_id", owner_id)
        .maybe_single()
        .execute()
    )

    if response.data:
        return response.data["token"]

    return None
