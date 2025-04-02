# Standard imports
import pytest

# Local imports
from config import OWNER_ID
from services.supabase.client import supabase
from services.supabase.owners_manager import get_stripe_customer_id
from tests.services.supabase.wipe_data import wipe_installation_owner_user_data
from utils.timer import timer_decorator


@pytest.fixture(scope="function")
def setup_test_data():
    """Set up test data in the owners table"""
    # First, clean up any existing test data
    wipe_installation_owner_user_data()

    # Insert test data
    test_stripe_customer_id = "cus_test123"
    supabase.table("owners").insert({
        "owner_id": OWNER_ID,
        "stripe_customer_id": test_stripe_customer_id,
        "owner_type": "Organization",
        "owner_name": "gitautoai"
    }).execute()

    yield test_stripe_customer_id

    # Clean up after test
    wipe_installation_owner_user_data()


@timer_decorator
def test_get_stripe_customer_id_success(setup_test_data):
    """Test successful retrieval of stripe_customer_id"""
    expected_customer_id = setup_test_data
    
    # Test the function
    result = get_stripe_customer_id(owner_id=OWNER_ID)
    
    # Verify the result
    assert result == expected_customer_id


@timer_decorator
def test_get_stripe_customer_id_not_found():
    """Test when owner_id doesn't exist in the database"""
    # Clean up any existing test data
    wipe_installation_owner_user_data()
    
    # Test with non-existent owner_id
    result = get_stripe_customer_id(owner_id=999999)
    assert result is None