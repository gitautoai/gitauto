from unittest.mock import patch, MagicMock
import pytest
from requests.exceptions import HTTPError, RequestException, Timeout

from config import GITHUB_API_URL, TIMEOUT
from services.github.users.get_owner_name import get_owner_name


@pytest.fixture
def mock_response():
    """Fixture to provide a mocked response object."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"login": "test-user"}
    mock_resp.raise_for_status.return_value = None
    return mock_resp


@pytest.fixture
def sample_owner_id():
    """Fixture to provide a sample owner ID."""
    return 123456789


@pytest.fixture
def sample_token():
    """Fixture to provide a sample token."""
    return "ghp_test_token_123456789"


def test_get_owner_name_successful_request(
    mock_response, sample_owner_id, sample_token
):
    """Test successful API request returns the login name."""
    with patch(
        "services.github.users.get_owner_name.requests.get", return_value=mock_response
    ):
        result = get_owner_name(owner_id=sample_owner_id, token=sample_token)
        assert result == "test-user"


def test_get_owner_name_calls_correct_api_endpoint(sample_owner_id, sample_token):
    """Test that the function calls the correct GitHub API endpoint."""
    with patch("services.github.users.get_owner_name.requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"login": "test-user"}
        mock_get.return_value.raise_for_status.return_value = None

        get_owner_name(owner_id=sample_owner_id, token=sample_token)

        expected_url = f"{GITHUB_API_URL}/user/{sample_owner_id}"
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs["url"] == expected_url


def test_get_owner_name_uses_correct_headers(sample_owner_id, sample_token):
    """Test that the function uses correct headers including authorization."""
    with patch("services.github.users.get_owner_name.requests.get") as mock_get, patch(
        "services.github.users.get_owner_name.create_headers"
    ) as mock_create_headers:

        mock_headers = {"Authorization": f"Bearer {sample_token}"}
        mock_create_headers.return_value = mock_headers
        mock_get.return_value.json.return_value = {"login": "test-user"}
        mock_get.return_value.raise_for_status.return_value = None

        get_owner_name(owner_id=sample_owner_id, token=sample_token)

        mock_create_headers.assert_called_once_with(token=sample_token)
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs["headers"] == mock_headers


def test_get_owner_name_uses_correct_timeout(sample_owner_id, sample_token):
    """Test that the function uses the configured timeout."""
    with patch("services.github.users.get_owner_name.requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"login": "test-user"}
        mock_get.return_value.raise_for_status.return_value = None

        get_owner_name(owner_id=sample_owner_id, token=sample_token)

        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs["timeout"] == TIMEOUT


def test_get_owner_name_calls_raise_for_status(
    mock_response, sample_owner_id, sample_token
):
    """Test that the function calls raise_for_status on the response."""
    with patch(
        "services.github.users.get_owner_name.requests.get", return_value=mock_response
    ):
        get_owner_name(owner_id=sample_owner_id, token=sample_token)
        mock_response.raise_for_status.assert_called_once()


def test_get_owner_name_extracts_login_from_response(sample_owner_id, sample_token):
    """Test that the function extracts the login field from the JSON response."""
    expected_login = "github-user-123"
    mock_response = MagicMock()
    mock_response.json.return_value = {"login": expected_login, "id": sample_owner_id}
    mock_response.raise_for_status.return_value = None

    with patch(
        "services.github.users.get_owner_name.requests.get", return_value=mock_response
    ):
        result = get_owner_name(owner_id=sample_owner_id, token=sample_token)
        assert result == expected_login


def test_get_owner_name_with_different_owner_ids():
    """Test the function with different owner ID values."""
    test_cases = [
        (1, "user1"),
        (999999999, "user999999999"),
        (123456789, "organization-name"),
    ]

    for owner_id, expected_login in test_cases:
        mock_response = MagicMock()
        mock_response.json.return_value = {"login": expected_login}
        mock_response.raise_for_status.return_value = None

        with patch(
            "services.github.users.get_owner_name.requests.get",
            return_value=mock_response,
        ):
            result = get_owner_name(owner_id=owner_id, token="test-token")
            assert result == expected_login


def test_get_owner_name_with_different_tokens():
    """Test the function with different token formats."""
    test_tokens = [
        "ghp_1234567890abcdef",
        "ghs_1234567890abcdef",
        "github_pat_1234567890abcdef",
        "token_with_special_chars!@#$%",
    ]

    for token in test_tokens:
        mock_response = MagicMock()
        mock_response.json.return_value = {"login": "test-user"}
        mock_response.raise_for_status.return_value = None

        with patch(
            "services.github.users.get_owner_name.requests.get",
            return_value=mock_response,
        ), patch(
            "services.github.users.get_owner_name.create_headers"
        ) as mock_create_headers:

            mock_create_headers.return_value = {"Authorization": f"Bearer {token}"}
            result = get_owner_name(owner_id=123456, token=token)

            assert result == "test-user"
            mock_create_headers.assert_called_with(token=token)


def test_get_owner_name_http_error_returns_none(sample_owner_id, sample_token):
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
        "services.github.users.get_owner_name.requests.get", return_value=mock_response
    ):
        result = get_owner_name(owner_id=sample_owner_id, token=sample_token)
        assert result is None


def test_get_owner_name_request_exception_returns_none(sample_owner_id, sample_token):
    """Test that request exceptions are handled and return None due to decorator."""
    with patch(
        "services.github.users.get_owner_name.requests.get",
        side_effect=RequestException("Network error"),
    ):
        result = get_owner_name(owner_id=sample_owner_id, token=sample_token)
        assert result is None


def test_get_owner_name_timeout_returns_none(sample_owner_id, sample_token):
    """Test that timeout exceptions are handled and return None due to decorator."""
    with patch(
        "services.github.users.get_owner_name.requests.get",
        side_effect=Timeout("Request timed out"),
    ):
        result = get_owner_name(owner_id=sample_owner_id, token=sample_token)
        assert result is None


def test_get_owner_name_json_decode_error_returns_none(sample_owner_id, sample_token):
    """Test that JSON decode errors are handled and return None due to decorator."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Invalid JSON")

    with patch(
        "services.github.users.get_owner_name.requests.get", return_value=mock_response
    ):
        result = get_owner_name(owner_id=sample_owner_id, token=sample_token)
        assert result is None


