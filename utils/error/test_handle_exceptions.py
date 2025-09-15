from unittest.mock import MagicMock, patch
import json

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
    with patch("requests.get") as mock_get:
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
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_get.return_value = mock_response

        result = mock_function_for_testing()

        assert result == {"success": True}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_handle_exceptions_primary_rate_limit_retry():
    """Test that primary rate limit (403) errors trigger retry with sleep."""
    with patch("requests.get") as mock_get, patch(
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
        http_error = requests.HTTPError("403 Forbidden")
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
    with patch("requests.get") as mock_get, patch(
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
        http_error = requests.HTTPError("403 Forbidden")
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
    with patch("requests.get") as mock_get, patch(
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
        http_error = requests.HTTPError("429 Too Many Requests")
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
    with patch("requests.get") as mock_get, patch(
        "utils.error.handle_exceptions.time.sleep"
    ) as mock_sleep:

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Not Found"

        http_error = requests.HTTPError("404 Not Found")
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
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        result = mock_function_for_testing()

        assert result is None
        mock_get.assert_called_once()


def test_handle_exceptions_timeout_error():
    """Test that timeout errors are handled without retry."""
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        result = mock_function_for_testing()

        assert result is None
        mock_get.assert_called_once()


def test_handle_exceptions_json_decode_error():
    """Test that JSON decode errors are handled without retry."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError(
            "Invalid JSON", "", 0
        )
        mock_get.return_value = mock_response

        result = mock_function_for_testing()

        assert result is None
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_handle_exceptions_generic_exception():
    """Test that generic exceptions are handled."""
    with patch("requests.get") as mock_get:
        mock_get.side_effect = ValueError("Generic error")

        result = mock_function_for_testing()

        assert result is None
        mock_get.assert_called_once()


def test_handle_exceptions_http_error_no_response_raise_on_error():
    """Test HTTPError with no response object and raise_on_error=True."""

    @handle_exceptions(default_return_value=None, raise_on_error=True)
    def mock_function_raise_on_error():
        """Mock function that raises HTTPError with no response."""
        http_error = requests.HTTPError("Connection failed")
        http_error.response = None  # No response object
        raise http_error

    with pytest.raises(requests.HTTPError, match="Connection failed"):
        mock_function_raise_on_error()


def test_handle_exceptions_http_error_no_response_no_raise():
    """Test HTTPError with no response object and raise_on_error=False."""

    @handle_exceptions(default_return_value="fallback", raise_on_error=False)
    def mock_function_no_raise():
        """Mock function that raises HTTPError with no response."""
        http_error = requests.HTTPError("Connection failed")
        http_error.response = None  # No response object
        raise http_error

    result = mock_function_no_raise()
    assert result == "fallback"


def test_handle_exceptions_google_api_rate_limit():
    """Test Google API rate limit handling (429 status code)."""

    @handle_exceptions(default_return_value=None, raise_on_error=False, api_type="google")
    def mock_google_function():
        """Mock function for Google API."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.reason = "Too Many Requests"
        mock_response.text = "Rate limit exceeded"
        mock_response.headers = {"Retry-After": "60"}

        http_error = requests.HTTPError("429 Too Many Requests")
        http_error.response = mock_response
        raise http_error

    # Google API rate limit should raise the exception (lines 96-99)
    with pytest.raises(requests.HTTPError, match="429 Too Many Requests"):
        mock_google_function()


def test_handle_exceptions_json_decode_error_with_doc():
    """Test JSONDecodeError with doc attribute."""

    @handle_exceptions(default_return_value="fallback", raise_on_error=False)
    def mock_function_json_error_with_doc():
        """Mock function that raises JSONDecodeError with doc."""
        json_error = json.JSONDecodeError("Invalid JSON", "bad json content", 0)
        # JSONDecodeError has doc attribute by default
        raise json_error

    result = mock_function_json_error_with_doc()
    assert result == "fallback"


def test_handle_exceptions_json_decode_error_without_doc():
    """Test JSONDecodeError without doc attribute (line 118)."""

    @handle_exceptions(default_return_value="fallback", raise_on_error=False)
    def mock_function_json_error_no_doc():
        """Mock function that raises JSONDecodeError without doc."""
        json_error = json.JSONDecodeError("Invalid JSON", "", 0)
        # Remove doc attribute to test the else branch
        delattr(json_error, "doc")
        raise json_error

    result = mock_function_json_error_no_doc()
    assert result == "fallback"


def test_handle_exceptions_json_decode_error_raise_on_error():
    """Test JSONDecodeError with raise_on_error=True."""

    @handle_exceptions(default_return_value=None, raise_on_error=True)
    def mock_function_json_error_raise():
        """Mock function that raises JSONDecodeError."""
        raise json.JSONDecodeError("Invalid JSON", "bad content", 0)

    with pytest.raises(json.JSONDecodeError, match="Invalid JSON"):
        mock_function_json_error_raise()


def test_handle_exceptions_500_error_raise_on_error():
    """Test 500 Internal Server Error with raise_on_error=True."""

    @handle_exceptions(default_return_value=None, raise_on_error=True)
    def mock_function_500_error():
        """Mock function that raises 500 error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "Server error"

        http_error = requests.HTTPError("500 Internal Server Error")
        http_error.response = mock_response
        raise http_error

    with pytest.raises(requests.HTTPError, match="500 Internal Server Error"):
        mock_function_500_error()


def test_handle_exceptions_500_error_no_raise():
    """Test 500 Internal Server Error with raise_on_error=False."""

    @handle_exceptions(default_return_value="server_error", raise_on_error=False)
    def mock_function_500_no_raise():
        """Mock function that raises 500 error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "Server error"

        http_error = requests.HTTPError("500 Internal Server Error")
        http_error.response = mock_response
        raise http_error

    result = mock_function_500_no_raise()
    assert result == "server_error"


def test_handle_exceptions_github_rate_limit_with_raise_on_error():
    """Test GitHub rate limit error with raise_on_error=True (non-retryable case)."""

    @handle_exceptions(default_return_value=None, raise_on_error=True, api_type="github")
    def mock_function_github_rate_limit():
        """Mock function that raises GitHub rate limit error."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.reason = "Forbidden"
        mock_response.text = "Rate limit exceeded"
        mock_response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "100",  # Not zero, so won't retry
            "X-RateLimit-Used": "4900",
        }

        http_error = requests.HTTPError("403 Forbidden")
        http_error.response = mock_response
        raise http_error

    with pytest.raises(requests.HTTPError, match="403 Forbidden"):
        mock_function_github_rate_limit()


def test_handle_exceptions_other_http_error_codes():
    """Test other HTTP error codes (not 403, 429, or 500) with raise_on_error=True."""

    @handle_exceptions(default_return_value=None, raise_on_error=True, api_type="github")
    def mock_function_other_error():
        """Mock function that raises other HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Resource not found"

        http_error = requests.HTTPError("404 Not Found")
        http_error.response = mock_response
        raise http_error

    with pytest.raises(requests.HTTPError, match="404 Not Found"):
        mock_function_other_error()


def test_handle_exceptions_attribute_error_raise_on_error():
    """Test AttributeError with raise_on_error=True."""

    @handle_exceptions(default_return_value=None, raise_on_error=True)
    def mock_function_attribute_error():
        """Mock function that raises AttributeError."""
        raise AttributeError("'NoneType' object has no attribute 'test'")

    with pytest.raises(AttributeError, match=r"'NoneType' object has no attribute 'test'"):
        mock_function_attribute_error()


def test_handle_exceptions_key_error_raise_on_error():
    """Test KeyError with raise_on_error=True."""

    @handle_exceptions(default_return_value=None, raise_on_error=True)
    def mock_function_key_error():
        """Mock function that raises KeyError."""
        raise KeyError("'missing_key' not found")

    with pytest.raises(KeyError, match=r"'missing_key' not found"):
        mock_function_key_error()
