from schemas.supabase.types import Owners
from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_owner(*, platform: Platform, owner_id: int):
    result = (
        supabase.table("owners")
        .select("*")
        .eq("platform", platform)
        .eq("owner_id", owner_id)
        .execute()
    )
    if not result.data:
        logger.info("get_owner: no row for %s/%s", platform, owner_id)
        return None

    logger.info("get_owner: found %s/%s", platform, owner_id)
    return Owners(**result.data[0])
