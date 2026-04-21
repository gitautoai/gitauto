# pylint: disable=too-few-public-methods,unused-argument
from typing import Any, cast
from unittest.mock import Mock

import pytest
from anthropic.types import MessageParam

from services.messages.trim_messages import trim_messages_to_token_limit


def make_message(role, content="test"):
    """Create a simple message dictionary."""
    return cast(MessageParam, {"role": role, "content": content})


def make_tool_use_message(role, tool_id, tool_name="test_tool", text="test text"):
    """Create a message with tool_use content."""
    content: list[Any] = [{"type": "text", "text": text}]
    if role == "assistant":
        content.append(
            {
                "type": "tool_use",
                "id": tool_id,
                "name": tool_name,
                "input": {"param": "value"},
            }
        )
    return cast(MessageParam, {"role": role, "content": content})


def make_tool_result_message(tool_use_id, result="test result"):
    """Create a message with tool_result content."""
    return cast(
        MessageParam,
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": result,
                }
            ],
        },
    )


class MessageObject:
    """Mock message object to test message_to_dict conversion."""

    def __init__(self, role, content):
        self.role = role
        self.content = content


@pytest.fixture
def count_fn():
    """Default token counter: 1000 tokens per message."""
    return Mock(side_effect=lambda msgs: len(msgs) * 1000)


def test_empty_messages(count_fn):
    """Test early return for empty message list."""
    messages = []
    trimmed, token_count = trim_messages_to_token_limit(
        messages, max_input=1000, count_tokens_fn=count_fn
    )
    assert len(trimmed) == 0
    assert token_count == 0
    count_fn.assert_not_called()


def test_no_trimming_needed(count_fn):
    """Test when messages are already under token limit."""
    messages = [make_message("user"), make_message("assistant")]
    trimmed, _ = trim_messages_to_token_limit(
        messages, max_input=5000, count_tokens_fn=count_fn
    )
    assert trimmed == messages
    assert len(trimmed) == 2


def test_trimming_at_boundary(count_fn):
    """Test when messages exactly meet token limit."""
    messages = [
        make_message("system"),
        make_message("user"),
        make_message("assistant"),
    ]
    trimmed, _ = trim_messages_to_token_limit(
        messages, max_input=3000, count_tokens_fn=count_fn
    )
    assert trimmed == messages


def test_trimming_removes_non_system(count_fn):
    """Test that non-system messages are removed while preserving system messages."""
    messages = [
        make_message("system"),
        make_message("user", "first"),
        make_message("assistant"),
        make_message("user", "second"),
    ]
    count_fn.side_effect = None
    count_fn.return_value = 10000
    trimmed, _ = trim_messages_to_token_limit(
        messages, max_input=1000, count_tokens_fn=count_fn
    )
    # System is index 0 so the "preserve first user" rule never applies; only
    # system survives after the loop strips the other three non-system messages.
    assert trimmed == [make_message("system")]


def test_trimming_keeps_system(count_fn):
    """Test that system messages are preserved even when over limit."""
    messages = [
        make_message("system"),
        make_message("user"),
        make_message("assistant"),
    ]
    trimmed, _ = trim_messages_to_token_limit(
        messages, max_input=100, count_tokens_fn=count_fn
    )
    assert trimmed == [make_message("system")]


def test_trimming_stops_at_one_message(count_fn):
    """Test that trimming stops when only one message remains."""
    messages = [make_message("user")]
    trimmed, _ = trim_messages_to_token_limit(
        messages, max_input=100, count_tokens_fn=count_fn
    )
    assert trimmed == [make_message("user")]


def test_preserves_first_user_message():
    """Test that the first user message is preserved."""
    messages = [
        make_message("user", "first"),
        make_message("assistant", "response"),
        make_message("user", "second"),
    ]

    def progressive(msgs):
        return 5000 if len(msgs) >= 3 else 800

    trimmed, _ = trim_messages_to_token_limit(
        messages, max_input=1000, count_tokens_fn=progressive
    )
    assert len(trimmed) == 2
    assert trimmed[0] == make_message("user", "first")
    assert trimmed[1] == make_message("user", "second")


