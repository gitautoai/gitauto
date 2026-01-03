from typing import cast

from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_circleci_token(owner_id: int):
    result = (
        supabase.table("circleci_tokens")
        .select("token")
        .eq("owner_id", owner_id)
        .maybe_single()
        .execute()
    )

    if result and result.data:
        return cast(str, result.data["token"])
    return None
