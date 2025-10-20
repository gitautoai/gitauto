# pylint: disable=redefined-outer-name
"""Unit tests for remove_get_remote_file_content_before_replace_remote_file_content.py"""

import pytest
from services.anthropic.remove_get_remote_file_content_before_replace_remote_file_content import \
    remove_get_remote_file_content_before_replace_remote_file_content


def test_empty_messages():
    """Test with empty messages list"""
    messages = []
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == []


def test_none_messages():
    """Test with None messages"""
    messages = None
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result is None


def test_messages_without_content_list():
    """Test messages where content is not a list"""
    messages = [
        {"role": "user", "content": "string content"},
        {"role": "assistant", "content": {"type": "text"}},
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_content_with_non_dict_items():
    """Test content list with non-dict items"""
    messages = [
        {
            "role": "user",
            "content": [
                "string item",
                123,
                None,
                {"type": "text", "text": "valid item"},
            ],
        }
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_replace_remote_file_content_without_input():
    """Test replace_remote_file_content tool_use without input field"""
    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    # No input field
                }
            ],
        }
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_replace_remote_file_content_with_non_dict_input():
    """Test replace_remote_file_content tool_use with non-dict input"""
    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": "not a dict",
                }
            ],
        }
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_replace_remote_file_content_without_file_path():
    """Test replace_remote_file_content tool_use without file_path in input"""
    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"other_field": "value"},
                }
            ],
        }
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_tool_result_not_from_user():
    """Test tool_result from non-user role"""
    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers\n1: content",
                }
            ],
        }
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_tool_result_without_file_markers():
    """Test tool_result without proper file markers"""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "content": "Some other content"},
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' but no line numbers",
                },
                {
                    "type": "tool_result",
                    "content": "No opened file marker with line numbers",
                },
            ],
        }
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_malformed_file_content_markers_first_pass():
    """Test malformed file content markers in first pass (line 60-61)"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers but malformed",
                    "tool_use_id": "tool1",
                }
            ],
        }
    ]
    # This should trigger the continue at line 61
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_malformed_file_content_markers_second_pass():
    """Test malformed file content markers in second pass (line 95-97)"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers but malformed",
                    "tool_use_id": "tool1",
                }
            ],
        }
    ]
    # This should trigger the continue at line 96-97
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_file_not_in_latest_positions():
    """Test file content that is not in latest_positions (line 112)"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'orphan.py' with line numbers\n1: content",
                    "tool_use_id": "tool1",
                }
            ],
        }
    ]
    # This file is never referenced in replace_remote_file_content, so latest_info will be None
    # This should trigger line 112
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_outdated_content_removed():
    """Test that outdated file content is replaced with placeholder"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers\n1: old content",
                    "tool_use_id": "tool1",
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "test.py", "file_content": "new content"},
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result[0]["content"][0]["content"] == "[Outdated content removed]"


def test_latest_content_preserved():
    """Test that latest file content is preserved"""
    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "test.py", "file_content": "new content"},
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers\n1: latest content",
                    "tool_use_id": "tool2",
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert (
        result[1]["content"][0]["content"]
        == "Opened file: 'test.py' with line numbers\n1: latest content"
    )


def test_multiple_files_tracking():
    """Test tracking multiple files"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file1.py' with line numbers\n1: content1",
                    "tool_use_id": "tool1",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file2.py' with line numbers\n1: content2",
                    "tool_use_id": "tool2",
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "file1.py", "file_content": "new1"},
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "file2.py", "file_content": "new2"},
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result[0]["content"][0]["content"] == "[Outdated content removed]"
    assert result[1]["content"][0]["content"] == "[Outdated content removed]"


def test_same_file_multiple_times():
    """Test same file opened multiple times"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers\n1: first",
                    "tool_use_id": "tool1",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers\n1: second",
                    "tool_use_id": "tool2",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers\n1: third",
                    "tool_use_id": "tool3",
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # First two should be outdated, last one should be preserved
    assert result[0]["content"][0]["content"] == "[Outdated content removed]"
    assert result[1]["content"][0]["content"] == "[Outdated content removed]"
    assert (
        result[2]["content"][0]["content"]
        == "Opened file: 'test.py' with line numbers\n1: third"
    )


