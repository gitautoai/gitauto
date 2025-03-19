import pytest
from services.supabase.owers_manager import get_stripe_customer_id
from tests.constants import INSTALLATION_ID

def test_get_stripe_customer_id():
    # Using INSTALLATION_ID as a valid owner ID for testing
    customer_id = get_stripe_customer_id(INSTALLATION_ID)
    assert isinstance(customer_id, (str, type(None)))

def test_get_stripe_customer_id_nonexistent():
    customer_id = get_stripe_customer_id(-1)
    assert customer_id is None

def test_get_stripe_customer_id_zero():
    customer_id = get_stripe_customer_id(0)
    assert customer_id is None
