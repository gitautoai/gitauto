# pylint: disable=unused-argument,redefined-outer-name
from unittest.mock import patch, MagicMock
import json

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
    mock_get_jwt, mock_create_headers, mock_requests_post
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
    mock_response.raise_for_status.assert_called_once()


def test_get_installation_access_token_suspended(
    mock_get_jwt, mock_create_headers, mock_requests_post, mock_delete_installation
):
    """Test handling of suspended installation"""
    # Arrange
    installation_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = "This installation has been suspended"
    mock_error = requests.exceptions.HTTPError(response=mock_response)
    mock_error.response = mock_response
    mock_requests_post.return_value.raise_for_status.side_effect = mock_error

    # Act
    result = get_installation_access_token(installation_id)

    # Assert
    assert result is None
    mock_requests_post.assert_called_once()
    mock_delete_installation.assert_called_once_with(
        installation_id=installation_id, user_id=0, user_name="System"
    )


def test_get_installation_access_token_not_found(
    mock_get_jwt, mock_create_headers, mock_requests_post, mock_delete_installation
):
    """Test handling of installation not found (404)"""
    # Arrange
    installation_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_error = requests.exceptions.HTTPError(response=mock_response)
    mock_error.response = mock_response
    mock_requests_post.return_value.raise_for_status.side_effect = mock_error

    # Act
    result = get_installation_access_token(installation_id)

    # Assert
    assert result is None
    mock_requests_post.assert_called_once()
    mock_delete_installation.assert_called_once_with(
        installation_id=installation_id, user_id=0, user_name="System"
    )


def test_get_installation_access_token_403_without_suspension_message(
    mock_get_jwt, mock_create_headers, mock_requests_post, mock_delete_installation
):
    """Test handling of 403 error without suspension message - should re-raise"""
    # Arrange
    installation_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden - different reason"
    mock_error = requests.exceptions.HTTPError(response=mock_response)
    mock_error.response = mock_response
    mock_requests_post.return_value.raise_for_status.side_effect = mock_error

    # Act
    result = get_installation_access_token(installation_id)

    # Assert - Should return None due to @handle_exceptions decorator
    assert result is None
    mock_requests_post.assert_called_once()
    mock_delete_installation.assert_not_called()


def test_get_installation_access_token_other_http_error(
    mock_get_jwt, mock_create_headers, mock_requests_post, mock_delete_installation
):
    """Test handling of other HTTP errors (e.g., 500) - should be handled by decorator"""
    # Arrange
    installation_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_error = requests.exceptions.HTTPError(response=mock_response)
    mock_error.response = mock_response
    mock_requests_post.return_value.raise_for_status.side_effect = mock_error

    # Act
    result = get_installation_access_token(installation_id)

    # Assert - Should return None due to @handle_exceptions decorator
    assert result is None
    mock_requests_post.assert_called_once()
    mock_delete_installation.assert_not_called()


def test_get_installation_access_token_422_error(
    mock_get_jwt, mock_create_headers, mock_requests_post, mock_delete_installation
):
    """Test handling of 422 Unprocessable Entity error"""
    # Arrange
    installation_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.text = "Unprocessable Entity"
    mock_error = requests.exceptions.HTTPError(response=mock_response)
    mock_error.response = mock_response
    mock_requests_post.return_value.raise_for_status.side_effect = mock_error

    # Act
    result = get_installation_access_token(installation_id)

    # Assert - Should return None due to @handle_exceptions decorator
    assert result is None
    mock_requests_post.assert_called_once()
    mock_delete_installation.assert_not_called()


def test_get_installation_access_token_json_decode_error(
    mock_get_jwt, mock_create_headers, mock_requests_post
):
    """Test handling of JSON decode error in response"""
    # Arrange
    installation_id = 12345
    mock_response = MagicMock()
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
    mock_requests_post.return_value = mock_response

    # Act
    result = get_installation_access_token(installation_id)

    # Assert - Should return None due to @handle_exceptions decorator
    assert result is None
    mock_requests_post.assert_called_once()


def test_get_installation_access_token_key_error(
    mock_get_jwt, mock_create_headers, mock_requests_post
):
    """Test handling of KeyError when token key is missing from response"""
    # Arrange
    installation_id = 12345
    mock_response = MagicMock()
    mock_response.json.return_value = {"access_token": "wrong_key"}  # Missing "token" key
    mock_requests_post.return_value = mock_response

    # Act
    result = get_installation_access_token(installation_id)

    # Assert - Should return None due to @handle_exceptions decorator
    assert result is None
    mock_requests_post.assert_called_once()


