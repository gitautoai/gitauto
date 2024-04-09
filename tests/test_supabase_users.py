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


def test_create_and_update_user_request_works() -> None:
    """Test that I can create and complete user request in usage table"""
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)
    assert SUPABASE_URL == "https://atarljruiontapnenrsj.supabase.co"
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


# test_create_and_update_user_request_works()


def test_how_many_requests_left() -> None:
    """Test that get_how_many_requests_left_and_cycle returns the correct values"""
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)

    requests_left, requests_made_in_this_cycle, end_date = (
        supabase_manager.get_how_many_requests_left_and_cycle(
            user_id=66699290, installation_id=47287862
        )
    )

    assert isinstance(requests_left, int)
    assert isinstance(requests_made_in_this_cycle, int)
    assert isinstance(end_date, datetime.datetime)

    requests_left, requests_made_in_this_cycle, end_date = (
        supabase_manager.get_how_many_requests_left_and_cycle(
            user_id=66699290, installation_id=48567750
        )
    )

    assert isinstance(requests_left, int)
    assert isinstance(requests_made_in_this_cycle, int)
    assert isinstance(end_date, datetime.datetime)


# test_how_many_requests_left()


def test_is_users_first_issue() -> None:
    """Check if it's a users first issue."""
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)
    assert not supabase_manager.is_users_first_issue(
        user_id=66699290, installation_id=47287862
    )

    assert supabase_manager.is_users_first_issue(
        user_id=66699290, installation_id=48567750
    )


# test_is_users_first_issue()


def test_parse_subscription_object() -> None:
    """Test parse_subscription_object function"""
    supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)

    # insert data into the db. is_selected will be true since we're not testing is_user_eligible_for_seat_handler here
    supabase_manager.client.table("owners").upsert(json={"owner_id": -1}).execute()
    supabase_manager.client.table("installations").upsert(
        json={
            "owner_id": -1,
            "installation_id": -1,
            "owner_name": "test_parse_subscription",
        }
    ).execute()
    try:
        supabase_manager.client.table("users").upsert(
            json={"user_id": -1, "installation_id": -1, "is_selected": True}
        ).execute()

    except Exception as e:
        pass

    STANDARD_PRICE_ID = "prod_PqZFpCs1Jq6X4E"
    FREE_PRICE_ID = "prod_PokLGIxiVUwCi6"
    EXAMPLE_PAID_PLAN = "prod_PtFfTPPNV18uEo"

    def assertion_test(customer_id: str, product_id: str):
        subscription = get_subscription(customer_id)
        _, _, product_id_output = supabase_manager.parse_subscription_object(
            subscription, -1, -1
        )
        assert product_id_output == product_id

    ## All active ##
    # [free, paid] -> paid
    assertion_test("cus_PtCxNdGs23X4QR", STANDARD_PRICE_ID)

    # [paid, free] -> paid
    assertion_test("cus_PpmpFh1sw0Gfcz", STANDARD_PRICE_ID)

    # TODO, not possible for users to do this right now on Website
    # [paid1, paid2] -> paid1

    ## First not active ##

    # [free - not active, paid] -> paid

    # [paid - not active, free] -> free

    # TODO, not possible for users to do this right now on Website
    # [paid1 - not active, paid2] -> paid2

    # Second not active ##

    # [free - not active, paid] -> paid

    # [paid - not active, free] -> free

    # TODO, not possible for users to do this right now on Website
    # [paid1 - not active, paid2] -> paid2


test_parse_subscription_object()

# TODO Test install uninstall
