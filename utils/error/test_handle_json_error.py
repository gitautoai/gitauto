import json
from unittest.mock import patch

import pytest

from utils.error.handle_json_error import handle_json_error


def _make_json_error():
    try:
        json.loads("not json")
    except json.JSONDecodeError as err:
        return err
    raise AssertionError("json.loads unexpectedly succeeded")


def test_returns_default_and_reports_to_sentry():
    err = _make_json_error()

    with patch("utils.error.handle_json_error.sentry_sdk") as mock_sentry:
        result = handle_json_error(
            err,
            func_name="test",
            log_args=[],
            log_kwargs={},
            raise_on_error=False,
            error_return="DEFAULT",
        )

    assert result == "DEFAULT"
    mock_sentry.capture_exception.assert_called_once_with(err)


def test_re_raises_when_raise_on_error_true():
    err = _make_json_error()

    with patch("utils.error.handle_json_error.sentry_sdk"):
        with pytest.raises(json.JSONDecodeError) as excinfo:
            handle_json_error(
                err,
                func_name="test",
                log_args=[],
                log_kwargs={},
                raise_on_error=True,
                error_return="DEFAULT",
            )

    assert excinfo.value is err
