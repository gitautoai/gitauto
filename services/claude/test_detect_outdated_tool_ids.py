# pyright: reportIndexIssue=false, reportArgumentType=false
from typing import cast

from anthropic.types import MessageParam

from services.claude.detect_outdated_tool_ids import detect_outdated_tool_ids


def test_empty_messages():
    ids, positions = detect_outdated_tool_ids([], file_paths_to_remove=set())
    assert ids == set()
    assert len(positions) == 0


def test_no_tool_calls():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {"role": "assistant", "content": "Hello"},
            {"role": "user", "content": [{"type": "text", "text": "Hi"}]},
        ],
    )
    ids, positions = detect_outdated_tool_ids(messages, file_paths_to_remove=set())
    assert ids == set()
    assert len(positions) == 0


def test_single_file_read_not_outdated():
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
                        "input": {"file_path": "src/main.py"},
                    }
                ],
            },
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
    ids, positions = detect_outdated_tool_ids(messages, file_paths_to_remove=set())
    assert ids == set()
    assert positions == {"src/main.py": {"message_index": 0, "action": "read"}}


def test_two_reads_same_file_first_outdated():
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
                        "input": {"file_path": "src/main.py"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "```src/main.py\n1\tprint('v1')\n```",
                    }
                ],
            },
            {"role": "assistant", "content": "I see version 1."},
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_2",
                        "name": "get_local_file_content",
                        "input": {"file_path": "src/main.py"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_2",
                        "content": "```src/main.py\n1\tprint('v2')\n```",
                    }
                ],
            },
        ],
    )
    ids, positions = detect_outdated_tool_ids(messages, file_paths_to_remove=set())
    assert ids == {"toolu_1"}
    assert positions == {"src/main.py": {"message_index": 3, "action": "read"}}


def test_read_then_edit_read_is_outdated():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_read",
                        "name": "get_local_file_content",
                        "input": {"file_path": "src/main.py"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_read",
                        "content": "file content here",
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_edit",
                        "name": "search_and_replace",
                        "input": {
                            "file_path": "src/main.py",
                            "old_string": "old",
                            "new_string": "new",
                        },
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_edit",
                        "content": "Updated src/main.py.",
                    }
                ],
            },
        ],
    )
    ids, positions = detect_outdated_tool_ids(messages, file_paths_to_remove=set())
    assert ids == {"toolu_read"}
    assert positions == {"src/main.py": {"message_index": 2, "action": "edit"}}


def test_different_files_none_outdated():
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
                        "input": {"file_path": "file1.py"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "content1",
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
                        "input": {"file_path": "file2.py"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_2",
                        "content": "content2",
                    }
                ],
            },
        ],
    )
    ids, positions = detect_outdated_tool_ids(messages, file_paths_to_remove=set())
    assert ids == set()
    assert positions == {
        "file1.py": {"message_index": 0, "action": "read"},
        "file2.py": {"message_index": 2, "action": "read"},
    }


def test_failed_diff_tracked():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": (
                            "diff partially applied to the file: test.py"
                            ". But, some changes were rejected"
                        ),
                    }
                ],
            },
        ],
    )
    ids, positions = detect_outdated_tool_ids(messages, file_paths_to_remove=set())
    assert ids == set()
    assert positions == {"test.py": {"message_index": 0, "action": "diff_failure"}}


def test_successful_diff_tracked():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "diff applied to the file: test.py successfully by apply_diff_to_file",
                    }
                ],
            },
        ],
    )
    ids, positions = detect_outdated_tool_ids(messages, file_paths_to_remove=set())
    assert ids == set()
    assert positions == {"test.py": {"message_index": 0, "action": "diff_success"}}


