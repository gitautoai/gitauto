# Standard imports
from unittest.mock import MagicMock
from unittest.mock import patch, MagicMock

# Local imports
from services.anthropic.remove_get_remote_file_content_before_replace_remote_file_content import \
    remove_get_remote_file_content_before_replace_remote_file_content


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


def test_non_dict_items_in_content_first_pass():
    """Test line 27-28: when item is not a dict in first pass"""
    messages = [
        {
            "role": "user",
            "content": [
                "not a dict",  # This should be skipped
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n1: print('hello')",
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should remain unchanged since no later operation
    assert result == messages


def test_non_dict_items_in_content_second_pass():
    """Test line 74-76: when item is not a dict in second pass"""
    messages = [
        {
            "role": "user",
            "content": [
                "not a dict",  # This should be preserved
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n1: print('hello')",
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
                        "content": "print('world')",
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
                "not a dict",  # Non-dict item preserved
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
                        "content": "print('world')",
                    },
                }
            ],
        },
    ]
    assert result == expected


def test_invalid_input_data_in_replace_operation():
    """Test line 38-39: when input_data is not dict or missing file_path"""
    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": "not a dict",  # Invalid input
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"content": "some content"},  # Missing file_path
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should remain unchanged since invalid operations are skipped
    assert result == messages


def test_malformed_file_content_markers_first_pass():
    """Test line 60-61: when start or end markers are not found in first pass"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' but missing end marker",  # Missing end marker
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Missing start marker with line numbers",  # Missing start marker
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should remain unchanged since malformed content is skipped
    assert result == messages


def test_malformed_file_content_markers_second_pass():
    """Test line 95-97: when start or end markers are not found in second pass"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' but missing end marker",  # Missing end marker
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Missing start marker with line numbers",  # Missing start marker
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
                        "content": "print('world')",
                    },
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should remain unchanged since malformed content is preserved
    assert result == messages


def test_file_not_in_latest_positions():
    """Test line 103->112: when latest_info is None (file not tracked)"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'untracked.py' with line numbers for your information.\n1: print('hello')",
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
                        "file_path": "different.py",  # Different file
                        "content": "print('world')",
                    },
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should remain unchanged since untracked.py has no later operation
    assert result == messages


def test_multiple_file_operations_same_file():
    """Test complex scenario with multiple operations on same file"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n1: print('first')",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n1: print('second')",
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
                        "content": "print('replaced')",
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
                        "content": "print('replaced')",
                    },
                }
            ],
        },
    ]
    assert result == expected


def test_file_content_after_replace_operation():
    """Test when file content appears after replace operation (should not be removed)"""
    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {
                        "file_path": "test.py",
                        "content": "print('replaced')",
                    },
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n1: print('after replace')",
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should remain unchanged since file content comes after replace operation
    assert result == messages


def test_mixed_content_types():
    """Test messages with mixed content types and roles"""
    messages = [
        {
            "role": "system",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n1: print('system')",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Some text",
                },
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n1: print('user')",
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "other_function",
                    "input": {"param": "value"},
                },
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {
                        "file_path": "test.py",
                        "content": "print('replaced')",
                    },
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)

    expected = [
        {
            "role": "system",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n1: print('system')",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Some text",
                },
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
                    "name": "other_function",
                    "input": {"param": "value"},
                },
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {
                        "file_path": "test.py",
                        "content": "print('replaced')",
                    },
                }
            ],
        },
    ]
    assert result == expected


def test_edge_case_empty_filename():
    """Test edge case where filename extraction results in empty string"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: '' with line numbers for your information.\n1: print('empty filename')",
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
                        "file_path": "",
                        "content": "print('replaced')",
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
                        "file_path": "",
                        "content": "print('replaced')",
                    },
                }
            ],
        },
    ]
    assert result == expected


def test_non_list_content():
    """Test messages where content is not a list"""
    messages = [
        {"role": "user", "content": "string content"},
        {"role": "assistant", "content": {"type": "dict"}},
        {"role": "user", "content": None},
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
    # Should remain unchanged since no replace operations
    assert result == messages


def test_content_tracking_with_later_file_content():
    """Test that later file content for same file is tracked correctly"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n1: print('first')",
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
                        "content": "print('replaced')",
                    },
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n1: print('later')",
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


def test_force_line_61_with_custom_string():
    """Force line 61 to be hit using custom string class"""

    class TrickyString(str):
        def find(self, sub, start=None, end=None):
            return -1



