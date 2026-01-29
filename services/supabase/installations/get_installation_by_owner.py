from typing import cast

from schemas.supabase.types import Installations
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_installation_by_owner(owner_name: str):
    result = (
        supabase.table("installations")
        .select("*")
        .eq("owner_name", owner_name)
        .is_("uninstalled_at", "null")
        .maybe_single()
        .execute()
    )

    if result and result.data:
        return cast(Installations, result.data)

    return None
