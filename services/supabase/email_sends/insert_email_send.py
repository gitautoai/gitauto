from postgrest.exceptions import APIError

from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def insert_email_send(owner_id: int, owner_name: str, email_type: str):
    try:
        result = (
            supabase.table("email_sends")
            .insert(
                {
                    "owner_id": owner_id,
                    "owner_name": owner_name,
                    "email_type": email_type,
                }
            )
            .execute()
        )

        if result.data and len(result.data) > 0:
            return True

        return False
    except APIError as e:
        if e.code == "23505":
            return False
        raise
