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
    trimmed = trim_messages_to_token_limit(messages, mock_client, max_tokens=5000)
    assert trimmed == messages


def test_trimming_at_boundary(mock_client):
    messages = [
        make_message("system"),
        make_message("user"),
        make_message("assistant"),
    ]
    # 3000 tokens == 3000 token limit - no trimming needed
    trimmed = trim_messages_to_token_limit(messages, mock_client, max_tokens=3000)
    assert trimmed == messages


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

def test_trimming_with_all_system_messages(mock_client):
    # Create a custom count_tokens function that returns different token counts
    # to simulate the case where token count decreases but is still above max_tokens
    token_counts = [5000, 4000, 3000, 2000]
    count_index = 0
    
    def custom_count_tokens(messages, model):
        nonlocal count_index
        result = Mock(input_tokens=token_counts[count_index])
        count_index = min(count_index + 1, len(token_counts) - 1)
        return result
    
    mock_client.messages.count_tokens.side_effect = custom_count_tokens
    messages = [make_message("system"), make_message("system"), make_message("system")]
