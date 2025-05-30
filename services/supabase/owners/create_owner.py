from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def create_owner(
    owner_id: int,
    owner_name: str,
    user_id: int,
    user_name: str,
    stripe_customer_id: str = "",
    owner_type: str = "",
    org_rules: str = "",
):
    (
        supabase.table("owners")
        .insert(
            {
                "owner_id": owner_id,
                "owner_name": owner_name,
                "stripe_customer_id": stripe_customer_id,
                "created_by": str(user_id) + ":" + user_name,
                "updated_by": str(user_id) + ":" + user_name,
                "owner_type": owner_type,
                "org_rules": org_rules,
            }
        )
        .execute()
    )
