# pylint: disable=redefined-outer-name

# Standard imports
import pytest

# Third party imports
from anthropic import Anthropic

# Local imports
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL_ID_37
from services.anthropic.trim_messages import trim_messages_to_token_limit


@pytest.fixture
def anthropic_client():
    return Anthropic(api_key=ANTHROPIC_API_KEY)


def make_message(role, content="test content"):
    return {"role": role, "content": content}


def test_integration_trim_messages_basic(anthropic_client):
    messages = [
        make_message("system", "You are a helpful assistant."),
        make_message("user", "Hello, how are you?"),
        make_message("assistant", "I'm doing well, thank you for asking!"),
        make_message("user", "Can you help me with a task?"),
    ]
    
    # Use a reasonable token limit for the test
    max_tokens = 1000
    
    # Get the actual token count
    initial_token_count = anthropic_client.messages.count_tokens(
        messages=messages, model=ANTHROPIC_MODEL_ID_37
    ).input_tokens
    
    # Trim messages if needed
    trimmed = trim_messages_to_token_limit(
        messages, anthropic_client, model=ANTHROPIC_MODEL_ID_37, max_tokens=max_tokens
    )
    
    # Get the token count after trimming
    final_token_count = anthropic_client.messages.count_tokens(
        messages=trimmed, model=ANTHROPIC_MODEL_ID_37
    ).input_tokens
    
    # If initial count was already under the limit, no trimming should occur
    if initial_token_count <= max_tokens:
        assert trimmed == messages
    else:
        # Otherwise, the final count should be less than or equal to the max
        assert final_token_count <= max_tokens
        # And we should have fewer messages
        assert len(trimmed) <= len(messages)
        # System message should be preserved
        assert any(msg["role"] == "system" for msg in trimmed)


def test_integration_all_system_messages(anthropic_client):
    messages = [
        make_message("system", "First system instruction."),
        make_message("system", "Second system instruction."),
        make_message("system", "Third system instruction."),
    ]
    
    # Get the actual token count
    token_count = anthropic_client.messages.count_tokens(
        messages=messages, model=ANTHROPIC_MODEL_ID_37
    ).input_tokens
    
    # Set max_tokens to half the actual token count to force trimming attempt
    max_tokens = token_count // 2
    
    # Try to trim messages
    trimmed = trim_messages_to_token_limit(
        messages, anthropic_client, model=ANTHROPIC_MODEL_ID_37, max_tokens=max_tokens
    )
    
    # All system messages should be preserved, even if over token limit
    assert trimmed == messages


def test_integration_mixed_messages_over_limit(anthropic_client):
    # Create a conversation with a mix of message types
    messages = [
        make_message("system", "You are a helpful assistant."),
        make_message("user", "First user message with some content."),
        make_message("assistant", "First assistant response with detailed information."),
        make_message("user", "Second user message asking a follow-up question."),
        make_message("assistant", "Second assistant response providing more details."),
        make_message("user", "Third user message with additional questions."),
    ]
    
    # Get the actual token count
    token_count = anthropic_client.messages.count_tokens(
        messages=messages, model=ANTHROPIC_MODEL_ID_37
    ).input_tokens
    
    # Set max_tokens to force removal of some messages but not all
    max_tokens = token_count // 2
    
    # Trim messages
    trimmed = trim_messages_to_token_limit(
        messages, anthropic_client, model=ANTHROPIC_MODEL_ID_37, max_tokens=max_tokens
    )
    
    # Get the token count after trimming
    final_token_count = anthropic_client.messages.count_tokens(
        messages=trimmed, model=ANTHROPIC_MODEL_ID_37
    ).input_tokens
    
    # The system message should be preserved
    assert any(msg["role"] == "system" for msg in trimmed)
    
    # The final token count should be less than or equal to max_tokens
    # or we should have only system messages remaining
    if not all(msg["role"] == "system" for msg in trimmed):
        assert final_token_count <= max_tokens
    
    # We should have fewer messages than we started with
    assert len(trimmed) < len(messages)