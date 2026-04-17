from constants.models import MAX_CREDIT_COST_USD, MODEL_REGISTRY, ModelId
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=MAX_CREDIT_COST_USD, raise_on_error=False)
def get_credit_price(model_id: ModelId | None):
    if not model_id:
        return MAX_CREDIT_COST_USD
    entry = MODEL_REGISTRY.get(model_id)
    if not entry:
        return MAX_CREDIT_COST_USD
    return entry["credit_cost_usd"]
