from services.supabase import SupabaseManager
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

# run locally with python -m tests.test_supabase_users


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


test_how_many_requests_left()


def test_is_users_first_issue() -> None:
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)
    assert not supabase_manager.is_users_first_issue(
        user_id=66699290, installation_id=47287862
    )

    assert supabase_manager.is_users_first_issue(
        user_id=66699290, installation_id=48567750
    )


# test_is_users_first_issue()
