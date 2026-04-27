from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_npm_token(*, platform: Platform, owner_id: int):
    result = (
        supabase.table("npm_tokens")
        .select("token")
        .eq("platform", platform)
        .eq("owner_id", owner_id)
        .maybe_single()
        .execute()
    )

    if result and result.data:
        token = result.data["token"]
        if isinstance(token, str):
            logger.info("get_npm_token: found for %s/%s", platform, owner_id)
            return token

        logger.warning(
            "get_npm_token: token for %s/%s is not str, got %s",
            platform,
            owner_id,
            type(token).__name__,
        )
        return None

    logger.info("get_npm_token: no token for %s/%s", platform, owner_id)
    return None
