# Local imports
from constants.models import CREDIT_GRANT_AMOUNT_USD, ModelId
from schemas.supabase.types import CreditTransactionType
from services.supabase.credits.get_credit_price import get_credit_price
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def insert_credit(
    owner_id: int,
    transaction_type: CreditTransactionType,
    usage_id: int | None = None,
    model_id: ModelId | None = None,
):
    if transaction_type == "usage":
        amount_usd = -get_credit_price(model_id)
    elif transaction_type == "grant":
        amount_usd = CREDIT_GRANT_AMOUNT_USD
    else:
        raise ValueError(f"Unknown transaction type: {transaction_type}")

    data = {
        "owner_id": owner_id,
        "amount_usd": amount_usd,
        "transaction_type": transaction_type,
    }
    if usage_id is not None:
        data["usage_id"] = usage_id

    supabase.table("credits").insert(data).execute()
