# Standard imports
import json
from unittest.mock import MagicMock, patch

import pytest
# Local imports
from config import UTF8
from services.openai.chat_with_functions import (chat_with_openai,
                                                 convert_tool_result,
                                                 find_function_name)


def test_claude_to_openai_message_conversion():
    """Test conversion of Claude-format messages to OpenAI format"""
    with open("services/anthropic/test_messages.json", "r", encoding=UTF8) as f:
        claude_messages = json.load(f)

    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()

    mock_message.role = "assistant"
    mock_message.content = "Test response"
    mock_message.tool_calls = None
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_completion

    with patch(
        "services.openai.chat_with_functions.create_openai_client",
        return_value=mock_client,
    ):
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

        actual_messages = mock_client.chat.completions.create.call_args[1]["messages"]

        assert actual_messages[0]["role"] == "developer"
        assert actual_messages[0]["content"] == "Test system content"

        assert actual_messages[1]["role"] == "user"
        assert actual_messages[1]["content"] == "First message"

        assert actual_messages[2]["role"] == "assistant"
        assert actual_messages[2]["content"] == "Second message"
        assert "tool_calls" in actual_messages[2]

        assert actual_messages[3]["role"] == "tool"
        assert actual_messages[3]["tool_call_id"] == "toolu_01UqpdeuMtRAfShXJjZnM1xr"
        assert actual_messages[3]["name"] == "get_remote_file_content"
        assert "Opened file" in actual_messages[3]["content"]


def test_claude_error_fallback_to_openai():
    """Test that Claude messages are properly converted for OpenAI"""
    with open("services/anthropic/test_messages.json", "r", encoding=UTF8) as f:
        claude_messages = json.load(f)

    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()

    mock_message.role = "assistant"
    mock_message.content = "Test response"
    mock_message.tool_calls = None
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_completion

    with patch(
        "services.openai.chat_with_functions.create_openai_client",
        return_value=mock_client,
    ):
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

        actual_messages = mock_client.chat.completions.create.call_args[1]["messages"]

        tool_messages = [msg for msg in actual_messages if msg["role"] == "tool"]
        assert len(tool_messages) > 0

        for tool_msg in tool_messages:
            assert "tool_call_id" in tool_msg
            assert "name" in tool_msg
            assert "content" in tool_msg


@patch("services.openai.chat_with_functions.insert_llm_request")
def test_chat_with_openai_logs_request(mock_insert_llm_request):
    """Test that LLM requests are properly logged"""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_usage = MagicMock()

    mock_message.role = "assistant"
    mock_message.content = "Test response"
    mock_message.tool_calls = None
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_completion.usage = mock_usage
    mock_usage.prompt_tokens = 15
    mock_usage.completion_tokens = 10
    mock_client.chat.completions.create.return_value = mock_completion

    with patch(
        "services.openai.chat_with_functions.create_openai_client",
        return_value=mock_client,
    ):
        result = chat_with_openai(
            messages=[{"role": "user", "content": "Hello"}],
            system_content="You are helpful",
            tools=[],
            usage_id=456,
        )

        assert result[4] == 15
        assert result[5] == 10

        mock_insert_llm_request.assert_called_once()
        call_args = mock_insert_llm_request.call_args[1]
        assert call_args["usage_id"] == 456
        assert call_args["provider"] == "openai"
        assert call_args["input_tokens"] == 15
        assert call_args["output_tokens"] == 10


def test_find_function_name_found():
    """Test finding function name when tool call ID exists"""
    openai_messages = [
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "call_123",
                    "function": {"name": "test_function", "arguments": "{}"},
                    "type": "function",
                }
            ],
        }
    ]
    result = find_function_name(openai_messages, "call_123")
    assert result == "test_function"


