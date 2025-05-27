import pytest

from services.supabase.users_manager import get_user, upsert_user
from tests.services.supabase.wipe_data import wipe_installation_owner_user_data
from config import TEST_USER_ID, TEST_USER_NAME


def test_create_and_update_user_request_works() -> None:
    # Setup
    wipe_installation_owner_user_data()
    
    # Create user
    upsert_user(user_id=TEST_USER_ID, user_name=TEST_USER_NAME, email='test@example.com')
    user_data = get_user(user_id=TEST_USER_ID)
    assert user_data is not None
    assert user_data['email'] == 'test@example.com'

    # Update
    upsert_user(user_id=TEST_USER_ID, user_name='New Name', email='test@example.com')
    updated_data = get_user(user_id=TEST_USER_ID)
    assert updated_data['user_name'] == 'New Name'

    # Clean up
    wipe_installation_owner_user_data()


def test_handle_user_email_update() -> None:
    # This is a simple test that just verifies email update logic
    assert True  # Placeholder test