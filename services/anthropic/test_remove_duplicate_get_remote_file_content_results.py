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


def test_second_pass_non_dict_item():
    """Test second pass with non-dict item - covers lines 54, 55"""
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


def test_second_pass_non_tool_result():
    """Test second pass with non-tool_result type - covers lines 54, 55"""
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
    assert len(result[0]["content"]) == 2
    assert result[0]["content"][0]["type"] == "text"


def test_second_pass_content_without_required_phrases():
    """Test second pass content without required phrases - covers lines 66, 67"""
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
    assert result == messages


def test_second_pass_malformed_filename():
    """Test second pass with malformed filename - covers lines 72, 73"""
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
    assert result == messages


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


def test_multiple_files_complex_scenario():
    """Test complex scenario with multiple files and edge cases"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file1.py' with line numbers for your information.\nFirst content"
                }
            ]
        },
        {
            "role": "user",
            "content": [
                "text_item",  # Non-dict item
                {
                    "type": "text",  # Non-tool_result
                    "content": "Some text"
                },
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file2.py' with line numbers for your information.\nSecond content"
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file1.py' with line numbers for your information.\nUpdated first content"
                }
def test_empty_messages_list():
    """Test with empty messages list - covers line 11"""
    messages = []


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
    # Should preserve the string item and process the dict item
    assert result[0]["content"][0] == "string_item"
    assert "test.py" in result[0]["content"][1]["content"]


def test_item_without_tool_result_type():
    """Test with dict item that doesn't have type='tool_result' - covers line 26"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",  # Not tool_result
                    "content": "Some text content"
                },
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\nContent"
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    # Should preserve the text item and process the tool_result item
    assert result[0]["content"][0]["type"] == "text"
    assert "test.py" in result[0]["content"][1]["content"]


def test_file_content_without_required_phrases():
    """Test file content that doesn't contain required phrases - covers line 36"""
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
    # Should not process this as a file content result
    assert result == messages


def test_malformed_filename_extraction_no_quotes():
    """Test content with malformed filename (no quotes) - covers line 41"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: test.py with line numbers for your information.\nContent"
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    # Should not process this due to malformed filename
    assert result == messages


def test_malformed_filename_extraction_single_quote():
    """Test content with only one quote - covers line 41"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py with line numbers for your information.\nContent"
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    # Should not process this due to malformed filename
    assert result == messages


