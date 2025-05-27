# run this file locally with: python -m tests.services.supabase.test_supabase_users

# Standard imports
import datetime
import os
from unittest import mock

# Third party imports
import pytest

# Local imports
from config import (
    GITHUB_NOREPLY_EMAIL_DOMAIN,
    PRODUCT_ID_FOR_FREE,
    TEST_INSTALLATION_ID,
    TEST_ISSUE_NUMBER,
    TEST_NEW_INSTALLATION_ID,
    TEST_OWNER_ID,
    TEST_OWNER_NAME,
    TEST_OWNER_TYPE,
    TEST_REPO_ID,
    TEST_USER_ID,
    TEST_USER_NAME,
    TEST_EMAIL,
    TEST_REPO_NAME,
)
from services.stripe.customer import get_subscription
from services.supabase.client import supabase
from services.supabase.gitauto_manager import create_installation, create_user_request
from services.supabase.installations.delete_installation import delete_installation
from services.supabase.usage.update_usage import update_usage
from services.supabase.users_manager import (
    get_how_many_requests_left_and_cycle,
    get_user,
    parse_subscription_object,
    upsert_user,
)
from services.webhook.webhook_handler import handle_webhook_event
from tests.services.supabase.wipe_data import (
    wipe_installation_owner_user_data,
)
from tests.test_payloads.deleted import deleted_payload
from tests.test_payloads.installation import (
    installation_payload,
    new_installation_payload,
)
from utils.time.timer import timer_decorator

pytest_plugins = ("pytest_asyncio",)
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""
SUPABASE_URL = os.getenv("SUPABASE_URL") or ""

@pytest.mark.skip(reason="Requires valid installation in installations table")

@timer_decorator
@pytest.mark.skip(reason="Requires valid installation in installations table")
@pytest.mark.asyncio
async def test_create_and_update_user_request_works() -> None:
    """Test that I can create and complete user request in usage table"""
    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data()

    # insert data into the db -> create installation
    create_installation(
        installation_id=TEST_INSTALLATION_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        owner_id=TEST_OWNER_ID,
        user_id=TEST_USER_ID,
        user_name=TEST_USER_NAME,
        email=TEST_EMAIL,
    )

    usage_record_id = await create_user_request(
        user_id=TEST_USER_ID,
        user_name=TEST_USER_NAME,
        installation_id=TEST_INSTALLATION_ID,
        owner_id=TEST_OWNER_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        repo_id=TEST_REPO_ID,
        repo_name=TEST_REPO_NAME,
        issue_number=TEST_ISSUE_NUMBER,
        source="github",
        email=TEST_EMAIL,
    )
    assert isinstance(usage_record_id, int)
    assert (
        update_usage(
            usage_record_id=usage_record_id,
            token_input=1000,
            token_output=100,
            total_seconds=100,
        )
        is None
    )

    # Clean up
    wipe_installation_owner_user_data()


@timer_decorator
def test_how_many_requests_left() -> None:
    """Test that get_how_many_requests_left_and_cycle returns the correct values"""
    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data()
    # insert data into the db -> create installation
    create_installation(
        installation_id=TEST_INSTALLATION_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        owner_id=TEST_OWNER_ID,
        user_id=TEST_USER_ID,
        user_name=TEST_USER_NAME,
        email=TEST_EMAIL,
    )
    # Testing 0 requests have been made on free tier
    requests_left, request_count, end_date, _is_retried = (
        get_how_many_requests_left_and_cycle(
            installation_id=TEST_INSTALLATION_ID,
            owner_id=TEST_OWNER_ID,
            owner_name=TEST_OWNER_NAME,
            owner_type=TEST_OWNER_TYPE,
            repo_name=TEST_REPO_NAME,
            issue_number=TEST_ISSUE_NUMBER,
        )
    )

    # Match request_count in Metadata in https://dashboard.stripe.com/test/products/prod_PokLGIxiVUwCi6
    assert requests_left == 5
    assert request_count == 5
    assert isinstance(end_date, datetime.datetime)

    # Generate 5 issues and 5 usage records
    for i in range(1, 6):
        supabase.table("issues").insert(
            json={
                "installation_id": TEST_INSTALLATION_ID,
                "owner_id": TEST_OWNER_ID,
                "owner_type": TEST_OWNER_TYPE,
                "owner_name": TEST_OWNER_NAME,
                "repo_id": TEST_REPO_ID,
                "repo_name": TEST_REPO_NAME,
                "issue_number": i,
            }
        ).execute()
        supabase.table("usage").insert(
            json={
                "user_id": TEST_USER_ID,
                "installation_id": TEST_INSTALLATION_ID,
                "is_completed": True,
                "owner_id": TEST_OWNER_ID,
                "owner_type": TEST_OWNER_TYPE,
                "owner_name": TEST_OWNER_NAME,
                "repo_id": TEST_REPO_ID,
                "repo_name": TEST_REPO_NAME,
                "issue_number": i,
            }
        ).execute()

    # Test no requests left
    requests_left, request_count, end_date, _is_retried = (
        get_how_many_requests_left_and_cycle(
            installation_id=TEST_INSTALLATION_ID,
            owner_id=TEST_OWNER_ID,
            owner_name=TEST_OWNER_NAME,
            owner_type=TEST_OWNER_TYPE,
            repo_name=TEST_REPO_NAME,
            issue_number=TEST_ISSUE_NUMBER,
        )
    )

    assert requests_left == 0
    assert request_count == 5
    assert isinstance(end_date, datetime.datetime)

    # Clean Up
    delete_installation(
        installation_id=TEST_INSTALLATION_ID,
        user_id=TEST_USER_ID,
        user_name=TEST_USER_NAME,
    )


