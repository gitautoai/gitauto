from services.supabase.owners_manager import get_stripe_customer_id
from services.supabase.client import supabase
from utils.timer import timer_decorator
from tests.services.supabase.wipe_data import wipe_installation_owner_user_data
"""Integration tests for owners_manager.py"""



def setup_function():
    """Clean up data before each test"""
    wipe_installation_owner_user_data()


def teardown_function():
    """Clean up data after each test"""
    wipe_installation_owner_user_data()


@timer_decorator
def test_get_stripe_customer_id():
    # Use test-specific owner IDs
    test_owner_id = 999888777
    test_stripe_id = "cus_RCZOxKQHsSk93v"

    owner_without_stripe = 444555666
    # Clean up test data
    supabase.table("owners").delete().eq("owner_id", test_owner_id).execute()
    supabase.table("owners").delete().eq("owner_id", owner_without_stripe).execute()

    # Test case 1: Valid owner with stripe_customer_id
    stripe_customer_id = "cus_RCZOxKQHsSk93v"
    supabase.table("owners").insert(
        json={"owner_id": test_owner_id, "stripe_customer_id": test_stripe_id}
    ).execute()
    assert get_stripe_customer_id(owner_id=test_owner_id) == test_stripe_id

    # Test case 2: Non-existent owner_id
    assert get_stripe_customer_id(owner_id=111222333) is None

    # Test case 3: Invalid owner_id (negative) should return None
    invalid_owner_id = -1
    assert get_stripe_customer_id(owner_id=invalid_owner_id) is None

    # Test case 4: Invalid owner_id (zero) should return None
    zero_owner_id = 0
    assert get_stripe_customer_id(owner_id=zero_owner_id) is None

    # Test case 5: Owner without stripe_customer_id should return None
    owner_without_stripe = 888888
    supabase.table("owners").insert(
        json={"owner_id": owner_without_stripe, "stripe_customer_id": None}
    ).execute()
    assert get_stripe_customer_id(owner_id=owner_without_stripe) is None

    # Clean up after tests
    wipe_installation_owner_user_data()
