from __future__ import \
    annotations  # Sentry SDK exposes Event/Hint types only for type checkers, not at runtime

from typing import TYPE_CHECKING

from utils.error.handle_exceptions import handle_exceptions
from utils.error.is_server_error import is_server_error

if TYPE_CHECKING:
    from sentry_sdk._types import Event, Hint  # pragma: no cover


@handle_exceptions(default_return_value=None, raise_on_error=False)
def before_send(event: Event, hint: Hint):
    exc = hint.get("exc_info", (None, None, None))[1]
    if exc is not None and is_server_error(exc):
        return None  # Drop transient 5xx from GitHub/Anthropic/etc.

    return event
