# Local imports
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def unsuspend_installation(installation_id: int):
    data = {
        "uninstalled_at": None,
        "uninstalled_by": None,
    }
    (
        supabase.table(table_name="installations")
        .update(json=data)
        .eq(column="installation_id", value=installation_id)
        .execute()
    )
