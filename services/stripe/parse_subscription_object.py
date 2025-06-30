# Standard imports
import logging

# Third party imports
import stripe

# Local imports
from config import STRIPE_FREE_TIER_PRICE_ID
from services.stripe.get_subscription import get_subscription
from services.stripe.subscribe_to_free_plan import subscribe_to_free_plan
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=True)
def parse_subscription_object(
    subscription: stripe.ListObject[stripe.Subscription],
    installation_id: int,
    customer_id: str,
    owner_id: int,
    owner_name: str,
):
    if len(subscription.data) > 2:
        msg = "There are more than 2 active subscriptions for this customer. This is a check when we move to multiple paid subscriptions."
        logging.error(msg)
        raise ValueError(msg)

    free_tier_start_date = 0
    free_tier_end_date = 0
    free_tier_product_id = ""
    free_tier_interval = "month"  # Default interval
    free_tier_quantity = 1  # Default quantity

    # return the first paid subscription if found, if not return the free one found
    for sub in subscription.data:
        # Iterate over the items, there should only be one item, but we do this just in case
        for item in sub["items"]["data"]:
            # Check if item is non-free tier
            if item["price"]["id"] == STRIPE_FREE_TIER_PRICE_ID:
                # Save free tier info to return just in case paid tier is not found
                free_tier_start_date = sub.current_period_start
                free_tier_end_date = sub.current_period_end
                free_tier_product_id = item["price"]["product"]
                free_tier_interval = item["price"]["recurring"]["interval"]
                free_tier_quantity = item["quantity"]
                continue

            return (
                sub["current_period_start"],
                sub["current_period_end"],
                item["price"]["product"],
                item["price"]["recurring"]["interval"],
                item["quantity"],
            )

    if (
        free_tier_start_date == 0
        or free_tier_end_date == 0
        or free_tier_product_id == ""
    ):
        # Customer should always have at least a free tier subscription, set by this codebase on installation webhook from github
        subscribe_to_free_plan(
            customer_id=customer_id,
            owner_id=owner_id,
            owner_name=owner_name,
            installation_id=installation_id,
        )
        subscription = get_subscription(customer_id=customer_id)
        return parse_subscription_object(
            subscription=subscription,
            installation_id=installation_id,
            customer_id=customer_id,
            owner_id=owner_id,
            owner_name=owner_name,
        )
    # Return from Free Tier Subscription if there is no paid subscription object
    return (
        free_tier_start_date,
        free_tier_end_date,
        free_tier_product_id,
        free_tier_interval,
        free_tier_quantity,
    )