def test_multiple_failed_diffs_earlier_outdated():
    """Two failed diffs for same file: earlier tool_result is outdated."""
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_edit1",
                        "name": "apply_diff_to_file",
                        "input": {"file_path": "test.py", "diff": "diff1"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_edit1",
                        "content": (
                            "diff partially applied to the file: test.py"
                            ". But, some changes were rejected"
                        ),
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_edit2",
                        "name": "apply_diff_to_file",
                        "input": {"file_path": "test.py", "diff": "diff2"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_edit2",
                        "content": (
                            "diff partially applied to the file: test.py"
                            ". But, some changes were rejected"
                        ),
                    }
                ],
            },
        ],
    )
    ids, positions = detect_outdated_tool_ids(messages, file_paths_to_remove=set())
    assert ids == {"toolu_edit1"}
    assert positions == {"test.py": {"message_index": 2, "action": "diff_failure"}}


def test_verify_results_all_but_last_outdated():
    """Multiple verify_task_is_complete results: all but the last are outdated."""
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_v1",
                        "name": "verify_task_is_complete",
                        "input": {},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_v1",
                        "content": "Task NOT complete. Fix errors.",
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_v2",
                        "name": "verify_task_is_complete",
                        "input": {},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_v2",
                        "content": "Task NOT complete. More errors.",
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_v3",
                        "name": "verify_task_is_complete",
                        "input": {},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_v3",
                        "content": "Task completed.",
                    }
                ],
            },
        ],
    )
    ids, positions = detect_outdated_tool_ids(messages, file_paths_to_remove=set())
    assert ids == {"toolu_v1", "toolu_v2"}
    assert len(positions) == 0


def test_single_verify_not_outdated():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_v1",
                        "name": "verify_task_is_complete",
                        "input": {},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_v1",
                        "content": "Task NOT complete. Fix errors.",
                    }
                ],
            },
        ],
    )
    ids, _ = detect_outdated_tool_ids(messages, file_paths_to_remove=set())
    assert ids == set()


def test_file_paths_to_remove_marks_all_outdated():
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
                        "input": {"file_path": "config.yml"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "```config.yml\nkey: value\n```",
                    }
                ],
            },
        ],
    )
    ids, positions = detect_outdated_tool_ids(
        messages, file_paths_to_remove={"config.yml"}
    )
    assert ids == {"toolu_1"}
    assert positions == {"config.yml": {"message_index": 2, "action": "remove"}}


def test_multiple_edits_same_file_all_but_last_outdated():
    """Six search_and_replace edits on same file: first 5 are outdated."""
    messages: list[MessageParam] = cast(list[MessageParam], [])
    for i in range(1, 7):
        messages.append(
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": f"toolu_{i}",
                        "name": "search_and_replace",
                        "input": {
                            "file_path": "app.ts",
                            "old_string": f"old_{i}",
                            "new_string": f"new_{i}",
                        },
                    }
                ],
            }
        )
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": f"toolu_{i}",
                        "content": f"Updated app.ts edit {i}.",
                    }
                ],
            }
        )

    ids, positions = detect_outdated_tool_ids(messages, file_paths_to_remove=set())
    assert ids == {"toolu_1", "toolu_2", "toolu_3", "toolu_4", "toolu_5"}
    assert positions == {"app.ts": {"message_index": 10, "action": "edit"}}


def test_cross_tool_edits_apply_diff_then_search_and_replace():
    """apply_diff_to_file followed by search_and_replace for same file."""
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_diff",
                        "name": "apply_diff_to_file",
                        "input": {"file_path": "test.py", "diff": "some diff"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_diff",
                        "content": "Applied.",
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_sr",
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
                        "tool_use_id": "toolu_sr",
                        "content": "Updated.",
                    }
                ],
            },
        ],
    )
    ids, positions = detect_outdated_tool_ids(messages, file_paths_to_remove=set())
    assert ids == {"toolu_diff"}
    assert positions == {"test.py": {"message_index": 2, "action": "edit"}}


