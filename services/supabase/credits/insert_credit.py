# Local imports
from constants.models import CREDIT_GRANT_AMOUNT_USD, ModelId
from schemas.supabase.types import CreditTransactionType
from services.supabase.client import supabase
from services.supabase.credits.get_credit_price import get_credit_price
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def insert_credit(
    *,
    platform: Platform,
    owner_id: int,
    transaction_type: CreditTransactionType,
    usage_id: int | None = None,
    model_id: ModelId | None = None,
):
    if transaction_type == "usage":
        logger.info("insert_credit: transaction_type=usage")
        amount_usd = -get_credit_price(model_id)
    elif transaction_type == "grant":
        logger.info("insert_credit: transaction_type=grant")
        amount_usd = CREDIT_GRANT_AMOUNT_USD
    else:
        logger.error("insert_credit: unknown transaction_type=%s", transaction_type)
        raise ValueError(f"Unknown transaction type: {transaction_type}")

    data = {
        "platform": platform,
        "owner_id": owner_id,
        "amount_usd": amount_usd,
        "transaction_type": transaction_type,
    }
    if usage_id is not None:
        logger.info("insert_credit: linking usage_id=%s", usage_id)
        data["usage_id"] = usage_id

    supabase.table("credits").insert(data).execute()
    logger.info(
        "insert_credit: %s %s usd for owner %s platform=%s",
        transaction_type,
        amount_usd,
        owner_id,
        platform,
    )
