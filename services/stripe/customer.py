import stripe
from config import (
    FREE_TIER_REQUEST_AMOUNT,
    STRIPE_API_KEY,
    STRIPE_FREE_TIER_PRICE_ID,
)
from utils.handle_exceptions import handle_exceptions

stripe.api_key = STRIPE_API_KEY


@handle_exceptions(raise_on_error=True)
def subscribe_to_free_plan(
    customer_id: str,
    owner_id: int,
    owner_name: str,
    installation_id: int,
):
    stripe.Subscription.create(
        customer=customer_id,
        items=[{"price": STRIPE_FREE_TIER_PRICE_ID}],
        description="GitAuto Github App Installation Event",
        metadata={
            "owner_id": str(owner_id),
            "owner_name": owner_name,
            "installation_id": str(installation_id),
        },
    )


@handle_exceptions(raise_on_error=True)
def create_stripe_customer(
    owner_name: str, owner_id: int, installation_id: int, user_id: int, user_name: str
) -> str:
    customer = stripe.Customer.create(
        name=owner_name,
        metadata={
            "owner_id": str(owner_id),
            "installation_id": str(installation_id),
            "description": "GitAuto Github App Installation Event",
            "user_id": str(user_id),
            "user_name": user_name,
        },
    )
    return customer["id"]


@handle_exceptions(raise_on_error=True)
def get_subscription(customer_id: str):
    response = stripe.Subscription.list(customer=customer_id, status="active")
    subscriptions = response.data

    # Get all subscriptions if there are more pages
    while response.has_more:
        response = stripe.Subscription.list(
            customer=customer_id,
            status="active",
            starting_after=subscriptions[-1].id,
        )
        subscriptions.extend(response.data)

    # If multiple subscriptions exist, return only the highest priced one
    if len(subscriptions) > 1:
        highest_subscription = max(subscriptions, key=lambda x: x.plan.amount)
        response.data = [highest_subscription]

    return response


@handle_exceptions(default_return_value=FREE_TIER_REQUEST_AMOUNT, raise_on_error=False)
def get_base_request_limit(product_id: str):
    """
    https://docs.stripe.com/api/products/retrieve?lang=python
    https://dashboard.stripe.com/test/products/prod_PqZFpCs1Jq6X4E
    """
    product = stripe.Product.retrieve(product_id)
    return int(product["metadata"]["request_count"])
