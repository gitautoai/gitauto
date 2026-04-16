from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def check_purchase_exists(owner_id: int):
    """Check if owner has ever purchased credits (transaction_type = 'purchase')."""
    result = (
        supabase.table("credits")
        .select("id")
        .eq("owner_id", owner_id)
        .eq("transaction_type", "purchase")
        .limit(1)
        .execute()
    )
    has_purchase = bool(result.data)
    logger.info("Owner %d has_purchase=%s", owner_id, has_purchase)
    return has_purchase
