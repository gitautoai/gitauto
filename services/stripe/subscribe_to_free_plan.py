from config import STRIPE_FREE_TIER_PRICE_ID
from services.stripe.client import stripe
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
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