def test_find_function_name_not_found():
    """Test finding function name when tool call ID doesn't exist - covers line 33"""
    openai_messages = [
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "call_123",
                    "function": {"name": "test_function", "arguments": "{}"},
                    "type": "function",
                }
            ],
        }
    ]
    result = find_function_name(openai_messages, "call_999")
    assert result == "unknown_function"


def test_find_function_name_no_tool_calls():
    """Test finding function name when message has no tool_calls - covers line 33"""
    openai_messages = [{"role": "user", "content": "Hello"}]
    result = find_function_name(openai_messages, "call_123")
    assert result == "unknown_function"


def test_convert_tool_result():
    """Test conversion of tool result block"""
    block = {"tool_use_id": "call_123", "content": "Tool result content"}
    openai_messages = [
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "call_123",
                    "function": {"name": "test_function", "arguments": "{}"},
                    "type": "function",
                }
            ],
        }
    ]
    result = convert_tool_result(block, openai_messages)
    assert result["role"] == "tool"
    assert result["tool_call_id"] == "call_123"
    assert result["name"] == "test_function"
    assert result["content"] == "Tool result content"


@patch("services.openai.chat_with_functions.insert_llm_request")
def test_chat_with_openai_with_tool_calls(mock_insert_llm_request):
    """Test chat with tool calls - covers lines 177-184, 193-194, 196"""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_usage = MagicMock()
    mock_tool_call = MagicMock()

    mock_message.role = "assistant"
    mock_message.content = ""
    mock_tool_call.id = "call_abc123"
    mock_tool_call.function.name = "get_file"
    mock_tool_call.function.arguments = '{"file_path": "test.py"}'
    mock_message.tool_calls = [mock_tool_call]
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_completion.usage = mock_usage
    mock_usage.prompt_tokens = 20
    mock_usage.completion_tokens = 15
    mock_client.chat.completions.create.return_value = mock_completion

    with patch(
        "services.openai.chat_with_functions.create_openai_client",
        return_value=mock_client,
    ):
        result = chat_with_openai(
            messages=[{"role": "user", "content": "Get the file"}],
            system_content="You are helpful",
            tools=[
                {
                    "function": {
                        "name": "get_file",
                        "description": "Get a file",
                        "parameters": {
                            "type": "object",
                            "properties": {"file_path": {"type": "string"}},
                        },
                    }
                }
            ],
        )

        response_message, tool_call_id, tool_name, tool_args, input_tokens, output_tokens = result

        assert tool_call_id == "call_abc123"
        assert tool_name == "get_file"
        assert tool_args == {"file_path": "test.py"}
        assert input_tokens == 20
        assert output_tokens == 15
        assert "tool_calls" in response_message
        assert "content" not in response_message


@patch("services.openai.chat_with_functions.insert_llm_request")
def test_chat_with_openai_with_tool_calls_and_content(mock_insert_llm_request):
    """Test chat with tool calls and content - covers lines 177-184, 196"""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_usage = MagicMock()
    mock_tool_call = MagicMock()

    mock_message.role = "assistant"
    mock_message.content = "Let me get that file for you"
    mock_tool_call.id = "call_xyz789"
    mock_tool_call.function.name = "read_file"
    mock_tool_call.function.arguments = '{"path": "example.txt"}'
    mock_message.tool_calls = [mock_tool_call]
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_completion.usage = mock_usage
    mock_usage.prompt_tokens = 25
    mock_usage.completion_tokens = 18
    mock_client.chat.completions.create.return_value = mock_completion

    with patch(
        "services.openai.chat_with_functions.create_openai_client",
        return_value=mock_client,
    ):
        result = chat_with_openai(
            messages=[{"role": "user", "content": "Read example.txt"}],
            system_content="You are helpful",
            tools=[
                {
                    "function": {
                        "name": "read_file",
                        "description": "Read a file",
                        "parameters": {
                            "type": "object",
                            "properties": {"path": {"type": "string"}},
                        },
                    }
                }
            ],
        )

        response_message, tool_call_id, tool_name, tool_args, input_tokens, output_tokens = result

        assert tool_call_id == "call_xyz789"
        assert tool_name == "read_file"
        assert tool_args == {"path": "example.txt"}
        assert "tool_calls" in response_message
        assert "content" in response_message
        assert response_message["content"] == "Let me get that file for you"


