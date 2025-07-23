"""Unit tests for check_user_is_collaborator function.

Related Documentation:
https://docs.github.com/en/rest/collaborators/collaborators?apiVersion=2022-11-28#check-if-a-user-is-a-repository-collaborator
"""

from unittest.mock import patch, MagicMock
import pytest
import requests

from services.github.collaborators.check_user_is_collaborator import (
    check_user_is_collaborator,
)


@pytest.fixture
def mock_requests_get():
    """Fixture to mock requests.get calls."""
    with patch(
        "services.github.collaborators.check_user_is_collaborator.requests.get"
    ) as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    """Fixture to mock create_headers function."""
    with patch(
        "services.github.collaborators.check_user_is_collaborator.create_headers"
    ) as mock:
        mock.return_value = {"Authorization": "Bearer test_token"}
        yield mock


@pytest.fixture
def sample_params():
    """Fixture providing sample parameters for testing."""
    return {
        "owner": "test-owner",
        "repo": "test-repo",
        "user": "test-user",
        "token": "test-token",
    }


def test_check_user_is_collaborator_returns_true_for_204(
    mock_requests_get, mock_create_headers, sample_params
):
    """Test that function returns True when user is a collaborator (204 status)."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_requests_get.return_value = mock_response

    # Execute
    result = check_user_is_collaborator(**sample_params)

    # Assert
    assert result is True
    mock_requests_get.assert_called_once()
    mock_create_headers.assert_called_once_with(token="test-token")
    mock_response.raise_for_status.assert_called_once()


def test_check_user_is_collaborator_returns_false_for_404(
    mock_requests_get, mock_create_headers, sample_params
):
    """Test that function returns False when user is not a collaborator (404 status)."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_requests_get.return_value = mock_response

    # Execute
    result = check_user_is_collaborator(**sample_params)

    # Assert
    assert result is False
    mock_requests_get.assert_called_once()
    mock_create_headers.assert_called_once_with(token="test-token")
    # raise_for_status should not be called for 404
    mock_response.raise_for_status.assert_not_called()


def test_check_user_is_collaborator_returns_false_for_non_204_success(
    mock_requests_get, mock_create_headers, sample_params
):
    """Test that function returns False for successful responses that are not 204."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_requests_get.return_value = mock_response

    # Execute
    result = check_user_is_collaborator(**sample_params)

    # Assert
    assert result is False
    mock_requests_get.assert_called_once()
    mock_create_headers.assert_called_once_with(token="test-token")
    mock_response.raise_for_status.assert_called_once()


def test_check_user_is_collaborator_constructs_correct_url(
    mock_requests_get, mock_create_headers, sample_params
):
    """Test that function constructs the correct GitHub API URL."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_requests_get.return_value = mock_response

    # Execute
    check_user_is_collaborator(**sample_params)

    # Assert
    expected_url = (
        "https://api.github.com/repos/test-owner/test-repo/collaborators/test-user"
    )
    mock_requests_get.assert_called_once_with(
        url=expected_url, headers={"Authorization": "Bearer test_token"}, timeout=120
    )


def test_check_user_is_collaborator_handles_http_error(
    mock_requests_get, mock_create_headers, sample_params
):
    """Test that function handles HTTP errors gracefully via decorator."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 403
    http_error = requests.exceptions.HTTPError("Forbidden")
    http_error.response = mock_response
    mock_response.reason = "Forbidden"
    mock_response.text = "Forbidden"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Used": "1",
        "X-RateLimit-Reset": "1234567890",
    }
    mock_response.raise_for_status.side_effect = http_error
    mock_requests_get.return_value = mock_response

    # Execute
    result = check_user_is_collaborator(**sample_params)

    # Assert - handle_exceptions decorator should return False on error
    assert result is False
    mock_requests_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


def test_check_user_is_collaborator_handles_request_exception(
    mock_requests_get, mock_create_headers, sample_params
):
    """Test that function handles request exceptions gracefully via decorator."""
    # Setup
    mock_requests_get.side_effect = requests.exceptions.RequestException(
        "Network error"
    )

    # Execute
    result = check_user_is_collaborator(**sample_params)

    # Assert - handle_exceptions decorator should return False on error
    assert result is False
    mock_requests_get.assert_called_once()


def test_check_user_is_collaborator_with_special_characters_in_params(
    mock_requests_get, mock_create_headers
):
    """Test that function handles special characters in parameters correctly."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_requests_get.return_value = mock_response

    params = {
        "owner": "test-owner-123",
        "repo": "test.repo_name",
        "user": "user-name_123",
        "token": "ghp_1234567890abcdef",
    }

    # Execute
    result = check_user_is_collaborator(**params)

    # Assert
    assert result is True
    expected_url = "https://api.github.com/repos/test-owner-123/test.repo_name/collaborators/user-name_123"
    mock_requests_get.assert_called_once_with(
        url=expected_url, headers={"Authorization": "Bearer test_token"}, timeout=120
    )


@pytest.mark.parametrize(
    "status_code,expected_result",
    [
        (204, True),  # User is a collaborator
        (404, False),  # User is not a collaborator
        (200, False),  # Unexpected success status
        (201, False),  # Unexpected success status
    ],
)
def test_check_user_is_collaborator_status_code_handling(
    mock_requests_get, mock_create_headers, sample_params, status_code, expected_result
):
    """Test function behavior with various status codes."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_requests_get.return_value = mock_response

    # Execute
    result = check_user_is_collaborator(**sample_params)

    # Assert
    assert result is expected_result
    mock_requests_get.assert_called_once()

    # raise_for_status should only be called for non-404 status codes
    if status_code != 404:
        mock_response.raise_for_status.assert_called_once()
    else:
        mock_response.raise_for_status.assert_not_called()
