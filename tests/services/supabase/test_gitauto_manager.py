# run this file locally with: python -m tests.services.supabase.test_gitauto_manager
import asyncio
from config import (
    TEST_EMAIL,
    TEST_INSTALLATION_ID,
    TEST_ISSUE_NUMBER,
    TEST_OWNER_ID,
    TEST_OWNER_NAME,
    TEST_OWNER_TYPE,
    TEST_REPO_ID,
    TEST_REPO_NAME,
    TEST_USER_ID,
    TEST_USER_NAME,
)
from services.supabase.client import supabase
from services.supabase.gitauto_manager import create_installation, create_user_request
from services.supabase.usage.update_usage import update_usage
from tests.services.supabase.wipe_data import (
    wipe_installation_owner_user_data,
)
from utils.time.timer import timer_decorator


@timer_decorator
async def test_create_update_user_request_works() -> None:
    """Tests based on creating a record and updating it in usage table"""
    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data()

    # insert data into the db -> create installation
    create_installation(
        installation_id=TEST_INSTALLATION_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name="gitautoai",
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
    assert isinstance(
        usage_record_id,
        int,
    )
    assert (
        update_usage(
            usage_record_id=usage_record_id,
            token_input=1000,
            token_output=100,
            total_seconds=100,
        )
        is None
    )

    # Clean Up
    wipe_installation_owner_user_data()


@timer_decorator
async def test_complete_and_update_usage_record_only_updates_one_record() -> None:
    """Tests based on creating a record and updating it in usage table"""
    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data()

    # insert data into the db -> create installation
    create_installation(
        installation_id=TEST_INSTALLATION_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        owner_id=TEST_OWNER_ID,
        user_id=TEST_USER_ID,
        user_name=TEST_USER_NAME,
        email=TEST_EMAIL,
    )

    # Creating multiple usage records where is_completed = false.
    for _ in range(0, 5):
        await create_user_request(
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
    assert isinstance(
        usage_record_id,
        int,
    )
    assert (
        update_usage(
            usage_record_id=usage_record_id,
            token_input=1000,
            token_output=100,
            total_seconds=100,
        )
        is None
    )

    data, _ = (
        supabase.table("usage")
        .select("*")
        .eq("user_id", TEST_USER_ID)
        .eq("installation_id", TEST_INSTALLATION_ID)
        .eq("is_completed", True)
        .execute()
    )
    assert len(data[1]) == 1
    # Clean Up
    wipe_installation_owner_user_data()


# Add this to run the async tests
if __name__ == "__main__":
    # asyncio.run(test_create_update_user_request_works())
    asyncio.run(test_complete_and_update_usage_record_only_updates_one_record())
