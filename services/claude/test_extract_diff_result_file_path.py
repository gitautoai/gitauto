# pyright: reportArgumentType=false
from typing import cast

from anthropic.types import ToolResultBlockParam

from services.claude.extract_diff_result_file_path import extract_diff_result_file_path


def test_successful_diff():
    item = cast(
        ToolResultBlockParam,
        {
            "type": "tool_result",
            "tool_use_id": "toolu_1",
            "content": "diff applied to the file: src/main.py successfully by apply_diff_to_file",
        },
    )
    filepath, action = extract_diff_result_file_path(item)
    assert filepath == "src/main.py"
    assert action == "diff_success"


def test_failed_diff():
    item = cast(
        ToolResultBlockParam,
        {
            "type": "tool_result",
            "tool_use_id": "toolu_2",
            "content": "diff partially applied to the file: src/utils.py. But, some changes were rejected",
        },
    )
    filepath, action = extract_diff_result_file_path(item)
    assert filepath == "src/utils.py"
    assert action == "diff_failure"


def test_no_diff_markers():
    item = cast(
        ToolResultBlockParam,
        {
            "type": "tool_result",
            "tool_use_id": "toolu_3",
            "content": "Updated src/main.py.",
        },
    )
    filepath, action = extract_diff_result_file_path(item)
    assert filepath == ""
    assert action == ""


def test_non_string_content():
    item = cast(
        ToolResultBlockParam,
        {
            "type": "tool_result",
            "tool_use_id": "toolu_4",
            "content": [{"type": "text", "text": "hello"}],
        },
    )
    filepath, action = extract_diff_result_file_path(item)
    assert filepath == ""
    assert action == ""


def test_failure_checked_before_success():
    """When content has both markers, failure is checked first (DIFF_MARKERS order)."""
    item = cast(
        ToolResultBlockParam,
        {
            "type": "tool_result",
            "tool_use_id": "toolu_5",
            "content": (
                "diff partially applied to the file: a.py. But, some changes were rejected. "
                "diff applied to the file: b.py successfully by apply_diff_to_file"
            ),
        },
    )
    filepath, action = extract_diff_result_file_path(item)
    assert filepath == "a.py"
    assert action == "diff_failure"
