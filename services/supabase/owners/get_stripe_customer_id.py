# Local imports
from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_stripe_customer_id(*, platform: Platform, owner_id: int):
    """https://supabase.com/docs/reference/python/select"""
    data, _count = (
        supabase.table(table_name="owners")
        .select("stripe_customer_id")
        .eq(column="platform", value=platform)
        .eq(column="owner_id", value=owner_id)
        .execute()
    )
    if not data or len(data) < 2 or not data[1]:
        logger.info("get_stripe_customer_id: no row for %s/%s", platform, owner_id)
        return None

    customer_id: str | None = data[1][0]["stripe_customer_id"]
    logger.info(
        "get_stripe_customer_id: %s/%s -> %s", platform, owner_id, bool(customer_id)
    )
    return customer_id
