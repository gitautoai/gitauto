import stripe

stripe.api_key = "sk_test_51OpME5KUN3yUNaHzn23LOJXtSJGapueOkEh0yZrBM7Yo8UQ0lFcRwbfjZUuLLSTjXPqu7pkP5KZgBYnaOYiaoy1y006HMOIwIg"


def create_stripe_customer(login: str, user_id: int, installation_id: int) -> str:
    customer = stripe.Customer.create(
        name=login,
        metadata={"user_id": user_id, "installation_id": installation_id},
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