def test_write_and_commit_file_tracked_as_edit():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_w1",
                        "name": "write_and_commit_file",
                        "input": {
                            "file_path": "test.py",
                            "file_content": "v1",
                        },
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_w1",
                        "content": "Written.",
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_w2",
                        "name": "write_and_commit_file",
                        "input": {
                            "file_path": "test.py",
                            "file_content": "v2",
                        },
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_w2",
                        "content": "Written.",
                    }
                ],
            },
        ],
    )
    ids, positions = detect_outdated_tool_ids(messages, file_paths_to_remove=set())
    assert ids == {"toolu_w1"}
    assert positions == {"test.py": {"message_index": 2, "action": "edit"}}


def test_successful_then_failed_diff():
    """Successful diff followed by failed diff for same file: successful is outdated."""
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_s",
                        "name": "apply_diff_to_file",
                        "input": {"file_path": "test.py", "diff": "diff1"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_s",
                        "content": "diff applied to the file: test.py successfully by apply_diff_to_file",
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_f",
                        "name": "apply_diff_to_file",
                        "input": {"file_path": "test.py", "diff": "diff2"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_f",
                        "content": (
                            "diff partially applied to the file: test.py"
                            ". But, some changes were rejected"
                        ),
                    }
                ],
            },
        ],
    )
    ids, positions = detect_outdated_tool_ids(messages, file_paths_to_remove=set())
    assert ids == {"toolu_s"}
    assert positions == {"test.py": {"message_index": 2, "action": "diff_failure"}}


def test_interleaved_files():
    """Alternating edits: file1 → file2 → file1 → file2. Earlier edits of each file are outdated."""
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "apply_diff_to_file",
                        "input": {"file_path": "file1.py", "diff": "1a"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "Applied.",
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_2",
                        "name": "apply_diff_to_file",
                        "input": {"file_path": "file2.py", "diff": "2a"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_2",
                        "content": "Applied.",
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_3",
                        "name": "apply_diff_to_file",
                        "input": {"file_path": "file1.py", "diff": "1b"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_3",
                        "content": "Applied.",
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_4",
                        "name": "apply_diff_to_file",
                        "input": {"file_path": "file2.py", "diff": "2b"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_4",
                        "content": "Applied.",
                    }
                ],
            },
        ],
    )
    ids, positions = detect_outdated_tool_ids(messages, file_paths_to_remove=set())
    assert ids == {"toolu_1", "toolu_2"}
    assert positions == {
        "file1.py": {"message_index": 4, "action": "edit"},
        "file2.py": {"message_index": 6, "action": "edit"},
    }


def test_complex_pattern_edit_fail_succeed_edit():
    """tool_use(edit) → failed_diff → successful_diff → tool_use(edit) for same file."""
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "apply_diff_to_file",
                        "input": {"file_path": "test.py", "diff": "diff1"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": (
                            "diff partially applied to the file: test.py"
                            ". But, some changes were rejected"
                        ),
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_2",
                        "name": "apply_diff_to_file",
                        "input": {"file_path": "test.py", "diff": "diff2"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_2",
                        "content": "diff applied to the file: test.py successfully by apply_diff_to_file",
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_3",
                        "name": "apply_diff_to_file",
                        "input": {"file_path": "test.py", "diff": "diff3"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_3",
                        "content": "Applied.",
                    }
                ],
            },
        ],
    )
    ids, positions = detect_outdated_tool_ids(messages, file_paths_to_remove=set())
    assert ids == {"toolu_1", "toolu_2"}
    assert positions == {"test.py": {"message_index": 4, "action": "edit"}}


def test_irrelevant_tools_preserved():
    """Non-edit tools (get_file, search) are not tracked or marked outdated."""
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_other",
                        "name": "get_file",
                        "input": {"file_path": "test.py"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_other",
                        "content": "File content here...",
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_edit",
                        "name": "apply_diff_to_file",
                        "input": {"file_path": "test.py", "diff": "some diff"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_edit",
                        "content": "Applied.",
                    }
                ],
            },
        ],
    )
    ids, positions = detect_outdated_tool_ids(messages, file_paths_to_remove=set())
    assert ids == set()
    assert positions == {"test.py": {"message_index": 2, "action": "edit"}}
