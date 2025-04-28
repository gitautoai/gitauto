# Standard imports
from datetime import datetime, timezone

# Local imports
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def delete_installation(installation_id: int, user_id: int, user_name: str):
    """We don't cancel a subscription associated with this installation id since paid users sometimes mistakenly uninstall our app"""
    data = {
        "uninstalled_at": datetime.now(tz=timezone.utc).isoformat(),
        "uninstalled_by": str(user_id) + ":" + user_name,
    }
    (
        supabase.table(table_name="installations")
        .update(json=data)
        .eq(column="installation_id", value=installation_id)
        .execute()
    )
