import inspect
from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError, JSONDecodeError, Timeout
from requests.exceptions import ConnectionError as RequestsConnectionError

from services.github.issues.is_issue_open import is_issue_open


def test_is_issue_open_with_open_issue(test_token):
    """Test is_issue_open returns True for an open issue."""
    issue_url = "https://github.com/owner/repo/issues/123"

    with patch("services.github.issues.is_issue_open.requests.get") as mock_get, patch(
        "services.github.issues.is_issue_open.create_headers"
    ) as mock_create_headers:

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"state": "open"}
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}

        result = is_issue_open(issue_url, test_token)

        assert result is True
        mock_get.assert_called_once()
        mock_response.json.assert_called_once()


def test_is_issue_open_with_closed_issue(test_token):
    """Test is_issue_open returns False for a closed issue."""
    issue_url = "https://github.com/owner/repo/issues/456"

    with patch("services.github.issues.is_issue_open.requests.get") as mock_get, patch(
        "services.github.issues.is_issue_open.create_headers"
    ) as mock_create_headers:

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"state": "closed"}
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}

        result = is_issue_open(issue_url, test_token)

        assert result is False
        mock_get.assert_called_once()
        mock_response.json.assert_called_once()


def test_is_issue_open_with_empty_url(test_token):
    result = is_issue_open("", test_token)
    assert result is False


def test_is_issue_open_with_invalid_url_format(test_token):
    """Test is_issue_open returns True for invalid URL formats (assumes open to avoid duplicates)."""
    invalid_urls = [
        "https://github.com/owner/repo",  # Missing issues part
        "https://github.com/owner",  # Too short
        "https://github.com/owner/repo/pulls/123",  # Not an issue URL
        "https://example.com/owner/repo/issues/123",  # Not GitHub
        "not-a-url-at-all",  # Invalid URL
    ]

    for url in invalid_urls:
        result = is_issue_open(url, test_token)
        assert result is True, f"Expected True for invalid URL: {url}"


def test_is_issue_open_api_url_construction(test_token):
    """Test that the correct GitHub API URL is constructed."""
    issue_url = "https://github.com/test-owner/test-repo/issues/789"

    with patch("services.github.issues.is_issue_open.requests.get") as mock_get, patch(
        "services.github.issues.is_issue_open.create_headers"
    ) as mock_create_headers, patch(
        "services.github.issues.is_issue_open.GITHUB_API_URL", "https://api.github.com"
    ):

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"state": "open"}
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}

        is_issue_open(issue_url, test_token)

        expected_api_url = (
            "https://api.github.com/repos/test-owner/test-repo/issues/789"
        )
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args.kwargs["url"] == expected_api_url


def test_is_issue_open_headers_creation():
    """Test that correct headers are created and passed."""
    issue_url = "https://github.com/owner/repo/issues/123"
    test_token = "test-token-123"

    with patch("services.github.issues.is_issue_open.requests.get") as mock_get, patch(
        "services.github.issues.is_issue_open.create_headers"
    ) as mock_create_headers:

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"state": "open"}
        mock_get.return_value = mock_response
        expected_headers = {"Authorization": f"Bearer {test_token}"}
        mock_create_headers.return_value = expected_headers

        is_issue_open(issue_url, test_token)

        mock_create_headers.assert_called_once_with(token=test_token)
        call_args = mock_get.call_args
        assert call_args.kwargs["headers"] == expected_headers


def test_is_issue_open_timeout_parameter(test_token):
    """Test that timeout parameter is correctly passed."""
    issue_url = "https://github.com/owner/repo/issues/123"

    with patch("services.github.issues.is_issue_open.requests.get") as mock_get, patch(
        "services.github.issues.is_issue_open.create_headers"
    ) as mock_create_headers, patch("services.github.issues.is_issue_open.TIMEOUT", 60):

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"state": "open"}
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}

        is_issue_open(issue_url, test_token)

        call_args = mock_get.call_args
        assert call_args.kwargs["timeout"] == 60


def test_is_issue_open_non_200_status_code(test_token):
    """Test is_issue_open returns True for non-200 status codes (assumes open to avoid duplicates)."""
    issue_url = "https://github.com/owner/repo/issues/123"

    status_codes = [404, 403, 500, 502, 503]

    for status_code in status_codes:
        with patch(
            "services.github.issues.is_issue_open.requests.get"
        ) as mock_get, patch(
            "services.github.issues.is_issue_open.create_headers"
        ) as mock_create_headers:

            mock_response = MagicMock()
            mock_response.status_code = status_code
            mock_get.return_value = mock_response
            mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}

            result = is_issue_open(issue_url, test_token)

            assert result is True, f"Expected True for status code {status_code}"
            mock_get.assert_called_once()
            # json() should not be called for non-200 status codes
            mock_response.json.assert_not_called()


def test_is_issue_open_missing_state_in_response(test_token):
    """Test is_issue_open returns False when state is missing from response."""
    issue_url = "https://github.com/owner/repo/issues/123"

    with patch("services.github.issues.is_issue_open.requests.get") as mock_get, patch(
        "services.github.issues.is_issue_open.create_headers"
    ) as mock_create_headers:

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Missing 'state' key
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}

        result = is_issue_open(issue_url, test_token)

        assert result is False
        mock_get.assert_called_once()
        mock_response.json.assert_called_once()


