# Standard imports
from copy import deepcopy

# Local imports
from services.anthropic.remove_duplicate_get_remote_file_content_results import \
    remove_duplicate_get_remote_file_content_results


def test_empty_messages_list():
    """Test with empty messages list"""
    messages = []
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == []


def test_no_file_content_messages():
    """Test with messages that don't contain file content"""
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]

    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_single_file_content():
    """Test with single file content - should not be deduplicated"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n\nContent here",
                }
            ],
        }
    ]

    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_duplicate_file_content():
    """Test with duplicate file content - should deduplicate"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n\nOld content",
                }
            ],
        },
        {"role": "assistant", "content": "I see the file"},
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id2",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n\nNew content",
                }
            ],
        },
    ]

    result = remove_duplicate_get_remote_file_content_results(messages)

    # Should have same number of messages
    assert len(result) == 3

    # First file content should be replaced with placeholder
    assert result[0]["content"][0]["content"] == "[Outdated 'test.py' content removed]"

    # Second file content should remain unchanged
    assert "New content" in result[2]["content"][0]["content"]

    # Assistant message should remain unchanged
    assert result[1]["content"] == "I see the file"


def test_multiple_files():
    """Test with multiple different files - should not deduplicate different files"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                    "content": "Opened file: 'file1.py' with line numbers for your information.\n\nContent 1",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id2",
                    "content": "Opened file: 'file2.py' with line numbers for your information.\n\nContent 2",
                }
            ],
        },
    ]

    result = remove_duplicate_get_remote_file_content_results(messages)

    # Should not deduplicate different files
    assert "Content 1" in result[0]["content"][0]["content"]
    assert "Content 2" in result[1]["content"][0]["content"]


def test_search_phrase_content():
    """Test with 'and found multiple occurrences of' phrase"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' and found multiple occurrences of 'search_term'"
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' and found multiple occurrences of 'another_term'"
                }
            ]
        }
    ]

    result = remove_duplicate_get_remote_file_content_results(messages)

    # First occurrence should be replaced
    assert "[Outdated 'test.py' content removed]" in result[0]["content"][0]["content"]
    # Second occurrence should remain
    assert "another_term" in result[1]["content"][0]["content"]


def test_non_dict_content_items():
    """Test with non-dict items in content list"""
    messages = [
        {
            "role": "user",
            "content": [
                "string_item",  # Non-dict item
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\nContent"
                }
            ]
        }
    ]

    result = remove_duplicate_get_remote_file_content_results(messages)
    assert len(result[0]["content"]) == 2
    assert result[0]["content"][0] == "string_item"


def test_non_tool_result_items():
    """Test with dict items that are not tool_result type"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "content": "Some text"
                },
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\nContent"
                }
            ]
        }
    ]

    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result[0]["content"][0]["type"] == "text"


def test_malformed_file_content():
    """Test with malformed file content that doesn't match expected patterns"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' but missing required phrase"
                }
            ]
        }
    ]

    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages  # Should remain unchanged


def test_malformed_filename_extraction():
    """Test cases where filename extraction fails"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: with line numbers for your information.\nContent"  # Missing quotes
                }
            ]
        }
    ]

    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages  # Should remain unchanged


def test_deep_copy_behavior():
    """Test that function returns a deep copy and doesn't modify original"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n\nOld content",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id2",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n\nNew content",
                }
            ],
        },
    ]

    original_messages = deepcopy(messages)
    result = remove_duplicate_get_remote_file_content_results(messages)

    # Original should be unchanged
    assert messages == original_messages

    # Result should be different
    assert result != messages

    # Result should be a deep copy (different object)
    assert result is not messages
