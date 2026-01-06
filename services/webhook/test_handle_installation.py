# pylint: disable=too-many-lines,too-many-public-methods
"""Unit tests for handle_installation.py"""

# Standard imports
from unittest.mock import patch

# Third-party imports
import pytest

# Local imports
from services.webhook.handle_installation import handle_installation_created


@pytest.fixture
def mock_installation_payload():
    """Fixture providing a mock installation created payload."""
    return {
        "installation": {
            "id": 12345,
            "account": {
                "id": 67890,
                "login": "test-owner",
                "type": "Organization",
            },
        },
        "sender": {
            "id": 11111,
            "login": "test-sender",
        },
        "repositories": [
            {
                "id": 111,
                "name": "test-repo-1",
                "full_name": "test-owner/test-repo-1",
                "private": False,
            },
            {
                "id": 222,
                "name": "test-repo-2",
                "full_name": "test-owner/test-repo-2",
                "private": True,
            },
        ],
    }


@pytest.fixture
def mock_get_installation_access_token():
    """Mock get_installation_access_token function."""
    with patch(
        "services.webhook.handle_installation.get_installation_access_token"
    ) as mock:
        yield mock


@pytest.fixture
def mock_get_user_public_email():
    """Mock get_user_public_email function."""
    with patch("services.webhook.handle_installation.get_user_public_email") as mock:
        yield mock


@pytest.fixture
def mock_check_owner_exists():
    """Mock check_owner_exists function."""
    with patch("services.webhook.handle_installation.check_owner_exists") as mock:
        yield mock


@pytest.fixture
def mock_create_stripe_customer():
    """Mock create_stripe_customer function."""
    with patch("services.webhook.handle_installation.create_stripe_customer") as mock:
        yield mock


@pytest.fixture
def mock_insert_owner():
    """Mock insert_owner function."""
    with patch("services.webhook.handle_installation.insert_owner") as mock:
        yield mock


@pytest.fixture
def mock_check_grant_exists():
    """Mock check_grant_exists function."""
    with patch("services.webhook.handle_installation.check_grant_exists") as mock:
        yield mock


@pytest.fixture
def mock_insert_credit():
    """Mock insert_credit function."""
    with patch("services.webhook.handle_installation.insert_credit") as mock:
        yield mock


@pytest.fixture
def mock_insert_installation():
    """Mock insert_installation function."""
    with patch("services.webhook.handle_installation.insert_installation") as mock:
        yield mock


@pytest.fixture
def mock_upsert_user():
    """Mock upsert_user function."""
    with patch("services.webhook.handle_installation.upsert_user") as mock:
        yield mock


@pytest.fixture
def mock_process_repositories():
    """Mock process_repositories function."""
    with patch("services.webhook.handle_installation.process_repositories") as mock:
        yield mock


@pytest.fixture
def all_mocks(
    mock_get_installation_access_token,
    mock_get_user_public_email,
    mock_check_owner_exists,
    mock_create_stripe_customer,
    mock_insert_owner,
    mock_check_grant_exists,
    mock_insert_credit,
    mock_insert_installation,
    mock_upsert_user,
    mock_process_repositories,
):
    """Fixture providing all mocked dependencies."""
    return {
        "get_installation_access_token": mock_get_installation_access_token,
        "get_user_public_email": mock_get_user_public_email,
        "check_owner_exists": mock_check_owner_exists,
        "create_stripe_customer": mock_create_stripe_customer,
        "insert_owner": mock_insert_owner,
        "check_grant_exists": mock_check_grant_exists,
        "insert_credit": mock_insert_credit,
        "insert_installation": mock_insert_installation,
        "upsert_user": mock_upsert_user,
        "process_repositories": mock_process_repositories,
    }


