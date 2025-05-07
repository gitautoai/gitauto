# Local imports
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_installation_valid(installation_id: int):
    """Check if the installation is still valid by checking if uninstalled_at is null"""
    response = (
        supabase.table(table_name="installations")
        .select("uninstalled_at")
        .eq(column="installation_id", value=installation_id)
        .execute()
    )

    if not response.data:
        return False

    return response.data[0]["uninstalled_at"] is None
