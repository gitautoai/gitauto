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
