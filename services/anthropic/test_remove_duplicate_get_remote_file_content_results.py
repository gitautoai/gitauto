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
    """Test with empty messages list - covers line 11"""
    messages = []
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == []


def test_non_dict_item_in_content():
    """Test with non-dict item in content list - covers line 26"""
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
    assert len(result) == 1
    assert len(result[0]["content"]) == 2
    assert result[0]["content"][0] == "string_item"


def test_item_without_tool_result_type():
    """Test with dict item that doesn't have type='tool_result' - covers line 26"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",  # Not tool_result
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
    assert len(result) == 1
    assert len(result[0]["content"]) == 2
    assert result[0]["content"][0]["type"] == "text"


def test_content_without_required_phrases():
    """Test content that starts with 'Opened file:' but lacks required phrases - covers line 36"""
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
    """Test cases where filename extraction fails - covers line 41"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: with line numbers for your information.\nContent"  # Missing quotes
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py with line numbers for your information.\nContent"  # Missing closing quote
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages  # Should remain unchanged


def test_content_with_search_phrase():
    """Test content with 'and found multiple occurrences of' phrase"""
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
    # First occurrence should be replaced
    assert "[Outdated 'test.py' content removed]" in result[0]["content"][0]["content"]
    # Second occurrence should remain
    assert "another_term" in result[1]["content"][0]["content"]


def test_content_modification_detection():
    """Test that content modification is properly detected and applied."""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                    "content": "Opened file: 'test.py' with line numbers for your information.\nOld content",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id2",
                    "content": "Opened file: 'test.py' with line numbers for your information.\nNew content",
                }
            ],
        },
    ]

    result = remove_duplicate_get_remote_file_content_results(messages)

    # First message should be modified
    assert result[0]["content"][0]["content"] == "[Outdated 'test.py' content removed]"
    # Second message should remain unchanged
    assert "New content" in result[1]["content"][0]["content"]
    # Should trigger line 84-85 (content modification detection)
    assert result[0]["content"] != messages[0]["content"]


def test_mixed_content_types():
    """Test with mixed content types in the same message"""
    messages = [
        {
            "role": "user",
            "content": [
                "text_item",
                {
                    "type": "image",
                    "content": "image_data"
                },
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\nContent"
                },
                123,  # Non-dict, non-string item
                {
                    "type": "tool_result",
                    "content": "Some other tool result"
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert len(result[0]["content"]) == 5
    assert result[0]["content"][0] == "text_item"
    assert result[0]["content"][1]["type"] == "image"
    assert result[0]["content"][3] == 123


def test_none_content_in_tool_result():
    """Test with None content in tool_result"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": None
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_empty_content_in_tool_result():
    """Test with empty content in tool_result"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": ""
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_edge_case_filename_extraction_boundaries():
    """Test edge cases in filename extraction with boundary conditions"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                    "content": "Opened file: '' with line numbers for your information.\nEmpty filename",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id2",
                    "content": "Opened file: 'a' with line numbers for your information.\nSingle char filename",
                }
            ],
        }
    ]

    result = remove_duplicate_get_remote_file_content_results(messages)

    # Empty filename should be skipped, single char should work
    assert result[0]["content"][0]["content"] == "Opened file: '' with line numbers for your information.\nEmpty filename"
    assert "Single char filename" in result[1]["content"][0]["content"]
    assert result is not messages  # Should be a deep copy


def test_complex_scenario_with_all_edge_cases():
    """Test a complex scenario that exercises multiple edge cases"""
    messages = [
        {
            "role": "user",
            "content": [
                "text item",  # Non-dict
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                    "content": "Opened file: 'valid.py' with line numbers for your information.\nFirst content",
                },
                {
                    "type": "other",  # Not tool_result
                    "content": "other content",
                },
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id2",
                    "content": "Opened file: 'invalid' without required phrase",  # Missing phrase
                },
                {
                    "type": "tool_result",
                    "tool_use_id": "id3",
                    "content": "Opened file: 'valid.py' with line numbers for your information.\nSecond content",
                },
            ],
        }
    ]

    result = remove_duplicate_get_remote_file_content_results(messages)

    # Should preserve non-dict and non-tool_result items
    assert result[0]["content"][0] == "text item"
    assert result[0]["content"][2]["type"] == "other"

    # Should deduplicate valid.py content
    assert "[Outdated 'valid.py' content removed]" in result[0]["content"][1]["content"]
    assert "Second content" in result[1]["content"][1]["content"]

    # Should preserve invalid content as-is
    assert "without required phrase" in result[1]["content"][0]["content"]
