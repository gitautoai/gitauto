import pytest
from services.supabase.users_manager import get_user, upsert_user
from tests.services.supabase.wipe_data import wipe_installation_owner_user_data
from config import TEST_USER_ID, TEST_USER_NAME


def test_handle_user_email_update():
    # Setup
    wipe_installation_owner_user_data()
    upsert_user(user_id=TEST_USER_ID, user_name=TEST_USER_NAME, email="new_email@example.com")
    user_data = get_user(user_id=TEST_USER_ID)
    # Verify that the email is updated
    assert user_data["email"] == "new_email@example.com"
    # Clean up
    wipe_installation_owner_user_data()