def test_is_issue_open_state_not_open(test_token):
    """Test is_issue_open returns False for states other than 'open'."""
    issue_url = "https://github.com/owner/repo/issues/123"

    non_open_states = ["closed", "draft", "merged", "unknown", None, ""]

    for state in non_open_states:
        with patch(
            "services.github.issues.is_issue_open.requests.get"
        ) as mock_get, patch(
            "services.github.issues.is_issue_open.create_headers"
        ) as mock_create_headers:

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"state": state}
            mock_get.return_value = mock_response
            mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}

            result = is_issue_open(issue_url, test_token)

            assert result is False, f"Expected False for state: {state}"
            mock_get.assert_called_once()
            mock_response.json.assert_called_once()


def test_is_issue_open_http_error(test_token):
    """Test is_issue_open returns True when HTTPError occurs (assumes open to avoid duplicates)."""
    issue_url = "https://github.com/owner/repo/issues/123"

    with patch("services.github.issues.is_issue_open.requests.get") as mock_get, patch(
        "services.github.issues.is_issue_open.create_headers"
    ) as mock_create_headers:

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Repository not found"
        mock_response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Used": "1",
        }

        http_error = HTTPError("404 Client Error")
        http_error.response = mock_response
        mock_get.side_effect = http_error
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}

        result = is_issue_open(issue_url, test_token)

        assert result is True
        mock_get.assert_called_once()


def test_is_issue_open_json_decode_error(test_token):
    """Test is_issue_open returns True when JSONDecodeError occurs."""
    issue_url = "https://github.com/owner/repo/issues/123"

    with patch("services.github.issues.is_issue_open.requests.get") as mock_get, patch(
        "services.github.issues.is_issue_open.create_headers"
    ) as mock_create_headers:

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "{", 0)
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}

        result = is_issue_open(issue_url, test_token)

        assert result is True
        mock_get.assert_called_once()
        mock_response.json.assert_called_once()


def test_is_issue_open_timeout_error(test_token):
    """Test is_issue_open returns True when Timeout occurs."""
    issue_url = "https://github.com/owner/repo/issues/123"

    with patch("services.github.issues.is_issue_open.requests.get") as mock_get, patch(
        "services.github.issues.is_issue_open.create_headers"
    ) as mock_create_headers:

        mock_get.side_effect = Timeout("Request timed out")
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}

        result = is_issue_open(issue_url, test_token)

        assert result is True
        mock_get.assert_called_once()


def test_is_issue_open_connection_error(test_token):
    """Test is_issue_open returns True when ConnectionError occurs."""
    issue_url = "https://github.com/owner/repo/issues/123"

    with patch("services.github.issues.is_issue_open.requests.get") as mock_get, patch(
        "services.github.issues.is_issue_open.create_headers"
    ) as mock_create_headers:

        mock_get.side_effect = RequestsConnectionError("Connection failed")
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}

        result = is_issue_open(issue_url, test_token)

        assert result is True
        mock_get.assert_called_once()


def test_is_issue_open_key_error(test_token):
    """Test is_issue_open returns True when KeyError occurs."""
    issue_url = "https://github.com/owner/repo/issues/123"

    with patch("services.github.issues.is_issue_open.requests.get") as mock_get, patch(
        "services.github.issues.is_issue_open.create_headers"
    ) as mock_create_headers:

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = KeyError("Missing key")
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}

        result = is_issue_open(issue_url, test_token)

        assert result is True
        mock_get.assert_called_once()
        mock_response.json.assert_called_once()


def test_is_issue_open_url_parsing_edge_cases(test_token):
    """Test URL parsing with various edge cases."""
    # URLs that will make API calls (have proper structure)
    api_call_urls = [
        "https://github.com/owner/repo/issues/123/",  # Trailing slash
        "https://github.com/owner/repo/issues/123#comment",  # With fragment
        "https://github.com/owner/repo/issues/123?tab=timeline",  # With query params
        "https://github.com/owner-with-dash/repo_with_underscore/issues/999",  # Special chars in names
        "https://github.com/a/b/issues/1",  # Minimal valid case
        "https://github.com/owner/repo/issues/",  # Missing issue number but still makes API call
    ]

    # URLs that will NOT make API calls (return True early)
    no_api_call_urls = [
        "https://github.com/owner/repo/issues",  # Missing slash and number - invalid format
    ]

    # Test URLs that make API calls
    for url in api_call_urls:
        with patch(
            "services.github.issues.is_issue_open.requests.get"
        ) as mock_get, patch(
            "services.github.issues.is_issue_open.create_headers"
        ) as mock_create_headers:

            # Mock successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"state": "open"}
            mock_get.return_value = mock_response
            mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}

            result = is_issue_open(url, test_token)
            assert result is True, f"Expected True for URL that makes API call: {url}"
            mock_get.assert_called_once()

    # Test URLs that do NOT make API calls
    for url in no_api_call_urls:
        with patch(
            "services.github.issues.is_issue_open.requests.get"
        ) as mock_get, patch(
            "services.github.issues.is_issue_open.create_headers"
        ) as mock_create_headers:

            result = is_issue_open(url, test_token)
            assert (
                result is True
            ), f"Expected True for URL that doesn't make API call: {url}"
            mock_get.assert_not_called()


def test_is_issue_open_decorator_applied():
    """Test that the @handle_exceptions decorator is properly applied."""
    assert hasattr(is_issue_open, "__wrapped__")


def test_is_issue_open_function_signature():
    """Test that the function has the correct signature."""
    sig = inspect.signature(is_issue_open)
    params = list(sig.parameters.keys())

    assert params == ["issue_url", "token"]
    assert sig.parameters["issue_url"].annotation is str
    assert sig.parameters["token"].annotation is str
    assert sig.return_annotation is bool
