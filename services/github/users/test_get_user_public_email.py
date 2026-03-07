"""Unit tests for get_user_public_info function.

Related Documentation:
https://docs.github.com/en/rest/users/users?apiVersion=2022-11-28#get-a-user
"""

from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import HTTPError, RequestException, Timeout

from config import GITHUB_API_URL, TIMEOUT
from services.github.users.get_user_public_email import (
    UserPublicInfo,
    get_user_public_info,
)

DEFAULT_RETURN = UserPublicInfo(email=None, display_name="")


@pytest.fixture
def mock_response():
    """Fixture to provide a mocked response object."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"email": "test@example.com", "name": "Test User"}
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


def test_get_user_public_info_successful_request(
    mock_response, sample_username, sample_token
):
    """Test successful API request returns email and display_name."""
    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_info(
            username=sample_username,
            token=sample_token,
        )
        assert result.email == "test@example.com"
        assert result.display_name == "Test User"


def test_get_user_public_info_bot_user_skips_api_call(sample_token):
    """Test that bot usernames skip the API call (bots have name=null, email=null)."""
    with patch("services.github.users.get_user_public_email.requests.get") as mock_get:
        result = get_user_public_info(
            username="github-actions[bot]",
            token=sample_token,
        )
        assert result == DEFAULT_RETURN
        mock_get.assert_not_called()


def test_get_user_public_info_calls_correct_api_endpoint(sample_username, sample_token):
    """Test that the function calls the correct GitHub API endpoint."""
    with patch("services.github.users.get_user_public_email.requests.get") as mock_get:
        mock_get.return_value.json.return_value = {
            "email": "test@example.com",
            "name": "Test User",
        }
        mock_get.return_value.raise_for_status.return_value = None

        get_user_public_info(
            username=sample_username,
            token=sample_token,
        )

        expected_url = f"{GITHUB_API_URL}/users/{sample_username}"
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs["url"] == expected_url


def test_get_user_public_info_uses_correct_headers(sample_username, sample_token):
    """Test that the function uses correct headers including authorization."""
    with patch(
        "services.github.users.get_user_public_email.requests.get"
    ) as mock_get, patch(
        "services.github.users.get_user_public_email.create_headers"
    ) as mock_create_headers:
        mock_headers = {"Authorization": f"Bearer {sample_token}"}
        mock_create_headers.return_value = mock_headers
        mock_get.return_value.json.return_value = {
            "email": "test@example.com",
            "name": "Test User",
        }
        mock_get.return_value.raise_for_status.return_value = None

        get_user_public_info(
            username=sample_username,
            token=sample_token,
        )

        mock_create_headers.assert_called_once_with(token=sample_token)
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs["headers"] == mock_headers


def test_get_user_public_info_uses_correct_timeout(sample_username, sample_token):
    """Test that the function uses the configured timeout."""
    with patch("services.github.users.get_user_public_email.requests.get") as mock_get:
        mock_get.return_value.json.return_value = {
            "email": "test@example.com",
            "name": "Test User",
        }
        mock_get.return_value.raise_for_status.return_value = None

        get_user_public_info(
            username=sample_username,
            token=sample_token,
        )

        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs["timeout"] == TIMEOUT


def test_get_user_public_info_calls_raise_for_status(
    mock_response, sample_username, sample_token
):
    """Test that the function calls raise_for_status on the response."""
    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        get_user_public_info(
            username=sample_username,
            token=sample_token,
        )
        mock_response.raise_for_status.assert_called_once()


def test_get_user_public_info_extracts_email_and_name_from_response(
    sample_username, sample_token
):
    """Test that the function extracts email and name from the JSON response."""
    expected_email = "user@example.com"
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "email": expected_email,
        "login": sample_username,
        "name": "Some User",
    }
    mock_response.raise_for_status.return_value = None

    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_info(
            username=sample_username,
            token=sample_token,
        )
        assert result.email == expected_email
        assert result.display_name == "Some User"


def test_get_user_public_info_with_different_usernames():
    """Test the function with different username values."""
    test_cases = [
        ("user1", "user1@example.com", "User One"),
        ("organization-name", "org@example.com", "Org Name"),
        ("user-with-dashes", "dashes@example.com", "Dash User"),
        ("user_with_underscores", "underscores@example.com", "Underscore User"),
    ]

    for username, expected_email, expected_name in test_cases:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "email": expected_email,
            "name": expected_name,
        }
        mock_response.raise_for_status.return_value = None

        with patch(
            "services.github.users.get_user_public_email.requests.get",
            return_value=mock_response,
        ):
            result = get_user_public_info(
                username=username,
                token="test-token",
            )
            assert result.email == expected_email
            assert result.display_name == expected_name


def test_get_user_public_info_with_different_tokens():
    """Test the function with different token formats."""
    test_tokens = [
        "ghp_1234567890abcdef",
        "ghs_1234567890abcdef",
        "github_pat_1234567890abcdef",
    ]

    for token in test_tokens:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "email": "test@example.com",
            "name": "Test User",
        }
        mock_response.raise_for_status.return_value = None

        with patch(
            "services.github.users.get_user_public_email.requests.get",
            return_value=mock_response,
        ), patch(
            "services.github.users.get_user_public_email.create_headers"
        ) as mock_create_headers:
            mock_create_headers.return_value = {"Authorization": f"Bearer {token}"}
            result = get_user_public_info(username="testuser", token=token)

            assert result.email == "test@example.com"
            assert result.display_name == "Test User"
            mock_create_headers.assert_called_with(token=token)


def test_get_user_public_info_404_returns_default_without_raising(sample_token):
    """Test that 404 (e.g. 'Copilot' user) returns default without hitting raise_for_status."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_info(username="Copilot", token=sample_token)
        assert result == DEFAULT_RETURN
        mock_response.raise_for_status.assert_not_called()


