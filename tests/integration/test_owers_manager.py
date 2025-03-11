import pytest

from services.supabase.owers_manager import get_stripe_customer_id

def test_valid_owner_id():
    assert get_stripe_customer_id(4620828) == "cus_RCZOxKQHsSk93v"

def test_invalid_owner_id():
    # assuming returns None if id not found
    assert get_stripe_customer_id(9999999) is None

def test_negative_owner_id():
    with pytest.raises(ValueError):
        get_stripe_customer_id(-1)

def test_owner_id_zero():
    with pytest.raises(ValueError):
        get_stripe_customer_id(0)

def test_owner_id_string():
    with pytest.raises(TypeError):
        get_stripe_customer_id("abc")
