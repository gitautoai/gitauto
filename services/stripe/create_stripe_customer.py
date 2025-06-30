from services.stripe.client import stripe
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def create_stripe_customer(
    owner_id: int,
    owner_name: str,
    installation_id: int,
    user_id: int,
    user_name: str,
):
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
    return customer.id
