from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def check_owner_exists(owner_id: int):
    data, _ = (
        supabase.table(table_name="owners")
        .select("owner_id")
        .eq(column="owner_id", value=owner_id)
        .execute()
    )
    return bool(data[1])
