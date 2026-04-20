import requests

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
