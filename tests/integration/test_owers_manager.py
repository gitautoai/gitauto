import os
import pytest
from services.supabase.owers_manager import get_stripe_customer_id

@pytest.mark.integration
def test_get_stripe_customer_id_not_found():
    result = get_stripe_customer_id(999999)
    assert result is None

@pytest.mark.integration
def test_get_stripe_customer_id_found():
    test_owner_id = os.getenv("TEST_OWNER_ID")
    expected_customer_id = os.getenv("TEST_STRIPE_CUSTOMER_ID")
    if test_owner_id is None or expected_customer_id is None:
        pytest.skip("Integration test requires TEST_OWNER_ID and TEST_STRIPE_CUSTOMER_ID environment variables to be set")
    result = get_stripe_customer_id(int(test_owner_id))
    assert result == expected_customer_id
