# Standard imports
from copy import deepcopy

# Local imports
from services.anthropic.remove_duplicate_get_remote_file_content_results import \
    remove_duplicate_get_remote_file_content_results


def test_empty_list():
    """Test with empty messages list - covers line 10-11"""
    messages = []
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == []


def test_none_messages():
    """Test with None messages - covers line 10-11"""
    messages = None
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result is None


def test_no_duplicates():
    """Test with no duplicate files"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file1.py' with line numbers for your information.\nContent 1",
                }
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_duplicate_files():
    """Test with duplicate file references"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file1.py' with line numbers for your information.\nOld content",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file1.py' with line numbers for your information.\nNew content",
                }
            ],
        },
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)

    # First occurrence should be replaced
    assert result[0]["content"][0]["content"] == "[Outdated 'file1.py' content removed]"
    # Latest occurrence should remain
    assert "New content" in result[1]["content"][0]["content"]


def test_multiple_files_with_duplicates():
    """Test with multiple files and duplicates"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file1.py' with line numbers for your information.\nContent 1",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file2.py' with line numbers for your information.\nContent 2",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file1.py' with line numbers for your information.\nContent 3",
                }
            ],
        },
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)

    # First file1.py should be replaced
    assert result[0]["content"][0]["content"] == "[Outdated 'file1.py' content removed]"
    # file2.py should remain (no duplicates)
    assert "Content 2" in result[1]["content"][0]["content"]
    # Latest file1.py should remain
    assert "Content 3" in result[2]["content"][0]["content"]


def test_non_user_role():
    """Test with non-user role messages"""
    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file1.py' with line numbers for your information.\nContent",
                }
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_non_list_content():
    """Test with non-list content"""
    messages = [
        {
            "role": "user",
            "content": "string content",
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_non_dict_item_in_content():
    """Test with non-dict items in content list - covers lines 25-26 and 53-55"""
    messages = [
        {
            "role": "user",
            "content": [
                "string item",  # Non-dict item
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\nContent",
                },
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    # Should handle non-dict items gracefully
    assert len(result) == 1
    assert result[0]["content"][0] == "string item"


def test_non_tool_result_type():
    """Test with items that are not tool_result type - covers lines 25-26 and 53-55"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "content": "Some text",
                },
                {
                    "type": "image",
                    "content": "Image data",
                },
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_tool_result_without_opened_file():
    """Test with tool_result that doesn't start with 'Opened file:'"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Some other tool result",
                }
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_content_without_required_phrases():
    """Test with content missing required phrases - covers lines 32-36 and 62-67"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' but missing required phrase",
                }
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    # Should keep items without required phrases unchanged
    assert len(result) == 1
    assert result[0]["content"][0]["content"] == "Opened file: 'test.py' but missing required phrase"


def test_content_with_multiple_occurrences_phrase():
    """Test with 'and found multiple occurrences of' phrase - covers lines 32-36 and 62-67"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' and found multiple occurrences of pattern",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' and found multiple occurrences of pattern",
                }
            ],
        },
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    # Should deduplicate with "multiple occurrences" phrase
    assert len(result) == 2
    assert "[Outdated 'test.py' content removed]" in result[0]["content"][0]["content"]


def test_invalid_filename_parsing_no_quotes():
    """Test with invalid filename format (no quotes) - covers lines 40-41 and 71-73"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: test.py with line numbers for your information.\nContent",
                }
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    # Should keep items with invalid filename format unchanged
    assert len(result) == 1
    assert "Opened file: test.py" in result[0]["content"][0]["content"]


def test_invalid_filename_parsing_single_quote():
    """Test with invalid filename format (only one quote) - covers lines 40-41 and 71-73"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py with line numbers for your information.\nContent",
                }
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    # Should keep items with invalid filename format unchanged
    assert len(result) == 1
    assert "Opened file: 'test.py" in result[0]["content"][0]["content"]


def test_tool_result_with_empty_filename():
    """Test with empty filename (adjacent quotes) - covers lines 40-41 and 71-73"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: '' with line numbers for your information.",
                }
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_mixed_content_with_duplicates():
    """Test with mixed content including non-dict items and duplicates"""
    messages = [
        {
            "role": "user",
            "content": [
                "text item",  # Non-dict
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\nContent v1",
                },
                {"type": "text", "content": "Some text"},  # Non-tool_result
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\nContent v2",
                },
            ],
        },
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)

    # First message should have outdated content replaced
    assert result[0]["content"][0] == "text item"
    assert "[Outdated 'test.py' content removed]" in result[0]["content"][1]["content"]
    assert result[0]["content"][2]["type"] == "text"

    # Second message should keep the latest content
    assert "Content v2" in result[1]["content"][0]["content"]


def test_original_not_modified():
    """Test that original messages are not modified"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file1.py' with line numbers for your information.\nOld content",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file1.py' with line numbers for your information.\nNew content",
                }
            ],
        },
    ]
    original = deepcopy(messages)
    result = remove_duplicate_get_remote_file_content_results(messages)

    # Original should not be modified
    assert messages == original
    # Result should be different
    assert result != messages
