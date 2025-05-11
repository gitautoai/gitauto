import pytest

from config import TEST_OWNER_ID, TEST_OWNER_NAME, TEST_OWNER_TYPE, TEST_INSTALLATION_ID, TEST_USER_ID, TEST_USER_NAME, TEST_EMAIL
from services.supabase.client import supabase
from services.supabase.gitauto_manager import create_installation
from services.supabase.owners.get_owner import get_owner
from tests.services.supabase.wipe_data import wipe_installation_owner_user_data
from utils.time.timer import timer_decorator


@timer_decorator
def test_get_owner_integration_success():
    """Test get_owner function with real database connection"""
    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data()
    
    # Insert test data into the database
    create_installation(
        installation_id=TEST_INSTALLATION_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        owner_id=TEST_OWNER_ID,
        user_id=TEST_USER_ID,
        user_name=TEST_USER_NAME,
        email=TEST_EMAIL,
    )
    
    # Act - Get the owner
    owner = get_owner(owner_id=TEST_OWNER_ID)
    
    # Assert
    assert owner is not None
    assert owner["owner_id"] == TEST_OWNER_ID
    assert owner["owner_name"] == TEST_OWNER_NAME
    assert owner["owner_type"] == TEST_OWNER_TYPE
    assert "stripe_customer_id" in owner
    
    # Clean up
    wipe_installation_owner_user_data()


@timer_decorator
def test_get_owner_integration_not_found():
    """Test get_owner function with non-existent owner ID"""
    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data()
    
    # Act - Try to get a non-existent owner
    non_existent_owner_id = 999999999
    owner = get_owner(owner_id=non_existent_owner_id)
    
    # Assert
    assert owner is None


@timer_decorator
def test_get_owner_integration_with_real_data():
    """Test get_owner function with real data from the database"""
    # This test assumes there's at least one owner in the database
    # We'll first check if the owner exists, and if not, we'll create one
    
    # Check if the test owner exists
    existing_owner = get_owner(owner_id=TEST_OWNER_ID)
    
    if existing_owner is None:
        # Create a test owner if it doesn't exist
        create_installation(
            installation_id=TEST_INSTALLATION_ID,
            owner_type=TEST_OWNER_TYPE,
            owner_name=TEST_OWNER_NAME,
            owner_id=TEST_OWNER_ID,
            user_id=TEST_USER_ID,
            user_name=TEST_USER_NAME,
            email=TEST_EMAIL,
        )
        
        # Get the newly created owner
        owner = get_owner(owner_id=TEST_OWNER_ID)
        
        # Clean up after the test
        wipe_installation_owner_user_data()
    else:
        # Use the existing owner
        owner = existing_owner
    
    # Assert
    assert owner is not None
    assert owner["owner_id"] == TEST_OWNER_ID
    assert "owner_name" in owner
    assert "owner_type" in owner
    assert "stripe_customer_id" in owner