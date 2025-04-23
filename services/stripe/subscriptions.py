import stripe
from config import STRIPE_API_KEY
from utils.error.handle_exceptions import handle_exceptions

stripe.api_key = STRIPE_API_KEY


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_stripe_product_id(customer_id: str):
    """https://docs.stripe.com/api/subscriptions/list?lang=python"""
    subscriptions = stripe.Subscription.list(customer=customer_id)
    data = subscriptions["data"]
    if len(data) == 0:
        return None

    # If multiple subscriptions exist, return only the highest priced one
    if len(data) > 1:
        data = [max(data, key=lambda x: x["plan"]["amount"])]

    subscription: stripe.Subscription = data[0]
    product_id: str = subscription["plan"]["product"]
    return product_id
