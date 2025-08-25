from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def insert_owner(
    owner_id: int, owner_type: str, owner_name: str, stripe_customer_id: str
):
    supabase.table(table_name="owners").insert(
        json={
            "owner_id": owner_id,
            "owner_type": owner_type,
            "owner_name": owner_name,
            "stripe_customer_id": stripe_customer_id,
        }
    ).execute()
