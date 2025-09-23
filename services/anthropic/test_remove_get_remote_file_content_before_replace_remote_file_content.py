from unittest.mock import patch

from services.anthropic.remove_get_remote_file_content_before_replace_remote_file_content import (
    remove_get_remote_file_content_before_replace_remote_file_content,
)


def test_remove_get_remote_file_content_before_replace_remote_file_content_empty_list():
    result = remove_get_remote_file_content_before_replace_remote_file_content([])
    assert result == []


def test_remove_get_remote_file_content_before_replace_remote_file_content_no_file_content():
    messages = [
        {"role": "assistant", "content": "Hello"},
        {"role": "user", "content": [{"type": "text", "text": "Hi there"}]},
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_remove_get_remote_file_content_before_replace_remote_file_content_with_replace_operation():
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n1: def hello():\n2:     print('world')",
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {
                        "file_path": "test.py",
                        "content": "def hello():\n    print('hello world')",
                    },
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)

    expected = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "[Outdated content removed]",
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {
                        "file_path": "test.py",
                        "content": "def hello():\n    print('hello world')",
                    },
                }
            ],
        },
    ]
    assert result == expected


def test_remove_get_remote_file_content_before_replace_remote_file_content_different_files():
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file1.py' with line numbers for your information.\n1: print('file1')",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file2.py' with line numbers for your information.\n1: print('file2')",
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)

    # Different files, so both should remain unchanged
    assert result == messages


def test_remove_get_remote_file_content_before_replace_remote_file_content_no_later_operation():
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n1: print('hello')",
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)

    # No later operation, so should remain unchanged
    assert result == messages


def test_handles_exception_gracefully():
    # Test by mocking deepcopy to raise an exception

    messages = [{"role": "user", "content": []}]

    with patch("copy.deepcopy", side_effect=RuntimeError("Simulated failure")):
        result = remove_get_remote_file_content_before_replace_remote_file_content(
            messages
        )
        # Should return original messages unchanged when exception occurs
        assert result == messages


def test_handles_runtime_exception():
    # Test by making dict access fail
    class BadDict:
        def get(self, key, default=None):
            if key == "role":
                return "user"
            if key == "content":
                raise KeyError("Simulated KeyError")
            return default

    messages = [BadDict()]

    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should return original messages unchanged when exception occurs
    assert result == messages
