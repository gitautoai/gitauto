from schemas.supabase.fastapi.schema_public_latest import Installations
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_installation(owner_id: int):
    data, _ = (
        supabase.table(table_name="installations")
        .select("*")
        .eq(column="owner_id", value=owner_id)
        .is_(column="uninstalled_at", value="null")
        .execute()
    )

    if not data[1]:
        return None

    return Installations(**data[1][0])
