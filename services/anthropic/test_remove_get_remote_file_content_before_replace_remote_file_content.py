# Standard imports
from unittest.mock import patch

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


def test_uncovered_line_28_non_dict_item_first_pass():
    """Test line 28: continue when item is not a dict in first pass"""
    messages = [
        {
            "role": "assistant",
            "content": [
                "string_item",  # This triggers line 27->28
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "test.py", "content": "content"},
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should work normally, non-dict item is skipped
    assert result == messages


def test_uncovered_line_39_invalid_input_data():
    """Test line 39: continue when input_data is invalid"""
    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": "not_a_dict",  # This triggers line 38->39
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should work normally, invalid input is skipped
    assert result == messages


def test_uncovered_line_61_malformed_markers_first_pass():
    """Test line 61: continue when markers are malformed in first pass"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' missing end marker",  # This triggers line 60->61
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should work normally, malformed content is skipped
    assert result == messages


def test_uncovered_lines_75_76_non_dict_item_second_pass():
    """Test lines 75-76: append non-dict item and continue in second pass"""
    messages = [
        {
            "role": "user",
            "content": [
                "string_item",  # This triggers line 74->75->76
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
                    "input": {"file_path": "test.py", "content": "new content"},
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)

    expected = [
        {
            "role": "user",
            "content": [
                "string_item",  # Non-dict preserved
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
                    "input": {"file_path": "test.py", "content": "new content"},
                }
            ],
        },
    ]
    assert result == expected


def test_uncovered_lines_96_97_malformed_markers_second_pass():
    """Test lines 96-97: append item and continue when markers malformed in second pass"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' missing end marker",  # This triggers line 95->96->97
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "test.py", "content": "new content"},
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should remain unchanged since malformed content is preserved
    assert result == messages


def test_uncovered_line_112_file_not_tracked():
    """Test line 112: append item when file is not in latest_positions (latest_info is None)"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'untracked.py' with line numbers for your information.\n1: print('hello')",  # This triggers line 103->112
                }
            ],
        },


def test_line_28_non_dict_item_in_first_pass():
    """Test line 28: continue when item is not a dict in first pass"""
    messages = [
        {
            "role": "assistant",
            "content": [
                "string_item",  # This triggers line 28
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "test.py", "content": "content"},
                }
            ],
        }
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_line_39_invalid_input_data():
    """Test line 39: continue when input_data is invalid or missing file_path"""
    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": "not_a_dict",  # This triggers line 39
                }
            ],
        }
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_line_61_malformed_markers_first_pass():
    """Test line 61: continue when start or end markers not found in first pass"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' missing end marker",  # This triggers line 61
                }
            ],
        }
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_line_75_76_non_dict_item_in_second_pass():
    """Test lines 75-76: append non-dict item and continue in second pass"""
    messages = [
        {
            "role": "user",
            "content": [
                "string_item",  # This triggers lines 75-76
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
                    "input": {"file_path": "test.py", "content": "print('world')"},
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)

    expected = [
        {
            "role": "user",
            "content": [
                "string_item",  # Non-dict preserved
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
                    "input": {"file_path": "test.py", "content": "print('world')"},
                }
            ],
        },
    ]
    assert result == expected


def test_line_96_97_malformed_markers_second_pass():
    """Test lines 96-97: append item and continue when markers not found in second pass"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' missing end marker",  # This triggers lines 96-97
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "test.py", "content": "print('world')"},
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should remain unchanged since malformed content is preserved
    assert result == messages


def test_line_112_file_not_in_latest_positions():
    """Test line 112: append item when file not in latest_positions (latest_info is None)"""
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
        # No replace operation for untracked.py, so latest_info will be None
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
