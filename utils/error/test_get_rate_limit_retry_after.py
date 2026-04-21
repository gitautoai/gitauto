import json
import time
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests
from google.genai import errors as google_errors

from utils.error.get_rate_limit_retry_after import get_rate_limit_retry_after

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _http_error(status, headers=None):
    response = Mock()
    response.status_code = status
    response.headers = headers or {}
    err = requests.HTTPError(response=response)
    return err


def test_returns_none_for_unrelated_exception():
    assert get_rate_limit_retry_after(ValueError("not a rate limit")) is None


def test_requests_http_error_non_rate_limit_status_returns_none():
    err = _http_error(500)
    assert get_rate_limit_retry_after(err) is None


def test_requests_http_error_with_retry_after_header_returns_delay():
    err = _http_error(429, headers={"Retry-After": "12"})
    assert get_rate_limit_retry_after(err) == 12.0


def test_requests_http_error_with_lowercase_retry_after_header_returns_delay():
    err = _http_error(429, headers={"retry-after": "3.5"})
    assert get_rate_limit_retry_after(err) == 3.5


def test_requests_http_error_without_retry_after_returns_none():
    err = _http_error(429, headers={})
    assert get_rate_limit_retry_after(err) is None


def test_github_primary_rate_limit_uses_reset_header_with_buffer():
    reset_ts = int(time.time()) + 20
    err = _http_error(
        403,
        headers={
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(reset_ts),
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Used": "5000",
        },
    )
    delay = get_rate_limit_retry_after(err)
    assert delay is not None
    # delay = reset_ts - now + 5s buffer; jitter within a couple seconds is OK
    assert 20.0 <= delay <= 30.0


def test_github_primary_rate_limit_past_reset_uses_one_second():
    reset_ts = int(time.time()) - 60
    err = _http_error(
        403,
        headers={
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(reset_ts),
        },
    )
    assert get_rate_limit_retry_after(err) == 1.0


def test_github_secondary_rate_limit_remaining_nonzero_uses_retry_after():
    err = _http_error(
        403,
        headers={
            "X-RateLimit-Remaining": "4000",
            "Retry-After": "60",
        },
    )
    assert get_rate_limit_retry_after(err) == 60.0


def test_anthropic_rate_limit_error_reads_retry_after_header():
    err = Mock(spec=Exception)
    err.status_code = 429
    err.response = Mock()
    err.response.headers = {"retry-after": "45"}
    assert get_rate_limit_retry_after(err) == 45.0


def test_anthropic_429_without_retry_after_returns_none():
    err = Mock(spec=Exception)
    err.status_code = 429
    err.response = Mock()
    err.response.headers = {}
    assert get_rate_limit_retry_after(err) is None


def test_anthropic_non_429_status_returns_none():
    err = Mock(spec=Exception)
    err.status_code = 500
    err.response = Mock()
    err.response.headers = {"retry-after": "45"}
    assert get_rate_limit_retry_after(err) is None


def test_google_client_error_with_retry_hint_returns_delay():
    err = google_errors.ClientError(
        code=429,
        response_json={
            "error": {
                "code": 429,
                "message": "You exceeded your current quota. Please retry in 3.337071738s.",
                "status": "RESOURCE_EXHAUSTED",
            }
        },
    )
    delay = get_rate_limit_retry_after(err)
    assert delay == pytest.approx(3.337071738, rel=1e-6)


def test_google_client_error_without_retry_hint_returns_none():
    err = google_errors.ClientError(
        code=429,
        response_json={
            "error": {
                "code": 429,
                "message": "You exceeded your current quota.",
                "status": "RESOURCE_EXHAUSTED",
            }
        },
    )
    assert get_rate_limit_retry_after(err) is None


def test_google_non_429_code_returns_none():
    err = google_errors.ClientError(
        code=400,
        response_json={"error": {"code": 400, "message": "bad request"}},
    )
    assert get_rate_limit_retry_after(err) is None


def test_real_google_429_payload_returns_correct_delay():
    """Fixture is the verbatim 429 line pulled from CloudWatch for the
    gitautoai/website incident on 2026-04-20 16:23 UTC (chat_with_google log
    entry). See fixtures/real_google_429.txt. The parser only needs the
    "Please retry in N.NNNs" substring — the surrounding details[] payload
    (Help link, QuotaFailure, RetryInfo) is preserved so the fixture doubles
    as a reference for future rate-limit work."""
    fixture_path = FIXTURES_DIR / "real_google_429.txt"
    raw_payload = fixture_path.read_text().strip()
    assert raw_payload.startswith("429 RESOURCE_EXHAUSTED. ")
    hint = "Please retry " + "in " + "59.739387544s"
    assert raw_payload.count(hint) == 1
    # The "{...}" after "429 RESOURCE_EXHAUSTED. " is a Python repr with \n
    # escapes, not JSON. Feed the exact message text through the SDK so
    # str(err) matches what the Lambda logged in production.
    message = (
        "You exceeded your current quota, please check your plan and billing details. "
        "For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. "
        "To monitor your current usage, head to: https://ai.dev/rate-limit. \n"
        "* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, "
        "limit: 15, model: gemma-4-31b\nPlease retry in 59.739387544s."
    )
    response_json = {
        "error": {
            "code": 429,
            "message": message,
            "status": "RESOURCE_EXHAUSTED",
        }
    }
    err = google_errors.ClientError(code=429, response_json=response_json)
    hint = "Please retry " + "in " + "59.739387544s"
    assert str(err).count(hint) == 1
    delay = get_rate_limit_retry_after(err)
    assert delay == pytest.approx(59.739387544, rel=1e-6)
    _ = json  # keeps import usable if fixture changes shape later
