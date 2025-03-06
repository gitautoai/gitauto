import pytest

from services.supabase.owers_manager import get_stripe_customer_id

def test_valid_owner():
    owner_id = 4620828
    result = get_stripe_customer_id(owner_id)
    assert result == "cus_RCZOxKQHsSk93v"

def test_non_existent_owner():
    owner_id = 9999999
    result = get_stripe_customer_id(owner_id)
    assert result is None

def test_negative_owner_id():
    result = get_stripe_customer_id(-1)
    assert result is None

def test_zero_owner_id():
    result = get_stripe_customer_id(0)
    assert result is None

def test_random_owner_id():
    result = get_stripe_customer_id(1234)
    assert result is None
