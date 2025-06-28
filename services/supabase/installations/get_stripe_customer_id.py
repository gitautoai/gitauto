from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_stripe_customer_id(installation_id: int) -> str | None:
    data, _ = (
        supabase.table(table_name="installations")
        .select(
            "owner_id, owners(stripe_customer_id)"
        )  # LEFTJOIN with owners table via owner_id FK
        .eq(column="installation_id", value=installation_id)
        .execute()
    )

    stripe_customer_id = (
        data[1][0].get("owners", {}).get("stripe_customer_id")
        if data and data[1] and data[1][0]
        else None
    )

    if not stripe_customer_id or not isinstance(stripe_customer_id, str):
        return None

    return stripe_customer_id
