from unittest.mock import Mock, patch

import pytest
from anthropic import AuthenticationError
from anthropic._exceptions import OverloadedError
from config import ANTHROPIC_MODEL_ID_40
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
    def sample_messages(self):
        """Sample messages for testing."""
        return [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

    @pytest.fixture
    def sample_tools(self):
        """Sample tools for testing."""
        return []

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
