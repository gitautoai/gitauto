import os
from config import TEST_OWNER_ID, TEST_USER_ID, TEST_INSTALLATION_ID, TEST_USER_NAME
from services.supabase.client import supabase
from utils.time.timer import timer_decorator

@timer_decorator

def wipe_installation_owner_user_data(installation_id: int = TEST_INSTALLATION_ID) -> None:
    """Wipe all data from installations, owners, and users tables for the test owner and user.
    This function deletes all records related to the owner and user, regardless of the installation id.
    """
    # Delete usage records for the user
    supabase.table("usage").delete().eq("user_id", TEST_USER_ID).execute()

    # Delete issues for this owner
    supabase.table("issues").delete().eq("owner_id", TEST_OWNER_ID).execute()

    # Delete installations for this owner
    supabase.table("installations").delete().eq("owner_id", TEST_OWNER_ID).execute()

    # Delete user records
    supabase.table("users").delete().eq("user_id", TEST_USER_ID).execute()
    supabase.table("users").delete().eq("user_name", TEST_USER_NAME).execute()

    # Delete owner record
    supabase.table("owners").delete().eq("owner_id", TEST_OWNER_ID).execute()
