from unittest.mock import MagicMock, patch
import pytest
import tiktoken

from services.openai.count_tokens import count_tokens


@pytest.fixture
def mock_encoding():
    """Mock tiktoken encoding"""
    encoding = MagicMock(spec=tiktoken.Encoding)
    # Mock encode method to return predictable token counts
    encoding.encode.side_effect = lambda text: [1] * len(text)  # 1 token per character
    return encoding


@pytest.fixture
def mock_tiktoken_encoding_for_model(mock_encoding):
    """Mock tiktoken.encoding_for_model"""
    with patch("services.openai.count_tokens.tiktoken.encoding_for_model") as mock:
        mock.return_value = mock_encoding
        yield mock


def test_count_tokens_empty_messages(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with empty message list"""
    messages = []
    result = count_tokens(messages)
    
    assert result == 0
    mock_tiktoken_encoding_for_model.assert_called_once()


def test_count_tokens_message_with_role_only(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with message containing only role"""
    messages = [{"role": "user"}]
    result = count_tokens(messages)
    
    # "user" = 4 characters = 4 tokens
    assert result == 4
    mock_encoding.encode.assert_called_with("user")


def test_count_tokens_message_with_string_content(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with message containing role and string content"""
    messages = [{"role": "user", "content": "Hello world"}]
    result = count_tokens(messages)
    
    # "user" (4) + "Hello world" (11) = 15 tokens
    assert result == 15
    assert mock_encoding.encode.call_count == 2


def test_count_tokens_message_with_empty_string_content(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with message containing empty string content"""
    messages = [{"role": "user", "content": ""}]
    result = count_tokens(messages)
    
    # "user" (4) + "" (0) = 4 tokens
    assert result == 4
    mock_encoding.encode.assert_any_call("user")
    mock_encoding.encode.assert_any_call("")


def test_count_tokens_message_with_none_string_content(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with message containing None string content"""
    messages = [{"role": "user", "content": None}]
    result = count_tokens(messages)
    
    # "user" (4) + 0 (None content is not processed as string) = 4 tokens
    assert result == 4
    mock_encoding.encode.assert_any_call("user")


def test_count_tokens_message_with_name(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with message containing name field"""
    messages = [{"role": "user", "content": "Hello", "name": "assistant"}]
    result = count_tokens(messages)
    
    # "user" (4) + "Hello" (5) + "assistant" (9) = 18 tokens
    assert result == 18
    mock_encoding.encode.assert_any_call("user")
    mock_encoding.encode.assert_any_call("Hello")
    mock_encoding.encode.assert_any_call("assistant")


def test_count_tokens_message_with_list_content_text_block(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with message containing list content with text block"""
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": "Hello world"}
        ]
    }]
    result = count_tokens(messages)
    
    # "user" (4) + "Hello world" (11) = 15 tokens
    assert result == 15
    mock_encoding.encode.assert_any_call("user")
    mock_encoding.encode.assert_any_call("Hello world")


def test_count_tokens_message_with_list_content_text_block_empty_text(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with message containing list content with text block having empty text"""
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": ""},
            {"type": "text"}  # Missing text field
        ]
    }]
    result = count_tokens(messages)
    
    # "user" (4) + "" (0) + "" (0, default for missing text) = 4 tokens
    assert result == 4
    mock_encoding.encode.assert_any_call("user")
    mock_encoding.encode.assert_any_call("")


def test_count_tokens_message_with_list_content_tool_use_block(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with message containing list content with tool_use block"""
    messages = [{
        "role": "assistant",
        "content": [
            {"type": "tool_use", "name": "search", "input": {"query": "test"}}
        ]
    }]
    result = count_tokens(messages)
    
    # "assistant" (9) + "search" (6) + "{'query': 'test'}" (17) = 32 tokens
    assert result == 32
    mock_encoding.encode.assert_any_call("assistant")
    mock_encoding.encode.assert_any_call("search")
    mock_encoding.encode.assert_any_call("{'query': 'test'}")


def test_count_tokens_message_with_list_content_tool_use_block_empty_fields(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with message containing list content with tool_use block having empty fields"""
    messages = [{
        "role": "assistant",
        "content": [
            {"type": "tool_use"},  # Missing name and input
            {"type": "tool_use", "name": "", "input": ""}
        ]
    }]
    result = count_tokens(messages)
    
    # "assistant" (9) + "" (0, default name) + "" (0, default input) + "" (0, empty name) + "" (0, empty input) = 9 tokens
    assert result == 9
    mock_encoding.encode.assert_any_call("assistant")
    mock_encoding.encode.assert_any_call("")


def test_count_tokens_message_with_list_content_tool_result_block(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with message containing list content with tool_result block"""
    messages = [{
        "role": "user",
        "content": [
            {"type": "tool_result", "content": "Result data"}
        ]
    }]
    result = count_tokens(messages)
    
    # "user" (4) + "Result data" (11) = 15 tokens
    assert result == 15
    mock_encoding.encode.assert_any_call("user")
    mock_encoding.encode.assert_any_call("Result data")


def test_count_tokens_message_with_list_content_tool_result_block_empty_content(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with message containing list content with tool_result block having empty content"""
    messages = [{
        "role": "user",
        "content": [
            {"type": "tool_result"},  # Missing content
            {"type": "tool_result", "content": ""}
        ]
    }]
    result = count_tokens(messages)
    
    # "user" (4) + "" (0, default content) + "" (0, empty content) = 4 tokens
    assert result == 4
    mock_encoding.encode.assert_any_call("user")
    mock_encoding.encode.assert_any_call("")


def test_count_tokens_message_with_list_content_unknown_block_type(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with message containing list content with unknown block type"""
    messages = [{
        "role": "user",
        "content": [
            {"type": "unknown", "data": "some data"},
            {"type": "image", "url": "http://example.com/image.jpg"}
        ]
    }]
    result = count_tokens(messages)
    
    # Only "user" (4) tokens, unknown blocks are ignored
    assert result == 4
    mock_encoding.encode.assert_called_once_with("user")


def test_count_tokens_message_with_tool_calls(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with message containing tool_calls"""
    messages = [{
        "role": "assistant",
        "content": "I'll search for that",
        "tool_calls": [
            {
                "function": {
                    "name": "search",
                    "arguments": '{"query": "test"}'
                }
            }
        ]
    }]
    result = count_tokens(messages)
    
    # "assistant" (9) + "I'll search for that" (20) + "search" (6) + '{"query": "test"}' (17) = 52 tokens
    assert result == 52
    mock_encoding.encode.assert_any_call("assistant")
    mock_encoding.encode.assert_any_call("I'll search for that")
    mock_encoding.encode.assert_any_call("search")
    mock_encoding.encode.assert_any_call('{"query": "test"}')


def test_count_tokens_message_with_tool_calls_no_function(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with message containing tool_calls without function field"""
    messages = [{
        "role": "assistant",
        "content": "Hello",
        "tool_calls": [
            {"id": "call_123"},  # No function field
            {}  # Empty tool call
        ]
    }]
    result = count_tokens(messages)
    
    # Only "assistant" (9) + "Hello" (5) = 14 tokens, tool_calls without function are ignored
    assert result == 14
    mock_encoding.encode.assert_any_call("assistant")
    mock_encoding.encode.assert_any_call("Hello")


def test_count_tokens_message_with_multiple_tool_calls(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with message containing multiple tool_calls"""
    messages = [{
        "role": "assistant",
        "tool_calls": [
            {
                "function": {
                    "name": "search",
                    "arguments": '{"query": "test1"}'
                }
            },
            {
                "function": {
                    "name": "calculate",
                    "arguments": '{"expression": "2+2"}'
                }
            }
        ]
    }]
    result = count_tokens(messages)
    
    # "assistant" (9) + "search" (6) + '{"query": "test1"}' (18) + "calculate" (9) + '{"expression": "2+2"}' (21) = 63 tokens
    assert result == 63
    mock_encoding.encode.assert_any_call("assistant")
    mock_encoding.encode.assert_any_call("search")
    mock_encoding.encode.assert_any_call('{"query": "test1"}')
    mock_encoding.encode.assert_any_call("calculate")
    mock_encoding.encode.assert_any_call('{"expression": "2+2"}')


def test_count_tokens_multiple_messages_complex(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with multiple complex messages"""
    messages = [
        {
            "role": "user",
            "content": "Hello",
            "name": "john"
        },
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Hi there"},
                {"type": "tool_use", "name": "search", "input": {"q": "test"}}
            ]
        },
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "content": "Found results"}
            ]
        }
    ]
    result = count_tokens(messages)
    
    # Message 1: "user" (4) + "Hello" (5) + "john" (4) = 13
    # Message 2: "assistant" (9) + "Hi there" (8) + "search" (6) + "{'q': 'test'}" (13) = 36
    # Message 3: "user" (4) + "Found results" (13) = 17
    # Total: 13 + 36 + 17 = 66 tokens
    assert result == 66


def test_count_tokens_message_without_role(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with message without role field"""
    messages = [{"content": "Hello world"}]
    result = count_tokens(messages)
    
    # Only "Hello world" (11) tokens, no role
    assert result == 11
    mock_encoding.encode.assert_called_once_with("Hello world")


def test_count_tokens_message_with_all_fields(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with message containing all possible fields"""
    messages = [{
        "role": "assistant",
        "content": "Response",
        "name": "bot",
        "tool_calls": [
            {
                "function": {
                    "name": "func",
                    "arguments": "{}"
                }
            }
        ]
    }]
    result = count_tokens(messages)
    
    # "assistant" (9) + "Response" (8) + "bot" (3) + "func" (4) + "{}" (2) = 26 tokens
    assert result == 26
    mock_encoding.encode.assert_any_call("assistant")
    mock_encoding.encode.assert_any_call("Response")
    mock_encoding.encode.assert_any_call("bot")
    mock_encoding.encode.assert_any_call("func")
    mock_encoding.encode.assert_any_call("{}")


def test_count_tokens_mixed_content_types(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with mixed content types in list"""
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": "Question"},
            {"type": "tool_use", "name": "search", "input": "query"},
            {"type": "tool_result", "content": "answer"},
            {"type": "unknown", "data": "ignored"}
        ]
    }]
    result = count_tokens(messages)
    
    # "user" (4) + "Question" (8) + "search" (6) + "query" (5) + "answer" (6) = 29 tokens
    # unknown type is ignored
    assert result == 29
    mock_encoding.encode.assert_any_call("user")
    mock_encoding.encode.assert_any_call("Question")
    mock_encoding.encode.assert_any_call("search")
    mock_encoding.encode.assert_any_call("query")
    mock_encoding.encode.assert_any_call("answer")


def test_count_tokens_uses_correct_model(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test that count_tokens uses the correct OpenAI model"""
    from config import OPENAI_MODEL_ID_GPT_4O
    
    messages = [{"role": "user", "content": "test"}]
    count_tokens(messages)
    
    mock_tiktoken_encoding_for_model.assert_called_once_with(model_name=OPENAI_MODEL_ID_GPT_4O)


@patch("services.openai.count_tokens.tiktoken.encoding_for_model")
def test_count_tokens_tiktoken_error_returns_default(mock_tiktoken_encoding_for_model):
    """Test that count_tokens returns default value (0) when tiktoken raises an error"""
    mock_tiktoken_encoding_for_model.side_effect = Exception("Tiktoken error")
    
    messages = [{"role": "user", "content": "test"}]
    result = count_tokens(messages)
    
    # Should return default value due to handle_exceptions decorator
    assert result == 0


@patch("services.openai.count_tokens.tiktoken.encoding_for_model")
def test_count_tokens_encoding_error_returns_default(mock_tiktoken_encoding_for_model):
    """Test that count_tokens returns default value when encoding.encode raises an error"""
    mock_encoding = MagicMock()
    mock_encoding.encode.side_effect = Exception("Encoding error")
    mock_tiktoken_encoding_for_model.return_value = mock_encoding
    
    messages = [{"role": "user", "content": "test"}]
    result = count_tokens(messages)
    
    # Should return default value due to handle_exceptions decorator
    assert result == 0


def test_count_tokens_unicode_content(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with unicode characters"""
    messages = [{
        "role": "user",
        "content": "Hello 🌍 世界",
        "name": "用户"
    }]
    result = count_tokens(messages)
    
    # "user" (4) + "Hello 🌍 世界" (10) + "用户" (2) = 16 tokens
    assert result == 16
    mock_encoding.encode.assert_any_call("user")
    mock_encoding.encode.assert_any_call("Hello 🌍 世界")
    mock_encoding.encode.assert_any_call("用户")


def test_count_tokens_special_characters(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with special characters and newlines"""
    messages = [{
        "role": "user",
        "content": "Line 1\nLine 2\tTabbed\r\nWindows newline"
    }]
    result = count_tokens(messages)
    
    # "user" (4) + content (39) = 43 tokens
    assert result == 43
    mock_encoding.encode.assert_any_call("user")
    mock_encoding.encode.assert_any_call("Line 1\nLine 2\tTabbed\r\nWindows newline")


def test_count_tokens_large_input(mock_tiktoken_encoding_for_model, mock_encoding):
    """Test count_tokens with large input"""
    large_content = "x" * 10000
    messages = [{
        "role": "user",
        "content": large_content
    }]
    result = count_tokens(messages)
    
    # "user" (4) + large_content (10000) = 10004 tokens
    assert result == 10004
    mock_encoding.encode.assert_any_call("user")
    mock_encoding.encode.assert_any_call(large_content)