@timer_decorator
def test_parse_subscription_object() -> None:
    """Test parse_subscription_object function"""
    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data()
    # insert data into the db -> create installation
    create_installation(
        installation_id=TEST_INSTALLATION_ID,
        owner_id=TEST_OWNER_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        user_id=TEST_USER_ID,
        user_name=TEST_USER_NAME,
        email=TEST_EMAIL,
    )

    def assertion_test(customer_id: str, product_id: str):
        subscription = get_subscription(customer_id=customer_id)
        _, _, product_id_output, _, _ = parse_subscription_object(
            subscription=subscription,
            installation_id=TEST_INSTALLATION_ID,
            customer_id=customer_id,
            owner_id=TEST_OWNER_ID,
            owner_name=TEST_OWNER_NAME,
        )
        assert product_id_output == product_id

    # All active ##
    # [free, paid] -> paid
    # assertion_test(customer_id="cus_PtCxNdGs23X4QR", product_id=PRODUCT_ID_FOR_STANDARD)
    assertion_test(customer_id="cus_PtCxNdGs23X4QR", product_id=PRODUCT_ID_FOR_FREE)

    # [paid, free] -> paid
    assertion_test(customer_id="cus_PpmpFh1sw0Gfcz", product_id=PRODUCT_ID_FOR_FREE)

    # Clean Up
    wipe_installation_owner_user_data()