def test_get_owner_name_missing_login_key_returns_none(sample_owner_id, sample_token):
    """Test that missing login key in response is handled and returns None due to decorator."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "id": sample_owner_id,
        "name": "Test User",
    }  # Missing "login" key

    with patch(
        "services.github.users.get_owner_name.requests.get", return_value=mock_response
    ):
        result = get_owner_name(owner_id=sample_owner_id, token=sample_token)
        assert result is None


def test_get_owner_name_empty_response_returns_none(sample_owner_id, sample_token):
    """Test that empty JSON response is handled and returns None due to decorator."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {}

    with patch(
        "services.github.users.get_owner_name.requests.get", return_value=mock_response
    ):
        result = get_owner_name(owner_id=sample_owner_id, token=sample_token)
        assert result is None


def test_get_owner_name_null_login_value_returns_none(sample_owner_id, sample_token):
    """Test that null login value in response returns None."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"login": None, "id": sample_owner_id}

    with patch(
        "services.github.users.get_owner_name.requests.get", return_value=mock_response
    ):
        result = get_owner_name(owner_id=sample_owner_id, token=sample_token)
        assert result is None


def test_get_owner_name_with_complete_github_response(sample_owner_id, sample_token):
    """Test with a complete GitHub API response structure."""
    complete_response = {
        "login": "octocat",
        "id": sample_owner_id,
        "node_id": "MDQ6VXNlcjE=",
        "avatar_url": "https://github.com/images/error/octocat_happy.gif",
        "gravatar_id": "",
        "url": "https://api.github.com/users/octocat",
        "html_url": "https://github.com/octocat",
        "type": "User",
        "site_admin": False,
        "name": "monalisa octocat",
        "company": "GitHub",
        "blog": "https://github.com/blog",
        "location": "San Francisco",
        "email": "octocat@github.com",
        "hireable": False,
        "bio": "There once was...",
        "public_repos": 2,
        "public_gists": 1,
        "followers": 20,
        "following": 0,
        "created_at": "2008-01-14T04:33:35Z",
        "updated_at": "2008-01-14T04:33:35Z",
    }

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = complete_response

    with patch(
        "services.github.users.get_owner_name.requests.get", return_value=mock_response
    ):
        result = get_owner_name(owner_id=sample_owner_id, token=sample_token)
        assert result == "octocat"


@pytest.mark.parametrize(
    "owner_id,expected_login",
    [
        (1, "mojombo"),
        (2, "defunkt"),
        (3, "pjhyett"),
        (583231, "octocat"),
        (9919, "github"),
    ],
)
def test_get_owner_name_with_various_owner_ids(owner_id, expected_login, sample_token):
    """Test the function with various owner IDs using parametrize."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"login": expected_login, "id": owner_id}

    with patch(
        "services.github.users.get_owner_name.requests.get", return_value=mock_response
    ):
        result = get_owner_name(owner_id=owner_id, token=sample_token)
        assert result == expected_login


def test_get_owner_name_decorator_behavior(sample_owner_id, sample_token):
    """Test that the handle_exceptions decorator is properly applied."""
    # Test that the function has the decorator applied by checking it returns None on exception
    with patch(
        "services.github.users.get_owner_name.requests.get",
        side_effect=Exception("Unexpected error"),
    ):
        result = get_owner_name(owner_id=sample_owner_id, token=sample_token)
        assert result is None


def test_get_owner_name_with_special_login_characters(sample_owner_id, sample_token):
    """Test the function with login names containing special characters."""
    special_logins = [
        "user-with-dashes",
        "user_with_underscores",
        "user123",
        "User-Name-123",
        "a",  # Single character
        "a" * 39,  # Maximum GitHub username length
    ]

    for login in special_logins:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"login": login, "id": sample_owner_id}

        with patch(
            "services.github.users.get_owner_name.requests.get",
            return_value=mock_response,
        ):
            result = get_owner_name(owner_id=sample_owner_id, token=sample_token)
            assert result == login
