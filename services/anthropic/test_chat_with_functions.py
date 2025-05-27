# Standard imports
from unittest.mock import Mock, patch

# Third party imports
import pytest
from anthropic import AuthenticationError
from anthropic._exceptions import OverloadedError
from anthropic.types import ToolUseBlock

# Local imports
from config import ANTHROPIC_MODEL_ID_37, ANTHROPIC_MODEL_ID_40
from services.anthropic.chat_with_functions import chat_with_claude
from services.anthropic.exceptions import (
    ClaudeAuthenticationError,
    ClaudeOverloadedError,
)


class MockContentBlock:
    def __init__(self, block_type, text=None, tool_use_data=None):
        self.type = block_type
        if block_type == "text":
            self.text = text
        elif block_type == "tool_use":
            self.id = tool_use_data.get("id", "toolu_123")
            self.name = tool_use_data.get("name", "test_function")
            self.input = tool_use_data.get("input", {})


class MockResponse:
    def __init__(self, content_blocks):
        self.content = content_blocks


@pytest.fixture
def mock_client():
    client = Mock()
    client.messages.count_tokens.return_value = Mock(input_tokens=100)
    return client


@pytest.fixture
def sample_messages():
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]


@pytest.fixture
def sample_tools():
    return [
        {
            "function": {
                "name": "get_weather",
                "description": "Get weather information",
                "parameters": {
                    "type": "object",
                    "properties": {"location": {"type": "string"}},
                },
            }
        }
    ]


def test_chat_with_claude_text_only_response(mock_client, sample_messages, sample_tools):
    """Test chat_with_claude with text-only response."""
    # Mock response with only text content
    mock_response = MockResponse([MockContentBlock("text", text="Hello there!")])
    mock_client.messages.create.return_value = mock_response

    with patch("services.anthropic.chat_with_functions.get_anthropic_client", return_value=mock_client), \
         patch("services.anthropic.chat_with_functions.trim_messages_to_token_limit", return_value=sample_messages):
        
        result = chat_with_claude(
            messages=sample_messages,
            system_content="You are a helpful assistant",
            tools=sample_tools,
            model_id=ANTHROPIC_MODEL_ID_40,
        )

        assistant_message, tool_call_id, tool_name, tool_args, token_input, token_output = result

        # Verify response structure
        assert assistant_message["role"] == "assistant"
        assert len(assistant_message["content"]) == 1
        assert assistant_message["content"][0]["type"] == "text"
        assert assistant_message["content"][0]["text"] == "Hello there!"
        
        # No tool calls
        assert tool_call_id is None
        assert tool_name is None
        assert tool_args is None
        assert token_input == 100
        assert token_output == 0


def test_chat_with_claude_with_tool_use(mock_client, sample_messages, sample_tools):
    """Test chat_with_claude with tool use response."""
    # Mock response with text and tool use
    tool_use_data = {
        "id": "toolu_123456",
        "name": "get_weather",
        "input": {"location": "New York"}
    }
    mock_response = MockResponse([
        MockContentBlock("text", text="I'll get the weather for you."),
        MockContentBlock("tool_use", tool_use_data=tool_use_data)
    ])
    mock_client.messages.create.return_value = mock_response

    with patch("services.anthropic.chat_with_functions.get_anthropic_client", return_value=mock_client), \
         patch("services.anthropic.chat_with_functions.trim_messages_to_token_limit", return_value=sample_messages):
        
        result = chat_with_claude(
            messages=sample_messages,
            system_content="You are a helpful assistant",
            tools=sample_tools,
            model_id=ANTHROPIC_MODEL_ID_40,
        )

        assistant_message, tool_call_id, tool_name, tool_args, token_input, token_output = result

        # Verify response structure
        assert assistant_message["role"] == "assistant"
        assert len(assistant_message["content"]) == 2
        
        # Text content
        assert assistant_message["content"][0]["type"] == "text"
        assert assistant_message["content"][0]["text"] == "I'll get the weather for you."
        
        # Tool use content
        assert assistant_message["content"][1]["type"] == "tool_use"
        assert assistant_message["content"][1]["id"] == "toolu_123456"
        assert assistant_message["content"][1]["name"] == "get_weather"
        assert assistant_message["content"][1]["input"] == {"location": "New York"}
        
        # Tool call details
        assert tool_call_id == "toolu_123456"
        assert tool_name == "get_weather"
        assert tool_args == {"location": "New York"}
        assert token_input == 100
        assert token_output == 0


def test_chat_with_claude_tool_only_response(mock_client, sample_messages, sample_tools):
    """Test chat_with_claude with tool-only response (no text)."""
    tool_use_data = {
        "id": "toolu_789",
        "name": "get_weather",
        "input": {"location": "London"}
    }
    mock_response = MockResponse([MockContentBlock("tool_use", tool_use_data=tool_use_data)])
    mock_client.messages.create.return_value = mock_response

    with patch("services.anthropic.chat_with_functions.get_anthropic_client", return_value=mock_client), \
         patch("services.anthropic.chat_with_functions.trim_messages_to_token_limit", return_value=sample_messages):
        
        result = chat_with_claude(
            messages=sample_messages,
            system_content="You are a helpful assistant",
            tools=sample_tools,
            model_id=ANTHROPIC_MODEL_ID_40,
        )

        assistant_message, tool_call_id, tool_name, tool_args, token_input, token_output = result

        # Verify response structure - only tool use, no text
        assert assistant_message["role"] == "assistant"
        assert len(assistant_message["content"]) == 1
        assert assistant_message["content"][0]["type"] == "tool_use"
        assert assistant_message["content"][0]["id"] == "toolu_789"
        assert assistant_message["content"][0]["name"] == "get_weather"
        assert assistant_message["content"][0]["input"] == {"location": "London"}
        
        # Tool call details
        assert tool_call_id == "toolu_789"
        assert tool_name == "get_weather"
        assert tool_args == {"location": "London"}


