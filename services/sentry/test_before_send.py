from __future__ import annotations

from typing import TYPE_CHECKING, cast

import requests
from services.sentry.before_send import before_send

if TYPE_CHECKING:
    from sentry_sdk._types import Event


def test_drops_server_error():
    """502 from GitHub should be dropped."""
    response = requests.models.Response()
    response.status_code = 502
    exc = requests.exceptions.HTTPError(response=response)
    hint = {"exc_info": (type(exc), exc, None)}
    event = cast("Event", {"exception": {"values": [{"type": "HTTPError"}]}})
    assert before_send(event, hint) is None


def test_passes_client_error():
    """404 should still be reported."""
    response = requests.models.Response()
    response.status_code = 404
    exc = requests.exceptions.HTTPError(response=response)
    hint = {"exc_info": (type(exc), exc, None)}
    event = cast("Event", {"exception": {"values": [{"type": "HTTPError"}]}})
    assert before_send(event, hint) == event


def test_passes_non_http_error():
    """Non-HTTP exceptions should still be reported."""
    exc = ValueError("some error")
    hint = {"exc_info": (type(exc), exc, None)}
    event = cast("Event", {"exception": {"values": [{"type": "ValueError"}]}})
    assert before_send(event, hint) == event


def test_passes_when_no_exc_info():
    """Events without exc_info should pass through."""
    event = cast("Event", {"message": "some log"})
    assert before_send(event, {}) == event


def test_drops_500_internal_server_error():
    # 500 is the lowest 5xx code; verify it's dropped like 502
    response = requests.models.Response()
    response.status_code = 500
    exc = requests.exceptions.HTTPError(response=response)
    hint = {"exc_info": (type(exc), exc, None)}
    event = cast("Event", {"exception": {"values": [{"type": "HTTPError"}]}})
    assert before_send(event, hint) is None


def test_drops_503_service_unavailable():
    # 503 is another common transient server error; confirm it's dropped
    response = requests.models.Response()
    response.status_code = 503
    exc = requests.exceptions.HTTPError(response=response)
    hint = {"exc_info": (type(exc), exc, None)}
    event = cast("Event", {"exception": {"values": [{"type": "HTTPError"}]}})
    assert before_send(event, hint) is None


def test_passes_499_boundary():
    # 499 is just below the 5xx threshold; must NOT be dropped
    response = requests.models.Response()
    response.status_code = 499
    exc = requests.exceptions.HTTPError(response=response)
    hint = {"exc_info": (type(exc), exc, None)}
    event = cast("Event", {"exception": {"values": [{"type": "HTTPError"}]}})
    assert before_send(event, hint) == event


def test_passes_when_exc_info_is_none_tuple():
    # exc_info present but exception element is None (e.g., manually constructed hint)
    hint = {"exc_info": (None, None, None)}
    event = cast("Event", {"message": "manual event"})
    assert before_send(event, hint) == event


def test_passes_when_hint_has_unrelated_keys():
    # hint dict has keys but no exc_info; should pass through
    hint = {"mechanism": {"type": "generic"}, "log_record": "something"}
    event = cast("Event", {"level": "info"})
    assert before_send(event, hint) == event


def test_drops_server_error_with_status_code_attr():
    # Anthropic/OpenAI SDK errors use a status_code attribute directly on the exception
    exc = Exception("API error")
    exc.status_code = 502  # type: ignore[attr-defined]
    hint = {"exc_info": (type(exc), exc, None)}
    event = cast("Event", {"exception": {"values": [{"type": "Exception"}]}})
    assert before_send(event, hint) is None


def test_drops_server_error_with_http_status_attr():
    # Stripe SDK errors use http_status attribute
    exc = Exception("Stripe error")
    exc.http_status = 500  # type: ignore[attr-defined]
    hint = {"exc_info": (type(exc), exc, None)}
    event = cast("Event", {"exception": {"values": [{"type": "Exception"}]}})
    assert before_send(event, hint) is None


def test_drops_server_error_with_status_attr():
    # PyGithub GithubException uses .status attribute
    exc = Exception("GitHub error")
    exc.status = 500  # type: ignore[attr-defined]
    hint = {"exc_info": (type(exc), exc, None)}
    event = cast("Event", {"exception": {"values": [{"type": "Exception"}]}})
    assert before_send(event, hint) is None


def test_passes_non_server_error_with_status_code_attr():
    # 400-level status_code on exception should NOT be dropped
    exc = Exception("Client error")
    exc.status_code = 400  # type: ignore[attr-defined]
    hint = {"exc_info": (type(exc), exc, None)}
    event = cast("Event", {"exception": {"values": [{"type": "Exception"}]}})
    assert before_send(event, hint) == event


def test_passes_empty_event():
    # Minimal empty event dict should pass through when no exception in hint
    hint: dict = {}
    event = cast("Event", {})
    assert before_send(event, hint) == event
