from config import (
    TEST_INSTALLATION_ID,
    TEST_OWNER_ID,
    TEST_OWNER_NAME,
    TEST_OWNER_TYPE,
)
from services.supabase.gitauto_manager import create_installation
from tests.services.supabase.wipe_data import wipe_installation_owner_user_data


def test_create_installation_runs_without_errors():
    # Clean up any existing data
    wipe_installation_owner_user_data()

    # Call create_installation; this should run without errors
    create_installation(
        installation_id=TEST_INSTALLATION_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        owner_id=TEST_OWNER_ID,
    )

    # Clean up
    wipe_installation_owner_user_data()