def test_chat_with_claude_model_id_37_max_tokens(mock_client, sample_messages, sample_tools):
    """Test that model ID 3.7 uses correct max_tokens."""
    mock_response = MockResponse([MockContentBlock("text", text="Test response")])
    mock_client.messages.create.return_value = mock_response

    with patch("services.anthropic.chat_with_functions.get_anthropic_client", return_value=mock_client), \
         patch("services.anthropic.chat_with_functions.trim_messages_to_token_limit", return_value=sample_messages):
        
        chat_with_claude(
            messages=sample_messages,
            system_content="Test",
            tools=sample_tools,
            model_id=ANTHROPIC_MODEL_ID_37,
        )

        # Verify max_tokens is 64000 for model 3.7
        call_args = mock_client.messages.create.call_args
        assert call_args[1]["max_tokens"] == 64000


def test_chat_with_claude_other_model_max_tokens(mock_client, sample_messages, sample_tools):
    """Test that other models use correct max_tokens."""
    mock_response = MockResponse([MockContentBlock("text", text="Test response")])
    mock_client.messages.create.return_value = mock_response

    with patch("services.anthropic.chat_with_functions.get_anthropic_client", return_value=mock_client), \
         patch("services.anthropic.chat_with_functions.trim_messages_to_token_limit", return_value=sample_messages):
        
        chat_with_claude(
            messages=sample_messages,
            system_content="Test",
            tools=sample_tools,
            model_id="claude-3-haiku-20240307",
        )

        # Verify max_tokens is 8192 for other models
        call_args = mock_client.messages.create.call_args
        assert call_args[1]["max_tokens"] == 8192


def test_chat_with_claude_tool_conversion(mock_client, sample_messages):
    """Test that OpenAI tools format is correctly converted to Anthropic format."""
    openai_tools = [
        {
            "function": {
                "name": "search_files",
                "description": "Search for files in repository",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                },
            }
        }
    ]
    
    mock_response = MockResponse([MockContentBlock("text", text="Test")])
    mock_client.messages.create.return_value = mock_response

    with patch("services.anthropic.chat_with_functions.get_anthropic_client", return_value=mock_client), \
         patch("services.anthropic.chat_with_functions.trim_messages_to_token_limit", return_value=sample_messages):
        
        chat_with_claude(
            messages=sample_messages,
            system_content="Test",
            tools=openai_tools,
        )

        # Verify tools were converted correctly
        call_args = mock_client.messages.create.call_args
        anthropic_tools = call_args[1]["tools"]
        
        assert len(anthropic_tools) == 1
        assert anthropic_tools[0]["name"] == "search_files"
        assert anthropic_tools[0]["description"] == "Search for files in repository"
        assert anthropic_tools[0]["input_schema"]["type"] == "object"
        assert "query" in anthropic_tools[0]["input_schema"]["properties"]


def test_chat_with_claude_overloaded_error(mock_client, sample_messages, sample_tools):
    """Test that OverloadedError is properly handled."""
    mock_client.messages.create.side_effect = OverloadedError("API overloaded")

    with patch("services.anthropic.chat_with_functions.get_anthropic_client", return_value=mock_client), \
         patch("services.anthropic.chat_with_functions.trim_messages_to_token_limit", return_value=sample_messages):
        
        with pytest.raises(ClaudeOverloadedError) as exc_info:
            chat_with_claude(
                messages=sample_messages,
                system_content="Test",
                tools=sample_tools,
            )
        
        assert "Claude API is overloaded (529)" in str(exc_info.value)


def test_chat_with_claude_authentication_error(mock_client, sample_messages, sample_tools):
    """Test that AuthenticationError is properly handled."""
    mock_client.messages.create.side_effect = AuthenticationError("Invalid API key")

    with patch("services.anthropic.chat_with_functions.get_anthropic_client", return_value=mock_client), \
         patch("services.anthropic.chat_with_functions.trim_messages_to_token_limit", return_value=sample_messages):
        
        with pytest.raises(ClaudeAuthenticationError) as exc_info:
            chat_with_claude(
                messages=sample_messages,
                system_content="Test",
                tools=sample_tools,
            )
        
        assert "Claude API authentication failed (401)" in str(exc_info.value)


def test_chat_with_claude_multiple_tool_uses(mock_client, sample_messages, sample_tools):
    """Test that only the first tool use is processed when multiple are present."""
    tool_use_data_1 = {"id": "toolu_1", "name": "tool_1", "input": {"param": "value1"}}
    tool_use_data_2 = {"id": "toolu_2", "name": "tool_2", "input": {"param": "value2"}}
    
    mock_response = MockResponse([
        MockContentBlock("tool_use", tool_use_data=tool_use_data_1),
        MockContentBlock("tool_use", tool_use_data=tool_use_data_2)
    ])
    mock_client.messages.create.return_value = mock_response

    with patch("services.anthropic.chat_with_functions.get_anthropic_client", return_value=mock_client), \
         patch("services.anthropic.chat_with_functions.trim_messages_to_token_limit", return_value=sample_messages):
        
        result = chat_with_claude(
            messages=sample_messages,
            system_content="Test",
            tools=sample_tools,
        )

        assistant_message, tool_call_id, tool_name, tool_args, _, _ = result

        # Should only process the first tool use
        assert tool_call_id == "toolu_1"
        assert tool_name == "tool_1"
        assert tool_args == {"param": "value1"}
        
        # But assistant message should contain only the first tool use
        assert len(assistant_message["content"]) == 1
        assert assistant_message["content"][0]["id"] == "toolu_1"