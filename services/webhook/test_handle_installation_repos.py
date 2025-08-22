"""Unit tests for handle_installation_repos.py"""

# Standard imports
from unittest.mock import patch, MagicMock
import json

# Third-party imports
import pytest

# Local imports
from services.webhook.handle_installation_repos import handle_installation_repos_added
from tests.constants import INSTALLATION_ID


@pytest.fixture
def mock_installation_payload():
    """Fixture providing a mock installation repositories payload."""
    return {
        "installation": {
            "id": INSTALLATION_ID,
            "account": {
                "id": 12345,
                "login": "test-owner",
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
        "services.webhook.handle_installation_repos.is_installation_valid"
    ) as mock:
        yield mock


@pytest.fixture
def mock_get_installation_access_token():
    """Mock get_installation_access_token function."""
    with patch(
        "services.webhook.handle_installation_repos.get_installation_access_token"
    ) as mock:
        yield mock


@pytest.fixture
def mock_process_repositories():
    """Mock process_repositories function."""
    with patch(
        "services.webhook.handle_installation_repos.process_repositories"
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
        mock_is_installation_valid.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_process_repositories.assert_called_once_with(
            owner_id=12345,
            owner_name="test-owner",
            repositories=[
                {"id": 111, "name": "test-repo-1"},
                {"id": 222, "name": "test-repo-2"},
            ],
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
        mock_is_installation_valid.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
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
        mock_is_installation_valid.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_process_repositories.assert_called_once_with(
            owner_id=12345,
            owner_name="test-owner",
            repositories=[],
            token="ghs_test_token",
            user_id=67890,
            user_name="test-sender",
        )

    async def test_handle_installation_repos_added_with_none_token(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when token is None."""
        # Setup
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = None

        # Execute
        await handle_installation_repos_added(mock_installation_payload)

        # Verify
        mock_is_installation_valid.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_process_repositories.assert_called_once_with(
            owner_id=12345,
            owner_name="test-owner",
            repositories=[
                {"id": 111, "name": "test-repo-1"},
                {"id": 222, "name": "test-repo-2"},
            ],
            token=None,
            user_id=67890,
            user_name="test-sender",
        )

    async def test_handle_installation_repos_added_with_empty_token(
        self,
        mock_installation_payload,
        mock_is_installation_valid,
        mock_get_installation_access_token,
        mock_process_repositories,
    ):
        """Test handling when token is empty string."""
        # Setup
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = ""

        # Execute
        await handle_installation_repos_added(mock_installation_payload)

        # Verify
        mock_is_installation_valid.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_process_repositories.assert_called_once_with(
            owner_id=12345,
            owner_name="test-owner",
            repositories=[
                {"id": 111, "name": "test-repo-1"},
                {"id": 222, "name": "test-repo-2"},
            ],
            token="",
            user_id=67890,
            user_name="test-sender",
        )

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

        # Execute
        result = await handle_installation_repos_added(mock_installation_payload)

        # Verify - function should return None due to handle_exceptions decorator
        assert result is None
        mock_is_installation_valid.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
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

        # Execute
        result = await handle_installation_repos_added(mock_installation_payload)

        # Verify - function should return None due to handle_exceptions decorator
        assert result is None
        mock_is_installation_valid.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=INSTALLATION_ID
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

        # Execute
        result = await handle_installation_repos_added(mock_installation_payload)

        # Verify - function should return None due to handle_exceptions decorator
        assert result is None
        mock_is_installation_valid.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_process_repositories.assert_called_once_with(
            owner_id=12345,
            owner_name="test-owner",
            repositories=[
                {"id": 111, "name": "test-repo-1"},
                {"id": 222, "name": "test-repo-2"},
            ],
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
                "id": INSTALLATION_ID,
                "account": {
                    "id": 12345,
                    "login": "test-owner",
                },
            },
            "repositories_added": [
                {"id": 111, "name": "test-repo-1"},
            ],
        }
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"

        # Execute
        result = await handle_installation_repos_added(incomplete_payload)

        # Verify - function should return None due to handle_exceptions decorator
        assert result is None
        mock_is_installation_valid.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=INSTALLATION_ID
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

        # Execute
        result = await handle_installation_repos_added(incomplete_payload)

        # Verify - function should return None due to handle_exceptions decorator
        assert result is None
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
                "id": INSTALLATION_ID,
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

        # Execute
        result = await handle_installation_repos_added(incomplete_payload)

        # Verify - function should return None due to handle_exceptions decorator
        assert result is None
        mock_is_installation_valid.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=INSTALLATION_ID
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
        mock_is_installation_valid.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_process_repositories.assert_called_once_with(
            owner_id=12345,
            owner_name="test-owner",
            repositories=[{"id": 333, "name": "single-repo"}],
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
            owner_id=12345,
            owner_name="test-owner",
            repositories=[
                {"id": 111, "name": "test-repo-1"},
                {"id": 222, "name": "test-repo-2"},
            ],
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
            owner_id=12345,
            owner_name="test-owner",
            repositories=[
                {"id": 111, "name": "test-repo-1"},
                {"id": 222, "name": "test-repo-2"},
            ],
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
        mock_installation_payload["installation"]["id"] = str(INSTALLATION_ID)
        mock_installation_payload["installation"]["account"]["id"] = "12345"
        mock_installation_payload["sender"]["id"] = "67890"
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"

        # Execute
        await handle_installation_repos_added(mock_installation_payload)

        # Verify
        mock_is_installation_valid.assert_called_once_with(
            installation_id=str(INSTALLATION_ID)
        )
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=str(INSTALLATION_ID)
        )
        mock_process_repositories.assert_called_once_with(
            owner_id="12345",
            owner_name="test-owner",
            repositories=[
                {"id": 111, "name": "test-repo-1"},
                {"id": 222, "name": "test-repo-2"},
            ],
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
        mock_is_installation_valid.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_process_repositories.assert_called_once_with(
            owner_id=12345,
            owner_name="test-owner",
            repositories=complex_repos,
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
        mock_is_installation_valid.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_process_repositories.assert_called_once_with(
            owner_id=12345,
            owner_name="tëst-öwnér",
            repositories=[
                {"id": 111, "name": "test-repo-1"},
                {"id": 222, "name": "test-repo-2"},
            ],
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
        # Execute
        result = await handle_installation_repos_added(None)

        # Verify - function should return None due to handle_exceptions decorator
        assert result is None
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
        # Execute
        result = await handle_installation_repos_added({})

        # Verify - function should return None due to handle_exceptions decorator
        assert result is None
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

        # Execute
        result = await handle_installation_repos_added(invalid_payload)

        # Verify - function should return None due to handle_exceptions decorator
        assert result is None
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
        mock_process_repositories.side_effect = AttributeError("'NoneType' object has no attribute 'some_attr'")

        # Execute
        result = await handle_installation_repos_added(mock_installation_payload)

        # Verify - function should return None due to handle_exceptions decorator
        assert result is None
        mock_is_installation_valid.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=INSTALLATION_ID
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

        # Execute
        result = await handle_installation_repos_added(mock_installation_payload)

        # Verify - function should return None due to handle_exceptions decorator
        assert result is None
        mock_is_installation_valid.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=INSTALLATION_ID
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

        # Execute
        result = await handle_installation_repos_added(mock_installation_payload)

        # Verify - function should return None due to handle_exceptions decorator
        assert result is None
        mock_is_installation_valid.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=INSTALLATION_ID
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
        mock_is_installation_valid.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=INSTALLATION_ID
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
        large_repo_list = [
            {"id": i, "name": f"repo-{i}"} for i in range(100)
        ]
        mock_installation_payload["repositories_added"] = large_repo_list
        mock_is_installation_valid.return_value = True
        mock_get_installation_access_token.return_value = "ghs_test_token"

        # Execute
        await handle_installation_repos_added(mock_installation_payload)

        # Verify
        mock_is_installation_valid.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_get_installation_access_token.assert_called_once_with(
            installation_id=INSTALLATION_ID
        )
        mock_process_repositories.assert_called_once_with(
            owner_id=12345,
            owner_name="test-owner",
            repositories=large_repo_list,
            token="ghs_test_token",
            user_id=67890,
            user_name="test-sender",
        )