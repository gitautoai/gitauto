# pylint: disable=too-many-lines,too-many-public-methods
"""Unit tests for handle_installation_repos.py"""

# Standard imports
import json
from typing import cast
from unittest.mock import AsyncMock, patch

# Third-party imports
import pytest

# Local imports
from services.github.types.github_types import InstallationRepositoriesPayload
from services.github.users.get_user_public_email import UserPublicInfo
from services.webhook.handle_installation_repos_added import (
    handle_installation_repos_added,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_installation_payload():
    """Fixture providing a mock installation repositories payload."""
    return {
        "installation": {
            "id": 67890,
            "account": {
                "id": 12345,
                "login": "test-owner",
                "type": "Organization",
            },
        },
        "sender": {
            "id": 67890,
            "login": "test-sender",
        },
        "repositories_added": [
            {
                "id": 111,
                "name": "test-repo-1",
            },
            {
                "id": 222,
                "name": "test-repo-2",
            },
        ],
    }


@pytest.fixture
def mock_is_installation_valid():
    """Mock is_installation_valid function."""
    with patch(
        "services.webhook.handle_installation_repos_added.is_installation_valid"
    ) as mock:
        yield mock


@pytest.fixture
def mock_get_installation_access_token():
    """Mock get_installation_access_token function."""
    with patch(
        "services.webhook.handle_installation_repos_added.get_installation_access_token"
    ) as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_get_user_public_info():
    """Mock get_user_public_info function."""
    with patch(
        "services.webhook.handle_installation_repos_added.get_user_public_info"
    ) as mock:
        mock.return_value = UserPublicInfo(
            email="test@example.com", display_name="Test Sender"
        )
        yield mock


@pytest.fixture(autouse=True)
def mock_get_email_from_commits():
    """Mock get_email_from_commits function."""
    with patch(
        "services.webhook.handle_installation_repos_added.get_email_from_commits"
    ) as mock:
        mock.return_value = None
        yield mock


@pytest.fixture(autouse=True)
def mock_upsert_user():
    """Mock upsert_user function."""
    with patch("services.webhook.handle_installation_repos_added.upsert_user") as mock:
        yield mock


@pytest.fixture
def mock_process_repositories():
    """Mock process_repositories function."""
    with patch(
        "services.webhook.handle_installation_repos_added.process_repositories",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


class TestHandleInstallationReposAdded:
    """Test cases for handle_installation_repos_added function."""

    async def test_handle_installation_repos_added_success(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test successful handling of installation repositories added event."""
        # Setup
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"

        # Execute
        await handle_installation_repos_added(mock_installation_payload)

        # Verify
        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=67890
        )
        mock_process_repositories.assert_called_once_with(
            installation_id=67890,
            owner_id=12345,
            owner_name="test-owner",
            owner_type="Organization",
            repositories=[
                {"id": 111, "name": "test-repo-1"},
                {"id": 222, "name": "test-repo-2"},
            ],
            sender_display_name="Test Sender",
            sender_email="test@example.com",
            token="ghs_test_token",
            user_id=67890,
            user_name="test-sender",
        )

    async def test_handle_installation_repos_added_invalid_installation(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when installation is invalid."""
        # Setup
        mock_is_installation_valid.return_value = False

        # Execute
        result = await handle_installation_repos_added(mock_installation_payload)

        # Verify
        assert result is None
        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_not_called()
        mock_process_repositories.assert_not_called()

    async def test_handle_installation_repos_added_empty_repositories(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when no repositories are added."""
        # Setup
        mock_installation_payload["repositories_added"] = []
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"

        # Execute
        await handle_installation_repos_added(mock_installation_payload)

        # Verify
        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=67890
        )
        mock_process_repositories.assert_called_once_with(
            installation_id=67890,
            owner_id=12345,
            owner_name="test-owner",
            owner_type="Organization",
            repositories=[],
            sender_display_name="Test Sender",
            sender_email="test@example.com",
            token="ghs_test_token",
            user_id=67890,
            user_name="test-sender",
        )

    async def test_handle_installation_repos_added_with_token_error(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when token retrieval raises - exception is re-raised."""
        # Setup - get_installation_access_token now raises instead of returning None
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.side_effect = ValueError(
            "Installation 67890 suspended or deleted"
        )

        # Execute - exception is re-raised due to raise_on_error=True
        with pytest.raises(ValueError, match="Installation 67890 suspended or deleted"):
            await handle_installation_repos_added(mock_installation_payload)

        # Verify - should return early when token retrieval fails
        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=67890
        )
        mock_process_repositories.assert_not_called()

    async def test_handle_installation_repos_added_with_exception_in_is_installation_valid(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when is_installation_valid raises an exception."""
        # Setup
        mock_is_installation_valid.side_effect = Exception("Database error")

        # Execute - exception is re-raised due to raise_on_error=True
        with pytest.raises(Exception, match="Database error"):
            await handle_installation_repos_added(mock_installation_payload)

        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_not_called()
        mock_process_repositories.assert_not_called()

    async def test_handle_installation_repos_added_with_exception_in_get_token(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when get_installation_access_token raises an exception."""
        # Setup
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.side_effect = Exception("Token error")

        # Execute - exception is re-raised due to raise_on_error=True
        with pytest.raises(Exception, match="Token error"):
            await handle_installation_repos_added(mock_installation_payload)

        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=67890
        )
        mock_process_repositories.assert_not_called()

    async def test_handle_installation_repos_added_with_exception_in_process_repositories(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when process_repositories raises an exception."""
        # Setup
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"
        mock_process_repositories.side_effect = Exception("Processing error")

        # Execute - exception is re-raised due to raise_on_error=True
        with pytest.raises(Exception, match="Processing error"):
            await handle_installation_repos_added(mock_installation_payload)

        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=67890
        )
        mock_process_repositories.assert_called_once_with(
            installation_id=67890,
            owner_id=12345,
            owner_name="test-owner",
            owner_type="Organization",
            repositories=[
                {"id": 111, "name": "test-repo-1"},
                {"id": 222, "name": "test-repo-2"},
            ],
            sender_display_name="Test Sender",
            sender_email="test@example.com",
            token="ghs_test_token",
            user_id=67890,
            user_name="test-sender",
        )

    async def test_handle_installation_repos_added_with_missing_payload_fields(
        self,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when payload is missing required fields."""
        # Setup - payload missing sender information
        incomplete_payload = {
            "installation": {
                "id": 67890,
                "account": {
                    "id": 12345,
                    "login": "test-owner",
                    "type": "Organization",
                },
            },
            "repositories_added": [
                {"id": 111, "name": "test-repo-1"},
            ],
        }
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"

        # Execute - exception is re-raised due to raise_on_error=True
        with pytest.raises(KeyError, match="sender"):
            await handle_installation_repos_added(
                cast(InstallationRepositoriesPayload, incomplete_payload)
            )

        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=67890
        )
        mock_process_repositories.assert_not_called()

    async def test_handle_installation_repos_added_with_missing_installation_id(
        self,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when payload is missing installation ID."""
        # Setup - payload missing installation ID
        incomplete_payload = {
            "installation": {
                "account": {
                    "id": 12345,
                    "login": "test-owner",
                    "type": "Organization",
                },
            },
            "sender": {
                "id": 67890,
                "login": "test-sender",
            },
            "repositories_added": [
                {"id": 111, "name": "test-repo-1"},
            ],
        }

        # Execute - exception is re-raised due to raise_on_error=True
        with pytest.raises(KeyError, match="id"):
            await handle_installation_repos_added(
                cast(InstallationRepositoriesPayload, incomplete_payload)
            )

        mock_is_installation_valid.assert_not_called()
        mock_get_installation_access_token.assert_not_called()
        mock_process_repositories.assert_not_called()

    async def test_handle_installation_repos_added_with_missing_account_info(
        self,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when payload is missing account information."""
        # Setup - payload missing account information
        incomplete_payload = {
            "installation": {
                "id": 67890,
            },
            "sender": {
                "id": 67890,
                "login": "test-sender",
            },
            "repositories_added": [
                {"id": 111, "name": "test-repo-1"},
            ],
        }
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"

        # Execute - exception is re-raised due to raise_on_error=True
        with pytest.raises(KeyError, match="account"):
            await handle_installation_repos_added(
                cast(InstallationRepositoriesPayload, incomplete_payload)
            )

        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=67890
        )
        mock_process_repositories.assert_not_called()

    async def test_handle_installation_repos_added_with_single_repository(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling with a single repository."""
        # Setup
        mock_installation_payload["repositories_added"] = [
            {"id": 333, "name": "single-repo"}
        ]
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"

        # Execute
        await handle_installation_repos_added(mock_installation_payload)

        # Verify
        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=67890
        )
        mock_process_repositories.assert_called_once_with(
            installation_id=67890,
            owner_id=12345,
            owner_name="test-owner",
            owner_type="Organization",
            repositories=[{"id": 333, "name": "single-repo"}],
            sender_display_name="Test Sender",
            sender_email="test@example.com",
            token="ghs_test_token",
            user_id=67890,
            user_name="test-sender",
        )

    async def test_handle_installation_repos_added_with_different_installation_id(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling with a different installation ID."""
        # Setup
        different_installation_id = 99999
        mock_installation_payload["installation"]["id"] = different_installation_id
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_different_token"

        # Execute
        await handle_installation_repos_added(mock_installation_payload)

        # Verify
        mock_is_installation_valid.assert_called_once_with(
            installation_id=different_installation_id
        )
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=different_installation_id
        )
        mock_process_repositories.assert_called_once_with(
            installation_id=different_installation_id,
            owner_id=12345,
            owner_name="test-owner",
            owner_type="Organization",
            repositories=[
                {"id": 111, "name": "test-repo-1"},
                {"id": 222, "name": "test-repo-2"},
            ],
            sender_display_name="Test Sender",
            sender_email="test@example.com",
            token="ghs_different_token",
            user_id=67890,
            user_name="test-sender",
        )

    async def test_handle_installation_repos_added_with_zero_installation_id(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling with zero installation ID."""
        # Setup
        mock_installation_payload["installation"]["id"] = 0
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"

        # Execute
        await handle_installation_repos_added(mock_installation_payload)

        # Verify
        mock_is_installation_valid.assert_called_once_with(installation_id=0)
        mock_get_installation_access_token.assert_called_once_with(installation_id=0)
        mock_process_repositories.assert_called_once_with(
            installation_id=0,
            owner_id=12345,
            owner_name="test-owner",
            owner_type="Organization",
            repositories=[
                {"id": 111, "name": "test-repo-1"},
                {"id": 222, "name": "test-repo-2"},
            ],
            sender_display_name="Test Sender",
            sender_email="test@example.com",
            token="ghs_test_token",
            user_id=67890,
            user_name="test-sender",
        )

    async def test_handle_installation_repos_added_with_string_ids(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when IDs are provided as strings."""
        # Setup
        mock_installation_payload["installation"]["id"] = str(67890)
        mock_installation_payload["installation"]["account"]["id"] = "12345"
        mock_installation_payload["sender"]["id"] = "67890"
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"

        # Execute
        await handle_installation_repos_added(mock_installation_payload)

        # Verify
        mock_is_installation_valid.assert_called_once_with(installation_id=str(67890))
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=str(67890)
        )
        mock_process_repositories.assert_called_once_with(
            installation_id=str(67890),
            owner_id="12345",
            owner_name="test-owner",
            owner_type="Organization",
            repositories=[
                {"id": 111, "name": "test-repo-1"},
                {"id": 222, "name": "test-repo-2"},
            ],
            sender_display_name="Test Sender",
            sender_email="test@example.com",
            token="ghs_test_token",
            user_id="67890",
            user_name="test-sender",
        )

    async def test_handle_installation_repos_added_with_complex_repository_data(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
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
            },
            {
                "id": 222,
                "name": "test-repo-2",
                "full_name": "test-owner/test-repo-2",
                "private": True,
                "description": None,
                "fork": True,
                "language": "JavaScript",
            },
        ]
        mock_installation_payload["repositories_added"] = complex_repos
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"

        # Execute
        await handle_installation_repos_added(mock_installation_payload)

        # Verify
        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=67890
        )
        mock_process_repositories.assert_called_once_with(
            installation_id=67890,
            owner_id=12345,
            owner_name="test-owner",
            owner_type="Organization",
            repositories=complex_repos,
            sender_display_name="Test Sender",
            sender_email="test@example.com",
            token="ghs_test_token",
            user_id=67890,
            user_name="test-sender",
        )

    async def test_handle_installation_repos_added_with_unicode_names(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling with unicode characters in names."""
        # Setup
        mock_installation_payload["installation"]["account"]["login"] = "tëst-öwnér"
        mock_installation_payload["sender"]["login"] = "tëst-sëndér"
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"

        # Execute
        await handle_installation_repos_added(mock_installation_payload)

        # Verify
        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=67890
        )
        mock_process_repositories.assert_called_once_with(
            installation_id=67890,
            owner_id=12345,
            owner_name="tëst-öwnér",
            owner_type="Organization",
            repositories=[
                {"id": 111, "name": "test-repo-1"},
                {"id": 222, "name": "test-repo-2"},
            ],
            sender_display_name="Test Sender",
            sender_email="test@example.com",
            token="ghs_test_token",
            user_id=67890,
            user_name="tëst-sëndér",
        )

    async def test_handle_installation_repos_added_with_none_payload(
        self,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when payload is None."""
        # Execute - exception is re-raised due to raise_on_error=True
        with pytest.raises(TypeError):
            await handle_installation_repos_added(None)  # type: ignore[arg-type]

        mock_is_installation_valid.assert_not_called()
        mock_get_installation_access_token.assert_not_called()
        mock_process_repositories.assert_not_called()

    async def test_handle_installation_repos_added_with_empty_payload(
        self,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when payload is empty dictionary."""
        # Execute - exception is re-raised due to raise_on_error=True
        with pytest.raises(KeyError, match="installation"):
            await handle_installation_repos_added({})  # type: ignore[arg-type]

        mock_is_installation_valid.assert_not_called()
        mock_get_installation_access_token.assert_not_called()
        mock_process_repositories.assert_not_called()

    async def test_handle_installation_repos_added_with_type_error_in_payload_access(
        self,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when payload access causes TypeError."""
        # Setup - payload with wrong data types
        invalid_payload = {
            "installation": "not_a_dict",
            "sender": {"id": 67890, "login": "test-sender"},
            "repositories_added": [],
        }

        # Execute - exception is re-raised due to raise_on_error=True
        with pytest.raises(TypeError):
            await handle_installation_repos_added(
                cast(InstallationRepositoriesPayload, invalid_payload)
            )

        mock_is_installation_valid.assert_not_called()
        mock_get_installation_access_token.assert_not_called()
        mock_process_repositories.assert_not_called()

    async def test_handle_installation_repos_added_with_attribute_error(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when AttributeError occurs during processing."""
        # Setup
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"
        mock_process_repositories.side_effect = AttributeError(
            "'NoneType' object has no attribute 'some_attr'"
        )

        # Execute - exception is re-raised due to raise_on_error=True
        with pytest.raises(AttributeError, match="some_attr"):
            await handle_installation_repos_added(mock_installation_payload)

        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=67890
        )
        mock_process_repositories.assert_called_once()

    async def test_handle_installation_repos_added_with_key_error(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when KeyError occurs during processing."""
        # Setup
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"
        mock_process_repositories.side_effect = KeyError("missing_key")

        # Execute - exception is re-raised due to raise_on_error=True
        with pytest.raises(KeyError, match="missing_key"):
            await handle_installation_repos_added(mock_installation_payload)

        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=67890
        )
        mock_process_repositories.assert_called_once()

    async def test_handle_installation_repos_added_with_json_decode_error(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when JSONDecodeError occurs during processing."""
        # Setup
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"
        json_error = json.JSONDecodeError("Expecting value", "invalid json", 0)
        mock_process_repositories.side_effect = json_error

        # Execute - exception is re-raised due to raise_on_error=True
        with pytest.raises(json.JSONDecodeError):
            await handle_installation_repos_added(mock_installation_payload)

        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=67890
        )
        mock_process_repositories.assert_called_once()

    async def test_handle_installation_repos_added_decorator_behavior(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test that the handle_exceptions decorator works correctly."""
        # Setup
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"
        mock_process_repositories.return_value = None

        # Execute
        result = await handle_installation_repos_added(mock_installation_payload)

        # Verify - function should return None (default_return_value from decorator)
        assert result is None
        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=67890
        )
        mock_process_repositories.assert_called_once()

    async def test_handle_installation_repos_added_with_large_repository_list(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling with a large number of repositories."""
        # Setup - create a large list of repositories
        large_repo_list = [{"id": i, "name": f"repo-{i}"} for i in range(100)]
        mock_installation_payload["repositories_added"] = large_repo_list
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"

        # Execute
        await handle_installation_repos_added(mock_installation_payload)

        # Verify
        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=67890
        )
        mock_process_repositories.assert_called_once_with(
            installation_id=67890,
            owner_id=12345,
            owner_name="test-owner",
            owner_type="Organization",
            repositories=large_repo_list,
            sender_display_name="Test Sender",
            sender_email="test@example.com",
            token="ghs_test_token",
            user_id=67890,
            user_name="test-sender",
        )

    async def test_handle_installation_repos_added_with_negative_installation_id(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling with negative installation ID."""
        # Setup
        mock_installation_payload["installation"]["id"] = -1
        mock_is_installation_valid.return_value = False

        # Execute
        result = await handle_installation_repos_added(mock_installation_payload)

        # Verify
        assert result is None
        mock_is_installation_valid.assert_called_once_with(installation_id=-1)
        mock_get_installation_access_token.assert_not_called()
        mock_process_repositories.assert_not_called()

    async def test_handle_installation_repos_added_with_repositories_added_none(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when repositories_added is None."""
        # Setup
        mock_installation_payload["repositories_added"] = None
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"

        # Execute
        await handle_installation_repos_added(mock_installation_payload)

        # Verify
        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=67890
        )
        mock_process_repositories.assert_called_once_with(
            installation_id=67890,
            owner_id=12345,
            owner_name="test-owner",
            owner_type="Organization",
            repositories=None,
            sender_display_name="Test Sender",
            sender_email="test@example.com",
            token="ghs_test_token",
            user_id=67890,
            user_name="test-sender",
        )

    async def test_handle_installation_repos_added_with_very_long_names(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling with very long owner and sender names."""
        # Setup
        long_name = "a" * 1000  # Very long name
        mock_installation_payload["installation"]["account"]["login"] = long_name
        mock_installation_payload["sender"]["login"] = long_name
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"

        # Execute
        await handle_installation_repos_added(mock_installation_payload)

        # Verify
        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=67890
        )
        mock_process_repositories.assert_called_once_with(
            installation_id=67890,
            owner_id=12345,
            owner_name=long_name,
            owner_type="Organization",
            repositories=[
                {"id": 111, "name": "test-repo-1"},
                {"id": 222, "name": "test-repo-2"},
            ],
            sender_display_name="Test Sender",
            sender_email="test@example.com",
            token="ghs_test_token",
            user_id=67890,
            user_name=long_name,
        )

    async def test_handle_installation_repos_added_with_special_characters_in_names(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling with special characters in owner and sender names."""
        # Setup
        special_owner = "test-owner@#$%^&*()_+-=[]{}|;':\",./<>?"
        special_sender = "test-sender!@#$%^&*()_+-=[]{}|;':\",./<>?"
        mock_installation_payload["installation"]["account"]["login"] = special_owner
        mock_installation_payload["sender"]["login"] = special_sender
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"

        # Execute
        await handle_installation_repos_added(mock_installation_payload)

        # Verify
        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=67890
        )
        mock_process_repositories.assert_called_once_with(
            installation_id=67890,
            owner_id=12345,
            owner_name=special_owner,
            owner_type="Organization",
            repositories=[
                {"id": 111, "name": "test-repo-1"},
                {"id": 222, "name": "test-repo-2"},
            ],
            sender_display_name="Test Sender",
            sender_email="test@example.com",
            token="ghs_test_token",
            user_id=67890,
            user_name=special_sender,
        )

    async def test_handle_installation_repos_added_with_max_int_values(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling with maximum integer values for IDs."""
        # Setup
        max_int = 2**63 - 1  # Maximum value for 64-bit signed integer
        mock_installation_payload["installation"]["id"] = max_int
        mock_installation_payload["installation"]["account"]["id"] = max_int
        mock_installation_payload["sender"]["id"] = max_int
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"

        # Execute
        await handle_installation_repos_added(mock_installation_payload)

        # Verify
        mock_is_installation_valid.assert_called_once_with(installation_id=max_int)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=max_int
        )
        mock_process_repositories.assert_called_once_with(
            installation_id=max_int,
            owner_id=max_int,
            owner_name="test-owner",
            owner_type="Organization",
            repositories=[
                {"id": 111, "name": "test-repo-1"},
                {"id": 222, "name": "test-repo-2"},
            ],
            sender_display_name="Test Sender",
            sender_email="test@example.com",
            token="ghs_test_token",
            user_id=max_int,
            user_name="test-sender",
        )

    async def test_handle_installation_repos_added_with_float_installation_id(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when installation ID is provided as float."""
        # Setup
        mock_installation_payload["installation"]["id"] = 12345.0
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"

        # Execute
        await handle_installation_repos_added(mock_installation_payload)

        # Verify
        mock_is_installation_valid.assert_called_once_with(installation_id=12345.0)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=12345.0
        )
        mock_process_repositories.assert_called_once_with(
            installation_id=12345.0,
            owner_id=12345,
            owner_name="test-owner",
            owner_type="Organization",
            repositories=[
                {"id": 111, "name": "test-repo-1"},
                {"id": 222, "name": "test-repo-2"},
            ],
            sender_display_name="Test Sender",
            sender_email="test@example.com",
            token="ghs_test_token",
            user_id=67890,
            user_name="test-sender",
        )

    async def test_handle_installation_repos_added_with_whitespace_only_names(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling with whitespace-only names."""
        # Setup
        mock_installation_payload["installation"]["account"]["login"] = "   "
        mock_installation_payload["sender"]["login"] = "\t\n\r"
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"

        # Execute
        await handle_installation_repos_added(mock_installation_payload)

        # Verify
        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=67890
        )
        mock_process_repositories.assert_called_once_with(
            installation_id=67890,
            owner_id=12345,
            owner_name="   ",
            owner_type="Organization",
            repositories=[
                {"id": 111, "name": "test-repo-1"},
                {"id": 222, "name": "test-repo-2"},
            ],
            sender_display_name="Test Sender",
            sender_email="test@example.com",
            token="ghs_test_token",
            user_id=67890,
            user_name="\t\n\r",
        )

    async def test_handle_installation_repos_added_with_boolean_installation_valid_response(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when is_installation_valid returns non-boolean truthy value."""
        # Setup
        mock_is_installation_valid.return_value = "valid"  # Truthy but not boolean
        mock_get_installation_access_token.return_value = "ghs_test_token"

        # Execute
        await handle_installation_repos_added(mock_installation_payload)

        # Verify - should still proceed since "valid" is truthy
        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=67890
        )
        mock_process_repositories.assert_called_once_with(
            installation_id=67890,
            owner_id=12345,
            owner_name="test-owner",
            owner_type="Organization",
            repositories=[
                {"id": 111, "name": "test-repo-1"},
                {"id": 222, "name": "test-repo-2"},
            ],
            sender_display_name="Test Sender",
            sender_email="test@example.com",
            token="ghs_test_token",
            user_id=67890,
            user_name="test-sender",
        )

    async def test_handle_installation_repos_added_with_falsy_installation_valid_response(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when is_installation_valid returns falsy non-boolean value."""
        # Setup
        mock_is_installation_valid.return_value = 0  # Falsy but not boolean

        # Execute
        result = await handle_installation_repos_added(mock_installation_payload)

        # Verify - should return early since 0 is falsy
        assert result is None
        mock_is_installation_valid.assert_called_once_with(installation_id=67890)
        mock_get_installation_access_token.assert_not_called()
        mock_process_repositories.assert_not_called()
