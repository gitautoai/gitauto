from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.email.check_email_is_valid import check_email_is_valid
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


# Cross-ref: website/app/actions/supabase/users/upsert-user.ts
@handle_exceptions(default_return_value=None, raise_on_error=False)
def upsert_user(
    *,
    platform: Platform,
    user_id: int,
    user_name: str,
    email: str | None,
    display_name: str,
):
    # Check if email is valid
    email = email if check_email_is_valid(email=email) else None

    json: dict = {
        "platform": platform,
        "user_id": user_id,
        "user_name": user_name,
        **({"display_name": display_name} if display_name else {}),
        **({"email": email} if email else {}),
        "created_by": f"{user_id}:{user_name}",
    }
    supabase.table(table_name="users").upsert(
        json=json, on_conflict="platform,user_id"
    ).execute()
    logger.info("upsert_user: user_id=%s platform=%s", user_id, platform)
