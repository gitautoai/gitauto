# run this file locally with: python -m tests.services.supabase.test_owers_manager
import os
import pytest
import random

from config import OWNER_ID, OWNER_NAME, OWNER_TYPE, USER_ID, USER_NAME, TEST_EMAIL, INSTALLATION_ID
from services.supabase import SupabaseManager
from services.supabase.owers_manager import get_stripe_customer_id
from tests.services.supabase.wipe_data import wipe_installation_owner_user_data
from utils.timer import timer_decorator


SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")


@timer_decorator
def test_get_stripe_customer_id_with_existing_owner():
    """Test get_stripe_customer_id with an existing owner_id."""
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)
    
    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data()
    
    # Create a test owner with a known stripe_customer_id
    test_owner_id = 99999999  # Using a very high number to avoid conflicts
    expected_stripe_customer_id = "cus_RCZOxKQHsSk93v"
    
    # Insert the test owner directly into the owners table
    supabase_manager.client.table("owners").insert({
        "owner_id": test_owner_id,
        "stripe_customer_id": expected_stripe_customer_id
    }).execute()
    
    # Test the function
    result = get_stripe_customer_id(owner_id=test_owner_id)
    
    # Verify the result
    assert result == expected_stripe_customer_id
    
    # Clean up
    supabase_manager.client.table("owners").delete().eq("owner_id", test_owner_id).execute()


@timer_decorator
def test_get_stripe_customer_id_with_nonexistent_owner():
    """Test get_stripe_customer_id with a non-existent owner_id."""
    # Use a non-existent owner_id
    non_existent_owner_id = 999999999
    
    # Test the function
    result = get_stripe_customer_id(owner_id=non_existent_owner_id)
    
    # Verify the result is None for non-existent owner
    assert result is None


@timer_decorator
def test_get_stripe_customer_id_with_null_customer_id():
    """Test get_stripe_customer_id with an owner that has a null stripe_customer_id."""
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)
    
    # Create a test owner with a null stripe_customer_id
    test_owner_id = 5555555
    
    # Insert the test owner directly into the owners table with null stripe_customer_id
    supabase_manager.client.table("owners").insert({
        "owner_id": test_owner_id,
        "stripe_customer_id": None
    }).execute()
    
    # Test the function
    result = get_stripe_customer_id(owner_id=test_owner_id)
    
    # Verify the result is None for null stripe_customer_id
    assert result is None
    
    # Clean up
    supabase_manager.client.table("owners").delete().eq("owner_id", test_owner_id).execute()


@timer_decorator
def test_get_stripe_customer_id_with_empty_string_customer_id():
    """Test get_stripe_customer_id with an owner that has an empty string stripe_customer_id."""
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)
    
    # Create a test owner with an empty string stripe_customer_id
    test_owner_id = 6666666
    
    # Insert the test owner directly into the owners table with empty string stripe_customer_id
    supabase_manager.client.table("owners").insert({
        "owner_id": test_owner_id,
        "stripe_customer_id": ""
    }).execute()
    
    # Test the function
    result = get_stripe_customer_id(owner_id=test_owner_id)
    
    # Verify the result is an empty string
    assert result == ""
    
    # Clean up
    supabase_manager.client.table("owners").delete().eq("owner_id", test_owner_id).execute()


@timer_decorator
def test_get_stripe_customer_id_with_invalid_owner_id_type():
    """Test get_stripe_customer_id with an invalid owner_id type."""
    # Test with None
    with pytest.raises(TypeError):
        get_stripe_customer_id(owner_id=None)
    
    # Test with string (should be int)
    with pytest.raises(TypeError):
        get_stripe_customer_id(owner_id="invalid_type")


@timer_decorator
def test_get_stripe_customer_id_with_zero_owner_id():
    """Test get_stripe_customer_id with owner_id=0."""
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)
    
    # Create a test owner with owner_id=0
    test_owner_id = 0
    expected_stripe_customer_id = "cus_zero_owner"
    
    # Insert the test owner directly into the owners table
    supabase_manager.client.table("owners").insert({
        "owner_id": test_owner_id,
        "stripe_customer_id": expected_stripe_customer_id
    }).execute()
    
    # Test the function
    result = get_stripe_customer_id(owner_id=test_owner_id)
    
    # Verify the result
    assert result == expected_stripe_customer_id
    
    # Clean up
    supabase_manager.client.table("owners").delete().eq("owner_id", test_owner_id).execute()


@timer_decorator
def test_get_stripe_customer_id_with_negative_owner_id():
    """Test get_stripe_customer_id with a negative owner_id."""
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)
    
    # Create a test owner with a negative owner_id
    test_owner_id = -9999
    expected_stripe_customer_id = "cus_negative_owner"
    
    # Insert the test owner directly into the owners table
    supabase_manager.client.table("owners").insert({
        "owner_id": test_owner_id,
        "stripe_customer_id": expected_stripe_customer_id
    }).execute()
    
    # Test the function
    result = get_stripe_customer_id(owner_id=test_owner_id)
    
    # Verify the result
    assert result == expected_stripe_customer_id
    
    # Clean up
    supabase_manager.client.table("owners").delete().eq("owner_id", test_owner_id).execute()
