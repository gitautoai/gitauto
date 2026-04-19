# pyright: reportIndexIssue=false
from services.claude.file_tracking import (
    FILE_EDIT_TOOLS,
    FileAction,
    FilePosition,
    FileReadEntry,
)


def test_file_edit_tools_exact_list():
    # Verify the exact set of edit tools — any change requires updating detect_outdated_tool_ids
    assert FILE_EDIT_TOOLS == [
        "apply_diff_to_file",
        "delete_file",
        "move_file",
        "search_and_replace",
        "write_and_commit_file",
    ]


def test_file_position_typed_dict():
    # FilePosition must accept message_index (int) and action (FileAction)
    pos: FilePosition = {"message_index": 5, "action": "edit"}
    assert pos["message_index"] == 5
    assert pos["action"] == "edit"


def test_file_read_entry_named_tuple():
    # FileReadEntry fields accessible by name and index
    entry = FileReadEntry(message_index=3, tool_id="toolu_abc")
    assert entry.message_index == 3
    assert entry.tool_id == "toolu_abc"
    assert entry[0] == 3
    assert entry[1] == "toolu_abc"


def test_file_action_values():
    # All valid FileAction literals — detect_outdated_tool_ids depends on these
    valid: list[FileAction] = ["read", "edit", "diff_success", "diff_failure", "remove"]
    assert len(valid) == 5
