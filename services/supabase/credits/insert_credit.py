# Local imports
from config import CREDIT_USAGE_COST_USD
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def insert_credit(owner_id: int, usage_id: int):
    supabase.table("credits").insert(
        {
            "owner_id": owner_id,
            "usage_id": usage_id,
            "amount_usd": -CREDIT_USAGE_COST_USD,
            "transaction_type": "usage",
        }
    ).execute()
