# pylint: disable=redefined-outer-name

# Standard imports
from unittest.mock import Mock

# Third party imports
import pytest

# Local imports
from config import ANTHROPIC_MODEL_ID_37
from services.anthropic.trim_messages import trim_messages_to_token_limit


def make_message(role, content="test"):
    return {"role": role, "content": content}


@pytest.fixture
def mock_client():
    client = Mock()

    # Default 1000 tokens per message
    def count_tokens(messages, model):
        assert model == ANTHROPIC_MODEL_ID_37
        return Mock(input_tokens=len(messages) * 1000)

    client.messages.count_tokens.side_effect = count_tokens
    return client


def test_no_trimming_needed(mock_client):
    messages = [make_message("user"), make_message("assistant")]
    messages_copy = list(messages)  # Create a copy to pass to the function
    expected_messages = [dict(msg) for msg in messages]
    trimmed = trim_messages_to_token_limit(messages_copy, mock_client, max_tokens=5000)
    assert trimmed == expected_messages


def test_trimming_at_boundary(mock_client):
    original_messages = [
        make_message("system"),
        make_message("user"),
        make_message("assistant"),
    ]
    expected_messages = [dict(msg) for msg in original_messages]
    # 3000 tokens == 3000 token limit - no trimming needed
    trimmed = trim_messages_to_token_limit(original_messages, mock_client, max_tokens=3000)
    assert trimmed == expected_messages


def test_trimming_removes_non_system(mock_client):
    messages = [
        make_message("system"),
        make_message("user", "first"),
        make_message("assistant", "second"),
        make_message("user", "third"),
    ]
    trimmed = trim_messages_to_token_limit(messages, mock_client, max_tokens=2500)
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
    trimmed = trim_messages_to_token_limit(messages, mock_client, max_tokens=500)
    assert trimmed == [make_message("system")]


def test_trimming_stops_at_one_message(mock_client):
    messages = [make_message("user")]
    trimmed = trim_messages_to_token_limit(messages, mock_client, max_tokens=100)
    assert trimmed == [make_message("user")]


def test_empty_messages_list():
    client = Mock()
    # We need to properly set up the mock before calling the function
    client.messages = Mock()
    client.messages.count_tokens = Mock()
    
    messages = []
    trimmed = trim_messages_to_token_limit(messages, client, max_tokens=1000)
    assert trimmed == []
    # Verify that count_tokens was not called since we return early for empty messages
    client.messages.count_tokens.assert_not_called()


def test_custom_token_counter(mock_client):
    mock_client.messages.count_tokens.return_value = Mock(input_tokens=0)
    # Create a copy of the messages to ensure we're comparing against the original
    original_messages = [make_message("user"), make_message("assistant")]
    # Store a deep copy of the messages to compare later
    messages_copy = list(original_messages)  # Create a copy to pass to the function
    expected_messages = [dict(msg) for msg in original_messages]
    trimmed = trim_messages_to_token_limit(messages_copy, mock_client, max_tokens=1)
    assert trimmed == expected_messages  # Compare with the expected messages


def test_all_system_messages(mock_client):
    original_messages = [
        make_message("system", "first"),
        make_message("system", "second")
    ]
    expected_messages = [dict(msg) for msg in original_messages]
    # Even though tokens > max_tokens, all messages are system messages so none will be removed
    trimmed = trim_messages_to_token_limit(original_messages, mock_client, max_tokens=1000)
    assert trimmed == expected_messages


def test_only_system_messages_with_high_token_count(mock_client):
    # Set up a custom token count that's higher than max_tokens
    mock_client.messages.count_tokens.return_value = Mock(input_tokens=5000)
    
    original_messages = [make_message("system", "first")]
    expected_messages = [dict(msg) for msg in original_messages]
    # Even though tokens > max_tokens, we only have one message so it won't be removed
    trimmed = trim_messages_to_token_limit(original_messages, mock_client, max_tokens=1000)
    assert trimmed == expected_messages
    assert mock_client.messages.count_tokens.call_count >= 1


def test_mixed_messages_with_no_non_system_to_remove(mock_client):
    # Create a custom side effect to simulate a situation where token count remains high
    def count_tokens_side_effect(messages, model):
        return Mock(input_tokens=5000)  # Always return high token count
    
    mock_client.messages.count_tokens.side_effect = count_tokens_side_effect
    original_messages = [make_message("system"), make_message("system")]
    expected_messages = [dict(msg) for msg in original_messages]
    trimmed = trim_messages_to_token_limit(original_messages, mock_client, max_tokens=1000)
    assert trimmed == expected_messages
