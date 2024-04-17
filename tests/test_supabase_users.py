# run this file locally with: python -m tests.test_supabase_users

import os

import supabase
from services.stripe.customer import get_subscription
from services.supabase import SupabaseManager
import datetime

# from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
# SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZmYWl5d2F0bHhiYWR4bHJtamZxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcwOTY5MDU0NywiZXhwIjoyMDI1MjY2NTQ3fQ.N9EIYESe2xNwddfgznuC_clkBdCZxDWSgbT111aaQFU"
# SUPABASE_URL = "https://vfaiywatlxbadxlrmjfq.supabase.co"

SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""
SUPABASE_URL = os.getenv("SUPABASE_URL") or ""

dummy = """
# Dummy data in each environment
installations: installation_id = 47287862, owner_name="nikita_dummy", owner_type="U", owner_id=1
Users: User Id = 66699290, installation_id = 47287862

installations: installation_id = 48567750, owner_name="lalager_dummy", owner_type="O", owner_id=4
Users: User Id = 66699290, installation_id = 48567750

installations: installation_id = 48332126, owner_name="gitautoai_dummy", owner_type="O", owner_id=3
issues: installation_id = 48332126, unique_issue_id="U/gitautoai/nextjs-website#52"
"""


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


def test_create_and_update_user_request_works() -> None:
    """Test that I can create and complete user request in usage table"""
    user_id = -1
    installation_id = -1
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)

    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data()

    # insert data into the db -> create installation
    supabase_manager.create_installation(
        installation_id=-1,
        owner_type="O",
        owner_name="gitautoai",
        owner_id=-1,
        user_id=-1,
        user_name="test",
    )

    assert (
        supabase_manager.create_user_request(
            user_id=user_id,
            installation_id=installation_id,
            unique_issue_id="U/gitautoai/nextjs-website#52",
        )
        is None
    )
    assert (
        supabase_manager.complete_user_request(
            user_id=user_id,
            installation_id=installation_id,
        )
        is None
    )


# test_create_and_update_user_request_works()


def test_how_many_requests_left() -> None:
    """Test that get_how_many_requests_left_and_cycle returns the correct values"""
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)

    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data()
    # insert data into the db -> create installation + create an issue
    supabase_manager.create_installation(
        installation_id=-1,
        owner_type="O",
        owner_name="gitautoai",
        owner_id=-1,
        user_id=-1,
        user_name="test",
    )
    # Testing 0 requests have been made on free tier
    requests_left, request_count, end_date = (
        supabase_manager.get_how_many_requests_left_and_cycle(
            user_id=-1, installation_id=-1
        )
    )

    assert requests_left == 5
    assert request_count == 5
    assert isinstance(end_date, datetime.datetime)

    supabase_manager.client.table("issues").insert(
        json={
            "installation_id": -1,
            "unique_id": "O/gitautoai/test#1",
            "progress": 100,
        }
    ).execute()
    for _ in range(1, 6):
        supabase_manager.client.table("usage").insert(
            json={
                "user_id": -1,
                "installation_id": -1,
                "is_completed": True,
                "unique_issue_id": "O/gitautoai/test#1",
            }
        ).execute()

    # Test no requests left
    requests_left, request_count, end_date = (
        supabase_manager.get_how_many_requests_left_and_cycle(
            user_id=-1, installation_id=-1
        )
    )

    assert requests_left == 0
    assert request_count == 5
    assert isinstance(end_date, datetime.datetime)

    # Clean Up
    supabase_manager.delete_installation(installation_id=-1)


# test_how_many_requests_left()


def test_is_users_first_issue() -> None:
    """Check if it's a users first issue."""

    user_id = -1
    installation_id = -1
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)

    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data()

    # insert data into the db -> create installation
    supabase_manager.create_installation(
        installation_id=-1,
        owner_type="O",
        owner_name="gitautoai",
        owner_id=-1,
        user_id=-1,
        user_name="test",
    )

    assert supabase_manager.is_users_first_issue(
        user_id=user_id, installation_id=installation_id
    )

    # Set user table user's first_issue to false
    supabase_manager.set_user_first_issue_to_false(
        user_id=user_id, installation_id=installation_id
    )

    assert not supabase_manager.is_users_first_issue(
        user_id=user_id, installation_id=installation_id
    )

    # Clean Up
    wipe_installation_owner_user_data()


test_is_users_first_issue()


def test_parse_subscription_object() -> None:
    """Test parse_subscription_object function"""
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)

    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data()
    # insert data into the db -> create installation
    supabase_manager.create_installation(
        installation_id=-1,
        owner_type="O",
        owner_name="gitautoai",
        owner_id=-1,
        user_id=-1,
        user_name="test",
    )

    standard_product_id = "prod_PqZFpCs1Jq6X4E"

    def assertion_test(customer_id: str, product_id: str):
        subscription = get_subscription(customer_id)
        _, _, product_id_output = supabase_manager.parse_subscription_object(
            subscription, -1, -1
        )
        assert product_id_output == product_id

    ## All active ##
    # [free, paid] -> paid
    assertion_test("cus_PtCxNdGs23X4QR", standard_product_id)

    # [paid, free] -> paid
    assertion_test("cus_PpmpFh1sw0Gfcz", standard_product_id)

    # Clean Up
    wipe_installation_owner_user_data()


# test_parse_subscription_object()

# TODO Test install uninstall
