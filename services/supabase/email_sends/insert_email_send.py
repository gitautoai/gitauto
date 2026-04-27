from postgrest.exceptions import APIError

from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def insert_email_send(
    *,
    platform: Platform,
    owner_id: int,
    owner_name: str,
    email_type: str,
):
    try:
        result = (
            supabase.table("email_sends")
            .insert(
                {
                    "platform": platform,
                    "owner_id": owner_id,
                    "owner_name": owner_name,
                    "email_type": email_type,
                }
            )
            .execute()
        )

        if result.data and len(result.data) > 0:
            logger.info(
                "insert_email_send: inserted %s for owner %s platform=%s",
                email_type,
                owner_id,
                platform,
            )
            return True

        logger.info(
            "insert_email_send: no row returned for %s owner %s", email_type, owner_id
        )
        return False
    except APIError as e:
        if e.code == "23505":
            logger.info(
                "insert_email_send: duplicate %s for owner %s, skipped",
                email_type,
                owner_id,
            )
            return False
        raise
