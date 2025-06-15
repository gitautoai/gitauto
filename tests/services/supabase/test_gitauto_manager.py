# run this file locally with: python -m tests.services.supabase.test_gitauto_manager
import asyncio
from config import (
    TEST_EMAIL,
    TEST_INSTALLATION_ID,
    TEST_OWNER_ID,
    TEST_OWNER_NAME,
    TEST_OWNER_TYPE,
    TEST_USER_ID,
    TEST_USER_NAME,
)
from services.supabase.client import supabase
from services.supabase.gitauto_manager import create_installation
from tests.services.supabase.wipe_data import (
    wipe_installation_owner_user_data,
)
from utils.time.timer import timer_decorator


@timer_decorator
async def test_create_installation_works() -> None:
    """Tests based on creating a record and updating it in usage table"""
    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data()

    # insert data into the db -> create installation
    response = create_installation(
        installation_id=TEST_INSTALLATION_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name="gitautoai",
        owner_id=TEST_OWNER_ID,
        user_id=TEST_USER_ID,
        user_name=TEST_USER_NAME,
        email=TEST_EMAIL,
    )
    assert response is not None

    # Verify the installation was created with correct data
    data, _ = (
        supabase.table("installations")
        .select("*")
        .eq("installation_id", TEST_INSTALLATION_ID)
        .execute()
    )
    assert len(data[1]) == 1
    assert data[1][0]["owner_name"] == "gitautoai"
    assert data[1][0]["owner_type"] == TEST_OWNER_TYPE
    assert data[1][0]["owner_id"] == TEST_OWNER_ID

    # Clean Up
    wipe_installation_owner_user_data()


@timer_decorator
async def test_create_installation_updates_existing() -> None:
    """Tests that creating an installation with the same ID updates the existing record"""
    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data()

    # Create initial installation
    create_installation(
        installation_id=TEST_INSTALLATION_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        owner_id=TEST_OWNER_ID,
        user_id=TEST_USER_ID,
        user_name=TEST_USER_NAME,
        email=TEST_EMAIL,
    )

    # Create another installation with same ID but different data
    new_owner_name = "different_owner"
    response = create_installation(
        installation_id=TEST_INSTALLATION_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=new_owner_name,
        owner_id=TEST_OWNER_ID,
        user_id=TEST_USER_ID,
        user_name=TEST_USER_NAME,
        email=TEST_EMAIL,
    )
    assert response is not None

    # Verify the record was updated
    data, _ = (
        supabase.table("installations")
        .select("*")
        .eq("installation_id", TEST_INSTALLATION_ID)
        .execute()
    )
    assert len(data[1]) == 1
    assert data[1][0]["owner_name"] == new_owner_name

    # Clean Up
    wipe_installation_owner_user_data()


# Add this to run the async tests
if __name__ == "__main__":
    asyncio.run(test_create_installation_works())
    asyncio.run(test_create_installation_updates_existing())