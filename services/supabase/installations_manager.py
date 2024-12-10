# Standard imports
from typing import Literal

# Third Party imports
from supabase import create_client, Client

# Local imports
from config import SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL
from utils.handle_exceptions import handle_exceptions

# Initialize Supabase client
supabase: Client = create_client(
    supabase_url=SUPABASE_URL, supabase_key=SUPABASE_SERVICE_ROLE_KEY
)


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
