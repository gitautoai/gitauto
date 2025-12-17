from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def insert_webhook_delivery(delivery_id: str, event_name: str):
    result = (
        supabase.table("webhook_deliveries")
        .insert({"delivery_id": delivery_id, "event_name": event_name})
        .execute()
    )

    if result.data and len(result.data) > 0:
        return True

    return False
