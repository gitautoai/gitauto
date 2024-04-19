# run this file locally with: python -m tests.test_stripe

from services.stripe.customer import get_subscription


def test_get_subscription() -> None:
    # free tier subscription
    subscription = get_subscription("cus_PpmBT8nwkEC6Vn")
    assert len(subscription["data"]) == 1
    assert (
        subscription["data"][0]["items"]["data"][0]["price"]["id"]
        == "price_1Oz6r2KUN3yUNaHzQQGk7SQ3"
    )


# test_get_subscription()
