# pyright: reportArgumentType=false
from typing import cast

from anthropic.types import ToolUseBlockParam

from services.claude.file_tracking import FilePosition, FileReadEntry
from services.claude.track_tool_use import track_tool_use


def test_tracks_file_read():
    item = cast(
        ToolUseBlockParam,
        {
            "type": "tool_use",
            "id": "toolu_read1",
            "name": "get_local_file_content",
            "input": {"file_path": "src/main.py"},
        },
    )
    positions: dict[str, FilePosition] = {}
    id_to_file: dict[str, str] = {}
    id_to_msg_index: dict[str, int] = {}
    file_read_ids: dict[str, list[FileReadEntry]] = {}

    track_tool_use(
        0, item, set(), positions, id_to_file, id_to_msg_index, file_read_ids
    )

    assert positions["src/main.py"] == FilePosition(message_index=0, action="read")
    assert id_to_file["toolu_read1"] == "src/main.py"
    assert id_to_msg_index["toolu_read1"] == 0
    assert len(file_read_ids["src/main.py"]) == 1
    assert file_read_ids["src/main.py"][0] == FileReadEntry(
        message_index=0, tool_id="toolu_read1"
    )


def test_tracks_file_edit():
    item = cast(
        ToolUseBlockParam,
        {
            "type": "tool_use",
            "id": "toolu_edit1",
            "name": "search_and_replace",
            "input": {"file_path": "src/main.py", "old_string": "a", "new_string": "b"},
        },
    )
    positions: dict[str, FilePosition] = {}
    id_to_file: dict[str, str] = {}
    id_to_msg_index: dict[str, int] = {}
    file_read_ids: dict[str, list[FileReadEntry]] = {}

    track_tool_use(
        5, item, set(), positions, id_to_file, id_to_msg_index, file_read_ids
    )

    assert positions["src/main.py"] == FilePosition(message_index=5, action="edit")
    assert id_to_file["toolu_edit1"] == "src/main.py"
    assert len(file_read_ids) == 0


def test_skips_forced_outdated_file():
    item = cast(
        ToolUseBlockParam,
        {
            "type": "tool_use",
            "id": "toolu_r1",
            "name": "get_local_file_content",
            "input": {"file_path": "removed.py"},
        },
    )
    positions: dict[str, FilePosition] = {}
    id_to_file: dict[str, str] = {}
    id_to_msg_index: dict[str, int] = {}
    file_read_ids: dict[str, list[FileReadEntry]] = {}

    track_tool_use(
        3, item, {"removed.py"}, positions, id_to_file, id_to_msg_index, file_read_ids
    )

    # Position NOT updated for forced-outdated files
    assert len(positions) == 0
    # But id_to_file and file_read_ids ARE still tracked
    assert id_to_file["toolu_r1"] == "removed.py"
    assert len(file_read_ids["removed.py"]) == 1


def test_ignores_irrelevant_tool():
    item = cast(
        ToolUseBlockParam,
        {
            "type": "tool_use",
            "id": "toolu_x",
            "name": "verify_task_is_complete",
            "input": {"result": "done"},
        },
    )
    positions: dict[str, FilePosition] = {}
    id_to_file: dict[str, str] = {}
    id_to_msg_index: dict[str, int] = {}
    file_read_ids: dict[str, list[FileReadEntry]] = {}

    track_tool_use(
        0, item, set(), positions, id_to_file, id_to_msg_index, file_read_ids
    )

    assert len(positions) == 0
    assert len(id_to_file) == 0
    assert len(file_read_ids) == 0


def test_multiple_reads_same_file():
    positions: dict[str, FilePosition] = {}
    id_to_file: dict[str, str] = {}
    id_to_msg_index: dict[str, int] = {}
    file_read_ids: dict[str, list[FileReadEntry]] = {}

    for idx, tool_id in enumerate(["toolu_a", "toolu_b"]):
        item = cast(
            ToolUseBlockParam,
            {
                "type": "tool_use",
                "id": tool_id,
                "name": "get_local_file_content",
                "input": {"file_path": "f.py"},
            },
        )
        track_tool_use(
            idx, item, set(), positions, id_to_file, id_to_msg_index, file_read_ids
        )

    # Latest position wins
    assert positions["f.py"] == FilePosition(message_index=1, action="read")
    # Both reads tracked
    assert len(file_read_ids["f.py"]) == 2
    assert file_read_ids["f.py"][0].tool_id == "toolu_a"
    assert file_read_ids["f.py"][1].tool_id == "toolu_b"
