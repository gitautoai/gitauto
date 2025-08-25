"""Unit tests for get_user_public_email function.

Related Documentation:
https://docs.github.com/en/rest/users/users?apiVersion=2022-11-28#get-a-user
"""

from unittest.mock import patch, MagicMock
import pytest
from requests.exceptions import HTTPError, RequestException, Timeout

from config import GITHUB_API_URL, TIMEOUT
from services.github.users.get_user_public_email import get_user_public_email


@pytest.fixture
def mock_response():
    """Fixture to provide a mocked response object."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"email": "test@example.com"}
    mock_resp.raise_for_status.return_value = None
    return mock_resp


@pytest.fixture
def sample_username():
    """Fixture to provide a sample username."""
    return "testuser"


@pytest.fixture
def sample_token():
    """Fixture to provide a sample token."""
    return "ghp_test_token_123456789"


def test_get_user_public_email_successful_request(
    mock_response, sample_username, sample_token
):
    """Test successful API request returns the email."""
    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_email(username=sample_username, token=sample_token)
        assert result == "test@example.com"


def test_get_user_public_email_bot_user_returns_none(sample_token):
    """Test that bot usernames return None without making API calls."""
    with patch("services.github.users.get_user_public_email.requests.get") as mock_get:
        result = get_user_public_email(
            username="github-actions[bot]", token=sample_token
        )
        assert result is None
        mock_get.assert_not_called()


def test_get_user_public_email_calls_correct_api_endpoint(
    sample_username, sample_token
):
    """Test that the function calls the correct GitHub API endpoint."""
    with patch("services.github.users.get_user_public_email.requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"email": "test@example.com"}
        mock_get.return_value.raise_for_status.return_value = None

        get_user_public_email(username=sample_username, token=sample_token)

        expected_url = f"{GITHUB_API_URL}/users/{sample_username}"
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs["url"] == expected_url


def test_get_user_public_email_uses_correct_headers(sample_username, sample_token):
    """Test that the function uses correct headers including authorization."""
    with patch(
        "services.github.users.get_user_public_email.requests.get"
    ) as mock_get, patch(
        "services.github.users.get_user_public_email.create_headers"
    ) as mock_create_headers:

        mock_headers = {"Authorization": f"Bearer {sample_token}"}
        mock_create_headers.return_value = mock_headers
        mock_get.return_value.json.return_value = {"email": "test@example.com"}
        mock_get.return_value.raise_for_status.return_value = None

        get_user_public_email(username=sample_username, token=sample_token)

        mock_create_headers.assert_called_once_with(token=sample_token)
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs["headers"] == mock_headers


def test_get_user_public_email_uses_correct_timeout(sample_username, sample_token):
    """Test that the function uses the configured timeout."""
    with patch("services.github.users.get_user_public_email.requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"email": "test@example.com"}
        mock_get.return_value.raise_for_status.return_value = None

        get_user_public_email(username=sample_username, token=sample_token)

        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs["timeout"] == TIMEOUT


def test_get_user_public_email_calls_raise_for_status(
    mock_response, sample_username, sample_token
):
    """Test that the function calls raise_for_status on the response."""
    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        get_user_public_email(username=sample_username, token=sample_token)
        mock_response.raise_for_status.assert_called_once()


def test_get_user_public_email_extracts_email_from_response(
    sample_username, sample_token
):
    """Test that the function extracts the email field from the JSON response."""
    expected_email = "user@example.com"
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "email": expected_email,
        "login": sample_username,
    }
    mock_response.raise_for_status.return_value = None

    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_email(username=sample_username, token=sample_token)
        assert result == expected_email


def test_get_user_public_email_with_different_usernames():
    """Test the function with different username values."""
    test_cases = [
        ("user1", "user1@example.com"),
        ("organization-name", "org@example.com"),
        ("user-with-dashes", "dashes@example.com"),
        ("user_with_underscores", "underscores@example.com"),
    ]

    for username, expected_email in test_cases:
        mock_response = MagicMock()
        mock_response.json.return_value = {"email": expected_email}
        mock_response.raise_for_status.return_value = None

        with patch(
            "services.github.users.get_user_public_email.requests.get",
            return_value=mock_response,
        ):
            result = get_user_public_email(username=username, token="test-token")
            assert result == expected_email


def test_get_user_public_email_with_different_tokens():
    """Test the function with different token formats."""
    test_tokens = [
        "ghp_1234567890abcdef",
        "ghs_1234567890abcdef",
        "github_pat_1234567890abcdef",
    ]

    for token in test_tokens:
        mock_response = MagicMock()
        mock_response.json.return_value = {"email": "test@example.com"}
        mock_response.raise_for_status.return_value = None

        with patch(
            "services.github.users.get_user_public_email.requests.get",
            return_value=mock_response,
        ), patch(
            "services.github.users.get_user_public_email.create_headers"
        ) as mock_create_headers:

            mock_create_headers.return_value = {"Authorization": f"Bearer {token}"}
            result = get_user_public_email(username="testuser", token=token)

            assert result == "test@example.com"
            mock_create_headers.assert_called_with(token=token)


def test_get_user_public_email_http_error_returns_none(sample_username, sample_token):
    """Test that HTTP errors are handled and return None due to decorator."""
    mock_response = MagicMock()
    # Create a proper HTTPError with a response object
    http_error = HTTPError("404 Not Found")
    error_response = MagicMock()
    error_response.status_code = 404
    error_response.reason = "Not Found"
    error_response.text = "User not found"
    http_error.response = error_response

    mock_response.raise_for_status.side_effect = http_error
    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_email(username=sample_username, token=sample_token)
        assert result is None


def test_get_user_public_email_request_exception_returns_none(
    sample_username, sample_token
):
    """Test that request exceptions are handled and return None due to decorator."""
    with patch(
        "services.github.users.get_user_public_email.requests.get",
        side_effect=RequestException("Network error"),
    ):
        result = get_user_public_email(username=sample_username, token=sample_token)
        assert result is None


def test_get_user_public_email_timeout_returns_none(sample_username, sample_token):
    """Test that timeout exceptions are handled and return None due to decorator."""
    with patch(
        "services.github.users.get_user_public_email.requests.get",
        side_effect=Timeout("Request timed out"),
    ):
        result = get_user_public_email(username=sample_username, token=sample_token)
        assert result is None


def test_get_user_public_email_json_decode_error_returns_none(
    sample_username, sample_token
):
    """Test that JSON decode errors are handled and return None due to decorator."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Invalid JSON")

    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_email(username=sample_username, token=sample_token)
        assert result is None


def test_get_user_public_email_missing_email_key_returns_none(
    sample_username, sample_token
):
    """Test that missing email key in response returns None."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "login": sample_username,
        "name": "Test User",
    }  # Missing "email" key

    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_email(username=sample_username, token=sample_token)
        assert result is None


def test_get_user_public_email_null_email_value_returns_none(
    sample_username, sample_token
):
    """Test that null email value in response returns None."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"login": sample_username, "email": None}

    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_email(username=sample_username, token=sample_token)
        assert result is None
