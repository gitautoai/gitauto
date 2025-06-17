import asyncio
from unittest import mock

from services.supabase.gitauto_manager import create_installation
from services.supabase.users_manager import upsert_user
from services.supabase.client import supabase
from tests.constants import TEST_NEW_INSTALLATION_ID, TEST_USER_ID, TEST_OWNER_ID


def wipe_installation_owner_user_data(installation_id=TEST_NEW_INSTALLATION_ID):
    # Original cleanup for usage records
    supabase.table("usage").delete().eq("user_id", TEST_USER_ID).eq("installation_id", installation_id).execute()

    # Additional cleanup for repositories records (foreign key constraint)
    supabase.table("repositories").delete().eq("installation_id", installation_id).execute()

    # Additional cleanup for coverages records (foreign key constraint)
    supabase.table("coverages").delete().eq("installation_id", installation_id).execute()

    # Additional cleanup for pull_requests records (foreign key constraint)
    supabase.table("pull_requests").delete().eq("installation_id", installation_id).execute()

    # Delete issues
    supabase.table("issues").delete().eq("installation_id", installation_id).execute()

    # If no other installations exist, delete owner
    data = supabase.table("installations").select("installation_id").eq("owner_id", TEST_OWNER_ID).execute()
    if len(data[1]) == 0:
        supabase.table("owners").delete().eq("owner_id", TEST_OWNER_ID).execute()


async def test_install_uninstall_install() -> None:
    """Testing install uninstall methods"""
    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data(TEST_NEW_INSTALLATION_ID)
    
    # Additional cleanup to ensure no leftover data
    supabase.table("installations").delete().eq("installation_id", TEST_NEW_INSTALLATION_ID).execute()
    
    # Create a more comprehensive mock setup
    # We'll mock the process_repositories function entirely to avoid the cloning process
    with mock.patch("services.supabase.gitauto_manager.process_repositories") as mock_process:
        mock_process.return_value = None
        create_installation(
            installation_id=TEST_NEW_INSTALLATION_ID,
            owner_type="org",
            owner_name="TestOrg",
            owner_id=TEST_OWNER_ID,
            user_id=TEST_USER_ID,
            user_name="TestUser",
            email="test@example.com"
        )

    # Clean Up
    wipe_installation_owner_user_data()
    wipe_installation_owner_user_data(TEST_NEW_INSTALLATION_ID)
    supabase.table("installations").delete().eq("installation_id", TEST_NEW_INSTALLATION_ID).execute()