class TestHandleInstallationCreated:
    """Test cases for handle_installation_created function."""

    def test_handle_installation_created_new_owner_with_grant(
        self, mock_installation_payload, all_mocks
    ):
        """Test successful handling of installation created for new owner with grant."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = False  # New owner
        all_mocks["create_stripe_customer"].return_value = "cus_test123"
        all_mocks["check_grant_exists"].return_value = False  # No existing grant

        # Execute
        handle_installation_created(mock_installation_payload)

        # Verify token and email retrieval
        all_mocks["get_installation_access_token"].assert_called_once_with(
            installation_id=12345
        )
        all_mocks["get_user_public_email"].assert_called_once_with(
            username="test-sender", token="ghs_test_token"
        )

        # Verify owner creation flow
        all_mocks["check_owner_exists"].assert_called_once_with(owner_id=67890)
        all_mocks["create_stripe_customer"].assert_called_once_with(
            owner_name="test-owner",
            owner_id=67890,
            installation_id=12345,
            user_id=11111,
            user_name="test-sender",
        )
        all_mocks["insert_owner"].assert_called_once_with(
            owner_id=67890,
            owner_type="Organization",
            owner_name="test-owner",
            stripe_customer_id="cus_test123",
        )

        # Verify grant creation flow
        all_mocks["check_grant_exists"].assert_called_once_with(owner_id=67890)
        all_mocks["insert_credit"].assert_called_once_with(
            owner_id=67890, transaction_type="grant"
        )

        # Verify installation creation
        all_mocks["insert_installation"].assert_called_once_with(
            installation_id=12345,
            owner_id=67890,
            owner_type="Organization",
            owner_name="test-owner",
        )

        # Verify user upsert
        all_mocks["upsert_user"].assert_called_once_with(
            user_id=11111, user_name="test-sender", email="test@example.com"
        )

        # Verify repository processing
        all_mocks["process_repositories"].assert_called_once_with(
            owner_id=67890,
            owner_name="test-owner",
            repositories=mock_installation_payload["repositories"],
            token="ghs_test_token",
            user_id=11111,
            user_name="test-sender",
        )

    def test_handle_installation_created_existing_owner_with_existing_grant(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling of installation created for existing owner with existing grant."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = True  # Existing owner
        all_mocks["check_grant_exists"].return_value = True  # Existing grant

        # Execute
        handle_installation_created(mock_installation_payload)

        # Verify token and email retrieval
        all_mocks["get_installation_access_token"].assert_called_once_with(
            installation_id=12345
        )
        all_mocks["get_user_public_email"].assert_called_once_with(
            username="test-sender", token="ghs_test_token"
        )

        # Verify owner creation flow is skipped
        all_mocks["check_owner_exists"].assert_called_once_with(owner_id=67890)
        all_mocks["create_stripe_customer"].assert_not_called()
        all_mocks["insert_owner"].assert_not_called()

        # Verify grant creation flow is skipped
        all_mocks["check_grant_exists"].assert_called_once_with(owner_id=67890)
        all_mocks["insert_credit"].assert_not_called()

        # Verify installation creation still happens
        all_mocks["insert_installation"].assert_called_once_with(
            installation_id=12345,
            owner_id=67890,
            owner_type="Organization",
            owner_name="test-owner",
        )

        # Verify user upsert still happens
        all_mocks["upsert_user"].assert_called_once_with(
            user_id=11111, user_name="test-sender", email="test@example.com"
        )

        # Verify repository processing still happens
        all_mocks["process_repositories"].assert_called_once_with(
            owner_id=67890,
            owner_name="test-owner",
            repositories=mock_installation_payload["repositories"],
            token="ghs_test_token",
            user_id=11111,
            user_name="test-sender",
        )

    def test_handle_installation_created_new_owner_existing_grant(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling of installation created for new owner with existing grant."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = False  # New owner
        all_mocks["create_stripe_customer"].return_value = "cus_test123"
        all_mocks["check_grant_exists"].return_value = True  # Existing grant

        # Execute
        handle_installation_created(mock_installation_payload)

        # Verify owner creation flow
        all_mocks["check_owner_exists"].assert_called_once_with(owner_id=67890)
        all_mocks["create_stripe_customer"].assert_called_once_with(
            owner_name="test-owner",
            owner_id=67890,
            installation_id=12345,
            user_id=11111,
            user_name="test-sender",
        )
        all_mocks["insert_owner"].assert_called_once_with(
            owner_id=67890,
            owner_type="Organization",
            owner_name="test-owner",
            stripe_customer_id="cus_test123",
        )

        # Verify grant creation flow is skipped
        all_mocks["check_grant_exists"].assert_called_once_with(owner_id=67890)
        all_mocks["insert_credit"].assert_not_called()

    def test_handle_installation_created_existing_owner_new_grant(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling of installation created for existing owner with new grant."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = True  # Existing owner
        all_mocks["check_grant_exists"].return_value = False  # No existing grant

        # Execute
        handle_installation_created(mock_installation_payload)

        # Verify owner creation flow is skipped
        all_mocks["check_owner_exists"].assert_called_once_with(owner_id=67890)
        all_mocks["create_stripe_customer"].assert_not_called()
        all_mocks["insert_owner"].assert_not_called()

        # Verify grant creation flow
        all_mocks["check_grant_exists"].assert_called_once_with(owner_id=67890)
        all_mocks["insert_credit"].assert_called_once_with(
            owner_id=67890, transaction_type="grant"
        )

    def test_handle_installation_created_with_user_type_owner(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling of installation created for User type owner."""
        # Setup
        mock_installation_payload["installation"]["account"]["type"] = "User"
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = False
        all_mocks["create_stripe_customer"].return_value = "cus_test123"
        all_mocks["check_grant_exists"].return_value = False

        # Execute
        handle_installation_created(mock_installation_payload)

        # Verify owner creation with User type
        all_mocks["insert_owner"].assert_called_once_with(
            owner_id=67890,
            owner_type="User",
            owner_name="test-owner",
            stripe_customer_id="cus_test123",
        )

        # Verify installation creation with User type
        all_mocks["insert_installation"].assert_called_once_with(
            installation_id=12345,
            owner_id=67890,
            owner_type="User",
            owner_name="test-owner",
        )

    def test_handle_installation_created_with_none_email(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling when user email is None."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = None
        all_mocks["check_owner_exists"].return_value = False
        all_mocks["create_stripe_customer"].return_value = "cus_test123"
        all_mocks["check_grant_exists"].return_value = False

        # Execute
        handle_installation_created(mock_installation_payload)

        # Verify user upsert with None email
        all_mocks["upsert_user"].assert_called_once_with(
            user_id=11111, user_name="test-sender", email=None
        )

    def test_handle_installation_created_with_empty_email(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling when user email is empty string."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = ""
        all_mocks["check_owner_exists"].return_value = False
        all_mocks["create_stripe_customer"].return_value = "cus_test123"
        all_mocks["check_grant_exists"].return_value = False

        # Execute
        handle_installation_created(mock_installation_payload)

        # Verify user upsert with empty email
        all_mocks["upsert_user"].assert_called_once_with(
            user_id=11111, user_name="test-sender", email=""
        )

    def test_handle_installation_created_with_token_error(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling when get_installation_access_token raises - returns early."""
        # Setup - get_installation_access_token now raises instead of returning None
        all_mocks["get_installation_access_token"].side_effect = ValueError(
            "Installation 12345 suspended or deleted"
        )

        # Execute - handle_exceptions decorator catches and returns None
        handle_installation_created(mock_installation_payload)

        # Verify - should return early when token retrieval fails
        all_mocks["get_installation_access_token"].assert_called_once()
        all_mocks["get_user_public_email"].assert_not_called()
        all_mocks["process_repositories"].assert_not_called()

    def test_handle_installation_created_with_empty_repositories(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling when repositories list is empty."""
        # Setup
        mock_installation_payload["repositories"] = []
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = False
        all_mocks["create_stripe_customer"].return_value = "cus_test123"
        all_mocks["check_grant_exists"].return_value = False

        # Execute
        handle_installation_created(mock_installation_payload)

        # Verify repository processing with empty list
        all_mocks["process_repositories"].assert_called_once_with(
            owner_id=67890,
            owner_name="test-owner",
            repositories=[],
            token="ghs_test_token",
            user_id=11111,
            user_name="test-sender",
        )

    def test_handle_installation_created_with_single_repository(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling with single repository."""
        # Setup
        single_repo = [{"id": 333, "name": "single-repo"}]
        mock_installation_payload["repositories"] = single_repo
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = False
        all_mocks["create_stripe_customer"].return_value = "cus_test123"
        all_mocks["check_grant_exists"].return_value = False

        # Execute
        handle_installation_created(mock_installation_payload)

        # Verify repository processing with single repository
        all_mocks["process_repositories"].assert_called_once_with(
            owner_id=67890,
            owner_name="test-owner",
            repositories=single_repo,
            token="ghs_test_token",
            user_id=11111,
            user_name="test-sender",
        )

    def test_handle_installation_created_with_exception_in_get_token(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling when get_installation_access_token raises exception."""
        # Setup
        all_mocks["get_installation_access_token"].side_effect = Exception(
            "Token error"
        )

        # Execute
        result = handle_installation_created(mock_installation_payload)

        # Verify function returns None due to handle_exceptions decorator
        assert result is None
        all_mocks["get_installation_access_token"].assert_called_once_with(
            installation_id=12345
        )
        all_mocks["get_user_public_email"].assert_not_called()

    def test_handle_installation_created_with_exception_in_get_email(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling when get_user_public_email raises exception."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].side_effect = Exception("Email error")

        # Execute
        result = handle_installation_created(mock_installation_payload)

        # Verify function returns None due to handle_exceptions decorator
        assert result is None
        all_mocks["get_installation_access_token"].assert_called_once_with(
            installation_id=12345
        )
        all_mocks["get_user_public_email"].assert_called_once_with(
            username="test-sender", token="ghs_test_token"
        )
        all_mocks["check_owner_exists"].assert_not_called()

    def test_handle_installation_created_with_exception_in_check_owner_exists(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling when check_owner_exists raises exception."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].side_effect = Exception("Database error")

        # Execute
        result = handle_installation_created(mock_installation_payload)

        # Verify function returns None due to handle_exceptions decorator
        assert result is None
        all_mocks["check_owner_exists"].assert_called_once_with(owner_id=67890)
        all_mocks["create_stripe_customer"].assert_not_called()

    def test_handle_installation_created_with_exception_in_create_stripe_customer(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling when create_stripe_customer raises exception."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = False
        all_mocks["create_stripe_customer"].side_effect = Exception("Stripe error")

        # Execute
        result = handle_installation_created(mock_installation_payload)

        # Verify function returns None due to handle_exceptions decorator
        assert result is None
        all_mocks["create_stripe_customer"].assert_called_once()
        all_mocks["insert_owner"].assert_not_called()

    def test_handle_installation_created_with_exception_in_insert_owner(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling when insert_owner raises exception."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = False
        all_mocks["create_stripe_customer"].return_value = "cus_test123"
        all_mocks["insert_owner"].side_effect = Exception("Insert error")

        # Execute
        result = handle_installation_created(mock_installation_payload)

        # Verify function returns None due to handle_exceptions decorator
        assert result is None
        all_mocks["insert_owner"].assert_called_once()
        all_mocks["check_grant_exists"].assert_not_called()

    def test_handle_installation_created_with_exception_in_check_grant_exists(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling when check_grant_exists raises exception."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = True  # Skip owner creation
        all_mocks["check_grant_exists"].side_effect = Exception("Grant check error")

        # Execute
        result = handle_installation_created(mock_installation_payload)

        # Verify function returns None due to handle_exceptions decorator
        assert result is None
        all_mocks["check_grant_exists"].assert_called_once_with(owner_id=67890)
        all_mocks["insert_credit"].assert_not_called()

    def test_handle_installation_created_with_exception_in_insert_credit(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling when insert_credit raises exception."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = True  # Skip owner creation
        all_mocks["check_grant_exists"].return_value = False
        all_mocks["insert_credit"].side_effect = Exception("Credit insert error")

        # Execute
        result = handle_installation_created(mock_installation_payload)

        # Verify function returns None due to handle_exceptions decorator
        assert result is None
        all_mocks["insert_credit"].assert_called_once()
        all_mocks["insert_installation"].assert_not_called()

    def test_handle_installation_created_with_exception_in_insert_installation(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling when insert_installation raises exception."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = True  # Skip owner creation
        all_mocks["check_grant_exists"].return_value = True  # Skip grant creation
        all_mocks["insert_installation"].side_effect = Exception(
            "Installation insert error"
        )

        # Execute
        result = handle_installation_created(mock_installation_payload)

        # Verify function returns None due to handle_exceptions decorator
        assert result is None
        all_mocks["insert_installation"].assert_called_once()
        all_mocks["upsert_user"].assert_not_called()

    def test_handle_installation_created_with_exception_in_upsert_user(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling when upsert_user raises exception."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = True  # Skip owner creation
        all_mocks["check_grant_exists"].return_value = True  # Skip grant creation
        all_mocks["upsert_user"].side_effect = Exception("User upsert error")

        # Execute
        result = handle_installation_created(mock_installation_payload)

        # Verify function returns None due to handle_exceptions decorator
        assert result is None
        all_mocks["upsert_user"].assert_called_once()
        all_mocks["process_repositories"].assert_not_called()

    def test_handle_installation_created_with_exception_in_process_repositories(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling when process_repositories raises exception."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = True  # Skip owner creation
        all_mocks["check_grant_exists"].return_value = True  # Skip grant creation
        all_mocks["process_repositories"].side_effect = Exception(
            "Repository processing error"
        )

        # Execute
        result = handle_installation_created(mock_installation_payload)

        # Verify function returns None due to handle_exceptions decorator
        assert result is None
        all_mocks["process_repositories"].assert_called_once()

    def test_handle_installation_created_with_missing_installation_id(self, all_mocks):
        """Test handling when payload is missing installation ID."""
        # Setup
        incomplete_payload = {
            "installation": {
                "account": {
                    "id": 67890,
                    "login": "test-owner",
                    "type": "Organization",
                },
            },
            "sender": {"id": 11111, "login": "test-sender"},
            "repositories": [],
        }

        # Execute
        result = handle_installation_created(incomplete_payload)

        # Verify function returns None due to handle_exceptions decorator
        assert result is None
        all_mocks["get_installation_access_token"].assert_not_called()

    def test_handle_installation_created_with_missing_account_info(self, all_mocks):
        """Test handling when payload is missing account information."""
        # Setup
        incomplete_payload = {
            "installation": {"id": 12345},
            "sender": {"id": 11111, "login": "test-sender"},
            "repositories": [],
        }

        # Execute
        result = handle_installation_created(incomplete_payload)

        # Verify function returns None due to handle_exceptions decorator
        assert result is None

    def test_handle_installation_created_with_missing_sender_info(self, all_mocks):
        """Test handling when payload is missing sender information."""
        # Setup
        incomplete_payload = {
            "installation": {
                "id": 12345,
                "account": {
                    "id": 67890,
                    "login": "test-owner",
                    "type": "Organization",
                },
            },
            "repositories": [],
        }

        # Execute
        result = handle_installation_created(incomplete_payload)

        # Verify function returns None due to handle_exceptions decorator
        assert result is None

    def test_handle_installation_created_with_missing_repositories(self, all_mocks):
        """Test handling when payload is missing repositories."""
        # Setup
        incomplete_payload = {
            "installation": {
                "id": 12345,
                "account": {
                    "id": 67890,
                    "login": "test-owner",
                    "type": "Organization",
                },
            },
            "sender": {"id": 11111, "login": "test-sender"},
        }

        # Execute
        result = handle_installation_created(incomplete_payload)

        # Verify function returns None due to handle_exceptions decorator
        assert result is None

    def test_handle_installation_created_with_none_payload(self, all_mocks):
        """Test handling when payload is None."""
        # Execute
        result = handle_installation_created(None)

        # Verify function returns None due to handle_exceptions decorator
        assert result is None
        all_mocks["get_installation_access_token"].assert_not_called()

    def test_handle_installation_created_with_empty_payload(self, all_mocks):
        """Test handling when payload is empty dictionary."""
        # Execute
        result = handle_installation_created({})

        # Verify function returns None due to handle_exceptions decorator
        assert result is None
        all_mocks["get_installation_access_token"].assert_not_called()

    def test_handle_installation_created_with_string_ids(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling when IDs are provided as strings."""
        # Setup
        mock_installation_payload["installation"]["id"] = "12345"
        mock_installation_payload["installation"]["account"]["id"] = "67890"
        mock_installation_payload["sender"]["id"] = "11111"
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = False
        all_mocks["create_stripe_customer"].return_value = "cus_test123"
        all_mocks["check_grant_exists"].return_value = False

        # Execute
        handle_installation_created(mock_installation_payload)

        # Verify calls with string IDs
        all_mocks["get_installation_access_token"].assert_called_once_with(
            installation_id="12345"
        )
        all_mocks["check_owner_exists"].assert_called_once_with(owner_id="67890")
        all_mocks["create_stripe_customer"].assert_called_once_with(
            owner_name="test-owner",
            owner_id="67890",
            installation_id="12345",
            user_id="11111",
            user_name="test-sender",
        )

    def test_handle_installation_created_with_unicode_names(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling with unicode characters in names."""
        # Setup
        mock_installation_payload["installation"]["account"]["login"] = "tëst-öwnér"
        mock_installation_payload["sender"]["login"] = "tëst-sëndér"
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "tëst@ëxämplë.com"
        all_mocks["check_owner_exists"].return_value = False
        all_mocks["create_stripe_customer"].return_value = "cus_test123"
        all_mocks["check_grant_exists"].return_value = False

        # Execute
        handle_installation_created(mock_installation_payload)

        # Verify calls with unicode names
        all_mocks["get_user_public_email"].assert_called_once_with(
            username="tëst-sëndér", token="ghs_test_token"
        )
        all_mocks["create_stripe_customer"].assert_called_once_with(
            owner_name="tëst-öwnér",
            owner_id=67890,
            installation_id=12345,
            user_id=11111,
            user_name="tëst-sëndér",
        )
        all_mocks["upsert_user"].assert_called_once_with(
            user_id=11111, user_name="tëst-sëndér", email="tëst@ëxämplë.com"
        )

    def test_handle_installation_created_with_zero_ids(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling with zero IDs."""
        # Setup
        mock_installation_payload["installation"]["id"] = 0
        mock_installation_payload["installation"]["account"]["id"] = 0
        mock_installation_payload["sender"]["id"] = 0
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = False
        all_mocks["create_stripe_customer"].return_value = "cus_test123"
        all_mocks["check_grant_exists"].return_value = False

        # Execute
        handle_installation_created(mock_installation_payload)

        # Verify calls with zero IDs
        all_mocks["get_installation_access_token"].assert_called_once_with(
            installation_id=0
        )
        all_mocks["check_owner_exists"].assert_called_once_with(owner_id=0)
        all_mocks["create_stripe_customer"].assert_called_once_with(
            owner_name="test-owner",
            owner_id=0,
            installation_id=0,
            user_id=0,
            user_name="test-sender",
        )

    def test_handle_installation_created_with_negative_ids(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling with negative IDs."""
        # Setup
        mock_installation_payload["installation"]["id"] = -1
        mock_installation_payload["installation"]["account"]["id"] = -2
        mock_installation_payload["sender"]["id"] = -3
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = False
        all_mocks["create_stripe_customer"].return_value = "cus_test123"
        all_mocks["check_grant_exists"].return_value = False

        # Execute
        handle_installation_created(mock_installation_payload)

        # Verify calls with negative IDs
        all_mocks["get_installation_access_token"].assert_called_once_with(
            installation_id=-1
        )
        all_mocks["check_owner_exists"].assert_called_once_with(owner_id=-2)
        all_mocks["create_stripe_customer"].assert_called_once_with(
            owner_name="test-owner",
            owner_id=-2,
            installation_id=-1,
            user_id=-3,
            user_name="test-sender",
        )

    def test_handle_installation_created_with_large_repository_list(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling with a large number of repositories."""
        # Setup
        large_repo_list = [{"id": i, "name": f"repo-{i}"} for i in range(100)]
        mock_installation_payload["repositories"] = large_repo_list
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = False
        all_mocks["create_stripe_customer"].return_value = "cus_test123"
        all_mocks["check_grant_exists"].return_value = False

        # Execute
        handle_installation_created(mock_installation_payload)

        # Verify repository processing with large list
        all_mocks["process_repositories"].assert_called_once_with(
            owner_id=67890,
            owner_name="test-owner",
            repositories=large_repo_list,
            token="ghs_test_token",
            user_id=11111,
            user_name="test-sender",
        )

    def test_handle_installation_created_with_none_repositories(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling when repositories is None."""
        # Setup
        mock_installation_payload["repositories"] = None
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = False
        all_mocks["create_stripe_customer"].return_value = "cus_test123"
        all_mocks["check_grant_exists"].return_value = False

        # Execute
        handle_installation_created(mock_installation_payload)

        # Verify repository processing with None
        all_mocks["process_repositories"].assert_called_once_with(
            owner_id=67890,
            owner_name="test-owner",
            repositories=None,
            token="ghs_test_token",
            user_id=11111,
            user_name="test-sender",
        )

    def test_handle_installation_created_with_complex_repository_data(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling with complex repository data structure."""
        # Setup
        complex_repos = [
            {
                "id": 111,
                "name": "test-repo-1",
                "full_name": "test-owner/test-repo-1",
                "private": False,
                "description": "Test repository 1",
                "fork": False,
                "language": "Python",
                "topics": ["python", "testing"],
            },
            {
                "id": 222,
                "name": "test-repo-2",
                "full_name": "test-owner/test-repo-2",
                "private": True,
                "description": None,
                "fork": True,
                "language": "JavaScript",
                "topics": [],
            },
        ]
        mock_installation_payload["repositories"] = complex_repos
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = False
        all_mocks["create_stripe_customer"].return_value = "cus_test123"
        all_mocks["check_grant_exists"].return_value = False

        # Execute
        handle_installation_created(mock_installation_payload)

        # Verify repository processing with complex data
        all_mocks["process_repositories"].assert_called_once_with(
            owner_id=67890,
            owner_name="test-owner",
            repositories=complex_repos,
            token="ghs_test_token",
            user_id=11111,
            user_name="test-sender",
        )

    def test_handle_installation_created_with_special_characters_in_names(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling with special characters in names."""
        # Setup
        special_owner = "test-owner@#$%^&*()_+-=[]{}|;':\",./<>?"
        special_sender = "test-sender!@#$%^&*()_+-=[]{}|;':\",./<>?"
        mock_installation_payload["installation"]["account"]["login"] = special_owner
        mock_installation_payload["sender"]["login"] = special_sender
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = False
        all_mocks["create_stripe_customer"].return_value = "cus_test123"
        all_mocks["check_grant_exists"].return_value = False

        # Execute
        handle_installation_created(mock_installation_payload)

        # Verify calls with special characters
        all_mocks["get_user_public_email"].assert_called_once_with(
            username=special_sender, token="ghs_test_token"
        )
        all_mocks["create_stripe_customer"].assert_called_once_with(
            owner_name=special_owner,
            owner_id=67890,
            installation_id=12345,
            user_id=11111,
            user_name=special_sender,
        )

    def test_handle_installation_created_with_very_long_names(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling with very long names."""
        # Setup
        long_name = "a" * 1000
        mock_installation_payload["installation"]["account"]["login"] = long_name
        mock_installation_payload["sender"]["login"] = long_name
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_user_public_email"].return_value = "test@example.com"
        all_mocks["check_owner_exists"].return_value = False
        all_mocks["create_stripe_customer"].return_value = "cus_test123"
        all_mocks["check_grant_exists"].return_value = False

        # Execute
        handle_installation_created(mock_installation_payload)

        # Verify calls with long names
        all_mocks["get_user_public_email"].assert_called_once_with(
            username=long_name, token="ghs_test_token"
        )
        all_mocks["create_stripe_customer"].assert_called_once_with(
            owner_name=long_name,
            owner_id=67890,
            installation_id=12345,
            user_id=11111,
            user_name=long_name,
        )

    def test_handle_installation_created_with_whitespace_only_names(
        self, mock_installation_payload, all_mocks
    ):
        """Test handling with whitespace-only names."""
        # Setup
        mock_installation_payload["installation"]["account"]["login"] = "   "
        mock_installation_payload["sender"]["login"] = "\t\n\r"
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
