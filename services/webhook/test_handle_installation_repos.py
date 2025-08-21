"""Unit tests for handle_installation_repos.py"""

# Standard imports
import pytest
from unittest.mock import patch, AsyncMock

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
