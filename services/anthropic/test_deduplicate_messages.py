# Standard imports
import json
from copy import deepcopy

# Local imports
from config import UTF8
from services.anthropic.deduplicate_messages import deduplicate_file_content


def test_deduplicate_file_content_only():
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

    result = deduplicate_file_content(messages)

    # Should NOT deduplicate non-file content
    assert result == messages  # Should be unchanged


def test_deduplicate_file_snapshots():
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

    result = deduplicate_file_content(messages)

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
    result = deduplicate_file_content(messages)

    # Should return messages unchanged
    assert result == original


def test_preserve_system_messages():
    messages = [
        {"role": "system", "content": "System prompt 1"},
        {"role": "system", "content": "System prompt 1"},  # Duplicate system
        {"role": "user", "content": "Hello"},
    ]

    result = deduplicate_file_content(messages)

    # System messages should never be deduplicated
    assert len(result) == 3
    assert result[0]["content"] == "System prompt 1"
    assert result[1]["content"] == "System prompt 1"
    assert result[2]["content"] == "Hello"


def test_with_real_agent_input():
    # Load actual data
    with open("payloads/anthropic/agent_pc_large_input.json", "r", encoding=UTF8) as f:
        original_messages = json.load(f)

    # Load expected result
    with open(
        "payloads/anthropic/agent_pc_large_expected.json", "r", encoding=UTF8
    ) as f:
        expected_messages = json.load(f)

    # Deduplicate using our function
    result = deduplicate_file_content(original_messages)

    # Should match expected output
    assert result == expected_messages
