# run this file locally with: python -m tests.test_supabase_users

from services.supabase import SupabaseManager

# from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
# SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZmYWl5d2F0bHhiYWR4bHJtamZxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcwOTY5MDU0NywiZXhwIjoyMDI1MjY2NTQ3fQ.N9EIYESe2xNwddfgznuC_clkBdCZxDWSgbT111aaQFU"
# SUPABASE_URL = "https://vfaiywatlxbadxlrmjfq.supabase.co"

import os

SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")


def test_create_and_update_user_request() -> None:
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)
    assert (
        supabase_manager.create_user_request(
            user_id=66699290,
            installation_id=48332126,
            unique_issue_id="U/gitautoai/nextjs-website#52",
        )
        is None
    )
    assert (
        supabase_manager.complete_user_request(
            user_id=66699290,
            installation_id=48332126,
        )
        is None
    )


# test_create_and_update_user_request()


def test_how_many_requests_left() -> None:
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)
    assert (
        supabase_manager.get_how_many_requests_left(
            user_id=66699290, installation_id=47287862
        )
        == 5
    )

    assert (
        supabase_manager.get_how_many_requests_left(
            user_id=66699290, installation_id=48567750
        )
        == 5
    )


def test_is_users_first_issue() -> None:
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)
    assert not supabase_manager.is_users_first_issue(
        user_id=66699290, installation_id=47287862
    )

    assert supabase_manager.is_users_first_issue(
        user_id=66699290, installation_id=48567750
    )


# test_is_users_first_issue()


# TODO Test install uninstall
