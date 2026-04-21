from typing import cast
from unittest.mock import Mock

from anthropic import Anthropic
from anthropic.types import MessageParam

from constants.models import ClaudeModelId
from services.claude.count_tokens import count_tokens_claude


def test_returns_input_tokens_from_anthropic_response():
    """count_tokens_claude delegates to client.messages.count_tokens and returns
    the input_tokens field from the response."""
    client = Mock()
    client.messages.count_tokens.return_value = Mock(input_tokens=1234)
    messages = cast(list[MessageParam], [{"role": "user", "content": "hi"}])

    result = count_tokens_claude(
        messages=messages,
        client=cast(Anthropic, client),
        model=ClaudeModelId.SONNET_4_6,
    )

    assert result == 1234
    client.messages.count_tokens.assert_called_once_with(
        messages=messages, model=ClaudeModelId.SONNET_4_6
    )


def test_returns_zero_on_sdk_failure():
    """If the Anthropic SDK raises (e.g. transient 5xx on count_tokens), the
    @handle_exceptions decorator returns the default (0) so trim_messages falls
    through and lets generate_content produce a meaningful error instead of
    infinite-looping the trim."""
    client = Mock()
    client.messages.count_tokens.side_effect = RuntimeError("transient")
    messages = cast(list[MessageParam], [{"role": "user", "content": "hi"}])

    result = count_tokens_claude(
        messages=messages,
        client=cast(Anthropic, client),
        model=ClaudeModelId.SONNET_4_6,
    )

    assert result == 0
