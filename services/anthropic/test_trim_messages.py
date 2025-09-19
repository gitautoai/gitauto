# pylint: disable=too-few-public-methods,unused-argument
# Standard imports
from typing import Any
from unittest.mock import Mock

# Third party imports
import pytest

# Local imports
from services.anthropic.trim_messages import trim_messages_to_token_limit


def make_message(role, content="test"):
    """Create a simple message dictionary."""
    return {"role": role, "content": content}


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
    return {"role": role, "content": content}


def make_tool_result_message(tool_use_id, result="test result"):
    """Create a message with tool_result content."""
    return {
        "role": "user",
        "content": [
            {"type": "tool_result", "tool_use_id": tool_use_id, "content": result}
        ],
    }


class MessageObject:
    """Mock message object to test message_to_dict conversion."""

    def __init__(self, role, content):
        self.role = role
        self.content = content


@pytest.fixture
def mock_client():
    """Mock Anthropic client with configurable token counting."""
    client = Mock()

    # Default 1000 tokens per message
    def count_tokens(messages, model):
        return Mock(input_tokens=len(messages) * 1000)

    client.messages.count_tokens.side_effect = count_tokens

    return client


def test_empty_messages(mock_client):
    """Test early return for empty message list."""
    messages = []
    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)
    assert len(trimmed) == 0
    # Should not call count_tokens for empty messages
    mock_client.messages.count_tokens.assert_not_called()


def test_no_trimming_needed(mock_client):
    """Test when messages are already under token limit."""
    messages = [make_message("user"), make_message("assistant")]
    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=5000)
    assert trimmed == messages
    assert len(trimmed) == 2


def test_trimming_at_boundary(mock_client):
    """Test when messages exactly meet token limit."""
    messages = [
        make_message("system"),
        make_message("user"),
        make_message("assistant"),
    ]
    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=3000)
    assert trimmed == messages


def test_trimming_removes_non_system(mock_client):
    """Test that non-system messages are removed while preserving system messages."""
    messages = [
        make_message("system"),
        make_message("user", "first"),
        make_message("assistant"),
        make_message("user", "second"),
    ]

    # Force trimming by returning high token count initially
    mock_client.messages.count_tokens.return_value = Mock(input_tokens=10000)

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)
    assert make_message("system") in trimmed


def test_trimming_keeps_system(mock_client):
    """Test that system messages are preserved even when over limit."""
    messages = [
        make_message("system"),
        make_message("user"),
        make_message("assistant"),
    ]
    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=100)
    assert make_message("system") in trimmed


def test_trimming_stops_at_one_message(mock_client):
    """Test that trimming stops when only one message remains."""
    messages = [make_message("user")]
    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=100)
    assert trimmed == [make_message("user")]


def test_preserves_first_user_message(mock_client):
    """Test that the first user message is preserved."""
    messages = [
        make_message("user", "first"),
        make_message("assistant", "response"),
        make_message("user", "second"),
    ]

    # Force trimming by setting high token count
    def count_tokens_progressive(messages, model):
        # Return tokens based on message count to simulate realistic behavior
        if len(messages) >= 3:
            return Mock(input_tokens=5000)  # Over limit, needs trimming
        return Mock(input_tokens=800)  # Under limit, stop trimming

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should keep first user message and remove assistant message
    assert len(trimmed) == 2
    assert trimmed[0] == make_message("user", "first")
    assert trimmed[1] == make_message("user", "second")


def test_tool_use_and_result_paired_trimming(mock_client):
    """Test that tool_use and corresponding tool_result messages are trimmed together."""
    messages = [
        make_message("user", "initial query"),
        make_tool_use_message("assistant", "tool123"),
        make_tool_result_message("tool123"),
        make_message("user", "follow up"),
    ]

    # Set up token counting to force trimming
    def count_tokens_for_pairs(messages, model):
        if len(messages) >= 4:
            return Mock(input_tokens=5000)  # Over limit
        return Mock(input_tokens=1000)  # Under limit

    mock_client.messages.count_tokens.side_effect = count_tokens_for_pairs

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=2000)

    # Should remove the tool_use and tool_result pair together
    assert len(trimmed) == 2
    assert trimmed == [messages[0], messages[3]]


