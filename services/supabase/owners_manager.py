# Local imports
from services.supabase.client import supabase
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_stripe_customer_id(owner_id: int):
    """https://supabase.com/docs/reference/python/select"""
    data, _count = (
        supabase.table(table_name="owners")
        .select("stripe_customer_id")
        .eq(column="owner_id", value=owner_id)
        .execute()
    )
    if not data or len(data) < 2 or not data[1]:
        return None
    customer_id: str | None = data[1][0]["stripe_customer_id"]
    return customer_id