def test_deep_copy_preserves_original():
    """Test that original messages are not modified"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers\n1: content",
                    "tool_use_id": "tool1",
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "test.py", "file_content": "new"},
                }
            ],
        },
    ]
    original_content = messages[0]["content"][0]["content"]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Original should be unchanged
    assert messages[0]["content"][0]["content"] == original_content
    # Result should be modified
    assert result[0]["content"][0]["content"] == "[Outdated content removed]"


def test_mixed_content_types():
    """Test messages with mixed content types"""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Some text"},
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers\n1: content",
                    "tool_use_id": "tool1",
                },
                {"type": "image", "source": "image_data"},
            ],
        },
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Response"},
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "test.py", "file_content": "new"},
                },
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Text and image should be preserved
    assert result[0]["content"][0] == {"type": "text", "text": "Some text"}
    assert result[0]["content"][2] == {"type": "image", "source": "image_data"}
    # File content should be replaced
    assert result[0]["content"][1]["content"] == "[Outdated content removed]"


def test_edge_case_empty_file_path():
    """Test edge case with empty file_path"""
    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "", "file_content": "content"},
                }
            ],
        }
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_edge_case_special_characters_in_filename():
    """Test edge case with special characters in filename"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test-file_v2.0.py' with line numbers\n1: content",
                    "tool_use_id": "tool1",
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
                        "file_path": "test-file_v2.0.py",
                        "file_content": "new",
                    },
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result[0]["content"][0]["content"] == "[Outdated content removed]"


def test_edge_case_unicode_in_filename():
    """Test edge case with unicode characters in filename"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test_文件.py' with line numbers\n1: content",
                    "tool_use_id": "tool1",
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "test_文件.py", "file_content": "new"},
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result[0]["content"][0]["content"] == "[Outdated content removed]"


def test_corner_case_missing_start_marker():
    """Test corner case where start marker is missing (line 60-61)"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "file: 'test.py' with line numbers\n1: content",
                    "tool_use_id": "tool1",
                }
            ],
        }
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_corner_case_missing_end_marker():
    """Test corner case where end marker is missing (line 60-61)"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' without line numbers\n1: content",
                    "tool_use_id": "tool1",
                }
            ],
        }
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_corner_case_markers_in_wrong_order():
    """Test corner case where markers appear in wrong order"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "' with line numbers Opened file: 'test.py'\n1: content",
                    "tool_use_id": "tool1",
                }
            ],
        }
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_corner_case_empty_content():
    """Test corner case with empty content"""
    messages = [
        {
            "role": "user",
            "content": [{"type": "tool_result", "content": "", "tool_use_id": "tool1"}],
        }
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_corner_case_none_content():
    """Test corner case with None content"""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "content": None, "tool_use_id": "tool1"}
            ],
        }
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_complex_scenario_multiple_operations():
    """Test complex scenario with multiple file operations"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file1.py' with line numbers\n1: v1",
                    "tool_use_id": "tool1",
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "file1.py", "file_content": "v2"},
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file1.py' with line numbers\n1: v2",
                    "tool_use_id": "tool2",
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "file1.py", "file_content": "v3"},
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file1.py' with line numbers\n1: v3",
                    "tool_use_id": "tool3",
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # First two file contents should be outdated
    assert result[0]["content"][0]["content"] == "[Outdated content removed]"
    assert result[2]["content"][0]["content"] == "[Outdated content removed]"
    # Last one should be preserved
    assert (
        result[4]["content"][0]["content"]
        == "Opened file: 'file1.py' with line numbers\n1: v3"
    )


def test_error_handling_with_exception():
    """Test error handling when exception occurs"""
    # The @handle_exceptions decorator should catch any exceptions
    # and return the original messages
    messages = [{"role": "user", "content": []}]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_file_content_after_replace_preserved():
    """Test that file content opened after replace is preserved"""
    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "test.py", "file_content": "new"},
                    "id": "tool1",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers\n1: new content",
                    "tool_use_id": "tool1",
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Content after replace should be preserved
    assert (
        result[1]["content"][0]["content"]
        == "Opened file: 'test.py' with line numbers\n1: new content"
    )


def test_no_modification_when_no_outdated_content():
    """Test that messages are not modified when there's no outdated content"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers\n1: content",
                    "tool_use_id": "tool1",
                }
            ],
        }
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should be equal but not the same object (due to deepcopy)
    assert result == messages
    assert result is not messages


