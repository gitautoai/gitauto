from typing import cast

from anthropic.types import MessageParam

from services.claude.remove_old_assistant_text import remove_old_assistant_text


def test_empty_messages():
    result = remove_old_assistant_text([])
    assert result == []


def test_fewer_than_keep_recent():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {"role": "assistant", "content": [{"type": "text", "text": "Hello"}]},
            {"role": "assistant", "content": [{"type": "text", "text": "World"}]},
        ],
    )
    result = remove_old_assistant_text(messages, keep_recent=5)
    assert result == messages


def test_strips_old_text_keeps_tool_use():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Old explanation 1"},
                    {"type": "tool_use", "id": "1", "name": "tool1", "input": {}},
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Old explanation 2"},
                    {"type": "tool_use", "id": "2", "name": "tool2", "input": {}},
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Recent explanation"},
                    {"type": "tool_use", "id": "3", "name": "tool3", "input": {}},
                ],
            },
        ],
    )
    result = remove_old_assistant_text(messages, keep_recent=1)

    # First two should have text stripped, only tool_use kept
    assert result[0]["content"] == [
        {"type": "tool_use", "id": "1", "name": "tool1", "input": {}}
    ]
    assert result[1]["content"] == [
        {"type": "tool_use", "id": "2", "name": "tool2", "input": {}}
    ]
    # Last one should keep text
    result_content = cast(list, result[2]["content"])
    assert len(result_content) == 2
    assert result_content[0]["type"] == "text"


def test_does_not_mutate_original():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Old"},
                    {"type": "tool_use", "id": "1", "name": "t", "input": {}},
                ],
            },
            {
                "role": "assistant",
                "content": [{"type": "text", "text": "Recent"}],
            },
        ],
    )
    original_content = cast(list, messages[0]["content"]).copy()
    remove_old_assistant_text(messages, keep_recent=1)
    assert messages[0]["content"] == original_content


def test_skips_non_assistant_messages():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {"role": "user", "content": [{"type": "text", "text": "User message"}]},
            {"role": "assistant", "content": [{"type": "text", "text": "Old"}]},
            {"role": "assistant", "content": [{"type": "text", "text": "Recent"}]},
        ],
    )
    result = remove_old_assistant_text(messages, keep_recent=1)
    # User message should be unchanged
    assert result[0]["content"] == [{"type": "text", "text": "User message"}]
