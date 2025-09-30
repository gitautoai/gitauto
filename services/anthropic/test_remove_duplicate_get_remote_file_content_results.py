# Standard imports
import json
from copy import deepcopy
from unittest.mock import patch

# Local imports
from config import UTF8
from services.anthropic.remove_duplicate_get_remote_file_content_results import (
    remove_duplicate_get_remote_file_content_results,
)


def test_remove_duplicate_get_remote_file_content_results_only():
    # Function only deduplicates get_remote_file_content, not generic messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "Hello"},  # Not deduplicated - not file content
        {
            "role": "assistant",
            "content": "Hi there!",
        },  # Not deduplicated - not file content
    ]

    result = remove_duplicate_get_remote_file_content_results(messages)

    # Should NOT deduplicate non-file content
    assert result == messages  # Should be unchanged


def test_remove_duplicate_get_remote_file_content_results_snapshots():
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                    "content": "Opened file: 'Calculator-MJ/ViewController.swift' with line numbers for your information.\n\nOriginal content",
                }
            ],
        },
        {"role": "assistant", "content": "OK"},
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id2",
                    "content": "Opened file: 'Calculator-MJ/ViewController.swift' with line numbers for your information.\n\nUpdated content",
                }
            ],
        },
    ]

    result = remove_duplicate_get_remote_file_content_results(messages)

    # Should deduplicate file content, keeping latest
    assert len(result) == 4
    assert result[0]["role"] == "system"
    assert (
        result[1]["content"][0]["content"]
        == "[Outdated 'Calculator-MJ/ViewController.swift' content removed]"
    )
    assert "Updated content" in result[3]["content"][0]["content"]


def test_no_duplicates():
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "First question"},
        {"role": "assistant", "content": "First answer"},
        {"role": "user", "content": "Second question"},
        {"role": "assistant", "content": "Second answer"},
    ]

    original = deepcopy(messages)
    result = remove_duplicate_get_remote_file_content_results(messages)

    # Should return messages unchanged
    assert result == original


def test_preserve_system_messages():
    messages = [
        {"role": "system", "content": "System prompt 1"},
        {"role": "system", "content": "System prompt 1"},  # Duplicate system
        {"role": "user", "content": "Hello"},
    ]

    result = remove_duplicate_get_remote_file_content_results(messages)

    # System messages should never be deduplicated
    assert len(result) == 3
    assert result[0]["content"] == "System prompt 1"
    assert result[1]["content"] == "System prompt 1"
    assert result[2]["content"] == "Hello"


def test_with_real_agent_input():
    # Load actual data (formatted/prettified version for readability)
    with open(
        "payloads/anthropic/llm_request_2816_input_content_formatted.json",
        "r",
        encoding=UTF8,
    ) as f:
        original_messages = json.load(f)

    # Load expected result
    with open(
        "payloads/anthropic/llm_request_2816_input_content_formatted_expected.json",
        "r",
        encoding=UTF8,
    ) as f:
        expected_messages = json.load(f)

    # Deduplicate using our function
    result = remove_duplicate_get_remote_file_content_results(original_messages)

    # Should match expected output
    assert result == expected_messages


def test_with_production_minified_json():
    # Test with real minified JSON from production database (llm_request ID 2816)
    # This is the actual format used in production - not prettified
    with open(
        "payloads/anthropic/llm_request_2816_input_content_raw.json", "r", encoding=UTF8
    ) as f:
        messages = json.load(f)

    # Should have 52 messages
    assert len(messages) == 52

    # Apply deduplication
    result = remove_duplicate_get_remote_file_content_results(messages)

    # Should still have 52 messages
    assert len(result) == 52

    # Check that deduplication occurred
    original_size = len(json.dumps(messages))
    deduplicated_size = len(json.dumps(result))

    # Should reduce size significantly (by ~50%)
    assert deduplicated_size < original_size
    assert (
        deduplicated_size < original_size * 0.6
    )  # Should be less than 60% of original

    # Count replaced file contents
    replaced_count = 0
    for msg in result:
        if msg.get("role") == "user" and isinstance(msg.get("content"), list):
            for item in msg["content"]:
                if isinstance(item, dict) and "[Outdated" in str(
                    item.get("content", "")
                ):
                    replaced_count += 1

    # Should have replaced 4 outdated file contents
    assert replaced_count == 4


def test_handles_exception_gracefully():
    # Test by mocking deepcopy to raise an exception

    messages = [{"role": "user", "content": []}]

    with patch("copy.deepcopy", side_effect=RuntimeError("Simulated failure")):
        result = remove_duplicate_get_remote_file_content_results(messages)
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

    result = remove_duplicate_get_remote_file_content_results(messages)
    # Should return original messages unchanged when exception occurs
    assert result == messages


def test_empty_messages_list():
    # Test with empty messages list
    messages = []
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == []


def test_none_messages():
    # Test with None messages
    messages = None
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result is None


def test_non_dict_items_in_content():
    # Test with non-dict items in content list
    messages = [
        {
            "role": "user",
            "content": [
                "string item",  # Non-dict item
                {"type": "tool_result", "content": "Some content"},
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_non_tool_result_type():
    # Test with items that are not tool_result type
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "content": "Some text"},
                {"type": "image", "content": "Image data"},
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_tool_result_without_required_phrases():
    # Test with tool_result that starts with "Opened file:" but lacks required phrases
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
    assert result == messages


def test_tool_result_with_invalid_filename_parsing():
    # Test with tool_result where filename parsing fails (no closing quote)
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: test.py with line numbers for your information.",
                }
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_tool_result_with_empty_filename():
    # Test with tool_result where filename is empty (quotes are adjacent)
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
    # Test with mixed content including non-dict items and duplicates
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


def test_tool_result_with_multiple_occurrences_phrase():
    # Test with "and found multiple occurrences of" phrase instead of "with line numbers"
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'search.py' and found multiple occurrences of pattern.\nContent v1",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
