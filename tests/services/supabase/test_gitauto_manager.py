# run this file locally with: python -m tests.services.supabase.test_gitauto_manager
import os

from services.supabase import SupabaseManager

SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")


def test_create_update_user_request_works() -> None:
    """Tests based on creating a record and updating it in usage table"""
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)
    usage_record_id = supabase_manager.create_user_request(
        user_id=-1,
        installation_id=-1,
        unique_issue_id="U/gitautoai/nextjs-website#52",
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
            pr_body="Example body",
            diffs=["Hello", "World"],
        )
        is None
    )

    # Clean Up
    supabase_manager.client.table(table_name="usage").delete().eq(
        column="id", value=usage_record_id
    ).execute()


test_create_update_user_request_works()
