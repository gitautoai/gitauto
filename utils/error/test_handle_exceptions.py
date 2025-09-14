from unittest.mock import patch, MagicMock
import pytest
import requests
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def mock_function_for_testing():
    """Mock function to test handle_exceptions decorator."""
    response = requests.get("https://api.github.com/test", timeout=120)
    response.raise_for_status()
    return response.json()


@handle_exceptions(default_return_value="default", raise_on_error=False)
def mock_function_with_custom_default():
    """Mock function to test custom default return value."""
    raise ValueError("Test error")


@handle_exceptions(default_return_value=None, raise_on_error=True)
def mock_function_with_raise_on_error():
    """Mock function to test raise_on_error=True."""
    raise ValueError("Test error")


def test_handle_exceptions_returns_none_on_error():
    """Test that decorator returns None when an error occurs."""
    with patch("utils.error.test_handle_exceptions.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        result = mock_function_for_testing()

        assert result is None
        mock_get.assert_called_once()


def test_handle_exceptions_returns_custom_default():
    """Test that decorator returns custom default value on error."""
    result = mock_function_with_custom_default()
    assert result == "default"


def test_handle_exceptions_raises_when_raise_on_error_true():
    """Test that decorator raises exception when raise_on_error=True."""
    with pytest.raises(ValueError, match="Test error"):
        mock_function_with_raise_on_error()


def test_handle_exceptions_success_case():
    """Test that decorator doesn't interfere with successful function calls."""
    with patch("utils.error.test_handle_exceptions.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_get.return_value = mock_response

        result = mock_function_for_testing()

        assert result == {"success": True}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_handle_exceptions_primary_rate_limit_retry():
    """Test that primary rate limit (403) errors trigger retry with sleep."""
    with patch("utils.error.test_handle_exceptions.requests.get") as mock_get, patch(
        "utils.error.handle_exceptions.time.sleep"
    ) as mock_sleep:

        # First response: 403 rate limit error
        mock_response_error = MagicMock()
        mock_response_error.status_code = 403
        mock_response_error.reason = "Forbidden"
        mock_response_error.text = "API rate limit exceeded"
        mock_response_error.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Used": "5000",
            "X-RateLimit-Reset": "1640995200",
        }

        # Second response: success
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"success": True}

        # Configure HTTP error for first response
        http_error = requests.exceptions.HTTPError("403 Forbidden")
        http_error.response = mock_response_error
        mock_response_error.raise_for_status.side_effect = http_error

        # Configure mock to return error first, then success
        mock_get.side_effect = [mock_response_error, mock_response_success]

        result = mock_function_for_testing()

        # Should succeed after retry
        assert result == {"success": True}
        assert mock_get.call_count == 2
        mock_sleep.assert_called_once()  # Should have slept before retry


def test_handle_exceptions_secondary_rate_limit_retry():
    """Test that secondary rate limit (403 with retry-after) errors trigger retry with sleep."""
    with patch("utils.error.test_handle_exceptions.requests.get") as mock_get, patch(
        "utils.error.handle_exceptions.time.sleep"
    ) as mock_sleep:

        # First response: secondary rate limit error
        mock_response_error = MagicMock()
        mock_response_error.status_code = 403
        mock_response_error.reason = "Forbidden"
        mock_response_error.text = "You have exceeded a secondary rate limit"
        mock_response_error.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4000",
            "X-RateLimit-Used": "1000",
            "Retry-After": "60",
        }

        # Second response: success
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"success": True}

        # Configure HTTP error for first response
        http_error = requests.exceptions.HTTPError("403 Forbidden")
        http_error.response = mock_response_error
        mock_response_error.raise_for_status.side_effect = http_error

        # Configure mock to return error first, then success
        mock_get.side_effect = [mock_response_error, mock_response_success]

        result = mock_function_for_testing()

        # Should succeed after retry
        assert result == {"success": True}
        assert mock_get.call_count == 2
        mock_sleep.assert_called_once_with(60)  # Should sleep for retry-after duration


