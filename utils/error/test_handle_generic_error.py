from unittest.mock import patch

import pytest
import requests

from utils.error.handle_generic_error import handle_generic_error


def test_non_special_error_captures_sentry_and_returns_default():
    err = ValueError("some bug")

    with patch("utils.error.handle_generic_error.sentry_sdk") as mock_sentry:
        result = handle_generic_error(
            err,
            func_name="test",
            log_args=[],
            log_kwargs={},
            raise_on_error=False,
            error_return="DEFAULT",
        )

    assert result == "DEFAULT"
    mock_sentry.capture_exception.assert_called_once_with(err)


def test_server_error_does_not_report_to_sentry():
    """is_server_error covers HTTPError/SDK-shaped 5xx — those should suppress Sentry."""
    response = requests.Response()
    response.status_code = 500
    err = requests.HTTPError()
    err.response = response

    with patch("utils.error.handle_generic_error.sentry_sdk") as mock_sentry:
        result = handle_generic_error(
            err,
            func_name="test",
            log_args=[],
            log_kwargs={},
            raise_on_error=False,
            error_return="DEFAULT",
        )

    assert result == "DEFAULT"
    mock_sentry.capture_exception.assert_not_called()


def test_raise_on_error_re_raises_original_exception():
    err = RuntimeError("boom")

    with patch("utils.error.handle_generic_error.sentry_sdk"):
        with pytest.raises(RuntimeError) as excinfo:
            handle_generic_error(
                err,
                func_name="test",
                log_args=[],
                log_kwargs={},
                raise_on_error=True,
                error_return="DEFAULT",
            )

    assert excinfo.value is err
