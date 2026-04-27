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
    assert call_args["system_prompt"] == system_content

    # Verify the trim path uses the shared count_tokens_claude function: when count_tokens is invoked on the Anthropic client, we should see the messages and model relayed through.
    mock_claude.messages.count_tokens.assert_called_with(
        messages=messages, model=ClaudeModelId.SONNET_4_6
    )

    # Opus 4.7 deprecated temperature (AGENT-36M cascade). Ensure we don't pass it.
    create_kwargs = mock_claude.messages.create.call_args.kwargs
    assert set(create_kwargs.keys()) == {
        "model",
        "system",
        "messages",
        "tools",
        "max_tokens",
    }


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


@patch("services.claude.chat_with_claude.insert_llm_request")
@patch("services.claude.chat_with_claude.claude")
def test_max_input_uses_full_context_window_no_200k_clamp(
    mock_claude, mock_insert_llm_request
):
    """Earlier versions of chat_with_claude clamped max_input to min(context_window - max_output - buffer, 200_000) and used CONTEXT_WINDOW.get(model_id, 200_000) defaults. The 200k cap was a leftover from when 1M context required a beta header that's no longer needed/used. With the clamp dropped and direct subscript replacing .get() defaults, max_tokens passed to messages.create for Sonnet 4.6 (1M context, 64k output) is the model's full output limit and the trim path's max_input budget is 1M - 64k - 4096 = 991840, not the old 200k clamp."""
    mock_response = Mock()
    mock_response.content = [Mock(type="text", text="ok")]
    mock_response.usage = Mock(output_tokens=5)
    mock_insert_llm_request.return_value = {"total_cost_usd": 0.0}
    mock_claude.messages.create.return_value = mock_response
    # 500k tokens — would have been clamped to 200k before the fix and trimmed; now well under 991840 max_input so the messages list survives intact.
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=500_000)

    chat_with_claude(
        messages=cast(list[MessageParam], [{"role": "user", "content": "x"}]),
        system_content="sys",
        tools=[],
        model_id=ClaudeModelId.SONNET_4_6,
        usage_id=1,
        created_by="4:test-user",
    )

    create_kwargs = mock_claude.messages.create.call_args.kwargs
    # Sonnet 4.6's MAX_OUTPUT_TOKENS is 64_000 per constants/claude.py.
    assert create_kwargs["max_tokens"] == 64_000
    # The 500k probe must be passed straight to messages.create (no trim) because the unclamped budget (991840) accommodates it.
    assert create_kwargs["messages"] == [{"role": "user", "content": "x"}]
