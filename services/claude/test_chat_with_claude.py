from typing import cast
from unittest.mock import Mock, patch

from anthropic.types import MessageParam, ToolUnionParam

from services.claude.chat_with_claude import chat_with_claude


@patch("services.claude.chat_with_claude.insert_llm_request")
@patch("services.claude.chat_with_claude.claude")
def test_chat_with_claude_success(mock_claude, mock_insert_llm_request):
    mock_response = Mock()
    mock_response.content = [Mock(type="text", text="Hello! How can I help you?")]
    mock_response.usage = Mock(output_tokens=15)

    mock_claude.messages.create.return_value = mock_response
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=20)

    # Test fixtures use cast as allowed by CLAUDE.md
    messages = cast(list[MessageParam], [{"role": "user", "content": "Hello"}])
    system_content = "You are a helpful assistant."
    tools: list[ToolUnionParam] = []

    result = chat_with_claude(
        messages=messages, system_content=system_content, tools=tools, usage_id=123
    )

    assistant_message, tool_calls, token_input, token_output = result
    assert assistant_message["role"] == "assistant"
    content = cast(list, assistant_message["content"])
    assert content[0]["text"] == "Hello! How can I help you?"
    assert not tool_calls
    assert token_input == 20
    assert token_output == 15

    mock_insert_llm_request.assert_called_once()
    call_args = mock_insert_llm_request.call_args[1]
    assert call_args["usage_id"] == 123
    assert call_args["provider"] == "claude"
    assert call_args["input_tokens"] == 20
    assert call_args["output_tokens"] == 15


@patch("services.claude.chat_with_claude.insert_llm_request")
@patch("services.claude.chat_with_claude.claude")
def test_chat_with_claude_with_tool_use(mock_claude, mock_insert_llm_request):
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

    messages = cast(list[MessageParam], [{"role": "user", "content": "Do something"}])
    system_content = "You are a helpful assistant."
    tools = cast(
        list[ToolUnionParam],
        [
            {
                "name": "test_function",
                "description": "Test",
                "input_schema": {"type": "object", "properties": {}},
            }
        ],
    )

    result = chat_with_claude(
        messages=messages, system_content=system_content, tools=tools, usage_id=None
    )

    _, tool_calls, _, _ = result
    assert len(tool_calls) == 1
    assert tool_calls[0].id == "tool_123"
    assert tool_calls[0].name == "test_function"
    assert tool_calls[0].args == {"param": "value"}

    mock_insert_llm_request.assert_not_called()


@patch("services.claude.chat_with_claude.insert_llm_request")
@patch("services.claude.chat_with_claude.claude")
def test_chat_with_claude_no_usage_response(mock_claude, mock_insert_llm_request):
    mock_response = Mock()
    mock_response.content = [Mock(type="text", text="Response")]
    mock_response.usage = None

    mock_claude.messages.create.return_value = mock_response
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=10)

    result = chat_with_claude(
        messages=cast(list[MessageParam], [{"role": "user", "content": "test"}]),
        system_content="assistant",
        tools=[],
        usage_id=None,
    )

    _, _, _, token_output = result
    assert token_output == 0  # output tokens should be 0 when no usage info
    mock_insert_llm_request.assert_not_called()


@patch(
    "services.claude.chat_with_claude.remove_outdated_apply_diff_to_file_attempts_and_results"
)
@patch("services.claude.chat_with_claude.insert_llm_request")
@patch("services.claude.chat_with_claude.claude")
def test_chat_with_claude_calls_optimization_functions(
    mock_claude,
    _mock_insert_llm_request,
    mock_remove_outdated_apply_diff_to_file_attempts_and_results,
):
    mock_response = Mock()
    mock_response.content = [Mock(type="text", text="Response")]
    mock_response.usage = Mock(output_tokens=10)
    mock_claude.messages.create.return_value = mock_response
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=15)

    original_messages = [{"role": "user", "content": "test"}]
    mock_remove_outdated_apply_diff_to_file_attempts_and_results.return_value = (
        original_messages
    )

    chat_with_claude(
        messages=cast(list[MessageParam], original_messages),
        system_content="You are helpful",
        tools=[],
    )

    mock_remove_outdated_apply_diff_to_file_attempts_and_results.assert_called_once()
