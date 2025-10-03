from unittest.mock import Mock, patch

import pytest
from anthropic import AuthenticationError
from anthropic._exceptions import OverloadedError
from services.anthropic.chat_with_functions import chat_with_claude
from services.anthropic.exceptions import (ClaudeAuthenticationError,
                                           ClaudeOverloadedError)


@pytest.fixture
def mock_trim_messages():
    with patch(
        "services.anthropic.chat_with_functions.trim_messages_to_token_limit"
    ) as mock:
        mock.side_effect = lambda messages, **kwargs: messages
        yield mock


@pytest.fixture
def mock_deduplication_functions():
    with patch(
        "services.anthropic.chat_with_functions.remove_duplicate_get_remote_file_content_results"
    ) as mock1, patch(
        "services.anthropic.chat_with_functions.remove_get_remote_file_content_before_replace_remote_file_content"
    ) as mock2, patch(
        "services.anthropic.chat_with_functions.remove_outdated_apply_diff_to_file_attempts_and_results"
    ) as mock3:
        mock1.side_effect = lambda messages: messages
        mock2.side_effect = lambda messages: messages
        mock3.side_effect = lambda messages: messages
        yield mock1, mock2, mock3


@patch("services.anthropic.chat_with_functions.insert_llm_request")
@patch("services.anthropic.chat_with_functions.claude")
def test_chat_with_claude_success(
    mock_claude, mock_insert_llm_request, mock_trim_messages, mock_deduplication_functions
):
    mock_response = Mock()
    mock_response.content = [Mock(type="text", text="Hello! How can I help you?")]
    mock_response.usage = Mock(output_tokens=15)

    mock_claude.messages.create.return_value = mock_response
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=20)

    messages = [{"role": "user", "content": "Hello"}]
    system_content = "You are a helpful assistant."
    tools = []

    result = chat_with_claude(
        messages=messages, system_content=system_content, tools=tools, usage_id=123
    )

    assert result[0]["role"] == "assistant"
    assert result[0]["content"][0]["text"] == "Hello! How can I help you?"
    assert result[4] == 20  # input tokens
    assert result[5] == 15  # output tokens

    mock_insert_llm_request.assert_called_once()
    call_args = mock_insert_llm_request.call_args[1]
    assert call_args["usage_id"] == 123
    assert call_args["provider"] == "claude"
    assert call_args["input_tokens"] == 20
    assert call_args["output_tokens"] == 15


@patch("services.anthropic.chat_with_functions.insert_llm_request")
@patch("services.anthropic.chat_with_functions.claude")
def test_chat_with_claude_with_tool_use(
    mock_claude, mock_insert_llm_request, mock_trim_messages, mock_deduplication_functions
):
    mock_tool_use = Mock()
    mock_tool_use.type = "tool_use"
    mock_tool_use.id = "tool_123"
    mock_tool_use.name = "test_function"
    mock_tool_use.input = {"param": "value"}

    mock_response = Mock()
    mock_response.content = [
        Mock(type="text", text="I'll help you with that."),
        mock_tool_use,
    ]
    mock_response.usage = Mock(output_tokens=25)

    mock_claude.messages.create.return_value = mock_response
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=30)

    messages = [{"role": "user", "content": "Do something"}]
    system_content = "You are a helpful assistant."
    tools = [
        {"function": {"name": "test_function", "description": "Test", "parameters": {}}}
    ]

    result = chat_with_claude(
        messages=messages, system_content=system_content, tools=tools, usage_id=None
    )

    assert result[1] == "tool_123"  # tool_call_id
    assert result[2] == "test_function"  # tool_name
    assert result[3] == {"param": "value"}  # tool_args

    mock_insert_llm_request.assert_called_once()
    call_args = mock_insert_llm_request.call_args[1]
    assert call_args["usage_id"] is None
    assert call_args["provider"] == "claude"


@patch("services.anthropic.chat_with_functions.insert_llm_request")
@patch("services.anthropic.chat_with_functions.claude")
def test_chat_with_claude_no_usage_response(
    mock_claude, mock_insert_llm_request, mock_trim_messages, mock_deduplication_functions
):
    mock_response = Mock()
    mock_response.content = [Mock(type="text", text="Response")]
    mock_response.usage = None

    mock_claude.messages.create.return_value = mock_response
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=10)

    result = chat_with_claude(
        messages=[{"role": "user", "content": "test"}],
        system_content="assistant",
        tools=[],
    )

    assert result[5] == 0  # output tokens should be 0 when no usage info
    mock_insert_llm_request.assert_called_once()


