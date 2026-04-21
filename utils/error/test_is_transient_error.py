import requests
from google.genai import errors as google_errors

from utils.error.is_transient_error import is_transient_error


def _http_error_with_status(status_code: int):
    response = requests.Response()
    response.status_code = status_code
    err = requests.HTTPError()
    err.response = response
    return err


def test_http_500_is_transient():
    assert is_transient_error(_http_error_with_status(500)) is True


def test_http_502_is_transient():
    assert is_transient_error(_http_error_with_status(502)) is True


def test_http_503_is_transient():
    assert is_transient_error(_http_error_with_status(503)) is True


def test_http_400_is_not_transient():
    assert is_transient_error(_http_error_with_status(400)) is False


def test_http_404_is_not_transient():
    assert is_transient_error(_http_error_with_status(404)) is False


def test_valueerror_with_remote_internal_server_error_is_transient():
    err = ValueError(
        "Command failed: remote: Internal Server Error\n"
        "To https://github.com/org/repo.git\n"
        " ! [remote rejected] HEAD -> branch (Internal Server Error)"
    )
    assert is_transient_error(err) is True


def test_valueerror_with_502_bad_gateway_is_transient():
    assert is_transient_error(ValueError("Command failed: 502 Bad Gateway")) is True


def test_valueerror_with_503_service_unavailable_is_transient():
    assert (
        is_transient_error(ValueError("Command failed: 503 Service Unavailable"))
        is True
    )


def test_valueerror_with_504_gateway_timeout_is_transient():
    assert is_transient_error(ValueError("Command failed: 504 Gateway Timeout")) is True


def test_valueerror_with_pathspec_error_is_not_transient():
    """A bad pathspec is a real bug — must NOT retry, or we'd burn time on
    errors that can never succeed."""
    err = ValueError(
        "Command failed: fatal: pathspec 'mongodb-binaries/x.tgz' did not match any files"
    )
    assert is_transient_error(err) is False


def test_valueerror_with_non_fast_forward_is_not_transient():
    err = ValueError("Command failed: ! [rejected] HEAD -> branch (fetch first)")
    assert is_transient_error(err) is False


def test_generic_runtimeerror_is_not_transient():
    assert is_transient_error(RuntimeError("something else broke")) is False


def test_google_499_cancelled_is_transient():
    """Reproduced from Sentry AGENT-3JY (2026-04-20T17:36:33 gitautoai/website):
    Google cancelled the stream server-side during a free-tier overload window.
    No Retry-After hint, so this must flow through the linear-backoff transient
    path rather than the rate-limit path."""
    err = google_errors.ClientError(
        code=499,
        response_json={
            "error": {
                "code": 499,
                "message": "The operation was cancelled.",
                "status": "CANCELLED",
            }
        },
    )
    assert is_transient_error(err) is True


def test_google_400_invalid_argument_is_not_transient():
    """400 INVALID_ARGUMENT (e.g. token count exceeds limit) is a real client
    bug that will never succeed on retry — must NOT be flagged transient."""
    err = google_errors.ClientError(
        code=400,
        response_json={
            "error": {
                "code": 400,
                "message": "The input token count exceeds the maximum.",
                "status": "INVALID_ARGUMENT",
            }
        },
    )
    assert is_transient_error(err) is False
