# Local imports
from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def check_grant_exists(*, platform: Platform, owner_id: int) -> bool:
    result = (
        supabase.table("credits")
        .select("id")
        .eq("platform", platform)
        .eq("owner_id", owner_id)
        .eq("transaction_type", "grant")
        .execute()
    )
    exists = len(result.data) > 0
    logger.info("check_grant_exists: %s/%s -> %s", platform, owner_id, exists)
    return exists