@patch("services.anthropic.chat_with_functions.insert_llm_request")
@patch("services.anthropic.chat_with_functions.claude")
def test_chat_with_claude_calls_deduplication(
    mock_claude, mock_insert_llm_request, mock_trim_messages
):
    # Setup mocks
    mock_response = Mock()
    mock_response.content = [Mock(type="text", text="Response")]
    mock_response.usage = Mock(output_tokens=10)
    mock_claude.messages.create.return_value = mock_response
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=15)

    # Mock all three functions to return the same messages
    original_messages = [{"role": "user", "content": "test"}]

    with patch(
        "services.anthropic.chat_with_functions.remove_duplicate_get_remote_file_content_results"
    ) as mock_remove_duplicate, patch(
        "services.anthropic.chat_with_functions.remove_get_remote_file_content_before_replace_remote_file_content"
    ) as mock_remove_get_remote, patch(
        "services.anthropic.chat_with_functions.remove_outdated_apply_diff_to_file_attempts_and_results"
    ) as mock_remove_outdated:
        mock_remove_duplicate.return_value = original_messages
        mock_remove_get_remote.return_value = original_messages
        mock_remove_outdated.return_value = original_messages

        # Call the function
        chat_with_claude(
            messages=original_messages, system_content="You are helpful", tools=[]
        )

        # Verify all three functions were called
        mock_remove_duplicate.assert_called_once_with(original_messages)
        mock_remove_get_remote.assert_called_once_with(original_messages)
        mock_remove_outdated.assert_called_once_with(original_messages)


@patch("services.anthropic.chat_with_functions.insert_llm_request")
@patch("services.anthropic.chat_with_functions.claude")
def test_chat_with_claude_tool_function_not_dict(
    mock_claude, mock_insert_llm_request, mock_trim_messages, mock_deduplication_functions
):
    """Test when tool function is not a dict - should be skipped if attributes not extractable"""
    mock_response = Mock()
    mock_response.content = [Mock(type="text", text="Response")]
    mock_response.usage = Mock(output_tokens=10)

    mock_claude.messages.create.return_value = mock_response
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=15)

    # Create a mock function object (not a dict)
    mock_function = Mock()
    mock_function.name = "test_tool"
    mock_function.description = "A test tool"
    mock_function.parameters = {"type": "object"}

    messages = [{"role": "user", "content": "test"}]
    system_content = "You are helpful"
    tools = [{"function": mock_function}]

    result = chat_with_claude(
        messages=messages, system_content=system_content, tools=tools
    )

    assert result[0]["role"] == "assistant"
    mock_claude.messages.create.assert_called_once()
    # Verify the tool was NOT added because message_to_dict doesn't extract
    # description and parameters attributes, so the tool fails validation
    call_args = mock_claude.messages.create.call_args[1]
    assert len(call_args["tools"]) == 0
    # The tool is skipped because description is missing after conversion


@patch("services.anthropic.chat_with_functions.insert_llm_request")
@patch("services.anthropic.chat_with_functions.claude")
def test_chat_with_claude_tool_missing_name_or_description(
    mock_claude, mock_insert_llm_request, mock_trim_messages, mock_deduplication_functions
):
    """Test when tool is missing name or description (line 69 false branch)"""
    mock_response = Mock()
    mock_response.content = [Mock(type="text", text="Response")]
    mock_response.usage = Mock(output_tokens=10)

    mock_claude.messages.create.return_value = mock_response
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=15)

    messages = [{"role": "user", "content": "test"}]
    system_content = "You are helpful"

    # Tool with missing name
    tools_missing_name = [{"function": {"description": "Test", "parameters": {}}}]

    result = chat_with_claude(
        messages=messages, system_content=system_content, tools=tools_missing_name
    )

    assert result[0]["role"] == "assistant"
    # Verify no tools were added
    call_args = mock_claude.messages.create.call_args[1]
    assert call_args["tools"] == []

    # Tool with missing description
    tools_missing_desc = [{"function": {"name": "test_tool", "parameters": {}}}]

    result = chat_with_claude(
        messages=messages, system_content=system_content, tools=tools_missing_desc
    )

    assert result[0]["role"] == "assistant"
    call_args = mock_claude.messages.create.call_args[1]
    assert call_args["tools"] == []

    # Tool with empty name
    tools_empty_name = [
        {"function": {"name": "", "description": "Test", "parameters": {}}}
    ]

    result = chat_with_claude(
        messages=messages, system_content=system_content, tools=tools_empty_name
    )

    assert result[0]["role"] == "assistant"
    call_args = mock_claude.messages.create.call_args[1]
    assert call_args["tools"] == []


