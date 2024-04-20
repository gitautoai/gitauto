"""Stripe APIs for customer pricing management"""

import logging
import stripe
from config import (
    STRIPE_API_KEY,
    STRIPE_FREE_TIER_PRICE_ID,
)

stripe.api_key = STRIPE_API_KEY


def subscribe_to_free_plan(
    customer_id: str,
    user_id: int,
    user_name: str,
    owner_id: int,
    owner_name: str,
    installation_id: int,
):
    "Subscribe this customer to the free tier plan in stripe"
    stripe.Subscription.create(
        customer=customer_id,
        items=[{"price": STRIPE_FREE_TIER_PRICE_ID}],
        description="GitAuto Github App Installation Event",
        metadata={
            "user_id": str(user_id),
            "user_name": user_name,
            "owner_id": str(owner_id),
            "owner_name": owner_name,
            "installation_id": str(installation_id),
        },
    )


def create_stripe_customer(
    owner_name: str, owner_id: int, installation_id: int, user_id: int, user_name: str
) -> str:
    """Create a customer with github metadata with Stripe"""
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


def get_subscription(customer_id: str) -> stripe.ListObject[stripe.Subscription]:
    """Get stripe subscription"""
    try:
        subscription = stripe.Subscription.list(customer=customer_id, status="active")
        return subscription
    except Exception as e:
        logging.error("get_subscriptiont %s", e)
        raise


def get_request_count_from_product_id_metadata(product_id: str) -> int:
    """https://docs.stripe.com/api/products/retrieve?lang=python"""
    try:
        price = stripe.Product.retrieve(product_id)
        return int(price["metadata"]["request_count"])
    except Exception as e:
        logging.error("get_request_count_from_product_id_metadata %s", e)
        raise
