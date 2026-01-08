from stripe import Subscription
from config import STRIPE_FREE_TIER_PRICE_ID
from services.stripe.client import stripe
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_paid_subscription(customer_id: str):
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

    # Filter out free tier subscriptions
    paid_subscriptions: list[Subscription] = []
    for sub in subscriptions:
        for item in sub["items"]["data"]:
            if item["price"]["id"] != STRIPE_FREE_TIER_PRICE_ID:
                paid_subscriptions.append(sub)
                break

    if not paid_subscriptions:
        return None

    # If multiple paid subscriptions exist, return only the highest priced one
    if len(paid_subscriptions) > 1:
        return max(
            paid_subscriptions,
            key=lambda x: x["items"]["data"][0]["price"]["unit_amount"] or 0,
        )

    return paid_subscriptions[0]