@patch("services.anthropic.chat_with_functions.insert_llm_request")
@patch("services.anthropic.chat_with_functions.claude")
def test_chat_with_claude_overloaded_error(
    mock_claude, mock_insert_llm_request, mock_trim_messages, mock_deduplication_functions
):
    """Test handling of OverloadedError (lines 94-95)"""
    mock_claude.messages.create.side_effect = OverloadedError(
        "Service overloaded", response=Mock(), body=None
    )
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=15)

    messages = [{"role": "user", "content": "test"}]
    system_content = "You are helpful"
    tools = []

    with pytest.raises(ClaudeOverloadedError) as exc_info:
        chat_with_claude(messages=messages, system_content=system_content, tools=tools)

    assert "Claude API is overloaded (529)" in str(exc_info.value)
    mock_insert_llm_request.assert_not_called()


@patch("services.anthropic.chat_with_functions.insert_llm_request")
@patch("services.anthropic.chat_with_functions.claude")
def test_chat_with_claude_authentication_error(
    mock_claude, mock_insert_llm_request, mock_trim_messages, mock_deduplication_functions
):
    """Test handling of AuthenticationError (lines 96-97)"""
    mock_claude.messages.create.side_effect = AuthenticationError(
        "Invalid API key", response=Mock(), body=None
    )
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=15)

    messages = [{"role": "user", "content": "test"}]
    system_content = "You are helpful"
    tools = []

    with pytest.raises(ClaudeAuthenticationError) as exc_info:
        chat_with_claude(messages=messages, system_content=system_content, tools=tools)

    assert "Claude API authentication failed (401)" in str(exc_info.value)
    mock_insert_llm_request.assert_not_called()


@patch("services.anthropic.chat_with_functions.insert_llm_request")
@patch("services.anthropic.chat_with_functions.claude")
def test_chat_with_claude_tool_use_only_no_text(
    mock_claude, mock_insert_llm_request, mock_trim_messages, mock_deduplication_functions
):
    """Test when response has only tool_use without text (line 126 false branch)"""
    mock_tool_use = Mock()
    mock_tool_use.type = "tool_use"
    mock_tool_use.id = "tool_456"
    mock_tool_use.name = "another_function"
    mock_tool_use.input = {"key": "value"}

    mock_response = Mock()
    # Only tool_use, no text content
    mock_response.content = [mock_tool_use]
    mock_response.usage = Mock(output_tokens=20)

    mock_claude.messages.create.return_value = mock_response
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=25)

    messages = [{"role": "user", "content": "Execute function"}]
    system_content = "You are a helpful assistant."
    tools = [
        {
            "function": {
                "name": "another_function",
                "description": "Another test",
                "parameters": {},
            }
        }
    ]

    result = chat_with_claude(
        messages=messages, system_content=system_content, tools=tools
    )

    # Verify the assistant message has no text block, only tool_use
    assert result[0]["role"] == "assistant"
    assert len(result[0]["content"]) == 1
    assert result[0]["content"][0]["type"] == "tool_use"
    assert result[0]["content"][0]["id"] == "tool_456"
    assert result[1] == "tool_456"  # tool_call_id
    assert result[2] == "another_function"  # tool_name
    assert result[3] == {"key": "value"}  # tool_args


