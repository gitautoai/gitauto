# run this file locally with: python -m tests.test_stripe

from services.stripe.customer import get_subscription


def test_get_subscription() -> None:
    # free tier subscription
    # https://dashboard.stripe.com/test/customers/cus_QO4R5vh6FJuN7t
    subscription = get_subscription("cus_QO4R5vh6FJuN7t")
    assert len(subscription["data"]) == 1
    assert (
        subscription["data"][0]["items"]["data"][0]["price"]["id"]
        == "price_1Oz6r2KUN3yUNaHzQQGk7SQ3"
    )


# test_get_subscription()
