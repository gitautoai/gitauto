# Local imports
from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_installation_valid(*, platform: Platform, installation_id: int):
    """Check if the installation is still valid by checking if uninstalled_at is null"""
    response = (
        supabase.table(table_name="installations")
        .select("uninstalled_at")
        .eq(column="platform", value=platform)
        .eq(column="installation_id", value=installation_id)
        .execute()
    )

    if not response.data:
        logger.info(
            "is_installation_valid: no row for %s/%s", platform, installation_id
        )
        return False

    valid = response.data[0]["uninstalled_at"] is None
    logger.info("is_installation_valid: %s/%s -> %s", platform, installation_id, valid)
    return valid
