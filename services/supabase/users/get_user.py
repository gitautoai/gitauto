from schemas.supabase.types import Users
from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_user(*, platform: Platform, user_id: int):
    result = (
        supabase.table(table_name="users")
        .select("*")
        .eq(column="platform", value=platform)
        .eq(column="user_id", value=user_id)
        .execute()
    )
    if result.data:
        logger.info("get_user: found user_id=%s platform=%s", user_id, platform)
        return Users(**result.data[0])

    logger.info("get_user: no row for user_id=%s platform=%s", user_id, platform)
    return None
