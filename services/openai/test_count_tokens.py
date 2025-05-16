from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from services.openai.count_tokens import count_tokens


def test_empty_messages():
    messages: list[ChatCompletionMessageParam] = []
    assert count_tokens(messages) == 0


def test_basic_message_with_role_and_content():
    messages: list[ChatCompletionMessageParam] = [
        {"role": "user", "content": "Hello world"}
    ]
    result = count_tokens(messages)
    assert result > 0


def test_message_with_none_content():
    messages: list[ChatCompletionMessageParam] = [{"role": "user", "content": None}]
    result = count_tokens(messages)
    assert result > 0


def test_message_with_name():
    messages: list[ChatCompletionMessageParam] = [
        {"role": "assistant", "content": "Hi", "name": "bot"}
    ]
    result = count_tokens(messages)
    assert result > 0


def test_message_with_tool_calls():
    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"location": "Tokyo"}',
                    }
                }
            ],
        }
    ]
    result = count_tokens(messages)
    assert result > 0


def test_message_with_multiple_tool_calls():
    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"location": "Tokyo"}',
                    }
                },
                {"function": {"name": "get_time", "arguments": '{"timezone": "JST"}'}},
            ],
        }
    ]
    result = count_tokens(messages)
    assert result > 0


def test_complex_conversation():
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "What's the weather like?"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"location": "Tokyo"}',
                    }
                }
            ],
        },
    ]
    result = count_tokens(messages)
    assert result > 0
