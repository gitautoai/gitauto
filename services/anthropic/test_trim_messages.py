# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

# Standard imports
from unittest.mock import Mock

# Third party imports
import pytest

# Local imports
from config import ANTHROPIC_MODEL_ID_40
from services.anthropic.trim_messages import trim_messages_to_token_limit


def make_message(role, content="test"):
    return {"role": role, "content": content}


@pytest.fixture
def mock_client():
    client = Mock()

    # Default 1000 tokens per message
    def count_tokens(messages, model):
        assert model == ANTHROPIC_MODEL_ID_40
        return Mock(input_tokens=len(messages) * 1000)

    client.messages.count_tokens.side_effect = count_tokens
    return client


def test_no_trimming_needed(mock_client):
    messages = [make_message("user"), make_message("assistant")]
    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=5000)
    assert trimmed == messages


def test_trimming_at_boundary(mock_client):
    messages = [
        make_message("system"),
        make_message("user"),
        make_message("assistant"),
    ]
    # 3000 tokens == 3000 token limit - no trimming needed
    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=3000)
    assert trimmed == messages


def test_trimming_removes_non_system(mock_client):
    messages = [
        make_message("system"),
        make_message("user", "first"),
        make_message("assistant", "second"),
        make_message("user", "third"),
    ]
    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=2500)
    expected = [
        make_message("system"),
        make_message("user", "third"),
    ]
    assert trimmed == expected


def test_trimming_keeps_system(mock_client):
    messages = [
        make_message("system"),
        make_message("user"),
        make_message("assistant"),
    ]
    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=500)
    assert trimmed == [make_message("system")]


def test_trimming_stops_at_one_message(mock_client):
    messages = [make_message("user")]
    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=100)
    assert trimmed == [make_message("user")]


def test_empty_messages(mock_client):
    messages = []
    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=1000)
    assert not trimmed


def make_complex_message(role, content=None):
    """Create a message with complex content structure like Claude's format"""
    if content is None:
        if role == "assistant":
            content = [{"type": "text", "text": "test text"}]
        else:
            content = "test content"

    return {"role": role, "content": content}


def test_complex_message_format(mock_client):
    """Test trimming with Claude's complex message format"""
    messages = [
        make_complex_message("user"),
        make_complex_message(
            "assistant",
            [
                {"type": "text", "text": "response text"},
                {
                    "type": "tool_use",
                    "id": "tool123",
                    "name": "some_tool",
                    "input": {"param": "value"},
                },
            ],
        ),
        make_complex_message(
            "user",
            [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool123",
                    "content": "tool result",
                }
            ],
        ),
    ]

    # Override token counting for this test
    mock_client.messages.count_tokens.side_effect = None
    mock_client.messages.count_tokens.return_value = Mock(input_tokens=10000)

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=5000)
    assert len(trimmed) < len(messages)
    assert trimmed == [messages[-1]]  # Only the last message remains


def test_real_message_json_format_trimming(mock_client):
    """Test with a format similar to the messages.json file format"""
    messages = [
        {"role": "user", "content": "long content..."},
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "assistant text..."},
                {
                    "type": "tool_use",
                    "id": "tool123",
                    "name": "search",
                    "input": {"query": "test"},
                },
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool123",
                    "content": "tool results...",
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "more text..."},
                {
                    "type": "tool_use",
                    "id": "tool456",
                    "name": "search",
                    "input": {"query": "more"},
                },
            ],
        },
    ]

    # Make the first message exceed token limit but keep others under
    # This simulates a real scenario where we need to remove older messages
    def count_tokens_variable(messages, model):
        num_msgs = len(messages)
        if num_msgs == 4:
            return Mock(input_tokens=200000)  # Over limit
        elif num_msgs == 3:
            return Mock(input_tokens=150000)  # Still over limit
        elif num_msgs == 2:
            return Mock(input_tokens=100000)  # Under limit
        else:
            return Mock(input_tokens=50000)  # Well under limit

    mock_client.messages.count_tokens.side_effect = count_tokens_variable

    trimmed = trim_messages_to_token_limit(messages, mock_client, max_input=128000)
    assert len(trimmed) == 2
    assert trimmed == messages[2:]  # Last two messages
