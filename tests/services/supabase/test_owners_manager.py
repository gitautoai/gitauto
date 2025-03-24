import pytest
from services.supabase.owners_manager import get_stripe_customer_id


def test_get_stripe_customer_id_success():
    owner_id = 4620828
    stripe_customer_id = get_stripe_customer_id(owner_id=owner_id)
    assert stripe_customer_id == "cus_RCZOxKQHsSk93v"


def test_get_stripe_customer_id_nonexistent():
    owner_id = 999999999
    stripe_customer_id = get_stripe_customer_id(owner_id=owner_id)
    assert stripe_customer_id is None


def test_get_stripe_customer_id_invalid():
    test_cases = [-1, 0]
    for owner_id in test_cases:
        stripe_customer_id = get_stripe_customer_id(owner_id=owner_id)
        assert stripe_customer_id is None