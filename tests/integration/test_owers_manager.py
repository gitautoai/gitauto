import os
import pytest

from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from services.supabase.owers_manager import get_stripe_customer_id
from supabase import create_client

client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def cleanup_owner(owner_id: int):
    client.table("owners").delete().eq("owner_id", owner_id).execute()

@pytest.fixture(autouse=True)
def run_around_tests():
    # Cleanup before test
    for owner_id in [4620828, 999999, 111, -1]:
        cleanup_owner(owner_id)
    yield
    # Cleanup after test
    for owner_id in [4620828, 999999, 111, -1]:
        cleanup_owner(owner_id)

def insert_owner(owner_id: int, stripe_customer_id):
    data = {"owner_id": owner_id, "stripe_customer_id": stripe_customer_id}
    client.table("owners").insert(data).execute()

def test_get_stripe_customer_id_valid():
    insert_owner(4620828, "cus_RCZOxKQHsSk93v")
    result = get_stripe_customer_id(4620828)
    assert result == "cus_RCZOxKQHsSk93v"

def test_get_stripe_customer_id_non_existing():
    result = get_stripe_customer_id(999999)
    assert result is None

def test_get_stripe_customer_id_null_value():
    insert_owner(111, None)
    result = get_stripe_customer_id(111)
    assert result is None

def test_get_stripe_customer_id_negative():
    result = get_stripe_customer_id(-1)
    assert result is None

def test_get_stripe_customer_id_invalid_type():
    try:
        result = get_stripe_customer_id("not_an_int")
    except Exception:
        result = None
    assert result is None
