from typing import cast
from unittest.mock import Mock, patch

from anthropic.types import MessageParam
from google.genai import Client

from constants.models import GoogleModelId
from services.google_ai.count_tokens import count_tokens_google


def test_converts_then_calls_count_tokens_and_returns_total():
    """count_tokens_google runs the Anthropic->Google content conversion first,
    then calls client.models.count_tokens with that converted payload, and
    returns total_tokens."""
    client = Mock()
    client.models.count_tokens.return_value = Mock(total_tokens=9876)
    messages = cast(list[MessageParam], [{"role": "user", "content": "hi"}])

    with patch(
        "services.google_ai.count_tokens.convert_messages_to_google",
        return_value="converted-payload",
    ) as mock_convert:
        result = count_tokens_google(
            messages=messages,
            client=cast(Client, client),
            model=GoogleModelId.GEMMA_4_31B,
        )

    assert result == 9876
    mock_convert.assert_called_once_with(messages)
    client.models.count_tokens.assert_called_once_with(
        model=GoogleModelId.GEMMA_4_31B, contents="converted-payload"
    )


def test_none_total_tokens_coerced_to_zero():
    """SDK may return total_tokens=None on edge cases; our code returns 0 rather
    than propagating None so trim_messages keeps comparing ints."""
    client = Mock()
    client.models.count_tokens.return_value = Mock(total_tokens=None)
    messages = cast(list[MessageParam], [{"role": "user", "content": "hi"}])

    with patch(
        "services.google_ai.count_tokens.convert_messages_to_google",
        return_value=[],
    ):
        result = count_tokens_google(
            messages=messages,
            client=cast(Client, client),
            model=GoogleModelId.GEMMA_4_31B,
        )

    assert result == 0


def test_returns_zero_on_sdk_failure():
    """If the SDK raises mid-count (transient 5xx, auth expiry), @handle_exceptions
    returns default 0 so the trim loop bails out and the underlying generate_content
    either succeeds or produces a real error."""
    client = Mock()
    client.models.count_tokens.side_effect = RuntimeError("boom")
    messages = cast(list[MessageParam], [{"role": "user", "content": "hi"}])

    with patch(
        "services.google_ai.count_tokens.convert_messages_to_google",
        return_value=[],
    ):
        result = count_tokens_google(
            messages=messages,
            client=cast(Client, client),
            model=GoogleModelId.GEMMA_4_31B,
        )

    assert result == 0
