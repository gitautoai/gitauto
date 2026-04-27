from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def update_email_send(
    *,
    platform: Platform,
    owner_id: int,
    email_type: str,
    resend_email_id: str,
):
    supabase.table("email_sends").update({"resend_email_id": resend_email_id}).eq(
        "platform", platform
    ).eq("owner_id", owner_id).eq("email_type", email_type).execute()
