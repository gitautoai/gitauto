from unittest.mock import patch, MagicMock

import pytest
import requests

from services.github.token.get_installation_token import get_installation_access_token
from config import GITHUB_API_URL, TIMEOUT


@pytest.fixture
def mock_get_jwt():
    with patch("services.github.token.get_installation_token.get_jwt") as mock:
        mock.return_value = "mock_jwt_token"
        yield mock


@pytest.fixture
def mock_create_headers():
    with patch("services.github.token.get_installation_token.create_headers") as mock:
        mock.return_value = {"Authorization": "Bearer mock_jwt_token"}
        yield mock


@pytest.fixture
def mock_delete_installation():
    with patch(
        "services.github.token.get_installation_token.delete_installation"
    ) as mock:
        yield mock


@pytest.fixture
def mock_requests_post():
    with patch("services.github.token.get_installation_token.requests.post") as mock:
        yield mock


def test_get_installation_access_token_success(
    _mock_get_jwt, _mock_create_headers, mock_requests_post
):
    """Test successful retrieval of installation access token"""
    # Arrange
    installation_id = 12345
    expected_token = "ghs_mock_token"
    mock_response = MagicMock()
    mock_response.json.return_value = {"token": expected_token}
    mock_requests_post.return_value = mock_response

    # Act
    result = get_installation_access_token(installation_id)

    # Assert
    assert result == expected_token
    mock_requests_post.assert_called_once_with(
        url=f"{GITHUB_API_URL}/app/installations/{installation_id}/access_tokens",
        headers={"Authorization": "Bearer mock_jwt_token"},
        timeout=TIMEOUT,
    )


def test_get_installation_access_token_suspended(
    _mock_get_jwt, _mock_create_headers, mock_requests_post, mock_delete_installation
):
    """Test handling of suspended installation"""
    # Arrange
    installation_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = "This installation has been suspended"
    mock_error = requests.exceptions.HTTPError(response=mock_response)
    mock_requests_post.side_effect = mock_error

    # Act
    result = get_installation_access_token(installation_id)

    # Assert
    assert result is None  # Function should return None due to @handle_exceptions
    mock_requests_post.assert_called_once()
    # Verify delete_installation was called with correct parameters
    mock_delete_installation.assert_called_once_with(
        installation_id=installation_id, user_id=0, user_name="Unknown"
    )


def test_get_installation_access_token_other_error(
    _mock_get_jwt, _mock_create_headers, mock_requests_post
):
    """Test handling of other HTTP errors"""
    # Arrange
    installation_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_error = requests.exceptions.HTTPError(response=mock_response)
    mock_requests_post.side_effect = mock_error

    # Act
    result = get_installation_access_token(installation_id)

    # Assert
    assert result is None  # Function should return None due to @handle_exceptions
