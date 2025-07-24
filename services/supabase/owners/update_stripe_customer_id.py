from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def update_stripe_customer_id(owner_id: int, stripe_customer_id: str):
    supabase.table("owners").update({"stripe_customer_id": stripe_customer_id}).eq(
        "owner_id", owner_id
    ).execute()
