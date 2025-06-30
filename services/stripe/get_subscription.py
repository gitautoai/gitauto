from services.stripe.client import stripe
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
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