def test_get_user_public_info_http_error_returns_default(sample_username, sample_token):
    """Test that non-404 HTTP errors are handled and return default UserPublicInfo due to decorator."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    http_error = HTTPError("500 Server Error")
    error_response = MagicMock()
    error_response.status_code = 500
    error_response.reason = "Server Error"
    error_response.text = "Internal Server Error"
    http_error.response = error_response

    mock_response.raise_for_status.side_effect = http_error
    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_info(
            username=sample_username,
            token=sample_token,
        )
        assert result == DEFAULT_RETURN


def test_get_user_public_info_request_exception_returns_default(
    sample_username, sample_token
):
    """Test that request exceptions are handled and return default UserPublicInfo due to decorator."""
    with patch(
        "services.github.users.get_user_public_email.requests.get",
        side_effect=RequestException("Network error"),
    ):
        result = get_user_public_info(
            username=sample_username,
            token=sample_token,
        )
        assert result == DEFAULT_RETURN


def test_get_user_public_info_timeout_returns_default(sample_username, sample_token):
    """Test that timeout exceptions are handled and return default UserPublicInfo due to decorator."""
    with patch(
        "services.github.users.get_user_public_email.requests.get",
        side_effect=Timeout("Request timed out"),
    ):
        result = get_user_public_info(
            username=sample_username,
            token=sample_token,
        )
        assert result == DEFAULT_RETURN


def test_get_user_public_info_json_decode_error_returns_default(
    sample_username, sample_token
):
    """Test that JSON decode errors are handled and return default UserPublicInfo due to decorator."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Invalid JSON")

    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_info(
            username=sample_username,
            token=sample_token,
        )
        assert result == DEFAULT_RETURN


def test_get_user_public_info_missing_email_key_returns_none_email(
    sample_username, sample_token
):
    """Test that missing email key in response returns None for email."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "login": sample_username,
        "name": "Test User",
    }

    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_info(
            username=sample_username,
            token=sample_token,
        )
        assert result.email is None
        assert result.display_name == "Test User"


def test_get_user_public_info_null_email_value_returns_none_email(
    sample_username, sample_token
):
    """Test that null email value in response returns None for email."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "login": sample_username,
        "email": None,
        "name": "Test User",
    }

    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_info(
            username=sample_username,
            token=sample_token,
        )
        assert result.email is None
        assert result.display_name == "Test User"


