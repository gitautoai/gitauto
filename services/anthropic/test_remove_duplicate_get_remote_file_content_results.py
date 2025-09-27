"""Unit tests for remove_duplicate_get_remote_file_content_results function."""

import pytest

# Test the import
try:
    from services.anthropic.remove_duplicate_get_remote_file_content_results import \
        remove_duplicate_get_remote_file_content_results
    IMPORT_SUCCESS = True
    IMPORT_ERROR = None
except Exception as e:
    IMPORT_SUCCESS = False
    IMPORT_ERROR = str(e)


def test_import_works():
    """Test that the import works."""
    if not IMPORT_SUCCESS:
        pytest.fail(f"Import failed: {IMPORT_ERROR}")
    assert IMPORT_SUCCESS


def test_empty_messages():
    """Test with empty messages list."""
    if not IMPORT_SUCCESS:
        pytest.skip("Import failed")

    result = remove_duplicate_get_remote_file_content_results([])
    assert result == []


def test_basic_functionality():
    """Test basic functionality."""
    if not IMPORT_SUCCESS:
        pytest.skip("Import failed")

    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_file_content_deduplication():
    """Test deduplication of file content."""
    if not IMPORT_SUCCESS:
        pytest.skip("Import failed")

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\nOld content",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\nNew content",
                }
            ],
        },
    ]

    result = remove_duplicate_get_remote_file_content_results(messages)

    assert len(result) == 2
    assert result[0]["content"][0]["content"] == "[Outdated 'test.py' content removed]"
    assert "New content" in result[1]["content"][0]["content"]


def test_search_phrase_deduplication():
    """Test deduplication with search phrase."""
    if not IMPORT_SUCCESS:
        pytest.skip("Import failed")

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

    assert len(result) == 2
    assert "[Outdated 'test.py' content removed]" in result[0]["content"][0]["content"]
    assert "another_term" in result[1]["content"][0]["content"]


def test_different_files_not_deduplicated():
    """Test that different files are not deduplicated."""
    if not IMPORT_SUCCESS:
        pytest.skip("Import failed")

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
    ]

    result = remove_duplicate_get_remote_file_content_results(messages)

    # Should not deduplicate different files
    assert "Content 1" in result[0]["content"][0]["content"]
    assert "Content 2" in result[1]["content"][0]["content"]


def test_non_file_content_preserved():
    """Test that non-file content is preserved."""
    if not IMPORT_SUCCESS:
        pytest.skip("Import failed")

    messages = [
        {
            "role": "user",
            "content": [
                "string_item",  # Non-dict item
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
    assert len(result[0]["content"]) == 3
    assert result[0]["content"][0] == "string_item"
    assert result[0]["content"][1]["type"] == "text"


def test_malformed_content_unchanged():
    """Test that malformed content remains unchanged."""
    if not IMPORT_SUCCESS:
        pytest.skip("Import failed")

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


def test_original_messages_unchanged():
    """Test that original messages are not modified."""
    if not IMPORT_SUCCESS:
        pytest.skip("Import failed")

    from copy import deepcopy

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\nOld content",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\nNew content",
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
