import pytest

from services.supabase.owers_manager import get_stripe_customer_id


def test_get_stripe_customer_id():
    owner_id = 4620828
    expected_customer_id = "cus_RCZOxKQHsSk93v"
    actual_customer_id = get_stripe_customer_id(owner_id)
    assert actual_customer_id == expected_customer_id