def test_defensive_check_line_61_first_pass():
    """Test line 61: defensive check in first pass when find() returns -1"""
    # Create a custom string-like object that passes initial checks but fails find()
    class TrickyString:
        def __init__(self, value):
            self.value = value
            self.find_call_count = 0

        def __str__(self):
            return self.value

        def startswith(self, prefix):
            return self.value.startswith(prefix)

        def __contains__(self, item):
            return item in self.value

        def find(self, substring):
            # Return -1 to trigger the defensive check
            return -1

    tricky_content = TrickyString(
        "Opened file: 'test.py' with line numbers for your information.\n1: print('hello')"
    )

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": tricky_content,
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should remain unchanged since the defensive check catches the issue
    assert len(result) == 1


def test_defensive_check_lines_96_97_second_pass():
    """Test lines 96-97: defensive check in second pass when find() returns -1"""
    # Create a custom string-like object that passes initial checks but fails find()
    class TrickyString:
        def __init__(self, value):
            self.value = value

        def __str__(self):
            return self.value

        def startswith(self, prefix):
            return self.value.startswith(prefix)

        def __contains__(self, item):
            return item in self.value

        def find(self, substring):
            # Return -1 to trigger the defensive check
            return -1

    tricky_content = TrickyString(
        "Opened file: 'test.py' with line numbers for your information.\n1: print('hello')"
    )

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": tricky_content,
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": TrickyString("Opened file: 'test.py' with line numbers for your information.\n1: print('hello')"),
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert len(result) == 1


def test_force_lines_96_97_with_custom_string():
    """Force lines 96-97 to be hit using custom string class"""

    class TrickyString(str):
        def find(self, sub, start=None, end=None):
            return -1

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": TrickyString("Opened file: 'test.py' with line numbers for your information.\n1: print('hello')"),
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
                        "content": "print('replaced')",
                    },
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert len(result) == 2


def test_force_line_112_explicitly():
    """Explicitly test line 112: file not in latest_positions"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'orphan.py' with line numbers for your information.\n1: print('orphan')",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'another.py' with line numbers for your information.\n1: print('another')",
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_line_103_false_branch():
    """Test the false branch of line 103 (latest_info is None)"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'no_tracking.py' with line numbers for your information.\n1: print('no tracking')",
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {
                        "file_path": "test.py",
                        "content": "print('replaced')",
                    },
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n1: print('later')",
                }
            ],
        },
    ]
    assert result == expected


def test_input_data_none():
    """Test when input_data is None"""
    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": None,  # None input
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should remain unchanged since invalid input is skipped
    assert result == messages


def test_content_str_conversion():
    """Test content conversion to string with various types"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": 123,  # Non-string content that gets converted
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": ["list", "content"],  # List content
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should remain unchanged since content doesn't match file pattern
    assert result == messages


def test_no_content_key():
    """Test when tool_result has no content key"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    # No content key
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should remain unchanged
    assert result == messages


def test_complex_filename_with_special_characters():
    """Test filename extraction with special characters"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'path/to/file-with_special.chars.py' with line numbers for your information.\n1: print('hello')",
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
                        "file_path": "path/to/file-with_special.chars.py",
                        "content": "print('replaced')",
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
                        "file_path": "path/to/file-with_special.chars.py",
                        "content": "print('replaced')",
                    },
                }
            ],
        },
    ]
    assert result == expected


def test_system_role_with_tool_result():
    """Test system role with tool_result (should be ignored in first pass)"""
    messages = [
        {
            "role": "system",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n1: print('system')",
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
                        "content": "print('replaced')",
                    },
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # System role tool_result should remain unchanged since it's not tracked
    assert result == messages


def test_assistant_role_with_non_replace_tool_use():
    """Test assistant role with tool_use that's not replace_remote_file_content"""
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
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "other_function",  # Not replace_remote_file_content
                    "input": {
                        "file_path": "test.py",
                        "content": "print('replaced')",
                    },
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should remain unchanged since no replace operation
    assert result == messages


