# Standard imports
import pytest
import uuid

# Local imports
from config import OWNER_ID
from services.supabase.client import supabase
from services.supabase.owners_manager import get_stripe_customer_id
from tests.services.supabase.wipe_data import wipe_installation_owner_user_data


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Setup and teardown for each test"""
    # Setup: Clean existing test data
    wipe_installation_owner_user_data()
    
    yield
    
    # Teardown: Clean up test data
    wipe_installation_owner_user_data()


def test_get_stripe_customer_id_success():
    """Test get_stripe_customer_id when customer exists"""
    # Setup: Insert test data
    test_stripe_customer_id = f"cus_test_{uuid.uuid4().hex}"
    supabase.table("owners").insert({
        "owner_id": OWNER_ID,
        "stripe_customer_id": test_stripe_customer_id,
        "owner_type": "Organization",
        "owner_name": "testorg"
    }).execute()

    # Execute
    result = get_stripe_customer_id(owner_id=OWNER_ID)

    # Assert
    assert result == test_stripe_customer_id


def test_get_stripe_customer_id_not_found():
    """Test get_stripe_customer_id when customer does not exist"""
    # Execute
    result = get_stripe_customer_id(owner_id=999999)  # Non-existent owner_id

    # Assert
    assert result is None


def test_get_stripe_customer_id_empty_customer_id():
    """Test get_stripe_customer_id when stripe_customer_id is empty"""
    # Setup: Insert test data with empty stripe_customer_id
    supabase.table("owners").insert({
        "owner_id": OWNER_ID,
        "stripe_customer_id": None,
        "owner_type": "Organization",
        "owner_name": "testorg"
    }).execute()

    # Execute and Assert
    assert get_stripe_customer_id(owner_id=OWNER_ID) is None
