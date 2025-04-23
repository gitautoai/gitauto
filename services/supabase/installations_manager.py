# Standard imports
from typing import Literal

# Local imports
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def get_installation_info(owner_name: str):
    """https://supabase.com/docs/reference/python/select"""
    data, _count = (
        supabase.table(table_name="installations")
        .select("installation_id, owner_id, owner_type")
        .eq(column="owner_name", value=owner_name)
        .is_(column="uninstalled_at", value="null")
        .execute()
    )
    installation_id: str | None = data[1][0]["installation_id"]
    owner_id: int | None = data[1][0]["owner_id"]
    owner_type: Literal["Organization", "User"] | None = data[1][0]["owner_type"]
    return installation_id, owner_id, owner_type
