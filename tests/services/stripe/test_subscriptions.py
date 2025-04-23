import unittest
from unittest.mock import patch

from services.stripe.subscriptions import get_stripe_product_id


def test_no_subscriptions():
    with patch("stripe.Subscription.list") as mock_list:
        mock_list.return_value = {"data": []}
        result = get_stripe_product_id("cust_empty")
        assert result is None


def test_single_subscription():
    with patch("stripe.Subscription.list") as mock_list:
        mock_list.return_value = {
            "data": [{
                "plan": {"amount": 1000, "product": "prod_single"}
            }]
        }
        result = get_stripe_product_id("cust_single")
        assert result == "prod_single"


def test_multiple_subscriptions():
    with patch("stripe.Subscription.list") as mock_list:
        subs = [
            {"plan": {"amount": 1000, "product": "prod_low"}},
            {"plan": {"amount": 2000, "product": "prod_high"}},
            {"plan": {"amount": 1500, "product": "prod_mid"}},
        ]
        mock_list.return_value = {"data": subs}
        result = get_stripe_product_id("cust_multiple")
        assert result == "prod_high"


def test_exception_handling():
    with patch("stripe.Subscription.list") as mock_list:
        mock_list.side_effect = Exception("API Error")
        result = get_stripe_product_id("cust_error")
        assert result is None


if __name__ == "__main__":
    unittest.main()