def test_handle_exceptions_callable_default_return_value():
    """Test that callable default_return_value receives args and kwargs."""

    @handle_exceptions(
        default_return_value=lambda content, **kwargs: content
        * kwargs.get("multiplier", 1),
        raise_on_error=False,
    )
    def transform_content(
        content: str, multiplier: int = 2
    ):  # pylint: disable=unused-argument
        """Test function that transforms content but might fail."""
        if content == "error":
            raise ValueError("Test error")
        return content.upper()

    # Normal case - should return uppercase
    assert transform_content("hello") == "HELLO"

    # Error case - should return original content (lambda returns first arg)
    assert transform_content("error") == "error"

    # Error case with multiplier - lambda should receive kwargs too
    assert transform_content("error", multiplier=3) == "errorerrorerror"


def test_handle_exceptions_callable_with_args_only():
    """Test callable default_return_value with positional args only."""

    @handle_exceptions(
        default_return_value=lambda first, second: f"{first}_{second}",
        raise_on_error=False,
    )
    def concat_strings(first: str, second: str):
        """Test function that concatenates strings."""
        if first == "fail":
            raise ValueError("Test failure")
        return f"{first}+{second}"

    # Normal case
    assert concat_strings("hello", "world") == "hello+world"

    # Error case - lambda returns custom combination
    assert concat_strings("fail", "safe") == "fail_safe"


def test_handle_exceptions_non_callable_default():
    """Test that non-callable default_return_value still works."""

    @handle_exceptions(default_return_value="fallback", raise_on_error=False)
    def might_fail(value: str):
        """Test function that might fail."""
        if value == "error":
            raise ValueError("Error occurred")
        return value.upper()

    # Normal case
    assert might_fail("hello") == "HELLO"

    # Error case - returns static default
    assert might_fail("error") == "fallback"


def test_handle_exceptions_429_rate_limit_retry():
    """Test that 429 rate limit errors trigger retry with sleep."""
    with patch("utils.error.test_handle_exceptions.requests.get") as mock_get, patch(
        "utils.error.handle_exceptions.time.sleep"
    ) as mock_sleep:

        # First response: 429 rate limit error
        mock_response_error = MagicMock()
        mock_response_error.status_code = 429
        mock_response_error.reason = "Too Many Requests"
        mock_response_error.text = "API rate limit exceeded"
        mock_response_error.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Used": "5000",
            "X-RateLimit-Reset": "1640995200",
        }

        # Second response: success
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"success": True}

        # Configure HTTP error for first response
        http_error = requests.exceptions.HTTPError("429 Too Many Requests")
        http_error.response = mock_response_error
        mock_response_error.raise_for_status.side_effect = http_error

        # Configure mock to return error first, then success
        mock_get.side_effect = [mock_response_error, mock_response_success]

        result = mock_function_for_testing()

        # Should succeed after retry
        assert result == {"success": True}
        assert mock_get.call_count == 2
        mock_sleep.assert_called_once()  # Should have slept before retry


def test_handle_exceptions_http_error_no_retry():
    """Test that non-rate-limit HTTP errors don't trigger retry."""
    with patch("utils.error.test_handle_exceptions.requests.get") as mock_get, patch(
        "utils.error.handle_exceptions.time.sleep"
    ) as mock_sleep:

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Not Found"

        http_error = requests.exceptions.HTTPError("404 Not Found")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        result = mock_function_for_testing()

        # Should return None without retry
        assert result is None
        assert mock_get.call_count == 1
        mock_sleep.assert_not_called()  # Should not sleep


def test_handle_exceptions_connection_error():
    """Test that connection errors are handled without retry."""
    with patch("utils.error.test_handle_exceptions.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        result = mock_function_for_testing()

        assert result is None
        mock_get.assert_called_once()


def test_handle_exceptions_timeout_error():
    """Test that timeout errors are handled without retry."""
    with patch("utils.error.test_handle_exceptions.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        result = mock_function_for_testing()

        assert result is None
        mock_get.assert_called_once()


def test_handle_exceptions_json_decode_error():
    """Test that JSON decode errors are handled without retry."""
    with patch("utils.error.test_handle_exceptions.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.side_effect = requests.exceptions.JSONDecodeError(
            "Invalid JSON", "", 0
        )
        mock_get.return_value = mock_response

        result = mock_function_for_testing()

        assert result is None
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_handle_exceptions_generic_exception():
    """Test that generic exceptions are handled."""
    with patch("utils.error.test_handle_exceptions.requests.get") as mock_get:
        mock_get.side_effect = ValueError("Generic error")

        result = mock_function_for_testing()

        assert result is None
        mock_get.assert_called_once()