def test_get_user_public_info_missing_name_key_returns_empty_display_name(
    sample_username, sample_token
):
    """Test that missing name key in response returns empty string for display_name."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "login": sample_username,
        "email": "test@example.com",
    }

    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_info(
            username=sample_username,
            token=sample_token,
        )
        assert result.email == "test@example.com"
        assert result.display_name == ""


def test_get_user_public_info_title_cases_lowercase_name(sample_username, sample_token):
    """Test that all-lowercase names are title-cased (e.g., 'wes nishio' -> 'Wes Nishio')."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "email": "wes@example.com",
        "name": "wes nishio",
    }

    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_info(
            username=sample_username,
            token=sample_token,
        )
        assert result.display_name == "Wes Nishio"


def test_get_user_public_info_title_cases_uppercase_name(sample_username, sample_token):
    """Test that all-uppercase names are title-cased (e.g., 'HIROSHI' -> 'Hiroshi')."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "email": "hiroshi@example.com",
        "name": "HIROSHI",
    }

    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_info(
            username=sample_username,
            token=sample_token,
        )
        assert result.display_name == "Hiroshi"


def test_get_user_public_info_title_cases_already_correct_name(
    sample_username, sample_token
):
    """Test that already title-cased names stay the same (e.g., 'Wes Nishio' stays 'Wes Nishio')."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "email": "wes@example.com",
        "name": "Wes Nishio",
    }

    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_info(
            username=sample_username,
            token=sample_token,
        )
        assert result.display_name == "Wes Nishio"


def test_get_user_public_info_title_cases_mixed_case_name(
    sample_username, sample_token
):
    """Test that mixed-case names like 'Naman joshi' are title-cased to 'Naman Joshi'."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "email": "naman@example.com",
        "name": "Naman joshi",
    }

    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_info(
            username=sample_username,
            token=sample_token,
        )
        assert result.display_name == "Naman Joshi"


def test_get_user_public_info_strips_unicode_bold(sample_username, sample_token):
    """Test that Unicode bold characters are normalized to plain ASCII and title-cased."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "email": "one@example.com",
        "name": "\U0001d40e\U0001d427\U0001d41e \U0001d405\U0001d422\U0001d427\U0001d41e \U0001d412\U0001d42d\U0001d41a\U0001d42b\U0001d42c\U0001d42d\U0001d42e\U0001d41f\U0001d41f",
    }

    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_info(
            username=sample_username,
            token=sample_token,
        )
        assert result.display_name == "One Fine Starstuff"


def test_get_user_public_info_replaces_dots_with_spaces(sample_username, sample_token):
    """Test that dots are replaced with spaces (e.g., 'Yang.qu' -> 'Yang Qu')."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "email": "yang@example.com",
        "name": "Yang.qu",
    }

    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_info(
            username=sample_username,
            token=sample_token,
        )
        assert result.display_name == "Yang Qu"


def test_get_user_public_info_preserves_accented_latin(sample_username, sample_token):
    """Test that accented Latin characters are preserved and title-cased."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "email": "andre@example.com",
        "name": "andré goulart",
    }

    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_info(
            username=sample_username,
            token=sample_token,
        )
        assert result.display_name == "André Goulart"


def test_get_user_public_info_preserves_cjk_characters(sample_username, sample_token):
    """Test that CJK characters pass through unchanged."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "email": "user@example.com",
        "name": "高森松太郎",
    }

    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_info(
            username=sample_username,
            token=sample_token,
        )
        assert result.display_name == "高森松太郎"


def test_get_user_public_info_empty_name_returns_empty_display_name(
    sample_username, sample_token
):
    """Test that empty string name returns empty display_name."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "email": "test@example.com",
        "name": "",
    }

    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_info(
            username=sample_username,
            token=sample_token,
        )
        assert result.display_name == ""


def test_get_user_public_info_null_name_returns_empty_display_name(
    sample_username, sample_token
):
    """Test that null name value returns empty display_name (via 'or' fallback)."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "email": "test@example.com",
        "name": None,
    }

    with patch(
        "services.github.users.get_user_public_email.requests.get",
        return_value=mock_response,
    ):
        result = get_user_public_info(
            username=sample_username,
            token=sample_token,
        )
        assert result.display_name == ""