@timer_decorator
@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires valid installation in installations table")
async def test_install_uninstall_install() -> None:
    """Testing install uninstall methods"""
    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data()
    wipe_installation_owner_user_data(TEST_NEW_INSTALLATION_ID)

    # Create a more comprehensive mock setup
    # We'll mock the process_repositories function entirely to avoid the cloning process
    with mock.patch(
        "services.git.clone_repo.clone_repo", return_value=None, autospec=True
    ), mock.patch(
        "services.git.clone_repo.subprocess.run", return_value=None
    ), mock.patch(
        "services.github.token.get_installation_token.get_installation_access_token",
        return_value="fake-token",
    ), mock.patch(
        "services.github.github_manager.get_user_public_email",
        return_value="test@example.com",
    ):

        await handle_webhook_event(
            event_name="installation", payload=installation_payload
        )

        # Check Owners Record (owner_id, stripe_customer_id)
        owners_data, _ = (
            supabase.table("owners")
            .select("*")
            .eq(column="owner_id", value=TEST_OWNER_ID)
            .execute()
        )
        assert owners_data[1][0]["owner_id"] == TEST_OWNER_ID
        assert isinstance(owners_data[1][0]["stripe_customer_id"], str)

        # Check Installation Record
        installation_data, _ = (
            supabase.table("installations")
            .select("*")
            .eq(column="installation_id", value=TEST_INSTALLATION_ID)
            .execute()
        )

        assert installation_data[1][0]["installation_id"] == TEST_INSTALLATION_ID
        assert installation_data[1][0]["owner_name"] == TEST_OWNER_NAME
        assert installation_data[1][0]["owner_id"] == TEST_OWNER_ID
        assert installation_data[1][0]["owner_type"] == TEST_OWNER_TYPE
        assert installation_data[1][0]["uninstalled_at"] is None

        # Check Users Record
        users_data, _ = (
            supabase.table("users")
            .select("*")
            .eq(column="user_id", value=TEST_USER_ID)
            .execute()
        )

        assert users_data[1][0]["user_id"] == TEST_USER_ID
        assert users_data[1][0]["user_name"] == TEST_USER_NAME

        await handle_webhook_event(event_name="installation", payload=deleted_payload)
        # We're going to check the same things, except that installation should have uninstalled_at

        # Check Owners Record (owner_id, stripe_customer_id)
        owners_data, _ = (
            supabase.table("owners")
            .select("*")
            .eq(column="owner_id", value=TEST_OWNER_ID)
            .execute()
        )
        assert owners_data[1][0]["owner_id"] == TEST_OWNER_ID
        assert isinstance(owners_data[1][0]["stripe_customer_id"], str)

        # Check Installation Record
        installation_data, _ = (
            supabase.table("installations")
            .select("*")
            .eq(column="installation_id", value=TEST_INSTALLATION_ID)
            .execute()
        )

        assert installation_data[1][0]["installation_id"] == TEST_INSTALLATION_ID
        assert installation_data[1][0]["owner_name"] == TEST_OWNER_NAME
        assert installation_data[1][0]["owner_id"] == TEST_OWNER_ID
        assert installation_data[1][0]["owner_type"] == TEST_OWNER_TYPE
        assert installation_data[1][0]["uninstalled_at"] is not None

        # Check Users Record
        users_data, _ = (
            supabase.table("users")
            .select("*")
            .eq(column="user_id", value=TEST_USER_ID)
            .execute()
        )

        assert users_data[1][0]["user_id"] == TEST_USER_ID
        assert users_data[1][0]["user_name"] == TEST_USER_NAME

        await handle_webhook_event(
            event_name="installation", payload=new_installation_payload
        )

        # Check Owners Record (owner_id, stripe_customer_id)
        owners_data, _ = (
            supabase.table("owners")
            .select("*")
            .eq(column="owner_id", value=TEST_OWNER_ID)
            .execute()
        )
        assert owners_data[1][0]["owner_id"] == TEST_OWNER_ID
        assert isinstance(owners_data[1][0]["stripe_customer_id"], str)

        # Check Installation Record
        installation_data, _ = (
            supabase.table("installations")
            .select("*")
            .eq(column="installation_id", value=TEST_NEW_INSTALLATION_ID)
            .execute()
        )

        assert installation_data[1][0]["installation_id"] == TEST_NEW_INSTALLATION_ID
        assert installation_data[1][0]["owner_name"] == TEST_OWNER_NAME
        assert installation_data[1][0]["owner_id"] == TEST_OWNER_ID
        assert installation_data[1][0]["owner_type"] == TEST_OWNER_TYPE
        assert installation_data[1][0]["uninstalled_at"] is None

        # Check Users Record
        users_data, _ = (
            supabase.table("users")
            .select("*")
            .eq(column="user_id", value=TEST_USER_ID)
            .execute()
        )

        assert users_data[1][0]["user_id"] == TEST_USER_ID
        assert users_data[1][0]["user_name"] == TEST_USER_NAME

    # Clean Up
    wipe_installation_owner_user_data()
    wipe_installation_owner_user_data(TEST_NEW_INSTALLATION_ID)


@timer_decorator
def test_handle_user_email_update() -> None:
    """Test updating a user's email in the users table"""
    # Clean up at the beginning just in case a prior test failed to clean
    wipe_installation_owner_user_data()

    # Insert a user into the database
    create_installation(
        installation_id=TEST_INSTALLATION_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
        owner_id=TEST_OWNER_ID,
        user_id=TEST_USER_ID,
        user_name=TEST_USER_NAME,
        email=TEST_EMAIL,
    )
    # Verify github no-reply email is not updated
    json_data = {"user_id": TEST_USER_ID, "user_name": TEST_USER_NAME}
    json_data["email"] = f"no_reply_email@{GITHUB_NOREPLY_EMAIL_DOMAIN}"
    upsert_user(**json_data)
    user_data = get_user(user_id=TEST_USER_ID)
    assert user_data["email"] == TEST_EMAIL

    # Verify None email is not updated
    json_data["email"] = None
    upsert_user(**json_data)
    user_data = get_user(user_id=TEST_USER_ID)
    assert user_data["email"] == TEST_EMAIL

    # Verify valid email is updated
    new_email = "new_email@example.com"
    json_data["email"] = "new_email@example.com"
    upsert_user(**json_data)
    user_data = get_user(user_id=TEST_USER_ID)
    assert user_data["email"] == new_email

    # Clean Up
    wipe_installation_owner_user_data()
