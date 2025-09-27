"""Unit tests for remove_duplicate_get_remote_file_content_results function."""

from services.anthropic.remove_duplicate_get_remote_file_content_results import \
    remove_duplicate_get_remote_file_content_results


def test_empty_messages():
    """Test with empty messages list."""
    result = remove_duplicate_get_remote_file_content_results([])
    assert result == []


def test_no_duplicates():
    """Test with no duplicate file content."""
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_basic_deduplication():
    """Test basic deduplication of file content."""
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
