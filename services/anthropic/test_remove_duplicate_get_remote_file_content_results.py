# Standard imports
import json
from copy import deepcopy
from unittest.mock import patch

# Local imports
from config import UTF8
from services.anthropic.remove_duplicate_get_remote_file_content_results import \
    remove_duplicate_get_remote_file_content_results


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
    # Test with empty list - covers line 11
    messages = []
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == []


def test_none_messages():
    # Test with None - covers line 11
    messages = None
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result is None


def test_non_dict_item_in_content():
    # Test with non-dict item in content list - covers lines 26, 54, 55
    messages = [
        {
            "role": "user",
            "content": [
                "string item",  # Not a dict
                {"type": "text", "text": "some text"},  # Dict but not tool_result
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_tool_result_without_opened_file_prefix():
    # Test tool_result that doesn't start with "Opened file: '" - covers lines 36, 66, 67
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                    "content": "Some other tool result",
                }
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_opened_file_without_required_suffix():
    # Test file content without required suffix - covers lines 36, 66, 67
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                    "content": "Opened file: 'test.py' but missing required suffix",
                }
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_invalid_filename_extraction():
    # Test with invalid filename extraction - covers lines 41, 72, 73
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                    "content": "Opened file: with line numbers for your information.",
                }
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_filename_with_no_closing_quote():
    # Test filename extraction with no closing quote - covers lines 41, 72, 73
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                    "content": "Opened file: 'test.py with line numbers for your information.",
                }
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_multiple_occurrences_suffix():
    # Test with "and found multiple occurrences of" suffix
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                    "content": "Opened file: 'test.py' and found multiple occurrences of pattern.\n\nOld content",
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
                    "content": "Opened file: 'test.py' and found multiple occurrences of pattern.\n\nNew content",
                }
            ],
        },
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result[0]["content"][0]["content"] == "[Outdated 'test.py' content removed]"
    assert "New content" in result[2]["content"][0]["content"]


def test_message_with_non_list_content():
    # Test message with content that is not a list
    messages = [
        {"role": "user", "content": "string content"},
        {"role": "assistant", "content": "response"},
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_message_without_role():
    # Test message without role field
    messages = [
        {"content": "some content"},
        {"role": "user", "content": "Hello"},
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_message_with_assistant_role():
    # Test that assistant messages are skipped
    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n\nContent",
                }
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_multiple_files_deduplication():
    # Test deduplication of multiple different files
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                    "content": "Opened file: 'file1.py' with line numbers for your information.\n\nFile1 v1",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id2",
                    "content": "Opened file: 'file2.py' with line numbers for your information.\n\nFile2 v1",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id3",
                    "content": "Opened file: 'file1.py' with line numbers for your information.\n\nFile1 v2",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id4",
                    "content": "Opened file: 'file2.py' with line numbers for your information.\n\nFile2 v2",
                }
            ],
        },
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    # First occurrences should be replaced
    assert result[0]["content"][0]["content"] == "[Outdated 'file1.py' content removed]"
    assert result[1]["content"][0]["content"] == "[Outdated 'file2.py' content removed]"
    # Latest occurrences should be kept
    assert "File1 v2" in result[2]["content"][0]["content"]
    assert "File2 v2" in result[3]["content"][0]["content"]


def test_mixed_content_types_in_message():
    # Test message with mixed content types
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Some text"},
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n\nOld content",
                },
                {"type": "image", "source": "image_data"},
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
    result = remove_duplicate_get_remote_file_content_results(messages)
    # First message should have file content replaced but other items preserved
    assert len(result[0]["content"]) == 3
    assert result[0]["content"][0]["type"] == "text"
    assert result[0]["content"][1]["content"] == "[Outdated 'test.py' content removed]"
    assert result[0]["content"][2]["type"] == "image"
    # Second message should be unchanged
    assert "New content" in result[1]["content"][0]["content"]


def test_same_file_single_occurrence():
    # Test file that appears only once (should not be replaced)
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                    "content": "Opened file: 'unique.py' with line numbers for your information.\n\nContent",
                }
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    # Should remain unchanged since there's no duplicate
    assert "Content" in result[0]["content"][0]["content"]
    assert "[Outdated" not in result[0]["content"][0]["content"]


def test_tool_result_with_empty_content():
    # Test tool_result with empty content
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                    "content": "",
                }
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_tool_result_without_content_key():
    # Test tool_result without content key
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                }
            ],
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_preserves_original_messages():
    # Test that original messages are not modified
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n\nOld",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id2",
                    "content": "Opened file: 'test.py' with line numbers for your information.\n\nNew",
                }
            ],
        },
    ]
    original_copy = deepcopy(messages)
    result = remove_duplicate_get_remote_file_content_results(messages)

    # Original should be unchanged
    assert messages == original_copy
    # Result should be different
    assert result != messages
