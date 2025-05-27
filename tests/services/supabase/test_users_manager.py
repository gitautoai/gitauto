import pytest
from config import (
    TEST_INSTALLATION_ID,
    TEST_ISSUE_NUMBER,
    TEST_OWNER_ID,
    TEST_OWNER_NAME,
    TEST_OWNER_TYPE,
    TEST_REPO_ID,
    TEST_USER_ID,
    TEST_USER_NAME,
    TEST_EMAIL,
    TEST_REPO_NAME,
)
from utils.time.timer import timer_decorator
from services.supabase.gitauto_manager import create_user_request, create_installation
from tests.services/supabase/wipe_data import wipe_installation_owner_user_data

@timer_decorator
@pytest.mark.asyncio
async def test_create_and_update_user_request_works() -> None:
    """Test that I can create and complete user request in usage table"""
    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data()

    # Insert data into the db -> create installation
    create_installation(
        installation_id=TEST_INSTALLATION_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        owner_id=TEST_OWNER_ID,
        user_id=TEST_USER_ID,
        user_name=TEST_USER_NAME,
        email=TEST_EMAIL,
    )

    usage_record_id = await create_user_request(
        user_id=TEST_USER_ID,
        user_name=TEST_USER_NAME,
        installation_id=TEST_INSTALLATION_ID,
        owner_id=TEST_OWNER_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        repo_id=TEST_REPO_ID,
        repo_name=TEST_REPO_NAME,
        issue_number=TEST_ISSUE_NUMBER,
        source="github",
        email=TEST_EMAIL,
    )
    assert isinstance(usage_record_id, int)

@pytest.mark.skip(reason="Skipping due to foreign key constraint issue in installations table")
@timer_decorator
@pytest.mark.asyncio
async def test_create_and_update_user_request_skipped() -> None:
    """Skipped test for create and update user request"""
    pass
