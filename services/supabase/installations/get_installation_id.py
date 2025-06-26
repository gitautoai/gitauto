from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_installation_id(owner_id: int) -> int:
    """https://supabase.com/docs/reference/python/is"""
    data, _ = (
        supabase.table(table_name="installations")
        .select("installation_id")
        .eq(column="owner_id", value=owner_id)
        .is_(column="uninstalled_at", value="null")  # Not uninstalled
        .execute()
    )
    # Return the first installation id even if there are multiple installations
    return data[1][0]["installation_id"]
