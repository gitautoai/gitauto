from unittest.mock import Mock, patch

import requests

from utils.error.handle_github_rate_limit import handle_github_rate_limit


def _github_http_error(
    status_code: int,
    limit: int,
    remaining: int,
    used: int,
    reset_ts: int = 0,
    retry_after: int = 60,
    body: str = "",
):
    response = requests.Response()
    response.status_code = status_code
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Used"] = str(used)
    response.headers["X-RateLimit-Reset"] = str(reset_ts)
    response.headers["Retry-After"] = str(retry_after)
    response._content = body.encode("utf-8")  # pylint: disable=protected-access
    response.reason = "Forbidden" if status_code == 403 else "Too Many Requests"
    err = requests.HTTPError()
    err.response = response
    return err


def test_primary_rate_limit_retries_via_callback():
    err = _github_http_error(403, limit=5000, remaining=0, used=5000)
    retry_callback = Mock(return_value="RETRIED")

    with patch("utils.error.handle_github_rate_limit.time.sleep"):
        result = handle_github_rate_limit(
            err,
            func_name="test_func",
            reason="Forbidden",
            text="rate limit exceeded",
            raise_on_error=False,
            retry_callback=retry_callback,
        )

    assert result == ("RETRIED", True)
    retry_callback.assert_called_once_with()


def test_secondary_rate_limit_retries_via_callback():
    err = _github_http_error(
        403,
        limit=5000,
        remaining=100,
        used=4900,
        body="You have exceeded a secondary rate limit",
    )
    retry_callback = Mock(return_value="RETRIED")

    with patch("utils.error.handle_github_rate_limit.time.sleep"):
        result = handle_github_rate_limit(
            err,
            func_name="test_func",
            reason="Forbidden",
            text="exceeded a secondary rate limit",
            raise_on_error=False,
            retry_callback=retry_callback,
        )

    assert result == ("RETRIED", True)
    retry_callback.assert_called_once_with()


def test_non_rate_limit_403_returns_none_for_fall_through():
    """403 without rate-limit signatures should fall through to the caller's
    generic Sentry-capture path."""
    err = _github_http_error(
        403, limit=5000, remaining=100, used=4900, body="Forbidden"
    )

    with patch("utils.error.handle_github_rate_limit.sentry_sdk"):
        result = handle_github_rate_limit(
            err,
            func_name="test_func",
            reason="Forbidden",
            text="not rate limited",
            raise_on_error=False,
            retry_callback=Mock(),
        )

    assert result is None


def test_non_rate_limit_403_re_raises_when_raise_on_error_true():
    err = _github_http_error(
        403, limit=5000, remaining=100, used=4900, body="Forbidden"
    )

    with patch("utils.error.handle_github_rate_limit.sentry_sdk"):
        try:
            handle_github_rate_limit(
                err,
                func_name="test_func",
                reason="Forbidden",
                text="not rate limited",
                raise_on_error=True,
                retry_callback=Mock(),
            )
        except requests.HTTPError as raised:
            assert raised is err
        else:
            raise AssertionError("expected HTTPError to be re-raised")