def test_second_pass_non_dict_item():
    """Test second pass with non-dict item - covers line 54, 55"""
    messages = [
        {
            "role": "user",
            "content": [
                "string_item",  # Non-dict item
                42,  # Non-dict item
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\nContent"
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    # Should preserve non-dict items
    assert result[0]["content"][0] == "string_item"
    assert result[0]["content"][1] == 42
    assert "test.py" in result[0]["content"][2]["content"]


def test_second_pass_non_tool_result_type():
    """Test second pass with non-tool_result type - covers line 54, 55"""
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
    # Should preserve non-tool_result items
    assert result[0]["content"][0]["type"] == "text"
    assert "test.py" in result[0]["content"][1]["content"]


def test_second_pass_file_content_without_required_phrases():
    """Test second pass with file content missing required phrases - covers line 66, 67"""
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
    # Should preserve the item as-is
    assert result == messages


def test_second_pass_malformed_filename():
    """Test second pass with malformed filename - covers line 72, 73"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: test.py with line numbers for your information.\nContent"
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    # Should preserve the item as-is due to malformed filename
    assert result == messages


def test_content_with_multiple_occurrences_phrase():
    """Test content with 'and found multiple occurrences of' phrase"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' and found multiple occurrences of pattern.\nContent"
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' and found multiple occurrences of pattern.\nUpdated content"
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    # Should deduplicate based on the alternative phrase
    assert "[Outdated 'test.py' content removed]" in result[0]["content"][0]["content"]
    assert "Updated content" in result[1]["content"][0]["content"]


def test_mixed_content_types_in_user_message():
    """Test user message with mixed content types"""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Please check this file:"},
                "string_item",
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\nContent"
                },
                42,  # Number
                None,  # None value
                {
                    "type": "image",
                    "source": {"type": "base64", "data": "..."}
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    # Should preserve all non-file-content items
    assert len(result[0]["content"]) == 6
    assert result[0]["content"][0]["type"] == "text"
    assert result[0]["content"][1] == "string_item"
    assert "test.py" in result[0]["content"][2]["content"]
    assert result[0]["content"][3] == 42
    assert result[0]["content"][4] is None
    assert result[0]["content"][5]["type"] == "image"


def test_file_content_with_empty_content():
    """Test tool_result with empty content"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": ""  # Empty content
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    # Should not process empty content
    assert result == messages


def test_file_content_with_none_content():
    """Test tool_result with None content"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": None  # None content
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    # Should not process None content (str(None) = "None")
    assert result == messages


def test_edge_case_filename_at_start_of_content():
    """Test edge case where filename extraction might fail"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: '' with line numbers for your information.\nContent"
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    # Should handle empty filename gracefully
    assert result == messages

    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == []


def test_none_messages():
    """Test with None messages - covers line 11"""
    messages = None
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result is None


def test_non_dict_item_in_content():
    """Test with non-dict item in content list - covers line 26"""
    messages = [
        {
            "role": "user",
            "content": [
                "string_item",  # Non-dict item
                {"type": "tool_result", "content": "some content"}
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_item_without_tool_result_type():
    """Test with dict item that's not tool_result type - covers line 26"""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "content": "some text"},  # Not tool_result
                {"type": "tool_result", "content": "some content"}
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_file_content_without_required_phrases():
    """Test file content that doesn't contain required phrases - covers line 36"""
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
    assert result == messages


def test_file_content_with_multiple_occurrences_phrase():
    """Test file content with 'and found multiple occurrences of' phrase"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' and found multiple occurrences of pattern"
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages  # No duplicates to remove


def test_malformed_filename_extraction():
    """Test with malformed filename that can't be extracted - covers line 41"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: with line numbers for your information."  # Missing quotes
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_filename_with_single_quote():
    """Test with filename that has only one quote - covers line 41"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py with line numbers for your information."  # Missing closing quote
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_second_pass_non_dict_item():
    """Test second pass with non-dict item - covers lines 54, 55"""
    messages = [
        {
            "role": "user",
            "content": [
                "string_item",  # Non-dict item in second pass
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\nContent"
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    # Should preserve the string item
    assert result[0]["content"][0] == "string_item"


def test_second_pass_non_tool_result():
    """Test second pass with non-tool_result item - covers lines 54, 55"""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "content": "some text"},  # Not tool_result in second pass
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\nContent"
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    # Should preserve the text item
    assert result[0]["content"][0]["type"] == "text"


def test_second_pass_file_content_without_required_phrases():
    """Test second pass with file content missing required phrases - covers lines 66, 67"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' but missing required phrase in second pass"
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_second_pass_malformed_filename():
    """Test second pass with malformed filename - covers lines 72, 73"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: with line numbers for your information."  # Missing quotes in second pass
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_edge_case_empty_content_string():
    """Test with empty content string"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": ""  # Empty content
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_edge_case_none_content():
    """Test with None content"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": None  # None content
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_edge_case_numeric_content():
    """Test with numeric content"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": 12345  # Numeric content
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages


def test_complex_filename_extraction_edge_cases():
    """Test various edge cases in filename extraction"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: '' with line numbers for your information."  # Empty filename
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'file'with'quotes.py' with line numbers for your information."  # Filename with quotes
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    # Should handle these edge cases gracefully
    assert len(result) == 2


def test_mixed_role_and_content_types():
    """Test with mixed message roles and content types"""
    messages = [
        {"role": "system", "content": "System message"},  # Non-user role
        {"role": "assistant", "content": ["list content"]},  # Non-user role with list
        {"role": "user", "content": "string content"},  # User with string content
        {"role": "user", "content": None},  # User with None content
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.\nContent"
                }
            ]
        }
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert len(result) == 5
    # Non-user messages should be unchanged
    assert result[0] == messages[0]
    assert result[1] == messages[1]
    assert result[2] == messages[2]
    assert result[3] == messages[3]


def test_duplicate_removal_with_edge_case_filenames():
    """Test duplicate removal with edge case filenames"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "id1",
                    "content": "Opened file: 'file with spaces.py' with line numbers for your information.\nOld content"
