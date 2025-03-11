import os
import pytest

from config import OWNER_ID
from services.supabase import SupabaseManager
from services.supabase.owers_manager import get_stripe_customer_id
from tests.services.supabase.wipe_data import wipe_installation_owner_user_data
from utils.timer import timer_decorator

SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""
SUPABASE_URL = os.getenv("SUPABASE_URL") or ""


@timer_decorator
def test_get_stripe_customer_id():
    """Test get_stripe_customer_id function with various scenarios"""
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)

    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data()

    # Test case 1: Non-existent owner_id should return None
    non_existent_owner_id = 999999999
    assert get_stripe_customer_id(owner_id=non_existent_owner_id) is None

    # Test case 2: Create an owner with a specific stripe_customer_id
    test_owner_id = 4620828
    expected_stripe_customer_id = "cus_RCZOxKQHsSk93v"

    # Insert test data directly into the owners table
    supabase_manager.client.table("owners").insert(
        json={
            "owner_id": test_owner_id,
            "stripe_customer_id": expected_stripe_customer_id
        }
    ).execute()

    # Verify the function returns the expected stripe_customer_id
    assert get_stripe_customer_id(owner_id=test_owner_id) == expected_stripe_customer_id

    # Test case 3: Test with empty stripe_customer_id
    empty_stripe_owner_id = 12345
    supabase_manager.client.table("owners").insert(
        json={
            "owner_id": empty_stripe_owner_id,
            "stripe_customer_id": ""
        }
    ).execute()
    assert get_stripe_customer_id(owner_id=empty_stripe_owner_id) == ""

    # Test case 4: Test with null stripe_customer_id
    null_stripe_owner_id = 67890
    supabase_manager.client.table("owners").insert(
        json={
            "owner_id": null_stripe_owner_id,
            "stripe_customer_id": None
        }
    ).execute()
    assert get_stripe_customer_id(owner_id=null_stripe_owner_id) is None

    # Clean up after the test
    supabase_manager.client.table("owners").delete().eq("owner_id", test_owner_id).execute()
    supabase_manager.client.table("owners").delete().eq("owner_id", empty_stripe_owner_id).execute()
    supabase_manager.client.table("owners").delete().eq("owner_id", null_stripe_owner_id).execute()
    wipe_installation_owner_user_data()