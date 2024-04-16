# run this file locally with: python -m tests.test_supabase_users
import os

from services.supabase import SupabaseManager

SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")


dummy = """
# Dummy data in each environment
installations: installation_id = 47287862, owner_name="nikita_dummy", owner_type="U", owner_id=1
Users: User Id = 66699290, installation_id = 47287862

installations: installation_id = 48567750, owner_name="lalager_dummy", owner_type="O", owner_id=4
Users: User Id = 66699290, installation_id = 48567750

installations: installation_id = 48332126, owner_name="gitautoai_dummy", owner_type="O", owner_id=3
issues: installation_id = 48332126, unique_issue_id="U/gitautoai/nextjs-website#52"
"""


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


# test_how_many_requests_left()
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