def test_tool_use_without_matching_result(mock_client):
    """Test assistant message with tool_use but no matching tool_result."""
    messages = [
        make_message("user", "query"),
        make_tool_use_message("assistant", "tool123"),
        make_message("user", "different message"),  # No tool_result
    ]

    # Force trimming
    def count_tokens_progressive(messages, model):
        # Return tokens based on message count to simulate realistic behavior
        if len(messages) >= 3:
            return Mock(input_tokens=5000)  # Over limit, needs trimming
        return Mock(input_tokens=800)  # Under limit, stop trimming

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should remove the assistant message without tool_result pairing
    assert len(trimmed) == 2
    assert trimmed == [messages[0], messages[2]]


def test_tool_use_with_non_matching_result(mock_client):
    """Test tool_use with tool_result that has different tool_use_id."""
    messages = [
        make_message("user", "query"),
        make_tool_use_message("assistant", "tool123"),
        make_tool_result_message("different_id"),  # Different tool_use_id
    ]

    # Force trimming
    def count_tokens_progressive(messages, model):
        # Return tokens based on message count to simulate realistic behavior
        if len(messages) >= 3:
            return Mock(input_tokens=5000)  # Over limit, needs trimming
        return Mock(input_tokens=800)  # Under limit, stop trimming

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should remove assistant message since tool_result doesn't match
    assert len(trimmed) == 2
    assert trimmed == [messages[0], messages[2]]


def test_assistant_message_with_non_list_content(mock_client):
    """Test assistant message with content that's not a list."""
    messages = [
        make_message("user", "query"),
        {"role": "assistant", "content": "simple string content"},
        make_message("user", "follow up"),
    ]

    # Force trimming
    def count_tokens_progressive(messages, model):
        # Return tokens based on message count to simulate realistic behavior
        if len(messages) >= 3:
            return Mock(input_tokens=5000)  # Over limit, needs trimming
        return Mock(input_tokens=800)  # Under limit, stop trimming

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should remove assistant message normally
    assert len(trimmed) == 2
    assert trimmed == [messages[0], messages[2]]


def test_content_with_non_dict_blocks(mock_client):
    """Test content list with non-dict blocks."""
    messages = [
        make_message("user", "query"),
        {
            "role": "assistant",
            "content": [
                "string block",  # Non-dict block
                {"type": "text", "text": "normal block"},
            ],
        },
        make_message("user", "follow up"),
    ]

    # Force trimming
    def count_tokens_progressive(messages, model):
        # Return tokens based on message count to simulate realistic behavior
        if len(messages) >= 3:
            return Mock(input_tokens=5000)  # Over limit, needs trimming
        return Mock(input_tokens=800)  # Under limit, stop trimming

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should handle non-dict blocks gracefully
    assert len(trimmed) == 2
    assert trimmed == [messages[0], messages[2]]


def test_tool_use_block_without_id(mock_client):
    """Test tool_use block that doesn't have an id field."""
    messages = [
        make_message("user", "query"),
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "test_tool",
                    # Missing "id" field
                    "input": {"param": "value"},
                }
            ],
        },
        make_message("user", "follow up"),
    ]

    # Force trimming
    def count_tokens_progressive(messages, model):
        # Return tokens based on message count to simulate realistic behavior
        if len(messages) >= 3:
            return Mock(input_tokens=5000)  # Over limit, needs trimming
        return Mock(input_tokens=800)  # Under limit, stop trimming

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should handle missing id gracefully
    assert len(trimmed) == 2
    assert trimmed == [messages[0], messages[2]]


def test_tool_result_without_tool_use_id(mock_client):
    """Test tool_result block without tool_use_id field."""
    messages = [
        make_message("user", "query"),
        make_tool_use_message("assistant", "tool123"),
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    # Missing "tool_use_id" field
                    "content": "result",
                }
            ],
        },
    ]

    # Force trimming
    def count_tokens_progressive(messages, model):
        # Return tokens based on message count to simulate realistic behavior
        if len(messages) >= 3:
            return Mock(input_tokens=5000)  # Over limit, needs trimming
        return Mock(input_tokens=800)  # Under limit, stop trimming

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should not match tool_use with tool_result missing tool_use_id
    assert len(trimmed) == 2
    assert trimmed == [messages[0], messages[2]]


def test_message_object_conversion(mock_client):
    """Test that message objects are converted to dicts using message_to_dict."""
    messages = [
        MessageObject("user", "query"),
        MessageObject("assistant", "response"),
    ]

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=5000)

    # Should work with message objects
    assert len(trimmed) == 2
    # Original objects should be preserved in the result
    assert trimmed == messages


