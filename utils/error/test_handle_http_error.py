from unittest.mock import Mock, patch

import requests

from utils.error.handle_http_error import handle_http_error


def _http_error(status_code: int, body: str = "error", reason: str = "Reason"):
    response = requests.Response()
    response.status_code = status_code
    response.reason = reason
    response._content = body.encode("utf-8")  # pylint: disable=protected-access
    err = requests.HTTPError()
    err.response = response
    return err


def test_no_response_returns_default():
    err = requests.HTTPError()
    err.response = None

    result = handle_http_error(
        err,
        func_name="test",
        log_args=[],
        log_kwargs={},
        api_type="github",
        raise_on_error=False,
        error_return="DEFAULT",
        retry_callback=Mock(),
    )

    assert result == ("DEFAULT", False)


def test_no_response_raises_when_raise_on_error_true():
    err = requests.HTTPError()
    err.response = None

    try:
        handle_http_error(
            err,
            func_name="test",
            log_args=[],
            log_kwargs={},
            api_type="github",
            raise_on_error=True,
            error_return="DEFAULT",
            retry_callback=Mock(),
        )
    except requests.HTTPError as raised:
        assert raised is err
    else:
        raise AssertionError("expected HTTPError to be re-raised")


def test_server_error_returns_default_without_sentry():
    err = _http_error(500, body="internal", reason="Internal Server Error")

    with patch("utils.error.handle_http_error.sentry_sdk") as mock_sentry:
        result = handle_http_error(
            err,
            func_name="test",
            log_args=[],
            log_kwargs={},
            api_type="github",
            raise_on_error=False,
            error_return="DEFAULT",
            retry_callback=Mock(),
        )

    assert result == ("DEFAULT", False)
    mock_sentry.capture_exception.assert_not_called()


def test_github_rate_limit_is_delegated_and_retries():
    err = _http_error(403, body="rate limit exceeded", reason="Forbidden")
    err.response.headers["X-RateLimit-Limit"] = "5000"
    err.response.headers["X-RateLimit-Remaining"] = "0"
    err.response.headers["X-RateLimit-Used"] = "5000"
    err.response.headers["X-RateLimit-Reset"] = "0"
    retry_callback = Mock(return_value="RETRIED")

    with patch("utils.error.handle_github_rate_limit.time.sleep"):
        result = handle_http_error(
            err,
            func_name="test",
            log_args=[],
            log_kwargs={},
            api_type="github",
            raise_on_error=False,
            error_return="DEFAULT",
            retry_callback=retry_callback,
        )

    assert result == ("RETRIED", True)
    retry_callback.assert_called_once_with()


def test_other_http_error_captures_sentry_and_returns_default():
    err = _http_error(418, body="teapot", reason="I'm a teapot")

    with patch("utils.error.handle_http_error.sentry_sdk") as mock_sentry:
        result = handle_http_error(
            err,
            func_name="test",
            log_args=[],
            log_kwargs={},
            api_type="github",
            raise_on_error=False,
            error_return="DEFAULT",
            retry_callback=Mock(),
        )

    assert result == ("DEFAULT", False)
    mock_sentry.capture_exception.assert_called_once_with(err)
