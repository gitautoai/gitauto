# run this file locally with: python -m tests.services.supabase.test_owners_manager

# Standard imports
import pytest

# Local imports
from config import OWNER_ID
from services.supabase.client import supabase
from services.supabase.owners_manager import get_stripe_customer_id
from tests.services.supabase.wipe_data import wipe_installation_owner_user_data
from utils.timer import timer_decorator


@timer_decorator
def test_get_stripe_customer_id_returns_id_for_existing_owner():
    """Test that get_stripe_customer_id returns the correct stripe_customer_id for an existing owner"""
    # Clean up at the beginning just in case
    wipe_installation_owner_user_data()

    # Setup test data
    test_owner_id = -999  # Use negative ID to avoid conflicts
    test_stripe_customer_id = "cus_test123"
    
    # Insert test owner data
    data, _ = (
        supabase.table("owners")
        .insert({"owner_id": test_owner_id, "stripe_customer_id": test_stripe_customer_id})
        .execute()
    )
    
    # Test the function
    result = get_stripe_customer_id(owner_id=test_owner_id)
    
    # Verify result
    assert result == test_stripe_customer_id
    
    # Clean up
    wipe_installation_owner_user_data()


@timer_decorator
def test_get_stripe_customer_id_returns_none_for_nonexistent_owner():
    """Test that get_stripe_customer_id returns None for a non-existent owner"""
    # Clean up at the beginning just in case
    wipe_installation_owner_user_data()
    
    # Test with non-existent owner ID
    result = get_stripe_customer_id(owner_id=-1000)
    
    # Verify result
    assert result is None
    
    # Clean up
    wipe_installation_owner_user_data()


@timer_decorator
def test_get_stripe_customer_id_handles_errors():
    """Test that get_stripe_customer_id handles errors gracefully"""
    # Test with invalid owner_id type
    result = get_stripe_customer_id(owner_id="invalid")  # type: ignore
    assert result is None

if __name__ == "__main__":
    pytest.main([__file__])