def test_custom_model_parameter(mock_client):
    """Test using a custom model parameter."""
    messages = [make_message("user"), make_message("assistant")]
    custom_model = "claude-3-sonnet-20240229"

    def count_tokens_custom(messages, model):
        assert model == custom_model
        return Mock(input_tokens=len(messages) * 1000)

    mock_client.messages.count_tokens.side_effect = count_tokens_custom

    trimmed = trim_messages_to_token_limit(
        messages, mock_client, max_input=5000, model=custom_model
    )
    assert trimmed == messages


def test_messages_list_is_copied(mock_client):
    """Test that the original messages list is not mutated."""
    original_messages = [
        make_message("user", "first"),
        make_message("assistant", "response"),
        make_message("user", "second"),
    ]
    messages_copy = list(original_messages)

    # Force trimming
    def count_tokens_progressive(messages, model):
        # Return tokens based on message count to simulate realistic behavior
        if len(messages) >= 3:
            return Mock(input_tokens=5000)  # Over limit, needs trimming
        return Mock(input_tokens=800)  # Under limit, stop trimming

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages_copy, mock_client, max_input=1000)

    # Original list should be unchanged
    assert messages_copy == original_messages
    # But trimmed should be different
    assert len(trimmed) < len(original_messages)


def test_complex_tool_chain_trimming(mock_client):
    """Test trimming removes both tool_use/tool_result pairs when over token limit."""
    messages = [
        make_message("user", "initial"),
        make_tool_use_message("assistant", "tool1"),
        make_tool_result_message("tool1"),
        make_tool_use_message("assistant", "tool2"),
        make_tool_result_message("tool2"),
        make_message("user", "final"),
    ]

    # Set up progressive token counting
    def count_tokens_progressive(messages, model):
        length = len(messages)
        if length >= 6:
            return Mock(input_tokens=6000)  # Over limit
        if length >= 4:
            return Mock(input_tokens=4000)  # Still over limit
        return Mock(input_tokens=2000)  # Under limit

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=3000)

    # Should remove both tool pairs, keep only user messages
    assert len(trimmed) == 2
    expected = [messages[0], messages[5]]
    assert trimmed == expected


def test_system_message_preserved_user_removed(mock_client):
    """Test scenario where system message is preserved and non-first user message is removed."""
    messages = [
        make_message("system", "system prompt"),
        make_message("user", "only user message"),
    ]

    # Force high token count to trigger trimming
    mock_client.messages.count_tokens.return_value = Mock(input_tokens=10000)

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should keep only the system message, remove the user message at index 1
    assert trimmed == [make_message("system", "system prompt")]


def test_edge_case_missing_role_attribute(mock_client):
    """Test message with missing role attribute."""
    messages = [
        make_message("user", "query"),
        {"content": "message without role"},  # Missing role
        make_message("user", "follow up"),
    ]

    # Force trimming
    def count_tokens_progressive(messages, model):
        # Return tokens based on message count to simulate realistic behavior
        if len(messages) >= 3:
            return Mock(input_tokens=5000)  # Over limit, needs trimming
        return Mock(input_tokens=800)  # Under limit, stop trimming

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should handle missing role gracefully (defaults to empty string)
    assert len(trimmed) == 2
    assert trimmed == [messages[0], messages[2]]


def test_tool_use_at_end_of_messages(mock_client):
    """Test tool_use message at the end with no following message."""
    messages = [
        make_message("user", "query"),
        make_tool_use_message("assistant", "tool123"),  # Last message
    ]

    # Force trimming
    def count_tokens_progressive(messages, model):
        # Return tokens based on message count to simulate realistic behavior
        if len(messages) >= 2:
            return Mock(input_tokens=5000)  # Over limit, needs trimming
        return Mock(input_tokens=800)  # Under limit, stop trimming

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should remove the tool_use message since no tool_result follows
    assert len(trimmed) == 1
    assert trimmed == [messages[0]]


def test_multiple_tool_use_blocks_in_single_message(mock_client):
    """Test assistant message with multiple tool_use blocks."""
    messages = [
        make_message("user", "query"),
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "response"},
                {"type": "tool_use", "id": "tool1", "name": "first_tool", "input": {}},
                {"type": "tool_use", "id": "tool2", "name": "second_tool", "input": {}},
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool1",  # Only matches first tool_use
                    "content": "result1",
                }
            ],
        },
    ]

    # Force trimming
    def count_tokens_progressive(messages, model):
        # Return tokens based on message count to simulate realistic behavior
        if len(messages) >= 3:
            return Mock(input_tokens=5000)  # Over limit, needs trimming
        return Mock(input_tokens=800)  # Under limit, stop trimming

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should remove assistant message since second tool_use has no matching result
    assert len(trimmed) == 2
    assert trimmed == [messages[0], messages[2]]
