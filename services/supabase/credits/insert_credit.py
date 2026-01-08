# Local imports
from config import CREDIT_AMOUNTS_USD
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def insert_credit(owner_id: int, transaction_type: str, usage_id: int | None = None):
    amount_usd = CREDIT_AMOUNTS_USD[transaction_type]

    data = {
        "owner_id": owner_id,
        "amount_usd": amount_usd,
        "transaction_type": transaction_type,
    }
    if usage_id is not None:
        data["usage_id"] = usage_id

    supabase.table("credits").insert(data).execute()
