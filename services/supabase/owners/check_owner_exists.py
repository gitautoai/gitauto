from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def check_owner_exists(*, platform: Platform, owner_id: int):
    result = (
        supabase.table(table_name="owners")
        .select("owner_id")
        .eq(column="platform", value=platform)
        .eq(column="owner_id", value=owner_id)
        .execute()
    )
    exists = bool(result.data)
    logger.info("check_owner_exists: %s/%s -> %s", platform, owner_id, exists)
    return exists
