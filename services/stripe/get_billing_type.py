from typing import Literal
from stripe import Subscription
from config import EXCEPTION_OWNERS
from utils.error.handle_exceptions import handle_exceptions


BillingType = Literal["exception", "subscription", "credit"]

DEFAULT_BILLING_TYPE: BillingType = "credit"


@handle_exceptions(default_return_value=DEFAULT_BILLING_TYPE, raise_on_error=False)
def get_billing_type(
    owner_name: str,
    stripe_customer_id: str | None,
    paid_subscription: Subscription | None,
) -> BillingType:
    """Determine the billing type for a given owner."""
    if owner_name in EXCEPTION_OWNERS:
        return "exception"

    if not stripe_customer_id:
        return "credit"

    if paid_subscription:
        return "subscription"

    return "credit"
