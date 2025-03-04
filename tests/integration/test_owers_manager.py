import pytest
from services.supabase.owers_manager import get_stripe_customer_id

def test_get_stripe_customer_id():
    owner_id = 4620828
    expected = "cus_RCZOxKQHsSk93v"
    result = get_stripe_customer_id(owner_id)
    assert result == expected
