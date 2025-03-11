import pytest
from services.supabase.owers_manager import get_stripe_customer_id
from tests.constants import OWNER


def test_get_stripe_customer_id_success():
    owner_id = 4620828
    result = get_stripe_customer_id(owner_id=owner_id)
    assert result == "cus_RCZOxKQHsSk93v"


def test_get_stripe_customer_id_nonexistent():
    owner_id = 999999999
    result = get_stripe_customer_id(owner_id=owner_id)
    assert result is None


def test_get_stripe_customer_id_invalid():
    owner_id = -1
    result = get_stripe_customer_id(owner_id=owner_id)
    assert result is None


def test_get_stripe_customer_id_zero():
    owner_id = 0
    result = get_stripe_customer_id(owner_id=owner_id)
    assert result is None


def test_get_stripe_customer_id_none():
    result = get_stripe_customer_id(owner_id=None)
    assert result is None