@patch("services.openai.chat_with_functions.insert_llm_request")
def test_chat_with_openai_message_with_tool_calls_field(mock_insert_llm_request):
    """Test message with tool_calls field - covers line 73"""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_usage = MagicMock()

    mock_message.role = "assistant"
    mock_message.content = "Response"
    mock_message.tool_calls = None
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_completion.usage = mock_usage
    mock_usage.prompt_tokens = 10
    mock_usage.completion_tokens = 5
    mock_client.chat.completions.create.return_value = mock_completion

    with patch(
        "services.openai.chat_with_functions.create_openai_client",
        return_value=mock_client,
    ):
        messages = [
            {"role": "user", "content": "Hello"},
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "function": {"name": "test_func", "arguments": "{}"},
                        "type": "function",
                    }
                ],
            },
        ]

        chat_with_openai(
            messages=messages,
            system_content="System",
            tools=[],
        )

        actual_messages = mock_client.chat.completions.create.call_args[1]["messages"]
        assert actual_messages[2]["role"] == "assistant"
        assert "tool_calls" in actual_messages[2]


@patch("services.openai.chat_with_functions.insert_llm_request")
def test_chat_with_openai_content_list_without_tool_use_or_result(
    mock_insert_llm_request,
):
    """Test content list without tool_use or tool_result - covers line 109"""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_usage = MagicMock()

    mock_message.role = "assistant"
    mock_message.content = "Response"
    mock_message.tool_calls = None
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_completion.usage = mock_usage
    mock_usage.prompt_tokens = 10
    mock_usage.completion_tokens = 5
    mock_client.chat.completions.create.return_value = mock_completion

    with patch(
        "services.openai.chat_with_functions.create_openai_client",
        return_value=mock_client,
    ):
        messages = [
            {
                "role": "user",
                "content": [{"type": "other", "data": "some data"}],
            }
        ]

        chat_with_openai(
            messages=messages,
            system_content="System",
            tools=[],
        )

        actual_messages = mock_client.chat.completions.create.call_args[1]["messages"]
        assert len(actual_messages) == 1


@patch("services.openai.chat_with_functions.insert_llm_request")
def test_chat_with_openai_tool_use_with_non_text_block(mock_insert_llm_request):
    """Test tool_use with non-text block - covers line 95"""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_usage = MagicMock()

    mock_message.role = "assistant"
    mock_message.content = "Response"
    mock_message.tool_calls = None
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_completion.usage = mock_usage
    mock_usage.prompt_tokens = 10
    mock_usage.completion_tokens = 5
    mock_client.chat.completions.create.return_value = mock_completion

    with patch(
        "services.openai.chat_with_functions.create_openai_client",
        return_value=mock_client,
    ):
        messages = [
            {
                "role": "assistant",
                "content": [
                    {"type": "other", "data": "some data"},
                    {
                        "type": "tool_use",
                        "id": "call_123",
                        "name": "test_func",
                        "input": {"arg": "value"},
                    },
                ],
            }
        ]

        chat_with_openai(
            messages=messages,
            system_content="System",
            tools=[],
        )

        actual_messages = mock_client.chat.completions.create.call_args[1]["messages"]
        assert actual_messages[1]["role"] == "assistant"
        assert "tool_calls" in actual_messages[1]


