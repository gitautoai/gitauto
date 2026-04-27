from schemas.supabase.types import OwnerType
from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def insert_owner(
    *,
    platform: Platform,
    owner_id: int,
    owner_name: str,
    owner_type: OwnerType,
    user_id: int,
    user_name: str,
    stripe_customer_id: str,
):
    (
        supabase.table("owners")
        .insert(
            {
                "platform": platform,
                "owner_id": owner_id,
                "owner_name": owner_name,
                "owner_type": owner_type,
                "stripe_customer_id": stripe_customer_id,
                "created_by": str(user_id) + ":" + user_name,
                "updated_by": str(user_id) + ":" + user_name,
            }
        )
        .execute()
    )
