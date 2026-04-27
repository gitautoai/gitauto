from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_codecov_token(*, platform: Platform, owner_id: int):
    response = (
        supabase.table("codecov_tokens")
        .select("token")
        .eq("platform", platform)
        .eq("owner_id", owner_id)
        .maybe_single()
        .execute()
    )

    if response and response.data:
        logger.info("get_codecov_token: found for %s/%s", platform, owner_id)
        return response.data["token"]

    logger.info("get_codecov_token: no token for %s/%s", platform, owner_id)
    return None
