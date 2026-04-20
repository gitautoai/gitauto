import asyncio
import json
from unittest.mock import patch, MagicMock

import pytest
import requests

from utils.error.handle_exceptions import handle_exceptions, TRANSIENT_MAX_ATTEMPTS


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def async_mock_function_for_testing():
    raise ValueError("Async test error")


@handle_exceptions(default_return_value="async_default", raise_on_error=False)
async def async_mock_function_with_custom_default():
    raise ValueError("Async test error")


@handle_exceptions(default_return_value=None, raise_on_error=True)
async def async_mock_function_with_raise_on_error():
    raise ValueError("Async test error")


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def async_mock_function_success():
    return {"async": "success"}


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
    """Test that non-rate-limit HTTP errors don't trigger retry and report to sentry."""
    with patch("utils.error.test_handle_exceptions.requests.get") as mock_get, patch(
        "utils.error.handle_exceptions.time.sleep"
    ) as mock_sleep, patch("sentry_sdk.capture_exception") as mock_sentry:

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
        mock_sentry.assert_called_once_with(http_error)


def test_handle_exceptions_connection_error():
    """Test that connection errors are handled without retry and report to sentry."""
    with patch("utils.error.test_handle_exceptions.requests.get") as mock_get, patch(
        "sentry_sdk.capture_exception"
    ) as mock_sentry:
        conn_error = requests.exceptions.ConnectionError("Connection failed")
        mock_get.side_effect = conn_error

        result = mock_function_for_testing()

        assert result is None
        mock_get.assert_called_once()
        mock_sentry.assert_called_once_with(conn_error)


def test_handle_exceptions_timeout_error():
    """Test that timeout errors are handled without retry and report to sentry."""
    with patch("utils.error.test_handle_exceptions.requests.get") as mock_get, patch(
        "sentry_sdk.capture_exception"
    ) as mock_sentry:
        timeout_error = requests.exceptions.Timeout("Request timed out")
        mock_get.side_effect = timeout_error

        result = mock_function_for_testing()

        assert result is None
        mock_get.assert_called_once()
        mock_sentry.assert_called_once_with(timeout_error)


def test_handle_exceptions_json_decode_error():
    """Test that JSON decode errors are handled without retry and report to sentry."""
    with patch("utils.error.test_handle_exceptions.requests.get") as mock_get, patch(
        "sentry_sdk.capture_exception"
    ) as mock_sentry:
        mock_response = MagicMock()
        json_error = requests.exceptions.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.json.side_effect = json_error
        mock_get.return_value = mock_response

        result = mock_function_for_testing()

        assert result is None
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        mock_sentry.assert_called_once_with(json_error)


def test_handle_exceptions_generic_exception():
    """Test that generic exceptions are handled and report to sentry."""
    with patch("utils.error.test_handle_exceptions.requests.get") as mock_get, patch(
        "sentry_sdk.capture_exception"
    ) as mock_sentry:
        value_error = ValueError("Generic error")
        mock_get.side_effect = value_error

        result = mock_function_for_testing()

        assert result is None
        mock_get.assert_called_once()
        mock_sentry.assert_called_once_with(value_error)


def test_handle_exceptions_preserves_return_type():
    """Test that decorator preserves function return type for type checkers."""

    @handle_exceptions(default_return_value=[], raise_on_error=False)
    def get_items(count: int):
        if count < 0:
            raise ValueError("Count must be non-negative")
        return [{"id": i} for i in range(count)]

    result = get_items(3)
    assert result == [{"id": 0}, {"id": 1}, {"id": 2}]
    assert isinstance(result, list)

    error_result = get_items(-1)
    assert not error_result
    assert isinstance(error_result, list)


def test_handle_exceptions_http_error_no_response_raises():
    @handle_exceptions(default_return_value=None, raise_on_error=True)
    def func_raises_http_error_no_response():
        error = requests.exceptions.HTTPError("No response")
        error.response = None
        raise error

    with pytest.raises(requests.exceptions.HTTPError):
        func_raises_http_error_no_response()


def test_handle_exceptions_http_error_no_response_returns_default():
    @handle_exceptions(default_return_value="default", raise_on_error=False)
    def func_raises_http_error_no_response():
        error = requests.exceptions.HTTPError("No response")
        error.response = None
        raise error

    result = func_raises_http_error_no_response()
    assert result == "default"


def test_handle_exceptions_500_error_raises():
    @handle_exceptions(default_return_value=None, raise_on_error=True)
    def func_raises_500():
        response = MagicMock()
        response.status_code = 500
        error = requests.exceptions.HTTPError("500 Server Error")
        error.response = response
        raise error

    with pytest.raises(requests.exceptions.HTTPError):
        func_raises_500()


def test_handle_exceptions_500_error_returns_default():
    @handle_exceptions(default_return_value="fallback", raise_on_error=False)
    def func_raises_500():
        response = MagicMock()
        response.status_code = 500
        error = requests.exceptions.HTTPError("500 Server Error")
        error.response = response
        raise error

    result = func_raises_500()
    assert result == "fallback"


