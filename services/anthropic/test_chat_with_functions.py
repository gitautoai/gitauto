from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

import pytest
from anthropic import AuthenticationError
from anthropic._exceptions import OverloadedError
from anthropic.types import MessageParam, ToolUseBlock
from config import ANTHROPIC_MODEL_ID_37, ANTHROPIC_MODEL_ID_40
from services.anthropic.chat_with_functions import chat_with_claude
from services.anthropic.exceptions import (ClaudeAuthenticationError,
                                           ClaudeOverloadedError)


class TestChatWithClaude:
    """Test cases for chat_with_claude function."""

    @pytest.fixture
    def mock_claude_client(self):
        """Mock Claude client with proper message creation and token counting."""
        mock_client = Mock()
        mock_messages = Mock()
        mock_client.messages = mock_messages

        # Mock count_tokens to return a mock with input_tokens attribute
        mock_token_response = Mock()
        mock_token_response.input_tokens = 1000
        mock_messages.count_tokens.return_value = mock_token_response

        return mock_client

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

        # Create a mock tool use block
        mock_tool_use = Mock(spec=ToolUseBlock)
        mock_tool_use.type = "tool_use"
        mock_tool_use.id = "toolu_01M3mtjuKhyQptQh5ASmQCFY"
        mock_tool_use.name = "apply_diff_to_file"
        mock_tool_use.input = {"file_path": "test.py", "diff": "test diff"}

        mock_response.content = [
            Mock(type="text", text="I'll help you with that."),
            mock_tool_use
        ]
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
                    "name": "apply_diff_to_file",
                    "description": "Apply a diff to a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"},
                            "diff": {"type": "string"}
                        }
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

        # Call function
        result = chat_with_claude(
            messages=sample_messages,
            system_content="You are a helpful assistant",
            tools=sample_tools
        )

        # Verify result structure
        assistant_message, tool_call_id, tool_name, tool_args, token_input, token_output = result

        assert assistant_message["role"] == "assistant"
        assert len(assistant_message["content"]) == 1
        assert assistant_message["content"][0]["type"] == "text"
        assert assistant_message["content"][0]["text"] == "Hello, how can I help you?"
        assert tool_call_id is None
        assert tool_name is None
        assert tool_args is None
        assert token_input == 1000
        assert token_output == 0

        # Verify Claude API was called correctly
        mock_claude.messages.create.assert_called_once()
        call_args = mock_claude.messages.create.call_args
        assert call_args[1]["model"] == ANTHROPIC_MODEL_ID_40
        assert call_args[1]["system"] == "You are a helpful assistant"
        assert call_args[1]["messages"] == sample_messages
        assert call_args[1]["max_tokens"] == 64000
        assert call_args[1]["temperature"] == 0.0

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

        # Verify result structure
        assistant_message, tool_call_id, tool_name, tool_args, token_input, token_output = result

        assert assistant_message["role"] == "assistant"
        assert len(assistant_message["content"]) == 2

        # Check text content
        assert assistant_message["content"][0]["type"] == "text"
        assert assistant_message["content"][0]["text"] == "I'll help you with that."

        # Check tool use content
        assert assistant_message["content"][1]["type"] == "tool_use"
        assert assistant_message["content"][1]["id"] == "toolu_01M3mtjuKhyQptQh5ASmQCFY"
        assert assistant_message["content"][1]["name"] == "apply_diff_to_file"
        assert assistant_message["content"][1]["input"] == {"file_path": "test.py", "diff": "test diff"}

        # Check extracted tool information
        assert tool_call_id == "toolu_01M3mtjuKhyQptQh5ASmQCFY"
        assert tool_name == "apply_diff_to_file"
        assert tool_args == {"file_path": "test.py", "diff": "test diff"}
        assert token_input == 1500
        assert token_output == 0

    @patch('services.anthropic.chat_with_functions.trim_messages_to_token_limit')
    @patch('services.anthropic.chat_with_functions.claude')
    def test_chat_with_claude_with_different_model(
        self, mock_claude, mock_trim_messages, mock_claude_response, sample_messages, sample_tools
    ):
        """Test chat with Claude using a different model."""
        # Setup mocks
        mock_trim_messages.return_value = sample_messages
        mock_claude.messages.create.return_value = mock_claude_response
        mock_token_response = Mock()
        mock_token_response.input_tokens = 800
        mock_claude.messages.count_tokens.return_value = mock_token_response

        # Call function with different model
        result = chat_with_claude(
            messages=sample_messages,
            system_content="You are a helpful assistant",
            tools=sample_tools,
            model_id=ANTHROPIC_MODEL_ID_37
        )

        # Verify Claude API was called with correct model
        mock_claude.messages.create.assert_called_once()
        call_args = mock_claude.messages.create.call_args
        assert call_args[1]["model"] == ANTHROPIC_MODEL_ID_37
        assert call_args[1]["max_tokens"] == 64000  # Should still be 64000 for this model

    @patch('services.anthropic.chat_with_functions.trim_messages_to_token_limit')
    @patch('services.anthropic.chat_with_functions.claude')
    def test_chat_with_claude_with_legacy_model(
        self, mock_claude, mock_trim_messages, mock_claude_response, sample_messages, sample_tools
    ):
        """Test chat with Claude using a legacy model with different token limits."""
        # Setup mocks
        mock_trim_messages.return_value = sample_messages
        mock_claude.messages.create.return_value = mock_claude_response
        mock_token_response = Mock()
        mock_token_response.input_tokens = 500
        mock_claude.messages.count_tokens.return_value = mock_token_response

        # Call function with legacy model
        result = chat_with_claude(
            messages=sample_messages,
            system_content="You are a helpful assistant",
            tools=sample_tools,
            model_id="claude-3-haiku-20240307"  # Legacy model
        )

        # Verify Claude API was called with correct max_tokens for legacy model
        mock_claude.messages.create.assert_called_once()
        call_args = mock_claude.messages.create.call_args
        assert call_args[1]["model"] == "claude-3-haiku-20240307"
        assert call_args[1]["max_tokens"] == 8192  # Should be 8192 for legacy models

    @patch('services.anthropic.chat_with_functions.trim_messages_to_token_limit')
    @patch('services.anthropic.chat_with_functions.claude')
    def test_chat_with_claude_overloaded_error(
        self, mock_claude, mock_trim_messages, sample_messages, sample_tools
    ):
        """Test handling of OverloadedError from Claude API."""
        # Setup mocks
        mock_trim_messages.return_value = sample_messages
        mock_claude.messages.create.side_effect = OverloadedError("API overloaded")

        # Verify exception is raised and converted
        with pytest.raises(ClaudeOverloadedError) as exc_info:
            chat_with_claude(
                messages=sample_messages,
                system_content="You are a helpful assistant",
                tools=sample_tools
            )

        assert str(exc_info.value) == "Claude API is overloaded (529)"
        assert exc_info.value.__cause__.__class__ == OverloadedError

    @patch('services.anthropic.chat_with_functions.trim_messages_to_token_limit')
    @patch('services.anthropic.chat_with_functions.claude')
    def test_chat_with_claude_authentication_error(
        self, mock_claude, mock_trim_messages, sample_messages, sample_tools
    ):
        """Test handling of AuthenticationError from Claude API."""
        # Setup mocks
        mock_trim_messages.return_value = sample_messages
        mock_claude.messages.create.side_effect = AuthenticationError("Invalid API key")

        # Verify exception is raised and converted
        with pytest.raises(ClaudeAuthenticationError) as exc_info:
            chat_with_claude(
                messages=sample_messages,
                system_content="You are a helpful assistant",
                tools=sample_tools
            )

        assert str(exc_info.value) == "Claude API authentication failed (401)"
        assert exc_info.value.__cause__.__class__ == AuthenticationError

    @patch('services.anthropic.chat_with_functions.trim_messages_to_token_limit')
    @patch('services.anthropic.chat_with_functions.claude')
    def test_chat_with_claude_empty_tools(
        self, mock_claude, mock_trim_messages, mock_claude_response, sample_messages
    ):
        """Test chat with Claude with empty tools list."""
        # Setup mocks
        mock_trim_messages.return_value = sample_messages
        mock_claude.messages.create.return_value = mock_claude_response
        mock_token_response = Mock()
        mock_token_response.input_tokens = 900
        mock_claude.messages.count_tokens.return_value = mock_token_response

        # Call function with empty tools
        result = chat_with_claude(
            messages=sample_messages,
            system_content="You are a helpful assistant",
            tools=[]
        )

        # Verify Claude API was called with empty tools
        mock_claude.messages.create.assert_called_once()
        call_args = mock_claude.messages.create.call_args
        assert call_args[1]["tools"] == []

    @patch('services.anthropic.chat_with_functions.trim_messages_to_token_limit')
    @patch('services.anthropic.chat_with_functions.claude')
    def test_chat_with_claude_malformed_tools(
        self, mock_claude, mock_trim_messages, mock_claude_response, sample_messages
    ):
        """Test chat with Claude with malformed tools."""
        # Setup mocks
        mock_trim_messages.return_value = sample_messages
        mock_claude.messages.create.return_value = mock_claude_response
        mock_token_response = Mock()
        mock_token_response.input_tokens = 900
        mock_claude.messages.count_tokens.return_value = mock_token_response

        # Malformed tools - missing required fields
        malformed_tools = [
            {"function": {"name": "test_tool"}},  # Missing description
            {"function": {"description": "A test tool"}},  # Missing name
            {"function": {}},  # Missing both name and description
            {"not_function": {"name": "invalid", "description": "Invalid structure"}},  # Wrong structure
        ]

        # Call function with malformed tools
        result = chat_with_claude(
            messages=sample_messages,
            system_content="You are a helpful assistant",
            tools=malformed_tools
        )

        # Verify Claude API was called with empty tools (malformed tools filtered out)
        mock_claude.messages.create.assert_called_once()
        call_args = mock_claude.messages.create.call_args
        assert call_args[1]["tools"] == []

    @patch('services.anthropic.chat_with_functions.trim_messages_to_token_limit')
    @patch('services.anthropic.chat_with_functions.claude')
    def test_chat_with_claude_tools_with_object_function(
        self, mock_claude, mock_trim_messages, mock_claude_response, sample_messages
    ):
        """Test chat with Claude where tools have function as object instead of dict."""
        # Setup mocks
        mock_trim_messages.return_value = sample_messages
        mock_claude.messages.create.return_value = mock_claude_response
        mock_token_response = Mock()
        mock_token_response.input_tokens = 900
        mock_claude.messages.count_tokens.return_value = mock_token_response

        # Tools with function as object
        function_obj = SimpleNamespace(
            name="test_function",
            description="A test function",
            parameters={"type": "object", "properties": {}}
        )
        tools_with_object = [{"function": function_obj}]

        # Call function
        result = chat_with_claude(
            messages=sample_messages,
            system_content="You are a helpful assistant",
            tools=tools_with_object
        )

        # Verify Claude API was called with properly converted tools
        mock_claude.messages.create.assert_called_once()
        call_args = mock_claude.messages.create.call_args
        expected_tools = [{
            "name": "test_function",
            "description": "A test function",
            "input_schema": {"type": "object", "properties": {}}
        }]
        assert call_args[1]["tools"] == expected_tools

    @patch('services.anthropic.chat_with_functions.trim_messages_to_token_limit')
    @patch('services.anthropic.chat_with_functions.claude')
    def test_chat_with_claude_response_with_only_tool_use(
        self, mock_claude, mock_trim_messages, sample_messages, sample_tools
    ):
        """Test Claude response that contains only tool use, no text."""
        # Setup mocks
        mock_trim_messages.return_value = sample_messages

        # Mock response with only tool use
        mock_response = Mock()
        mock_tool_use = Mock(spec=ToolUseBlock)
        mock_tool_use.type = "tool_use"
        mock_tool_use.id = "toolu_123"
        mock_tool_use.name = "test_tool"
        mock_tool_use.input = {"param": "value"}

        mock_response.content = [mock_tool_use]
        mock_claude.messages.create.return_value = mock_response

        mock_token_response = Mock()
        mock_token_response.input_tokens = 1200
        mock_claude.messages.count_tokens.return_value = mock_token_response

        # Call function
        result = chat_with_claude(
            messages=sample_messages,
            system_content="You are a helpful assistant",
            tools=sample_tools
        )

        # Verify result structure
        assistant_message, tool_call_id, tool_name, tool_args, token_input, token_output = result

        # Should only have tool use content, no text content
        assert assistant_message["role"] == "assistant"
        assert len(assistant_message["content"]) == 1
        assert assistant_message["content"][0]["type"] == "tool_use"
        assert assistant_message["content"][0]["id"] == "toolu_123"
        assert assistant_message["content"][0]["name"] == "test_tool"
        assert assistant_message["content"][0]["input"] == {"param": "value"}

    @patch('services.anthropic.chat_with_functions.trim_messages_to_token_limit')
    @patch('services.anthropic.chat_with_functions.claude')
    def test_chat_with_claude_response_with_empty_text(
        self, mock_claude, mock_trim_messages, sample_messages, sample_tools
    ):
        """Test Claude response with empty text content."""
        # Setup mocks
        mock_trim_messages.return_value = sample_messages

        # Mock response with empty text
        mock_response = Mock()
        mock_response.content = [
            Mock(type="text", text="")  # Empty text
        ]
        mock_claude.messages.create.return_value = mock_response

        mock_token_response = Mock()
        mock_token_response.input_tokens = 800
        mock_claude.messages.count_tokens.return_value = mock_token_response

        # Call function
        result = chat_with_claude(
            messages=sample_messages,
            system_content="You are a helpful assistant",
            tools=sample_tools
        )

        # Verify result structure - empty text should not be included
        assistant_message, tool_call_id, tool_name, tool_args, token_input, token_output = result

        assert assistant_message["role"] == "assistant"
        assert len(assistant_message["content"]) == 0  # Empty text should not be added

    @patch('services.anthropic.chat_with_functions.trim_messages_to_token_limit')
    @patch('services.anthropic.chat_with_functions.claude')
    def test_chat_with_claude_multiple_tool_use_blocks(

    @patch('services.anthropic.chat_with_functions.trim_messages_to_token_limit')
    @patch('services.anthropic.chat_with_functions.claude')
    def test_chat_with_claude_multiple_text_blocks(
        self, mock_claude, mock_trim_messages, sample_messages, sample_tools
    ):
        """Test Claude response with multiple text blocks that should be concatenated."""
        # Setup mocks
        mock_trim_messages.return_value = sample_messages

        # Mock response with multiple text blocks
        mock_response = Mock()
        mock_response.content = [
            Mock(type="text", text="First part of the response. "),
            Mock(type="text", text="Second part of the response. "),
            Mock(type="text", text="Third part of the response.")
        ]
        mock_claude.messages.create.return_value = mock_response

        mock_token_response = Mock()
        mock_token_response.input_tokens = 1100
        mock_claude.messages.count_tokens.return_value = mock_token_response

        # Call function
        result = chat_with_claude(
            messages=sample_messages,
            system_content="You are a helpful assistant",
            tools=sample_tools
        )

        # Verify result structure - text should be concatenated
        assistant_message, tool_call_id, tool_name, tool_args, token_input, token_output = result

        assert assistant_message["role"] == "assistant"
        assert len(assistant_message["content"]) == 1
        assert assistant_message["content"][0]["type"] == "text"
        assert assistant_message["content"][0]["text"] == "First part of the response. Second part of the response. Third part of the response."

        # No tool use
        assert tool_call_id is None
        assert tool_name is None
        assert tool_args is None
        assert token_input == 1100
        assert token_output == 0
        self, mock_claude, mock_trim_messages, sample_messages, sample_tools
    ):
        """Test Claude response with multiple tool use blocks (only first should be processed)."""
        # Setup mocks
        mock_trim_messages.return_value = sample_messages

        # Mock response with multiple tool use blocks
        mock_response = Mock()
        mock_tool_use_1 = Mock(spec=ToolUseBlock)
        mock_tool_use_1.type = "tool_use"
        mock_tool_use_1.id = "toolu_first"
        mock_tool_use_1.name = "first_tool"
        mock_tool_use_1.input = {"param": "first"}

        mock_tool_use_2 = Mock(spec=ToolUseBlock)
        mock_tool_use_2.type = "tool_use"
        mock_tool_use_2.id = "toolu_second"
        mock_tool_use_2.name = "second_tool"
        mock_tool_use_2.input = {"param": "second"}

        mock_response.content = [
            Mock(type="text", text="I'll use multiple tools."),
            mock_tool_use_1,
            mock_tool_use_2
        ]
        mock_claude.messages.create.return_value = mock_response

        mock_token_response = Mock()
        mock_token_response.input_tokens = 1800
        mock_claude.messages.count_tokens.return_value = mock_token_response

        # Call function
        result = chat_with_claude(
            messages=sample_messages,
            system_content="You are a helpful assistant",
            tools=sample_tools
        )

        # Verify result structure - should only process first tool use
        assistant_message, tool_call_id, tool_name, tool_args, token_input, token_output = result

        assert assistant_message["role"] == "assistant"
        assert len(assistant_message["content"]) == 2  # Text + first tool use only

        # Check that only the first tool use is returned in extracted values
        assert tool_call_id == "toolu_first"
        assert tool_name == "first_tool"
        assert tool_args == {"param": "first"}

    @patch('services.anthropic.chat_with_functions.trim_messages_to_token_limit')
    def test_trim_messages_called_with_correct_parameters(self, mock_trim_messages, sample_messages, sample_tools):
        """Test that trim_messages_to_token_limit is called with correct parameters."""
        with patch('services.anthropic.chat_with_functions.claude') as mock_claude:
            # Setup mocks
            mock_trim_messages.return_value = sample_messages
            mock_response = Mock()
            mock_response.content = [Mock(type="text", text="Test response")]
            mock_claude.messages.create.return_value = mock_response
            mock_token_response = Mock()
            mock_token_response.input_tokens = 1000
            mock_claude.messages.count_tokens.return_value = mock_token_response

            # Call function with default model
            chat_with_claude(
                messages=sample_messages,
                system_content="You are a helpful assistant",
                tools=sample_tools
            )

            # Verify trim_messages was called with correct parameters
            mock_trim_messages.assert_called_once()
            call_args = mock_trim_messages.call_args
            assert call_args[1]["messages"] == sample_messages
            assert call_args[1]["client"] == mock_claude
            assert call_args[1]["model"] == ANTHROPIC_MODEL_ID_40
            assert call_args[1]["max_input"] == 200_000 - 64000 - 4096  # max_input calculation

    @patch('services.anthropic.chat_with_functions.trim_messages_to_token_limit')
    def test_trim_messages_called_with_legacy_model_parameters(self, mock_trim_messages, sample_messages, sample_tools):
        """Test that trim_messages_to_token_limit is called with correct parameters for legacy model."""
        with patch('services.anthropic.chat_with_functions.claude') as mock_claude:
            # Setup mocks
            mock_trim_messages.return_value = sample_messages
            mock_response = Mock()
            mock_response.content = [Mock(type="text", text="Test response")]
            mock_claude.messages.create.return_value = mock_response
            mock_token_response = Mock()
            mock_token_response.input_tokens = 1000
            mock_claude.messages.count_tokens.return_value = mock_token_response

            # Call function with legacy model
            legacy_model = "claude-3-haiku-20240307"
            chat_with_claude(
                messages=sample_messages,
                system_content="You are a helpful assistant",
                tools=sample_tools,
                model_id=legacy_model
            )

            # Verify trim_messages was called with correct parameters for legacy model
            mock_trim_messages.assert_called_once()
            call_args = mock_trim_messages.call_args
            assert call_args[1]["model"] == legacy_model
            assert call_args[1]["max_input"] == 200_000 - 8192 - 4096  # max_input calculation for legacy model
