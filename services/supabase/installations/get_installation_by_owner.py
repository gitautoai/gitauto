from schemas.supabase.types import Installations
from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_installation_by_owner(*, platform: Platform, owner_name: str):
    result = (
        supabase.table("installations")
        .select("*")
        .eq("platform", platform)
        .eq("owner_name", owner_name)
        .is_("uninstalled_at", "null")
        .maybe_single()
        .execute()
    )

    if result and result.data:
        logger.info("get_installation_by_owner: found %s/%s", platform, owner_name)
        return Installations(**result.data)

    logger.info("get_installation_by_owner: no row for %s/%s", platform, owner_name)
    return None