def test_get_installation_access_token_get_jwt_exception(mock_create_headers, mock_requests_post):
    """Test handling of exception in get_jwt function"""
    # Arrange
    installation_id = 12345
    
    with patch("services.github.token.get_installation_token.get_jwt") as mock_get_jwt:
        mock_get_jwt.side_effect = Exception("JWT generation failed")

        # Act
        result = get_installation_access_token(installation_id)

        # Assert - Should return None due to @handle_exceptions decorator
        assert result is None
        mock_requests_post.assert_not_called()


def test_get_installation_access_token_create_headers_exception(mock_get_jwt, mock_requests_post):
    """Test handling of exception in create_headers function"""
    # Arrange
    installation_id = 12345
    
    with patch("services.github.token.get_installation_token.create_headers") as mock_create_headers:
        mock_create_headers.side_effect = Exception("Header creation failed")

        # Act
        result = get_installation_access_token(installation_id)

        # Assert - Should return None due to @handle_exceptions decorator
        assert result is None
        mock_requests_post.assert_not_called()


def test_get_installation_access_token_requests_exception(
    mock_get_jwt, mock_create_headers, mock_requests_post
):
    """Test handling of general requests exception"""
    # Arrange
    installation_id = 12345
    mock_requests_post.side_effect = requests.exceptions.RequestException("Network error")

    # Act
    result = get_installation_access_token(installation_id)

    # Assert - Should return None due to @handle_exceptions decorator
    assert result is None
    mock_requests_post.assert_called_once()


def test_get_installation_access_token_http_error_without_response(
    mock_get_jwt, mock_create_headers, mock_requests_post, mock_delete_installation
):
    """Test handling of HTTPError without response object"""
    # Arrange
    installation_id = 12345
    mock_error = requests.exceptions.HTTPError("HTTP Error without response")
    mock_error.response = None
    mock_requests_post.return_value.raise_for_status.side_effect = mock_error

    # Act
    result = get_installation_access_token(installation_id)

    # Assert - Should return None due to @handle_exceptions decorator
    assert result is None
    mock_requests_post.assert_called_once()
    mock_delete_installation.assert_not_called()


def test_get_installation_access_token_rate_limit_403(
    mock_get_jwt, mock_create_headers, mock_requests_post, mock_delete_installation
):
    """Test handling of 403 rate limit error (should be handled by decorator)"""
    # Arrange
    installation_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = "Rate limit exceeded"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Used": "5000",
        "X-RateLimit-Reset": "1640995200"
    }
    mock_error = requests.exceptions.HTTPError(response=mock_response)
    mock_error.response = mock_response
    mock_requests_post.return_value.raise_for_status.side_effect = mock_error

    # Act
    result = get_installation_access_token(installation_id)

    # Assert - Should return None due to @handle_exceptions decorator handling rate limits
    assert result is None
    mock_requests_post.assert_called_once()
    mock_delete_installation.assert_not_called()


def test_get_installation_access_token_rate_limit_429(
    mock_get_jwt, mock_create_headers, mock_requests_post, mock_delete_installation
):
    """Test handling of 429 rate limit error (should be handled by decorator)"""
    # Arrange
    installation_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.text = "Rate limit exceeded"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Used": "5000",
        "X-RateLimit-Reset": "1640995200"
    }
    mock_error = requests.exceptions.HTTPError(response=mock_response)
    mock_error.response = mock_response
    mock_requests_post.return_value.raise_for_status.side_effect = mock_error

    # Act
    result = get_installation_access_token(installation_id)

    # Assert - Should return None due to @handle_exceptions decorator handling rate limits
    assert result is None
    mock_requests_post.assert_called_once()
    mock_delete_installation.assert_not_called()


def test_get_installation_access_token_with_different_installation_ids(
    mock_get_jwt, mock_create_headers, mock_requests_post
):
    """Test function works with different installation IDs"""
    # Test with various installation ID formats
    test_cases = [0, 1, 999999, 12345678]
    
    for installation_id in test_cases:
        # Arrange
        expected_token = f"ghs_token_for_{installation_id}"
        mock_response = MagicMock()
        mock_response.json.return_value = {"token": expected_token}
        mock_requests_post.return_value = mock_response
        mock_requests_post.reset_mock()

        # Act
        result = get_installation_access_token(installation_id)

        # Assert
        assert result == expected_token
        mock_requests_post.assert_called_once_with(
            url=f"{GITHUB_API_URL}/app/installations/{installation_id}/access_tokens",
            headers={"Authorization": "Bearer mock_jwt_token"},
            timeout=TIMEOUT,
        )