def test_handle_exceptions_502_error_returns_default_no_sentry():
    """Test that 502 server errors return default without reporting to Sentry."""

    @handle_exceptions(default_return_value="fallback", raise_on_error=False)
    def func_raises_502():
        response = MagicMock()
        response.status_code = 502
        error = requests.exceptions.HTTPError("502 Bad Gateway")
        error.response = response
        raise error

    with patch("sentry_sdk.capture_exception") as mock_sentry:
        result = func_raises_502()
        assert result == "fallback"
        mock_sentry.assert_not_called()


def test_handle_exceptions_503_error_returns_default_no_sentry():
    """Test that 503 server errors return default without reporting to Sentry."""

    @handle_exceptions(default_return_value="fallback", raise_on_error=False)
    def func_raises_503():
        response = MagicMock()
        response.status_code = 503
        error = requests.exceptions.HTTPError("503 Service Unavailable")
        error.response = response
        raise error

    with patch("sentry_sdk.capture_exception") as mock_sentry:
        result = func_raises_503()
        assert result == "fallback"
        mock_sentry.assert_not_called()


def test_handle_exceptions_anthropic_500_no_sentry():
    """Test that exceptions with status_code >= 500 skip Sentry (e.g. Anthropic InternalServerError)."""

    class FakeServerError(Exception):
        status_code = 500

    @handle_exceptions(default_return_value="fallback", raise_on_error=False)
    def func_raises_anthropic_500():
        raise FakeServerError("Internal server error")

    with patch("sentry_sdk.capture_exception") as mock_sentry:
        result = func_raises_anthropic_500()
        assert result == "fallback"
        mock_sentry.assert_not_called()


def test_handle_exceptions_supabase_502_no_sentry():
    """Test that Supabase APIError with code 502 skips Sentry."""

    @handle_exceptions(default_return_value="fallback", raise_on_error=False)
    def func_raises_supabase_502():
        err = Exception("Bad Gateway")
        err.code = "502"  # type: ignore[attr-defined]
        raise err

    with patch("sentry_sdk.capture_exception") as mock_sentry:
        result = func_raises_supabase_502()
        assert result == "fallback"
        mock_sentry.assert_not_called()


def test_handle_exceptions_supabase_non_5xx_reports_sentry():
    """Test that Supabase APIError with non-5xx code still reports to Sentry."""

    @handle_exceptions(default_return_value="fallback", raise_on_error=False)
    def func_raises_supabase_404():
        err = Exception("Not found")
        err.code = "PGRST204"  # type: ignore[attr-defined]
        raise err

    with patch("sentry_sdk.capture_exception") as mock_sentry:
        result = func_raises_supabase_404()
        assert result == "fallback"
        mock_sentry.assert_called_once()


def test_handle_exceptions_primary_rate_limit_with_future_reset():
    with patch("utils.error.handle_exceptions.time.sleep") as mock_sleep, patch(
        "utils.error.handle_exceptions.time.time"
    ) as mock_time:
        mock_time.return_value = 1000
        future_reset = 1010
        call_count = [0]

        @handle_exceptions(default_return_value=None, raise_on_error=False)
        def func_rate_limited():
            call_count[0] += 1
            if call_count[0] == 1:
                response = MagicMock()
                response.status_code = 403
                response.reason = "Forbidden"
                response.text = "rate limit exceeded"
                response.headers = {
                    "X-RateLimit-Limit": "5000",
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Used": "5000",
                    "X-RateLimit-Reset": str(future_reset),
                }
                error = requests.exceptions.HTTPError("403 Forbidden")
                error.response = response
                raise error
            return "success"

        result = func_rate_limited()
        assert result == "success"
        mock_sleep.assert_called_with(15)


def test_handle_exceptions_403_remaining_positive_raises():
    @handle_exceptions(default_return_value=None, raise_on_error=True)
    def func_403_remaining():
        response = MagicMock()
        response.status_code = 403
        response.reason = "Forbidden"
        response.text = "Access denied"
        response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "100",
            "X-RateLimit-Used": "4900",
        }
        error = requests.exceptions.HTTPError("403 Forbidden")
        error.response = response
        raise error

    with patch("sentry_sdk.capture_exception") as mock_sentry:
        with pytest.raises(requests.exceptions.HTTPError):
            func_403_remaining()
        mock_sentry.assert_called_once()


def test_handle_exceptions_web_search_429_raises():
    @handle_exceptions(
        default_return_value=None, raise_on_error=False, api_type="web_search"
    )
    def func_web_search_429():
        response = MagicMock()
        response.status_code = 429
        response.reason = "Too Many Requests"
        response.text = "quota exceeded"
        response.headers = {"Retry-After": "60"}
        error = requests.exceptions.HTTPError("429 Too Many Requests")
        error.response = response
        raise error

    with pytest.raises(requests.exceptions.HTTPError):
        func_web_search_429()