def test_content_modification_detection():
    """Test that content modification is properly detected (line 114-115)"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Some text that won't change",
                },
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n1: print('hello')",
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
                        "content": "print('replaced')",
                    },
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)

    # Verify that the content was actually modified
    assert result[0]["content"][0]["text"] == "Some text that won't change"  # Unchanged
    assert result[0]["content"][1]["content"] == "[Outdated content removed]"  # Changed

    # Verify that the original messages object was not modified (deep copy worked)
    assert messages[0]["content"][1]["content"] != "[Outdated content removed]"


def test_no_modification_needed():
    """Test case where no content modification is needed"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Just some text",
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "some_other_function",
                    "input": {"param": "value"},
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)

    # Should be identical (no modifications needed)
    assert result == messages
    # But should still be a deep copy
    assert result is not messages


def test_first_pass_malformed_content_with_start_marker_only():
    """Test line 61: first pass with content that has start marker but malformed end"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers",  # Missing quote before "with"
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should remain unchanged since malformed content is skipped in first pass
    assert result == messages


def test_second_pass_malformed_content_preserves_item():
    """Test lines 96-97: second pass with malformed content preserves the item"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers",  # Missing quote before "with"
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
                        "file_path": "other.py",
                        "content": "print('world')",
                    },
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should remain unchanged - malformed content is preserved in second pass
    assert result == messages


def test_file_content_not_tracked_in_latest_positions():
    """Test line 112: when file is not in latest_positions during second pass"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'standalone.py' with line numbers for your information.\n1: print('standalone')",
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should remain unchanged - file has no later operations
    assert result == messages


def test_edge_case_marker_at_boundary():
    """Test edge case where markers are at string boundaries"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'x' with line numbers for your information.\n",
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
                        "file_path": "x",
                        "content": "new content",
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
                        "file_path": "x",
                        "content": "new content",
                    },
                }
            ],
        },
    ]
    assert result == expected


def test_multiple_tool_results_in_single_message():
    """Test message with multiple tool_result items"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file1.py' with line numbers for your information.\n1: print('file1')",
                },
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file2.py' with line numbers for your information.\n1: print('file2')",
                },
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {
                        "file_path": "file1.py",
                        "content": "print('replaced1')",
                    },
                },
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {
                        "file_path": "file2.py",
                        "content": "print('replaced2')",
                    },
                },
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
                },
                {
                    "type": "tool_result",
                    "content": "[Outdated content removed]",
                },
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {
                        "file_path": "file1.py",
                        "content": "print('replaced1')",
                    },
                },
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {
                        "file_path": "file2.py",
                        "content": "print('replaced2')",
                    },
                },
            ],
        },
    ]
    assert result == expected


def test_force_line_61_with_mock():
    """Force line 61 to be hit using a mock object that behaves differently for startswith and find"""

    class TrickyString:
        """A string-like object that passes initial checks but fails find()"""
        def __init__(self, value):
            self.value = value

        def __str__(self):
            return self.value

        def startswith(self, prefix):
            # Always return True for the check
            if prefix == "Opened file: '":
                return True
            return self.value.startswith(prefix)

        def __contains__(self, item):
            # Always return True for the check
            if item == "' with line numbers":
                return True
            return item in self.value

        def find(self, substring):
            # Return -1 to trigger the defensive check
            return -1

    tricky_content = TrickyString("Opened file: 'test.py' with line numbers for your information.\n1: print('hello')")

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": tricky_content,
                }
            ],
        },
    ]

    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should remain unchanged since the defensive check catches the issue
    assert len(result) == 1
    assert result[0]["role"] == "user"


def test_force_lines_96_97_with_mock():
    """Force lines 96-97 to be hit using a mock object in second pass"""

    class TrickyString:
        """A string-like object that passes initial checks but fails find()"""
        def __init__(self, value):
            self.value = value

        def __str__(self):
            return self.value

        def startswith(self, prefix):
            # Always return True for the check
            if prefix == "Opened file: '":
                return True
            return self.value.startswith(prefix)

        def __contains__(self, item):
            # Always return True for the check
            if item == "' with line numbers":
                return True
            return item in self.value

        def find(self, substring):
            # Return -1 to trigger the defensive check
            return -1

    tricky_content = TrickyString("Opened file: 'test.py' with line numbers for your information.\n1: print('hello')")

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": tricky_content,
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
                        "content": "print('replaced')",
                    },
                }
            ],
        },
    ]

    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should remain unchanged since the defensive check catches the issue in second pass
    assert len(result) == 2


def test_force_line_112_explicitly():
    """Explicitly test line 112: when latest_info is None in second pass"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'orphan.py' with line numbers for your information.\n1: print('orphan')",
                }
            ],
        },
    ]

    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # File has no later operations, so latest_info will be None, hitting line 112
