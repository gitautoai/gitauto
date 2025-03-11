import pytest
from services.supabase.owers_manager import get_stripe_customer_id


def test_get_stripe_customer_id():
    owner_id = 4620828
    expected_customer_id = "cus_RCZOxKQHsSk93v"
    customer_id = get_stripe_customer_id(owner_id=owner_id)
    assert customer_id == expected_customer_id


def test_get_stripe_customer_id_nonexistent():
    owner_id = 999999999
    customer_id = get_stripe_customer_id(owner_id=owner_id)
    assert customer_id is None


def test_get_stripe_customer_id_invalid():
    owner_id = -1
    customer_id = get_stripe_customer_id(owner_id=owner_id)
    assert customer_id is None