def test_handle_exceptions_http_error_non_rate_limit_raise_on_error():
    @handle_exceptions(default_return_value=None, raise_on_error=True)
    def func_raises_404():
        response = MagicMock()
        response.status_code = 404
        response.reason = "Not Found"
        response.text = "Not Found"
        error = requests.exceptions.HTTPError("404 Not Found")
        error.response = response
        raise error

    with patch("sentry_sdk.capture_exception") as mock_sentry:
        with pytest.raises(requests.exceptions.HTTPError):
            func_raises_404()
        mock_sentry.assert_called_once()


def test_handle_exceptions_json_decode_error_no_doc():
    @handle_exceptions(default_return_value="default", raise_on_error=False)
    def func_json_error_no_doc():
        error = json.JSONDecodeError("Invalid", "", 0)
        if hasattr(error, "doc"):
            delattr(error, "doc")
        raise error

    with patch("sentry_sdk.capture_exception"):
        result = func_json_error_no_doc()
        assert result == "default"


def test_handle_exceptions_json_decode_error_raise_on_error():
    @handle_exceptions(default_return_value=None, raise_on_error=True)
    def func_json_error_raises():
        raise json.JSONDecodeError("Invalid", "bad json", 0)

    with patch("sentry_sdk.capture_exception") as mock_sentry:
        with pytest.raises(json.JSONDecodeError):
            func_json_error_raises()
        mock_sentry.assert_called_once()


@pytest.mark.asyncio
async def test_async_handle_exceptions_returns_none_on_error():
    with patch("sentry_sdk.capture_exception"):
        coro = async_mock_function_for_testing()
        assert coro is not None
        result = await coro
        assert result is None


@pytest.mark.asyncio
async def test_async_handle_exceptions_returns_custom_default():
    with patch("sentry_sdk.capture_exception"):
        coro = async_mock_function_with_custom_default()
        assert coro is not None
        result = await coro
        assert result == "async_default"


@pytest.mark.asyncio
async def test_async_handle_exceptions_raises_when_raise_on_error_true():
    with patch("sentry_sdk.capture_exception"):
        with pytest.raises(ValueError, match="Async test error"):
            coro = async_mock_function_with_raise_on_error()
            assert coro is not None
            await coro


@pytest.mark.asyncio
async def test_async_handle_exceptions_success_case():
    coro = async_mock_function_success()
    assert coro is not None
    result = await coro
    assert result == {"async": "success"}


@pytest.mark.asyncio
async def test_async_handle_exceptions_reports_to_sentry():
    with patch("sentry_sdk.capture_exception") as mock_sentry:
        coro = async_mock_function_for_testing()
        assert coro is not None
        await coro
        mock_sentry.assert_called_once()


@pytest.mark.asyncio
async def test_async_handle_exceptions_cancelled_error_returns_default():
    @handle_exceptions(default_return_value="cancelled_default", raise_on_error=False)
    async def func_gets_cancelled():
        raise asyncio.CancelledError()

    result = await func_gets_cancelled()
    assert result == "cancelled_default"


@pytest.mark.asyncio
async def test_async_handle_exceptions_cancelled_error_raises_when_raise_on_error():
    @handle_exceptions(default_return_value=None, raise_on_error=True)
    async def func_gets_cancelled():
        raise asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        await func_gets_cancelled()


# --- Transient retry behavior (AGENT-36Z/36J) ---


def test_decorator_retries_on_transient_value_error():
    """Sentry AGENT-36Z/36J: retry a ValueError whose message indicates a
    transient upstream failure, then succeed on the second attempt."""
    attempts = {"count": 0}

    @handle_exceptions(default_return_value=None, raise_on_error=False)
    def flaky():
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise ValueError("Command failed: remote: Internal Server Error")
        return "ok"

    with patch("utils.error.handle_exceptions.time.sleep"):
        assert flaky() == "ok"
    assert attempts["count"] == 2


def test_decorator_gives_up_after_max_attempts_on_transient_error():
    """If every attempt hits a transient error, surface the failure via the
    default_return_value — the bounded retry prevents infinite loops."""
    attempts = {"count": 0}

    @handle_exceptions(default_return_value="DEFAULT", raise_on_error=False)
    def always_500():
        attempts["count"] += 1
        raise ValueError("Command failed: HTTP 502 Bad Gateway")

    with patch("utils.error.handle_exceptions.time.sleep"):
        assert always_500() == "DEFAULT"
    # TRANSIENT_MAX_ATTEMPTS controls the total number of attempts.
    assert attempts["count"] == TRANSIENT_MAX_ATTEMPTS


def test_decorator_does_not_retry_non_transient_error():
    """Non-transient failures must fail fast on the first attempt."""
    attempts = {"count": 0}

    @handle_exceptions(default_return_value="DEFAULT", raise_on_error=False)
    def real_bug():
        attempts["count"] += 1
        raise ValueError("Command failed: fatal: pathspec 'x' did not match any files")

    with patch("utils.error.handle_exceptions.time.sleep"):
        assert real_bug() == "DEFAULT"
    assert attempts["count"] == 1
