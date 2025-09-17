# Standard imports
import json
from unittest import mock

# Local imports
from config import UTF8
from services.openai.chat_with_functions import chat_with_openai


def test_claude_to_openai_message_conversion():
    # Load test messages from test_messages.json
    with open("services/anthropic/test_messages.json", "r", encoding=UTF8) as f:
        claude_messages = json.load(f)

    # Mock the OpenAI client and its response
    mock_client = mock.MagicMock()
    mock_completion = mock.MagicMock()
    mock_choice = mock.MagicMock()
    mock_message = mock.MagicMock()

    # Configure the mock response
    mock_message.role = "assistant"
    mock_message.content = "Test response"
    mock_message.tool_calls = None
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_completion

    # Mock the create_openai_client function
    with mock.patch(
        "services.openai.chat_with_functions.create_openai_client",
        return_value=mock_client,
    ):
        # Call chat_with_openai with Claude-format messages
        (
            _response_message,
            _tool_call_id,
            _tool_name,
            _tool_args,
            _token_input,
            _token_output,
        ) = chat_with_openai(
            messages=claude_messages,
            system_content="Test system content",
            tools=[
                {
                    "function": {
                        "name": "get_remote_file_content",
                        "description": "Get content of a remote file",
                        "parameters": {
                            "type": "object",
                            "properties": {"file_path": {"type": "string"}},
                        },
                    }
                }
            ],
        )

        # Get the actual messages sent to OpenAI
        actual_messages = mock_client.chat.completions.create.call_args[1]["messages"]

        # Verify system message
        assert actual_messages[0]["role"] == "developer"
        assert actual_messages[0]["content"] == "Test system content"

        # Verify user message conversion
        assert actual_messages[1]["role"] == "user"
        assert actual_messages[1]["content"] == "First message"

        # Verify assistant message with tool use
        assert actual_messages[2]["role"] == "assistant"
        assert actual_messages[2]["content"] == "Second message"
        assert "tool_calls" in actual_messages[2]

        # Verify tool result message conversion
        assert actual_messages[3]["role"] == "tool"
        assert actual_messages[3]["tool_call_id"] == "toolu_01UqpdeuMtRAfShXJjZnM1xr"
        assert actual_messages[3]["name"] == "get_remote_file_content"
        assert "Opened file" in actual_messages[3]["content"]


def test_claude_error_fallback_to_openai():
    # Load test messages from test_messages.json
    with open("services/anthropic/test_messages.json", "r", encoding=UTF8) as f:
        claude_messages = json.load(f)

    # Mock the OpenAI client and its response
    mock_client = mock.MagicMock()
    mock_completion = mock.MagicMock()
    mock_choice = mock.MagicMock()
    mock_message = mock.MagicMock()

    # Configure the mock response
    mock_message.role = "assistant"
    mock_message.content = "Test response"
    mock_message.tool_calls = None
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_completion

    # Mock the create_openai_client function
    with mock.patch(
        "services.openai.chat_with_functions.create_openai_client",
        return_value=mock_client,
    ):
        # Call chat_with_openai with Claude-format messages
        (
            _response_message,
            _tool_call_id,
            _tool_name,
            _tool_args,
            _token_input,
            _token_output,
        ) = chat_with_openai(
            messages=claude_messages,
            system_content="Test system content",
            tools=[
                {
                    "function": {
                        "name": "get_remote_file_content",
                        "description": "Get content of a remote file",
                        "parameters": {
                            "type": "object",
                            "properties": {"file_path": {"type": "string"}},
                        },
                    }
                }
            ],
        )

        # Verify that the messages were properly converted and sent to OpenAI
        actual_messages = mock_client.chat.completions.create.call_args[1]["messages"]

        # Verify that tool result messages were properly converted
        tool_messages = [msg for msg in actual_messages if msg["role"] == "tool"]
        assert len(tool_messages) > 0

        for tool_msg in tool_messages:
            assert "tool_call_id" in tool_msg
            assert "name" in tool_msg
            assert "content" in tool_msg


@mock.patch("services.openai.chat_with_functions.insert_llm_request")
def test_chat_with_openai_logs_request(mock_insert_llm_request):
    mock_client = mock.MagicMock()
    mock_completion = mock.MagicMock()
    mock_choice = mock.MagicMock()
    mock_message = mock.MagicMock()
    mock_usage = mock.MagicMock()

    mock_message.role = "assistant"
    mock_message.content = "Test response"
    mock_message.tool_calls = None
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_completion.usage = mock_usage
    mock_usage.prompt_tokens = 15
    mock_usage.completion_tokens = 10
    mock_client.chat.completions.create.return_value = mock_completion

    with mock.patch(
        "services.openai.chat_with_functions.create_openai_client",
        return_value=mock_client,
    ):
        result = chat_with_openai(
            messages=[{"role": "user", "content": "Hello"}],
            system_content="You are helpful",
            tools=[],
            usage_id=456,
        )

        assert result[4] == 15  # input tokens
        assert result[5] == 10  # output tokens

        mock_insert_llm_request.assert_called_once()
        call_args = mock_insert_llm_request.call_args[1]
        assert call_args["usage_id"] == 456
        assert call_args["provider"] == "openai"
        assert call_args["input_tokens"] == 15
        assert call_args["output_tokens"] == 10