def test_tool_use_and_result_paired_trimming():
    """Test that tool_use and corresponding tool_result messages are trimmed together."""
    messages = [
        make_message("user", "initial query"),
        make_tool_use_message("assistant", "tool123"),
        make_tool_result_message("tool123"),
        make_message("user", "follow up"),
    ]

    def progressive(msgs):
        return 5000 if len(msgs) >= 4 else 1000

    trimmed, _ = trim_messages_to_token_limit(
        messages, max_input=2000, count_tokens_fn=progressive
    )
    assert len(trimmed) == 2
    assert trimmed == [messages[0], messages[3]]


def test_tool_use_without_matching_result():
    """Test assistant message with tool_use but no matching tool_result."""
    messages = [
        make_message("user", "query"),
        make_tool_use_message("assistant", "tool123"),
        make_message("user", "different message"),
    ]

    def progressive(msgs):
        return 5000 if len(msgs) >= 3 else 800

    trimmed, _ = trim_messages_to_token_limit(
        messages, max_input=1000, count_tokens_fn=progressive
    )
    assert len(trimmed) == 2
    assert trimmed == [messages[0], messages[2]]


def test_tool_use_with_non_matching_result():
    """Test tool_use with tool_result that has different tool_use_id."""
    messages = [
        make_message("user", "query"),
        make_tool_use_message("assistant", "tool123"),
        make_tool_result_message("different_id"),
    ]

    def progressive(msgs):
        return 5000 if len(msgs) >= 3 else 800

    trimmed, _ = trim_messages_to_token_limit(
        messages, max_input=1000, count_tokens_fn=progressive
    )
    assert len(trimmed) == 2
    assert trimmed == [messages[0], messages[2]]


def test_assistant_message_with_non_list_content():
    """Test assistant message with content that's not a list."""
    messages = [
        make_message("user", "query"),
        cast(MessageParam, {"role": "assistant", "content": "simple string content"}),
        make_message("user", "follow up"),
    ]

    def progressive(msgs):
        return 5000 if len(msgs) >= 3 else 800

    trimmed, _ = trim_messages_to_token_limit(
        messages, max_input=1000, count_tokens_fn=progressive
    )
    assert len(trimmed) == 2
    assert trimmed == [messages[0], messages[2]]


def test_message_object_conversion(count_fn):
    """Test that message objects are converted to dicts using message_to_dict."""
    messages = cast(
        list[MessageParam],
        [
            MessageObject("user", "query"),
            MessageObject("assistant", "response"),
        ],
    )
    trimmed, _ = trim_messages_to_token_limit(
        messages, max_input=5000, count_tokens_fn=count_fn
    )
    assert len(trimmed) == 2
    assert trimmed == messages


def test_messages_list_is_copied():
    """Test that the original messages list is not mutated."""
    original_messages = [
        make_message("user", "first"),
        make_message("assistant", "response"),
        make_message("user", "second"),
    ]
    messages_copy = list(original_messages)

    def progressive(msgs):
        return 5000 if len(msgs) >= 3 else 800

    trimmed, _ = trim_messages_to_token_limit(
        messages_copy, max_input=1000, count_tokens_fn=progressive
    )
    assert messages_copy == original_messages
    assert len(trimmed) < len(original_messages)


def test_complex_tool_chain_trimming():
    """Test trimming removes both tool_use/tool_result pairs when over token limit."""
    messages = [
        make_message("user", "initial"),
        make_tool_use_message("assistant", "tool1"),
        make_tool_result_message("tool1"),
        make_tool_use_message("assistant", "tool2"),
        make_tool_result_message("tool2"),
        make_message("user", "final"),
    ]

    def progressive(msgs):
        length = len(msgs)
        if length >= 6:
            return 6000
        if length >= 4:
            return 4000
        return 2000

    trimmed, _ = trim_messages_to_token_limit(
        messages, max_input=3000, count_tokens_fn=progressive
    )
    assert len(trimmed) == 2
    assert trimmed == [messages[0], messages[5]]