def test_all_uncovered_branches_combined():
    """Test all uncovered branches in a single comprehensive test"""
    messages = [
        # Test line 60-61: malformed markers in first pass
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'malformed1.py' with line numbers",
                    "tool_use_id": "tool1",
                }
            ],
        },
        # Test line 112: file not in latest_positions
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'orphan.py' with line numbers\n1: orphan content",
                    "tool_use_id": "tool2",
                }
            ],
        },
        # Test line 95-97: malformed markers in second pass
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'malformed2.py' with line numbers",
                    "tool_use_id": "tool3",
                }
            ],
        },
        # Normal case for comparison
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'normal.py' with line numbers\n1: normal content",
                    "tool_use_id": "tool4",
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "normal.py", "file_content": "new content"},
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Malformed and orphan files should be unchanged
    assert result[0] == messages[0]
    assert result[1] == messages[1]
    assert result[2] == messages[2]
    # Normal file should be marked as outdated
    assert result[3]["content"][0]["content"] == "[Outdated content removed]"


def test_marker_at_start_of_content():
    """Test when marker is at the very start of content"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers\n1: content",
                    "tool_use_id": "tool1",
                }
            ],
        }
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result == messages


def test_marker_with_extra_spaces():
    """Test markers with extra spaces"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file:  'test.py'  with line numbers\n1: content",
                    "tool_use_id": "tool1",
                }
            ],
        }
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should not match due to extra spaces
    assert result == messages


def test_case_sensitive_markers():
    """Test that markers are case-sensitive"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "OPENED FILE: 'test.py' WITH LINE NUMBERS\n1: content",
                    "tool_use_id": "tool1",
                }
            ],
        }
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Should not match due to case difference
    assert result == messages


def test_multiple_tool_results_in_single_message():
    """Test multiple tool_result items in a single message"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file1.py' with line numbers\n1: content1",
                    "tool_use_id": "tool1",
                },
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file2.py' with line numbers\n1: content2",
                    "tool_use_id": "tool2",
                },
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "file1.py", "file_content": "new1"},
                },
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "file2.py", "file_content": "new2"},
                },
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    assert result[0]["content"][0]["content"] == "[Outdated content removed]"
    assert result[0]["content"][1]["content"] == "[Outdated content removed]"


def test_position_tracking_accuracy():
    """Test that position tracking is accurate across multiple messages"""
    messages = [
        {"role": "user", "content": [{"type": "text", "text": "Message 0"}]},
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers\n1: v1",
                    "tool_use_id": "tool1",
                }
            ],
        },
        {"role": "assistant", "content": [{"type": "text", "text": "Message 2"}]},
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "test.py", "file_content": "v2"},
                }
            ],
        },
        {"role": "user", "content": [{"type": "text", "text": "Message 4"}]},
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # File content at position 1 should be outdated (position 1 < position 3)
    assert result[1]["content"][0]["content"] == "[Outdated content removed]"


def test_latest_position_wins():
    """Test that the latest position is used when file appears multiple times"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers\n1: v1",
                    "tool_use_id": "tool1",
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "test.py", "file_content": "v2"},
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers\n1: v2",
                    "tool_use_id": "tool2",
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "test.py", "file_content": "v3"},
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # Both file contents should be outdated (positions 0 and 2 < position 3)
    assert result[0]["content"][0]["content"] == "[Outdated content removed]"
    assert result[2]["content"][0]["content"] == "[Outdated content removed]"


def test_content_type_tracking():
    """Test that both 'replace' and 'content' types are tracked correctly"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers\n1: v1",
                    "tool_use_id": "tool1",
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "replace_remote_file_content",
                    "input": {"file_path": "test.py", "file_content": "v2"},
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers\n1: v2",
                    "tool_use_id": "tool2",
                }
            ],
        },
    ]
    result = remove_get_remote_file_content_before_replace_remote_file_content(messages)
    # First content should be outdated, last should be preserved
    assert result[0]["content"][0]["content"] == "[Outdated content removed]"
    assert (
        result[2]["content"][0]["content"]
        == "Opened file: 'test.py' with line numbers\n1: v2"
    )
