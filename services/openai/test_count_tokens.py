import pytest
import tiktoken

from services.openai.count_tokens import count_tokens


class DummyEncoding:
    def encode(self, text):
        return list(text)


def dummy_encoding_for_model(model_name):
    return DummyEncoding()


@pytest.fixture(autouse=True)
def patch_tiktoken(monkeypatch):
    monkeypatch.setattr(tiktoken, 'encoding_for_model', dummy_encoding_for_model)


def test_empty_messages():
    result = count_tokens([])
    assert result == 0


def test_message_with_role():
    message = {"role": "system"}
    expected = len("system")
    result = count_tokens([message])
    assert result == expected


def test_message_with_content_none():
    message = {"content": None}
    # content is None, so defaults to empty string
    expected = 0
    result = count_tokens([message])
    assert result == expected


def test_message_with_all_fields():
    message = {
        "role": "assistant",
        "content": "this is a test",
        "name": "testname",
        "tool_calls": [
            {"function": {"name": "func1", "arguments": "arg1"}},
            {"function": {"name": "func2", "arguments": "arg2"}}
        ]
    }
    expected = (len("assistant") + len("this is a test") + len("testname") +
                len("func1") + len("arg1") + len("func2") + len("arg2"))
    result = count_tokens([message])
    assert result == expected


def test_message_with_missing_keys():
    message = {"foo": "bar", "content": "hello"}
    expected = len("hello")
    result = count_tokens([message])
    assert result == expected


def test_message_with_empty_tool_calls():
    message = {"tool_calls": []}
    expected = 0
    result = count_tokens([message])
    assert result == expected


def test_multiple_messages():
    messages = [
        {"role": "system"},
        {"content": "hi there"},
        {"name": "username", "tool_calls": [{"function": {"name": "func", "arguments": "args"}}]}
    ]
    expected = (len("system") + len("hi there") +
                len("username") + len("func") + len("args"))
    result = count_tokens(messages)
    assert result == expected


def test_exception_handling(monkeypatch):
    def error_encoding_for_model(model_name):
        raise Exception("test error")
    monkeypatch.setattr(tiktoken, 'encoding_for_model', error_encoding_for_model)
    result = count_tokens([{"role": "system"}])
    assert result == 0


def test_tool_calls_without_function():
    message = {"tool_calls": [{"not_function": {}}]}
    expected = 0
    result = count_tokens([message])
    assert result == expected



