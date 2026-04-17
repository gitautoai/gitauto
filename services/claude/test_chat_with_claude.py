from typing import cast
from unittest.mock import Mock, patch

from anthropic.types import MessageParam, ToolUnionParam

from constants.models import ClaudeModelId
from services.claude.chat_with_claude import chat_with_claude


@patch("services.claude.chat_with_claude.insert_llm_request")
@patch("services.claude.chat_with_claude.claude")
def test_chat_with_claude_success(mock_claude, mock_insert_llm_request):
    mock_response = Mock()
    mock_response.content = [Mock(type="text", text="Hello! How can I help you?")]
    mock_response.usage = Mock(output_tokens=15)
    mock_insert_llm_request.return_value = {"total_cost_usd": 0.05}

    mock_claude.messages.create.return_value = mock_response
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=20)

    # Test fixtures use cast as allowed by CLAUDE.md
    messages = cast(list[MessageParam], [{"role": "user", "content": "Hello"}])
    system_content = "You are a helpful assistant."
    tools: list[ToolUnionParam] = []

    result = chat_with_claude(
        messages=messages,
        system_content=system_content,
        tools=tools,
        model_id=ClaudeModelId.SONNET_4_6,
        usage_id=123,
        created_by="4:test-user",
    )

    assert result.assistant_message["role"] == "assistant"
    content = cast(list, result.assistant_message["content"])
    assert content[0]["text"] == "Hello! How can I help you?"
    assert not result.tool_calls
    assert result.token_input == 20
    assert result.token_output == 15
    assert result.cost_usd == 0.05

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
        messages=messages,
        system_content=system_content,
        tools=tools,
        model_id=ClaudeModelId.SONNET_4_6,
        usage_id=456,
        created_by="4:test-user",
    )

    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].id == "tool_123"
    assert result.tool_calls[0].name == "test_function"
    assert result.tool_calls[0].args == {"param": "value"}

    mock_insert_llm_request.assert_called_once()


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
        model_id=ClaudeModelId.SONNET_4_6,
        usage_id=789,
        created_by="4:test-user",
    )

    assert result.token_output == 0  # output tokens should be 0 when no usage info
    mock_insert_llm_request.assert_called_once()


@patch("services.claude.chat_with_claude.remove_outdated_file_edit_attempts")
@patch("services.claude.chat_with_claude.insert_llm_request")
@patch("services.claude.chat_with_claude.claude")
def test_chat_with_claude_calls_optimization_functions(
    mock_claude,
    _mock_insert_llm_request,
    mock_remove_outdated_file_edit_attempts,
):
    mock_response = Mock()
    mock_response.content = [Mock(type="text", text="Response")]
    mock_response.usage = Mock(output_tokens=10)
    mock_claude.messages.create.return_value = mock_response
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=15)

    original_messages = [{"role": "user", "content": "test"}]
    mock_remove_outdated_file_edit_attempts.return_value = original_messages

    chat_with_claude(
        messages=cast(list[MessageParam], original_messages),
        system_content="You are helpful",
        tools=[],
        model_id=ClaudeModelId.SONNET_4_6,
        usage_id=101,
        created_by="4:test-user",
    )

    mock_remove_outdated_file_edit_attempts.assert_called_once()


@patch("services.claude.chat_with_claude.insert_llm_request")
@patch("services.claude.chat_with_claude.claude")
def test_strict_tools_passed_through_unchanged(mock_claude, mock_insert_llm_request):
    """Strict tools must not be stripped — all current models support strict."""
    mock_response = Mock()
    mock_response.content = [Mock(type="text", text="ok")]
    mock_response.usage = Mock(output_tokens=5)
    mock_insert_llm_request.return_value = {"total_cost_usd": 0.01}
    mock_claude.messages.create.return_value = mock_response
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=10)

    tools = cast(
        list[ToolUnionParam],
        [
            {
                "name": "test_tool",
                "description": "Test",
                "strict": True,
                "input_schema": {"type": "object", "properties": {}},
            }
        ],
    )

    chat_with_claude(
        messages=cast(list[MessageParam], [{"role": "user", "content": "test"}]),
        system_content="system",
        tools=tools,
        model_id=ClaudeModelId.HAIKU_4_5,
        usage_id=999,
        created_by="4:test-user",
    )

    call_args = mock_claude.messages.create.call_args
    passed_tools = call_args.kwargs["tools"]
    assert passed_tools[0]["strict"] is True
