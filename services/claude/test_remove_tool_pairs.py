# pyright: reportIndexIssue=false, reportArgumentType=false
from typing import cast

from anthropic.types import MessageParam

from services.claude.remove_tool_pairs import remove_tool_pairs


def test_empty_ids_no_change():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "get_local_file_content",
                        "input": {"file_path": "test.py"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "file content",
                    }
                ],
            },
        ],
    )
    original_len = len(messages)
    remove_tool_pairs(messages, set())
    assert len(messages) == original_len


def test_removes_tool_use_and_result_blocks():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "get_local_file_content",
                        "input": {"file_path": "test.py"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "file content",
                    }
                ],
            },
            {"role": "assistant", "content": "I see the file."},
        ],
    )
    remove_tool_pairs(messages, {"toolu_1"})
    # Both tool_use and tool_result messages popped (empty after block removal)
    assert len(messages) == 1
    assert messages[0]["content"] == "I see the file."


def test_keeps_other_blocks_in_same_message():
    """When a message has multiple tool blocks, only the outdated one is removed."""
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "get_local_file_content",
                        "input": {"file_path": "old.py"},
                    },
                    {
                        "type": "tool_use",
                        "id": "toolu_2",
                        "name": "get_local_file_content",
                        "input": {"file_path": "keep.py"},
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "old content",
                    },
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_2",
                        "content": "keep content",
                    },
                ],
            },
        ],
    )
    remove_tool_pairs(messages, {"toolu_1"})
    assert len(messages) == 2
    # Assistant message: only toolu_2 remains
    assert len(messages[0]["content"]) == 1
    assert messages[0]["content"][0]["id"] == "toolu_2"
    # User message: only toolu_2 result remains
    assert len(messages[1]["content"]) == 1
    assert messages[1]["content"][0]["tool_use_id"] == "toolu_2"


def test_pops_messages_with_no_remaining_tool_blocks():
    """After removing all tool blocks, the message itself is popped."""
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {"role": "assistant", "content": "Before."},
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "search_and_replace",
                        "input": {
                            "file_path": "test.py",
                            "old_string": "a",
                            "new_string": "b",
                        },
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "Updated test.py.",
                    }
                ],
            },
            {"role": "assistant", "content": "After."},
        ],
    )
    remove_tool_pairs(messages, {"toolu_1"})
    assert len(messages) == 2
    assert messages[0]["content"] == "Before."
    assert messages[1]["content"] == "After."


def test_multiple_ids_removed():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "get_local_file_content",
                        "input": {"file_path": "a.py"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "a content",
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_2",
                        "name": "get_local_file_content",
                        "input": {"file_path": "b.py"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_2",
                        "content": "b content",
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_3",
                        "name": "get_local_file_content",
                        "input": {"file_path": "c.py"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_3",
                        "content": "c content",
                    }
                ],
            },
        ],
    )
    remove_tool_pairs(messages, {"toolu_1", "toolu_2"})
    # Only toolu_3 pair remains
    assert len(messages) == 2
    assert messages[0]["content"][0]["id"] == "toolu_3"
    assert messages[1]["content"][0]["tool_use_id"] == "toolu_3"


def test_skips_non_list_content():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {"role": "assistant", "content": "Just text."},
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "get_local_file_content",
                        "input": {"file_path": "test.py"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "content",
                    }
                ],
            },
        ],
    )
    remove_tool_pairs(messages, {"toolu_1"})
    assert len(messages) == 1
    assert messages[0]["content"] == "Just text."
