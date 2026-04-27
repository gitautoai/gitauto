from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def update_stripe_customer_id(
    *,
    platform: Platform,
    owner_id: int,
    stripe_customer_id: str,
    updated_by: str,
):
    supabase.table("owners").update(
        {"stripe_customer_id": stripe_customer_id, "updated_by": updated_by}
    ).eq("platform", platform).eq("owner_id", owner_id).execute()
