# run this file locally with: python -m tests.services.supabase.test_gitauto_manager
import os
import asyncio
from config import OWNER_TYPE, TEST_EMAIL, USER_NAME
from services.supabase import SupabaseManager
from tests.services.supabase.wipe_data import (
    wipe_installation_owner_user_data,
)
from utils.timer import timer_decorator

SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")


@timer_decorator
async def test_create_update_user_request_works() -> None:
    """Tests based on creating a record and updating it in usage table"""
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)

    # using -1 to not conflict with real data
    user_id = -1
    installation_id = -1

    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data()

    # insert data into the db -> create installation
    supabase_manager.create_installation(
        installation_id=installation_id,
        owner_type=OWNER_TYPE,
        owner_name="gitautoai",
        owner_id=-1,
        user_id=user_id,
        user_name=USER_NAME,
        email=TEST_EMAIL,
    )

    usage_record_id = await supabase_manager.create_user_request(
        user_id=user_id,
        user_name=USER_NAME,
        installation_id=installation_id,
        # fake issue creation
        unique_issue_id="U/gitautoai/test#01",
        email=TEST_EMAIL,
    )
    assert isinstance(
        usage_record_id,
        int,
    )
    assert (
        supabase_manager.complete_and_update_usage_record(
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
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)

    # using -1 to not conflict with real data
    user_id = -1
    installation_id = -1
    unique_issue_id = "U/gitautoai/test#01"

    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data()

    # insert data into the db -> create installation
    supabase_manager.create_installation(
        installation_id=installation_id,
        owner_type=OWNER_TYPE,
        owner_name="gitautoai",
        owner_id=-1,
        user_id=user_id,
        user_name=USER_NAME,
        email=TEST_EMAIL,
    )

    # Creating multiple usage records where is_completed = false.
    for _ in range(0, 5):
        await supabase_manager.create_user_request(
            user_id=user_id,
            user_name=USER_NAME,
            installation_id=installation_id,
            # fake issue creation
            unique_issue_id=unique_issue_id,
            email=TEST_EMAIL,
        )

    usage_record_id = await supabase_manager.create_user_request(
        user_id=user_id,
        user_name=USER_NAME,
        installation_id=installation_id,
        # fake issue creation
        unique_issue_id=unique_issue_id,
        email=TEST_EMAIL,
    )
    assert isinstance(
        usage_record_id,
        int,
    )
    assert (
        supabase_manager.complete_and_update_usage_record(
            usage_record_id=usage_record_id,
            token_input=1000,
            token_output=100,
            total_seconds=100,
        )
        is None
    )

    data, _ = (
        supabase_manager.client.table("usage")
        .select("*")
        .eq("user_id", user_id)
        .eq("installation_id", installation_id)
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