@patch("services.openai.chat_with_functions.insert_llm_request")
def test_chat_with_openai_tool_result_with_non_result_block(mock_insert_llm_request):
    """Test tool_result with non-result block - covers line 111"""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_usage = MagicMock()

    mock_message.role = "assistant"
    mock_message.content = "Response"
    mock_message.tool_calls = None
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_completion.usage = mock_usage
    mock_usage.prompt_tokens = 10
    mock_usage.completion_tokens = 5
    mock_client.chat.completions.create.return_value = mock_completion

    with patch(
        "services.openai.chat_with_functions.create_openai_client",
        return_value=mock_client,
    ):
        messages = [
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "function": {"name": "test_func", "arguments": "{}"},
                        "type": "function",
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "other", "data": "some data"},
                    {
                        "type": "tool_result",
                        "tool_use_id": "call_123",
                        "content": "Result",
                    },
                ],
            },
        ]

        chat_with_openai(
            messages=messages,
            system_content="System",
            tools=[],
        )

        actual_messages = mock_client.chat.completions.create.call_args[1]["messages"]
        tool_messages = [msg for msg in actual_messages if msg.get("role") == "tool"]
        assert len(tool_messages) == 1


@patch("services.openai.chat_with_functions.insert_llm_request")
def test_chat_with_openai_no_usage_info(mock_insert_llm_request):
    """Test when usage info is None"""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()

    mock_message.role = "assistant"
    mock_message.content = "Response"
    mock_message.tool_calls = None
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_completion.usage = None
    mock_client.chat.completions.create.return_value = mock_completion

    with patch(
        "services.openai.chat_with_functions.create_openai_client",
        return_value=mock_client,
    ):
        result = chat_with_openai(
            messages=[{"role": "user", "content": "Hello"}],
            system_content="System",
            tools=[],
        )

        assert result[4] == 0
        assert result[5] == 0


@patch("services.openai.chat_with_functions.insert_llm_request")
def test_chat_with_openai_tool_use_with_text_block(mock_insert_llm_request):
    """Test tool_use with text block"""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_usage = MagicMock()

    mock_message.role = "assistant"
    mock_message.content = "Response"
    mock_message.tool_calls = None
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_completion.usage = mock_usage
    mock_usage.prompt_tokens = 10
    mock_usage.completion_tokens = 5
    mock_client.chat.completions.create.return_value = mock_completion

    with patch(
        "services.openai.chat_with_functions.create_openai_client",
        return_value=mock_client,
    ):
        messages = [
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Let me help you"},
                    {
                        "type": "tool_use",
                        "id": "call_456",
                        "name": "helper_func",
                        "input": {"param": "test"},
                    },
                ],
            }
        ]

        chat_with_openai(
            messages=messages,
            system_content="System",
            tools=[],
        )

        actual_messages = mock_client.chat.completions.create.call_args[1]["messages"]
        assert actual_messages[1]["role"] == "assistant"
        assert actual_messages[1]["content"] == "Let me help you"
        assert "tool_calls" in actual_messages[1]


@patch("services.openai.chat_with_functions.insert_llm_request")
def test_convert_tool_result_unknown_function(mock_insert_llm_request):
    """Test convert_tool_result when function name is not found"""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_usage = MagicMock()

    mock_message.role = "assistant"
    mock_message.content = "Response"
    mock_message.tool_calls = None
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_completion.usage = mock_usage
    mock_usage.prompt_tokens = 10
    mock_usage.completion_tokens = 5
    mock_client.chat.completions.create.return_value = mock_completion

    with patch(
        "services.openai.chat_with_functions.create_openai_client",
        return_value=mock_client,
    ):
        messages = [
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_existing",
                        "function": {"name": "existing_func", "arguments": "{}"},
                        "type": "function",
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "call_nonexistent",
                        "content": "Result for unknown function",
                    },
                ],
            },
        ]

        chat_with_openai(
            messages=messages,
            system_content="System",
            tools=[],
        )

        actual_messages = mock_client.chat.completions.create.call_args[1]["messages"]
        tool_messages = [msg for msg in actual_messages if msg.get("role") == "tool"]
        assert len(tool_messages) == 1
        assert tool_messages[0]["name"] == "unknown_function"
