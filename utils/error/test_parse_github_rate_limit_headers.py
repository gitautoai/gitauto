import time
from unittest.mock import Mock

from utils.error.parse_github_rate_limit_headers import parse_github_rate_limit_headers


def _response(headers):
    r = Mock()
    r.headers = headers
    return r


def test_returns_none_when_response_has_no_headers_attr():
    r = Mock(spec=[])
    assert parse_github_rate_limit_headers(r) is None


def test_returns_none_when_headers_is_empty():
    assert parse_github_rate_limit_headers(_response({})) is None


def test_returns_none_when_no_rate_limit_remaining_header():
    assert (
        parse_github_rate_limit_headers(_response({"Content-Type": "application/json"}))
        is None
    )


def test_returns_none_when_remaining_is_unparseable():
    assert (
        parse_github_rate_limit_headers(
            _response({"X-RateLimit-Remaining": "not-a-number"})
        )
        is None
    )


def test_falls_back_to_retry_after_when_remaining_nonzero():
    # Non-zero remaining = secondary (abuse) rate limit; use Retry-After
    response = _response({"X-RateLimit-Remaining": "4000", "Retry-After": "60"})
    assert parse_github_rate_limit_headers(response) == 60.0


def test_secondary_rate_limit_without_retry_after_returns_none():
    response = _response({"X-RateLimit-Remaining": "4000"})
    assert parse_github_rate_limit_headers(response) is None


def test_primary_rate_limit_uses_reset_with_buffer():
    reset_ts = int(time.time()) + 30
    response = _response(
        {
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(reset_ts),
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Used": "5000",
        }
    )
    delay = parse_github_rate_limit_headers(response)
    assert delay is not None
    # reset_ts - now + 5s buffer, allowing a few seconds of wall-clock jitter
    assert 30.0 <= delay <= 40.0


def test_primary_rate_limit_past_reset_uses_one_second_floor():
    reset_ts = int(time.time()) - 120
    response = _response(
        {
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(reset_ts),
        }
    )
    assert parse_github_rate_limit_headers(response) == 1.0


def test_primary_rate_limit_without_reset_falls_back_to_retry_after():
    response = _response(
        {
            "X-RateLimit-Remaining": "0",
            "Retry-After": "15",
        }
    )
    assert parse_github_rate_limit_headers(response) == 15.0


def test_primary_rate_limit_with_unparseable_reset_returns_none():
    response = _response(
        {
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": "garbage",
        }
    )
    assert parse_github_rate_limit_headers(response) is None
