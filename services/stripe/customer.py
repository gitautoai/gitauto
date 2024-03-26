import stripe
from config import STRIPE_API_KEY

stripe.api_key = STRIPE_API_KEY


def create_stripe_customer(
    owner_name: str, owner_id: int, installation_id: int, user_id: int, user_name: str
) -> str:
    customer = stripe.Customer.create(
        name=owner_name,
        metadata={
            "owner_id": owner_id,
            "installation_id": installation_id,
            "description": "GitAuto Github App Installation Event",
            "user_id": user_id,
            "user_name": user_name,
        },
    )
    print(customer)

    return customer["id"]


def get_subscription(stripe_customer_id: str):
    # Retrieve the customer object
    customer = stripe.Customer.retrieve(stripe_customer_id)

    # Check if the customer has any subscriptions
    if "subscriptions" in customer:
        subscriptions = customer.subscriptions.data
        # TODO return billing cycle
        if subscriptions:
            print("Customer has an active subscription.")
        else:
            print("Customer does not have an active subscription.")
    else:
        return -1
