# pyright: reportIndexIssue=false, reportArgumentType=false
from typing import cast

from anthropic.types import MessageParam

from services.claude.file_tracking import FilePosition
from services.claude.remove_outdated_user_messages import (
    remove_outdated_user_messages,
)


def test_no_positions_no_change():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {"role": "user", "content": "```src/main.py\n1\tprint('hello')\n```"},
        ],
    )
    remove_outdated_user_messages(messages, {})
    assert len(messages) == 1


def test_removes_string_message_for_tracked_file():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {"role": "user", "content": "```src/main.py\n1\tprint('hello')\n```"},
            {"role": "assistant", "content": "I see the file."},
        ],
    )
    positions: dict[str, FilePosition] = {
        "src/main.py": FilePosition(message_index=5, action="read"),
    }
    remove_outdated_user_messages(messages, positions)
    assert len(messages) == 1
    assert messages[0]["content"] == "I see the file."


def test_keeps_string_message_for_untracked_file():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {"role": "user", "content": "```src/other.py\n1\tprint('other')\n```"},
        ],
    )
    positions: dict[str, FilePosition] = {
        "src/main.py": FilePosition(message_index=5, action="read"),
    }
    remove_outdated_user_messages(messages, positions)
    assert len(messages) == 1


def test_keeps_non_file_string_content():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {"role": "user", "content": "Please read src/main.py"},
        ],
    )
    positions: dict[str, FilePosition] = {
        "src/main.py": FilePosition(message_index=5, action="read"),
    }
    remove_outdated_user_messages(messages, positions)
    assert len(messages) == 1
    assert messages[0]["content"] == "Please read src/main.py"


def test_keeps_non_user_messages():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {"role": "assistant", "content": "```src/main.py\n1\tprint('hello')\n```"},
        ],
    )
    positions: dict[str, FilePosition] = {
        "src/main.py": FilePosition(message_index=5, action="read"),
    }
    remove_outdated_user_messages(messages, positions)
    assert len(messages) == 1


def test_keeps_list_content_messages():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "```src/main.py\n1\tprint('hello')\n```",
                    }
                ],
            },
        ],
    )
    positions: dict[str, FilePosition] = {
        "src/main.py": FilePosition(message_index=5, action="read"),
    }
    remove_outdated_user_messages(messages, positions)
    # List content is handled by remove_tool_pairs, not this function
    assert len(messages) == 1


def test_removes_multiple_outdated_string_messages():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {"role": "user", "content": "```src/main.py\n1\tversion1\n```"},
            {"role": "assistant", "content": "ok"},
            {"role": "user", "content": "```src/utils.py\n1\thelper\n```"},
            {"role": "assistant", "content": "ok"},
            {"role": "user", "content": "```src/other.py\n1\tkeep this\n```"},
        ],
    )
    positions: dict[str, FilePosition] = {
        "src/main.py": FilePosition(message_index=10, action="read"),
        "src/utils.py": FilePosition(message_index=10, action="edit"),
    }
    remove_outdated_user_messages(messages, positions)
    # main.py and utils.py messages removed, other.py and assistant messages kept
    assert len(messages) == 3
    assert messages[0]["content"] == "ok"
    assert messages[1]["content"] == "ok"
    assert messages[2]["content"] == "```src/other.py\n1\tkeep this\n```"