@patch("services.anthropic.chat_with_functions.insert_llm_request")
@patch("services.anthropic.chat_with_functions.claude")
def test_chat_with_claude_empty_text_content(
    mock_claude, mock_insert_llm_request, mock_trim_messages, mock_deduplication_functions
):
    """Test when text content is empty string (line 126 false branch)"""
    mock_tool_use = Mock()
    mock_tool_use.type = "tool_use"
    mock_tool_use.id = "tool_789"
    mock_tool_use.name = "test_func"
    mock_tool_use.input = {}

    mock_response = Mock()
    # Text block with empty string
    mock_response.content = [Mock(type="text", text=""), mock_tool_use]
    mock_response.usage = Mock(output_tokens=15)

    mock_claude.messages.create.return_value = mock_response
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=20)

    messages = [{"role": "user", "content": "test"}]
    system_content = "You are helpful"
    tools = [
        {"function": {"name": "test_func", "description": "Test", "parameters": {}}}
    ]

    result = chat_with_claude(
        messages=messages, system_content=system_content, tools=tools
    )

    # Empty text should not be added to content
    assert result[0]["role"] == "assistant"
    assert len(result[0]["content"]) == 1
    assert result[0]["content"][0]["type"] == "tool_use"


@patch("services.anthropic.chat_with_functions.insert_llm_request")
@patch("services.anthropic.chat_with_functions.claude")
def test_chat_with_claude_unknown_content_type(
    mock_claude, mock_insert_llm_request, mock_trim_messages, mock_deduplication_functions
):
    """Test when content block has unknown type (line 117 false branch)"""
    mock_unknown = Mock()
    mock_unknown.type = "unknown_type"

    mock_response = Mock()
    mock_response.content = [
        Mock(type="text", text="Hello"),
        mock_unknown,  # Unknown type should be ignored
    ]
    mock_response.usage = Mock(output_tokens=10)

    mock_claude.messages.create.return_value = mock_response
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=15)

    messages = [{"role": "user", "content": "test"}]
    system_content = "You are helpful"
    tools = []

    result = chat_with_claude(
        messages=messages, system_content=system_content, tools=tools
    )

    # Should only have text content, unknown type ignored
    assert result[0]["role"] == "assistant"
    assert len(result[0]["content"]) == 1
    assert result[0]["content"][0]["type"] == "text"
    assert result[0]["content"][0]["text"] == "Hello"
    # No tool calls
    assert result[1] is None  # tool_call_id
    assert result[2] is None  # tool_name
    assert result[3] is None  # tool_args


@patch("services.anthropic.chat_with_functions.insert_llm_request")
@patch("services.anthropic.chat_with_functions.claude")
def test_chat_with_claude_multiple_tool_uses(
    mock_claude, mock_insert_llm_request, mock_trim_messages, mock_deduplication_functions
):
    """Test when response has multiple tool_use blocks (only first should be used)"""
    mock_tool_use_1 = Mock()
    mock_tool_use_1.type = "tool_use"
    mock_tool_use_1.id = "tool_first"
    mock_tool_use_1.name = "first_function"
    mock_tool_use_1.input = {"first": "data"}

    mock_tool_use_2 = Mock()
    mock_tool_use_2.type = "tool_use"
    mock_tool_use_2.id = "tool_second"
    mock_tool_use_2.name = "second_function"
    mock_tool_use_2.input = {"second": "data"}

    mock_response = Mock()
    mock_response.content = [
        Mock(type="text", text="Using tools"),
        mock_tool_use_1,
        mock_tool_use_2,
    ]
    mock_response.usage = Mock(output_tokens=30)

    mock_claude.messages.create.return_value = mock_response
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=25)

    messages = [{"role": "user", "content": "test"}]
    system_content = "You are helpful"
    tools = [
        {
            "function": {
                "name": "first_function",
                "description": "First",
                "parameters": {},
            }
        },
        {
            "function": {
                "name": "second_function",
                "description": "Second",
                "parameters": {},
            }
        },
    ]

    result = chat_with_claude(
        messages=messages, system_content=system_content, tools=tools
    )

    # Should use only the first tool
    assert result[1] == "tool_first"  # tool_call_id
    assert result[2] == "first_function"  # tool_name
    assert result[3] == {"first": "data"}  # tool_args

    # But assistant message should contain only the first tool_use
    assert result[0]["role"] == "assistant"
    assert len(result[0]["content"]) == 2  # text + tool_use
    assert result[0]["content"][1]["type"] == "tool_use"
    assert result[0]["content"][1]["id"] == "tool_first"
