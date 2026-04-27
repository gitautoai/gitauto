from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=True)
def insert_installation(
    *,
    platform: Platform,
    installation_id: int,
    owner_id: int,
    owner_type: str,
    owner_name: str,
    user_id: int,
    user_name: str,
):
    supabase.table(table_name="installations").insert(
        json={
            "platform": platform,
            "installation_id": installation_id,
            "owner_id": owner_id,
            "owner_type": owner_type,
            "owner_name": owner_name,
            "created_by": f"{user_id}:{user_name}",
        }
    ).execute()
