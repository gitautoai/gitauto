from unittest.mock import Mock, patch

import pytest
from anthropic import AuthenticationError
from anthropic._exceptions import OverloadedError
from services.anthropic.chat_with_functions import chat_with_claude
from services.anthropic.exceptions import (ClaudeAuthenticationError,
                                           ClaudeOverloadedError)


class TestChatWithClaude:
    """Test cases for chat_with_claude function."""

    @pytest.fixture
    def mock_claude_response(self):
        """Mock Claude API response."""
        mock_response = Mock()
        mock_response.content = [
            Mock(type="text", text="Hello, how can I help you?")
        ]
        return mock_response

    @pytest.fixture
    def mock_claude_response_with_tool_use(self):
        """Mock Claude API response with tool use."""
        mock_response = Mock()
        mock_text_block = Mock(type="text", text="I'll help you with that.")
        mock_tool_block = Mock(
            type="tool_use",
            id="toolu_01M3mtjuKhyQptQh5ASmQCFY",
            name="get_file_content",
            input={"file_path": "test.py"}
        )
        mock_response.content = [mock_text_block, mock_tool_block]
        return mock_response

    @pytest.fixture
    def sample_messages(self):
        """Sample messages for testing."""
        return [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

    @pytest.fixture
    def sample_tools(self):
        """Sample tools for testing."""
        return [
            {
                "function": {
                    "name": "get_file_content",
                    "description": "Get content of a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to the file"}
                        },
                        "required": ["file_path"]
                    }
                }
            }
        ]

    @patch('services.anthropic.chat_with_functions.trim_messages_to_token_limit')
    @patch('services.anthropic.chat_with_functions.claude')
    def test_chat_with_claude_successful_response(
        self, mock_claude, mock_trim_messages, mock_claude_response, sample_messages, sample_tools
    ):
        """Test successful chat with Claude without tool use."""
        # Setup mocks
        mock_trim_messages.return_value = sample_messages
        mock_claude.messages.create.return_value = mock_claude_response
        mock_token_response = Mock()
        mock_token_response.input_tokens = 1000
        mock_claude.messages.count_tokens.return_value = mock_token_response

        # Call function - this should not raise any errors
        result = chat_with_claude(
            messages=sample_messages,
            system_content="You are a helpful assistant",
            tools=sample_tools
        )

        # Basic verification that function returns expected structure
        assert result is not None
        assert len(result) == 6  # Should return 6 values
        assistant_message, tool_call_id, tool_name, tool_args, token_input, token_output = result
        assert assistant_message["role"] == "assistant"
        assert "content" in assistant_message
        assert isinstance(assistant_message["content"], list)
        assert len(assistant_message["content"]) == 1
        assert assistant_message["content"][0]["type"] == "text"
        assert assistant_message["content"][0]["text"] == "Hello, how can I help you?"
        assert tool_call_id is None
        assert tool_name is None
        assert tool_args is None
        assert token_input == 1000
        assert token_output == 0

    @patch('services.anthropic.chat_with_functions.trim_messages_to_token_limit')
    @patch('services.anthropic.chat_with_functions.claude')
    def test_chat_with_claude_with_tool_use(
        self, mock_claude, mock_trim_messages, mock_claude_response_with_tool_use, sample_messages, sample_tools
    ):
        """Test successful chat with Claude with tool use."""
        # Setup mocks
        mock_trim_messages.return_value = sample_messages
        mock_claude.messages.create.return_value = mock_claude_response_with_tool_use
        mock_token_response = Mock()
        mock_token_response.input_tokens = 1500
        mock_claude.messages.count_tokens.return_value = mock_token_response

        # Call function
        result = chat_with_claude(
            messages=sample_messages,
            system_content="You are a helpful assistant",
            tools=sample_tools
        )

        # Verify response structure
        assistant_message, tool_call_id, tool_name, tool_args, token_input, token_output = result
        assert assistant_message["role"] == "assistant"
        assert len(assistant_message["content"]) == 2

        # Check text content
        text_content = assistant_message["content"][0]
        assert text_content["type"] == "text"
        assert text_content["text"] == "I'll help you with that."

        # Check tool use content
        tool_content = assistant_message["content"][1]
        assert tool_content["type"] == "tool_use"
        assert tool_content["id"] == "toolu_01M3mtjuKhyQptQh5ASmQCFY"
        assert tool_content["name"] == "get_file_content"
        assert tool_content["input"] == {"file_path": "test.py"}

        # Check extracted tool information
        assert tool_call_id == "toolu_01M3mtjuKhyQptQh5ASmQCFY"
        assert tool_name == "get_file_content"
        assert tool_args == {"file_path": "test.py"}
        assert token_input == 1500
        assert token_output == 0

    @patch('services.anthropic.chat_with_functions.trim_messages_to_token_limit')
    @patch('services.anthropic.chat_with_functions.claude')
    def test_chat_with_claude_overloaded_error(
        self, mock_claude, mock_trim_messages, sample_messages, sample_tools
    ):
        """Test Claude API overloaded error handling."""
        # Setup mocks
        mock_trim_messages.return_value = sample_messages
        mock_claude.messages.create.side_effect = OverloadedError("API overloaded")

        # Call function and expect ClaudeOverloadedError
        with pytest.raises(ClaudeOverloadedError, match="Claude API is overloaded \\(529\\)"):
            chat_with_claude(
                messages=sample_messages,
                system_content="You are a helpful assistant",
                tools=sample_tools
            )

    @patch('services.anthropic.chat_with_functions.trim_messages_to_token_limit')
    @patch('services.anthropic.chat_with_functions.claude')
    def test_chat_with_claude_authentication_error(
        self, mock_claude, mock_trim_messages, sample_messages, sample_tools
    ):
        """Test Claude API authentication error handling."""
        # Setup mocks
        mock_trim_messages.return_value = sample_messages
        mock_claude.messages.create.side_effect = AuthenticationError("Invalid API key")

        # Call function and expect ClaudeAuthenticationError
        with pytest.raises(ClaudeAuthenticationError, match="Claude API authentication failed \\(401\\)"):
            chat_with_claude(
                messages=sample_messages,
                system_content="You are a helpful assistant",
                tools=sample_tools
            )

    @patch('services.anthropic.chat_with_functions.trim_messages_to_token_limit')
    @patch('services.anthropic.chat_with_functions.claude')
    def test_chat_with_claude_no_tools(
        self, mock_claude, mock_trim_messages, mock_claude_response, sample_messages
    ):
        """Test successful chat with Claude with no tools provided."""
        # Setup mocks
        mock_trim_messages.return_value = sample_messages
        mock_claude.messages.create.return_value = mock_claude_response
        mock_token_response = Mock()
        mock_token_response.input_tokens = 800
        mock_claude.messages.count_tokens.return_value = mock_token_response

        # Call function with empty tools list
        result = chat_with_claude(
            messages=sample_messages,
            system_content="You are a helpful assistant",
            tools=[]
        )

