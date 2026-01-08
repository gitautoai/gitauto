from unittest.mock import Mock, patch

from openai.types.chat import ChatCompletionToolParam

from services.anthropic.chat_with_functions import chat_with_claude


@patch("services.anthropic.chat_with_functions.insert_llm_request")
@patch("services.anthropic.chat_with_functions.claude")
def test_chat_with_claude_success(mock_claude, mock_insert_llm_request):
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

    messages = [{"role": "user", "content": "Do something"}]
    system_content = "You are a helpful assistant."
    tools: list[ChatCompletionToolParam] = [
        {
            "type": "function",
            "function": {
                "name": "test_function",
                "description": "Test",
                "parameters": {},
            },
        }
    ]

    result = chat_with_claude(
        messages=messages, system_content=system_content, tools=tools, usage_id=None
    )

    assert result[1] == "tool_123"  # tool_call_id
    assert result[2] == "test_function"  # tool_name
    assert result[3] == {"param": "value"}  # tool_args

    mock_insert_llm_request.assert_not_called()


@patch("services.anthropic.chat_with_functions.insert_llm_request")
@patch("services.anthropic.chat_with_functions.claude")
def test_chat_with_claude_no_usage_response(mock_claude, mock_insert_llm_request):
    mock_response = Mock()
    mock_response.content = [Mock(type="text", text="Response")]
    mock_response.usage = None

    mock_claude.messages.create.return_value = mock_response
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=10)

    result = chat_with_claude(
        messages=[{"role": "user", "content": "test"}],
        system_content="assistant",
        tools=[],
        usage_id=None,
    )

    assert result[5] == 0  # output tokens should be 0 when no usage info
    mock_insert_llm_request.assert_not_called()


@patch(
    "services.anthropic.chat_with_functions.remove_duplicate_get_remote_file_content_results"
)
@patch(
    "services.anthropic.chat_with_functions.remove_get_remote_file_content_before_replace_remote_file_content"
)
@patch(
    "services.anthropic.chat_with_functions.remove_outdated_apply_diff_to_file_attempts_and_results"
)
@patch("services.anthropic.chat_with_functions.insert_llm_request")
@patch("services.anthropic.chat_with_functions.claude")
def test_chat_with_claude_calls_deduplication(
    mock_claude,
    _mock_insert_llm_request,
    mock_remove_duplicate_get_remote_file_content_results,
    mock_remove_get_remote_file_content_before_replace_remote_file_content,
    mock_remove_outdated_apply_diff_to_file_attempts_and_results,
):
    # Setup mocks
    mock_response = Mock()
    mock_response.content = [Mock(type="text", text="Response")]
    mock_response.usage = Mock(output_tokens=10)
    mock_claude.messages.create.return_value = mock_response
    mock_claude.messages.count_tokens.return_value = Mock(input_tokens=15)

    # Mock all three functions to return the same messages
    original_messages = [{"role": "user", "content": "test"}]
    mock_remove_duplicate_get_remote_file_content_results.return_value = (
        original_messages
    )
    mock_remove_get_remote_file_content_before_replace_remote_file_content.return_value = (
        original_messages
    )
    mock_remove_outdated_apply_diff_to_file_attempts_and_results.return_value = (
        original_messages
    )

    # Call the function
    chat_with_claude(
        messages=original_messages, system_content="You are helpful", tools=[]
    )

    # Verify all three functions were called
    mock_remove_duplicate_get_remote_file_content_results.assert_called_once_with(
        original_messages
    )
    mock_remove_get_remote_file_content_before_replace_remote_file_content.assert_called_once_with(
        original_messages
    )
    mock_remove_outdated_apply_diff_to_file_attempts_and_results.assert_called_once_with(
        original_messages
    )