def test_system_message_at_different_positions(mock_client):
    """Test system messages at various positions in the message list."""
    messages = [
        make_message("user", "first user"),
        make_message("system", "system in middle"),
        make_message("assistant", "response"),
        make_message("user", "second user"),
    ]

    # Force trimming
    def count_tokens_progressive(messages, model):
        if len(messages) >= 4:
            return Mock(input_tokens=5000)  # Over limit
        return Mock(input_tokens=800)  # Under limit

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should preserve system message and first user message
    assert len(trimmed) == 3
    assert make_message("user", "first user") in trimmed
    assert make_message("system", "system in middle") in trimmed
    assert make_message("user", "second user") in trimmed


def test_assistant_message_with_empty_content_list(mock_client):
    """Test assistant message with empty content list."""
    messages = [
        make_message("user", "query"),
        {"role": "assistant", "content": []},  # Empty content list
        make_message("user", "follow up"),
    ]

    # Force trimming
    def count_tokens_progressive(messages, model):
        if len(messages) >= 3:
            return Mock(input_tokens=5000)  # Over limit
        return Mock(input_tokens=800)  # Under limit

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should remove assistant message with empty content
    assert len(trimmed) == 2
    assert trimmed == [messages[0], messages[2]]


def test_tool_use_with_none_id(mock_client):
    """Test tool_use block with None as id value."""
    messages = [
        make_message("user", "query"),
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": None,  # None id
                    "name": "test_tool",
                    "input": {"param": "value"},
                }
            ],
        },
        make_message("user", "follow up"),
    ]

    # Force trimming
    def count_tokens_progressive(messages, model):
        if len(messages) >= 3:
            return Mock(input_tokens=5000)  # Over limit
        return Mock(input_tokens=800)  # Under limit

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should handle None id gracefully
    assert len(trimmed) == 2
    assert trimmed == [messages[0], messages[2]]


def test_tool_result_with_none_tool_use_id(mock_client):
    """Test tool_result block with None as tool_use_id value."""
    messages = [
        make_message("user", "query"),
        make_tool_use_message("assistant", "tool123"),
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": None,  # None tool_use_id
                    "content": "result",
                }
            ],
        },
    ]

    # Force trimming
    def count_tokens_progressive(messages, model):
        if len(messages) >= 3:
            return Mock(input_tokens=5000)  # Over limit
        return Mock(input_tokens=800)  # Under limit

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should not match tool_use with tool_result having None tool_use_id
    assert len(trimmed) == 2
    assert trimmed == [messages[0], messages[2]]


def test_single_system_message_over_limit(mock_client):
    """Test single system message that exceeds token limit."""
    messages = [make_message("system", "very long system message")]

    # Force high token count
    mock_client.messages.count_tokens.return_value = Mock(input_tokens=10000)

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should keep the system message even if over limit (only one message)
    assert len(trimmed) == 1
    assert trimmed == messages


def test_default_model_parameter_usage(mock_client):
    """Test that default model parameter is used when not specified."""
    messages = [make_message("user"), make_message("assistant")]

    def count_tokens_with_model_check(messages, model):
        # Verify default model is used
        from config import ANTHROPIC_MODEL_ID_40
        assert model == ANTHROPIC_MODEL_ID_40
        return Mock(input_tokens=len(messages) * 1000)

    mock_client.messages.count_tokens.side_effect = count_tokens_with_model_check

    # Call without specifying model parameter
    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=5000)
    assert trimmed == messages


def test_assistant_message_at_index_zero(mock_client):
    """Test assistant message at index 0 (edge case)."""
    messages = [
        make_message("assistant", "first message"),
        make_message("user", "user message"),
    ]

    # Force trimming
    def count_tokens_progressive(messages, model):
        if len(messages) >= 2:
            return Mock(input_tokens=5000)  # Over limit
        return Mock(input_tokens=800)  # Under limit

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should remove assistant message at index 0
    assert len(trimmed) == 1
    assert trimmed == [messages[1]]


