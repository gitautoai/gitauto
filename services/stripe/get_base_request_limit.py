from config import FREE_TIER_REQUEST_AMOUNT
from services.stripe.client import stripe
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=FREE_TIER_REQUEST_AMOUNT, raise_on_error=False)
def get_base_request_limit(product_id: str):
    """
    https://docs.stripe.com/api/products/retrieve?lang=python
    https://dashboard.stripe.com/test/products/prod_PqZFpCs1Jq6X4E
    """
    product = stripe.Product.retrieve(product_id)
    return int(product["metadata"]["request_count"])
