import pytest
from services.supabase.owers_manager import get_stripe_customer_id
from tests.constants import OWNER
from services.github.user_manager import get_user_id

def test_get_stripe_customer_id():
    owner_id = get_user_id(OWNER)
    customer_id = get_stripe_customer_id(owner_id)
    assert isinstance(customer_id, (str, type(None)))

def test_get_stripe_customer_id_nonexistent():
    customer_id = get_stripe_customer_id(-1)
    assert customer_id is None

def test_get_stripe_customer_id_zero():
    customer_id = get_stripe_customer_id(0)
    assert customer_id is None