def test_tool_use_message_at_last_index(mock_client):
    """Test tool_use message at the last index with no following message."""
    messages = [
        make_message("user", "query"),
        make_tool_use_message("assistant", "tool123"),  # Last message, no tool_result follows
    ]

    # Force trimming
    def count_tokens_progressive(messages, model):
        if len(messages) >= 2:
            return Mock(input_tokens=5000)  # Over limit
        return Mock(input_tokens=800)  # Under limit

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should remove the tool_use message since no tool_result follows
    assert len(trimmed) == 1
    assert trimmed == [messages[0]]


def test_content_attribute_missing(mock_client):
    """Test message with missing content attribute."""
    messages = [
        make_message("user", "query"),
        {"role": "assistant"},  # Missing content attribute
        make_message("user", "follow up"),
    ]

    # Force trimming
    def count_tokens_progressive(messages, model):
        if len(messages) >= 3:
            return Mock(input_tokens=5000)  # Over limit
        return Mock(input_tokens=800)  # Under limit

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should handle missing content gracefully (defaults to empty list)
    assert len(trimmed) == 2
    assert trimmed == [messages[0], messages[2]]


def test_progressive_token_reduction(mock_client):
    """Test that token count is recalculated after each message removal."""
    messages = [
        make_message("user", "first"),
        make_message("assistant", "second"),
        make_message("user", "third"),
        make_message("assistant", "fourth"),
    ]

    # Simulate progressive token reduction
    call_count = 0
    def count_tokens_decreasing(messages, model):
        nonlocal call_count
        call_count += 1
        # First call: over limit, subsequent calls: under limit
        if call_count == 1:
            return Mock(input_tokens=5000)  # Over limit
        return Mock(input_tokens=800)  # Under limit

    mock_client.messages.count_tokens.side_effect = count_tokens_decreasing

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should verify that count_tokens was called multiple times
    assert call_count > 1


def test_tool_use_with_empty_string_id(mock_client):
    """Test tool_use block with empty string as id value."""
    messages = [
        make_message("user", "query"),
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "",  # Empty string id
                    "name": "test_tool",
                    "input": {"param": "value"},
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "",  # Empty string tool_use_id
                    "content": "result",
                }
            ],
        },
    ]

    # Force trimming
    def count_tokens_progressive(messages, model):
        if len(messages) >= 3:
            return Mock(input_tokens=5000)  # Over limit
        return Mock(input_tokens=800)  # Under limit

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should not match empty string ids (treated as invalid), remove only assistant message
    assert len(trimmed) == 2
    assert trimmed == [messages[0], messages[2]]


def test_mixed_content_types_in_assistant_message(mock_client):
    """Test assistant message with mixed content types including tool_use."""
    messages = [
        make_message("user", "query"),
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Here's the result:"},
                {"type": "tool_use", "id": "tool1", "name": "search", "input": {}},
                {"type": "text", "text": "Additional text"},
                {"type": "tool_use", "id": "tool2", "name": "analyze", "input": {}},  # Second tool_use
            ],
        },
        make_tool_result_message("tool1"),  # Only matches first tool_use
    ]

    # Force trimming
    def count_tokens_progressive(messages, model):
        if len(messages) >= 3:
            return Mock(input_tokens=5000)  # Over limit
        return Mock(input_tokens=800)  # Under limit

    mock_client.messages.count_tokens.side_effect = count_tokens_progressive

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should remove assistant message since second tool_use has no matching result
    assert len(trimmed) == 2

    assert trimmed == [messages[0], messages[2]]


def test_aggressive_trimming_until_one_message_remains(mock_client):
    """Test aggressive trimming that continues until only one message remains."""
    messages = [
        make_message("user", "first"),
        make_message("assistant", "second"),
        make_message("user", "third"),
        make_message("assistant", "fourth"),
        make_message("user", "fifth"),
    ]

    # Always return high token count to force aggressive trimming
    mock_client.messages.count_tokens.return_value = Mock(input_tokens=10000)

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should trim down to just one message (the first user message)
    assert len(trimmed) == 1
    assert trimmed == [messages[0]]


def test_no_removable_messages_scenario(mock_client):
    """Test scenario where no messages can be removed (all system or first user)."""
    messages = [
        make_message("user", "only user message"),  # First user message, can't be removed
    ]

    # Force high token count
    mock_client.messages.count_tokens.return_value = Mock(input_tokens=10000)

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)

    # Should keep the only message even if over limit
    assert len(trimmed) == 1
    assert trimmed == messages
