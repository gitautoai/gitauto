import pytest
from google.genai import errors as google_errors

from utils.error.parse_google_retry_in_message import parse_google_retry_in_message


def _client_error(message):
    return google_errors.ClientError(
        code=429,
        response_json={
            "error": {"code": 429, "message": message, "status": "RESOURCE_EXHAUSTED"}
        },
    )


def test_extracts_retry_delay_from_fractional_seconds():
    err = _client_error("Please retry in 3.337071738s.")
    assert parse_google_retry_in_message(err) == pytest.approx(3.337071738, rel=1e-6)


def test_extracts_retry_delay_from_integer_seconds():
    err = _client_error("Please retry in 60s.")
    assert parse_google_retry_in_message(err) == 60.0


def test_case_insensitive_match():
    err = _client_error("Please RETRY IN 5.5s now.")
    assert parse_google_retry_in_message(err) == 5.5


def test_returns_none_when_hint_missing():
    err = _client_error("You exceeded your current quota.")
    assert parse_google_retry_in_message(err) is None


def test_returns_none_for_different_phrasing():
    # Parser specifically looks for "retry in N.NNNs"; a "wait Ns" variant doesn't match.
    err = _client_error("Please wait 10s before retrying.")
    assert parse_google_retry_in_message(err) is None
