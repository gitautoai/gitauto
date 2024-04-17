# run this file locally with: python -m tests.services.supabase.test_gitauto_manager
import os

from services.supabase import SupabaseManager

SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")


def wipe_installation_owner_user_data() -> None:
    """Wipe all data from installations, owners, and users tables"""
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)
    supabase_manager.client.table("usage").delete().eq("user_id", -1).eq(
        "installation_id", -1
    ).execute()

    supabase_manager.client.table("users").delete().eq("user_id", -1).eq(
        "installation_id", -1
    ).execute()

    supabase_manager.client.table("issues").delete().eq("installation_id", -1).execute()

    supabase_manager.client.table("installations").delete().eq(
        "installation_id", -1
    ).eq("owner_id", -1).execute()
    supabase_manager.client.table("owners").delete().eq("owner_id", -1).execute()


def test_create_update_user_request_works() -> None:
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
        owner_type="O",
        owner_name="gitautoai",
        owner_id=-1,
        user_id=user_id,
        user_name="test",
    )

    usage_record_id = supabase_manager.create_user_request(
        user_id=user_id,
        installation_id=installation_id,
        # fake issue creation
        unique_issue_id="U/gitautoai/test#01",
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
        )
        is None
    )

    # Clean Up
    wipe_installation_owner_user_data()


# test_create_update_user_request_works()
