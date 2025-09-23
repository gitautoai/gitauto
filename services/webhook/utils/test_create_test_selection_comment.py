from unittest import TestCase
from unittest.mock import patch

import pytest
from config import PRODUCT_NAME
from constants.messages import SETTINGS_LINKS
from services.webhook.utils.create_test_selection_comment import (
    FileChecklistItem, create_test_selection_comment)
from utils.text.comment_identifiers import TEST_SELECTION_COMMENT_IDENTIFIER


@pytest.fixture
def mock_reset_command():
    with patch(
        "services.webhook.utils.create_test_selection_comment.create_reset_command_message"
    ) as mock:
        mock.return_value = "MOCK_RESET_COMMAND"
        yield mock


def test_create_test_selection_comment_empty_checklist(mock_reset_command):
    """Test creating a comment with an empty checklist."""
    branch_name = "test-branch"
    result = create_test_selection_comment([], branch_name)

    # Verify the reset command was called with the correct branch name
    mock_reset_command.assert_called_once_with(branch_name)

    # Check that the comment has the expected structure
    expected_lines = [
        TEST_SELECTION_COMMENT_IDENTIFIER,
        "",
        "Select files to manage tests for (create, update, or remove):",
        "",
        "",
        "---",
        "",
        "- [ ] Yes, manage tests",
        "",
        f"Click the checkbox and {PRODUCT_NAME} will add/update/remove tests for the selected files to this PR.",
        "MOCK_RESET_COMMAND",
        "",
        SETTINGS_LINKS,
    ]
    expected_comment = "\n".join(expected_lines)
    assert result == expected_comment


def test_create_test_selection_comment_with_items(mock_reset_command):
    """Test creating a comment with checklist items."""
    branch_name = "feature-branch"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/file1.py",
            "checked": True,
            "coverage_info": " (Coverage: 75%)",
            "status": "modified",
        },
        {
            "path": "src/file2.py",
            "checked": False,
            "coverage_info": " (Coverage: 0%)",
            "status": "added",
        },
    ]

    result = create_test_selection_comment(checklist, branch_name)

    # Verify the reset command was called with the correct branch name
    mock_reset_command.assert_called_once_with(branch_name)

    # Check that the comment has the expected structure with checklist items
    expected_lines = [
        TEST_SELECTION_COMMENT_IDENTIFIER,
        "",
        "Select files to manage tests for (create, update, or remove):",
        "",
        "- [x] modified `src/file1.py` (Coverage: 75%)",
        "- [ ] added `src/file2.py` (Coverage: 0%)",
        "",
        "---",
        "",
        "- [ ] Yes, manage tests",
        "",
        f"Click the checkbox and {PRODUCT_NAME} will add/update/remove tests for the selected files to this PR.",
        "MOCK_RESET_COMMAND",
        "",
        SETTINGS_LINKS,
    ]
    expected_comment = "\n".join(expected_lines)
    assert result == expected_comment


def test_create_test_selection_comment_with_all_status_types():
    """Test creating a comment with all possible status types."""
    branch_name = "main"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/added.py",
            "checked": True,
            "coverage_info": "",
            "status": "added",
        },
        {
            "path": "src/modified.py",
            "checked": True,
            "coverage_info": " (Coverage: 50%)",
            "status": "modified",
        },
        {
            "path": "src/removed.py",
            "checked": False,
            "coverage_info": "",
            "status": "removed",
        },
    ]

    result = create_test_selection_comment(checklist, branch_name)

    # Verify the result contains all status types
    assert "- [x] added `src/added.py`" in result
    assert "- [x] modified `src/modified.py` (Coverage: 50%)" in result
    assert "- [ ] removed `src/removed.py`" in result


def test_create_test_selection_comment_integration():
    """Test the full integration of the comment creation with actual dependencies."""
    branch_name = "integration-branch"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/example.py",
            "checked": True,
            "coverage_info": " (Coverage: 30%)",
            "status": "modified",
        }
    ]

    result = create_test_selection_comment(checklist, branch_name)

    # Verify the comment contains all required components
    assert TEST_SELECTION_COMMENT_IDENTIFIER in result
    assert "Select files to manage tests for (create, update, or remove):" in result
    assert "- [x] modified `src/example.py` (Coverage: 30%)" in result
    assert "- [ ] Yes, manage tests" in result
    assert PRODUCT_NAME in result
    assert SETTINGS_LINKS in result
    assert branch_name in result  # Branch name should be in the reset command


def test_create_test_selection_comment_with_special_characters():
    """Test creating a comment with paths containing special characters."""
    branch_name = "feature/special-chars"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/file-with-dashes.py",
            "checked": True,
            "coverage_info": "",
            "status": "modified",
        },
        {
            "path": "src/file_with_underscores.py",
            "checked": False,
            "coverage_info": " (Coverage: 0%)",
            "status": "added",
        },
    ]

    result = create_test_selection_comment(checklist, branch_name)

    assert "- [x] modified `src/file-with-dashes.py`" in result
    assert "- [ ] added `src/file_with_underscores.py` (Coverage: 0%)" in result


def test_create_test_selection_comment_with_empty_coverage_info():
    """Test creating a comment with empty coverage info."""
    branch_name = "test-branch"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/file1.py",
            "checked": True,
            "coverage_info": "",
            "status": "added",
        },
        {
            "path": "src/file2.py",
            "checked": False,
            "coverage_info": "",
            "status": "modified",
        },
    ]

    result = create_test_selection_comment(checklist, branch_name)

    # Verify items with empty coverage info are handled correctly
    assert "- [x] added `src/file1.py`" in result
    assert "- [ ] modified `src/file2.py`" in result
    # Ensure no extra spaces are added when coverage_info is empty
    assert "`src/file1.py` " not in result  # No trailing space after backtick
    assert "`src/file2.py` " not in result  # No trailing space after backtick


def test_create_test_selection_comment_with_long_file_paths():
    """Test creating a comment with very long file paths."""
    branch_name = "feature/long-paths"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/very/deep/nested/directory/structure/with/many/levels/file.py",
            "checked": True,
            "coverage_info": " (Coverage: 85%)",
            "status": "modified",
        },
    ]

    result = create_test_selection_comment(checklist, branch_name)

    assert (
        "- [x] modified `src/very/deep/nested/directory/structure/with/many/levels/file.py` (Coverage: 85%)"
        in result
    )


def test_create_test_selection_comment_with_mixed_checked_states():
    """Test creating a comment with a mix of checked and unchecked items."""
    branch_name = "mixed-states"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/checked1.py",
            "checked": True,
            "coverage_info": " (Coverage: 90%)",
            "status": "modified",
        },
        {
            "path": "src/unchecked1.py",
            "checked": False,
            "coverage_info": " (Coverage: 10%)",
            "status": "added",
        },
        {
            "path": "src/checked2.py",
            "checked": True,
            "coverage_info": "",
            "status": "removed",
        },
        {
            "path": "src/unchecked2.py",
            "checked": False,
            "coverage_info": " (Coverage: 0%)",
            "status": "modified",
        },
    ]

    result = create_test_selection_comment(checklist, branch_name)

    # Verify all items are present with correct checkbox states
    assert "- [x] modified `src/checked1.py` (Coverage: 90%)" in result
    assert "- [ ] added `src/unchecked1.py` (Coverage: 10%)" in result
    assert "- [x] removed `src/checked2.py`" in result
    assert "- [ ] modified `src/unchecked2.py` (Coverage: 0%)" in result


def test_create_test_selection_comment_structure_consistency():
    """Test that the comment structure is consistent regardless of checklist content."""
    branch_name = "consistency-test"

    # Basic structure verification for empty checklist
    result = create_test_selection_comment([], branch_name)

    # Verify consistent structure elements are always present
    assert TEST_SELECTION_COMMENT_IDENTIFIER in result
    assert "Select files to manage tests for (create, update, or remove):" in result
    assert "---" in result
    assert "- [ ] Yes, manage tests" in result
    assert PRODUCT_NAME in result
    assert SETTINGS_LINKS in result

    # Verify the structure is consistent
    lines = result.split("\n")
    assert lines[0] == TEST_SELECTION_COMMENT_IDENTIFIER
    assert lines[1] == ""
    assert lines[2] == "Select files to manage tests for (create, update, or remove):"
    assert lines[3] == ""


def test_create_test_selection_comment_structure_consistency_complete():
    """Test that the comment structure is consistent regardless of checklist content."""
    branch_name = "consistency-test"

    # Test with different checklist sizes
    for size in [0, 1, 3, 5]:
        checklist: list[FileChecklistItem] = []
        for i in range(size):
            checklist.append(
                {
                    "path": f"src/file{i}.py",
                    "checked": i % 2 == 0,  # Alternate checked state
                    "coverage_info": f" (Coverage: {i * 20}%)" if i > 0 else "",
                    "status": "modified",
                }
            )

        result = create_test_selection_comment(checklist, branch_name)

        # Verify consistent structure elements are always present
        assert TEST_SELECTION_COMMENT_IDENTIFIER in result
        assert "Select files to manage tests for (create, update, or remove):" in result
        assert "---" in result
        assert "- [ ] Yes, manage tests" in result
        assert PRODUCT_NAME in result
        assert SETTINGS_LINKS in result

        # Verify the number of file items matches the checklist size
        file_lines = [line for line in result.split("\n") if line.startswith("- [")]
        # Subtract 1 for the "Yes, manage tests" line
        assert len(file_lines) - 1 == size


def test_create_test_selection_comment_with_all_coverage_variations():
    """Test creating a comment with various coverage info formats."""
    branch_name = "coverage-variations"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/no_coverage.py",
            "checked": True,
            "coverage_info": "",
            "status": "added",
        },
        {
            "path": "src/zero_coverage.py",
            "checked": False,
            "coverage_info": " (Coverage: 0%)",
            "status": "modified",
        },
        {
            "path": "src/full_coverage.py",
            "checked": True,
            "coverage_info": " (Coverage: 100%)",
            "status": "modified",
        },
        {
            "path": "src/partial_coverage.py",
            "checked": False,
            "coverage_info": " (Coverage: 42%)",
            "status": "added",
        },
    ]

    result = create_test_selection_comment(checklist, branch_name)

    # Verify all coverage variations are handled correctly
    assert "- [x] added `src/no_coverage.py`" in result
    assert "- [ ] modified `src/zero_coverage.py` (Coverage: 0%)" in result
    assert "- [x] modified `src/full_coverage.py` (Coverage: 100%)" in result
    assert "- [ ] added `src/partial_coverage.py` (Coverage: 42%)" in result


def test_create_test_selection_comment_with_unicode_paths():
    """Test creating a comment with paths containing unicode characters."""
    branch_name = "unicode-test"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/测试文件.py",
            "checked": True,
            "coverage_info": " (Coverage: 50%)",
            "status": "added",
        },
        {
            "path": "src/файл.py",
            "checked": False,
            "coverage_info": "",
            "status": "modified",
        },
    ]

    result = create_test_selection_comment(checklist, branch_name)

    # Verify unicode paths are handled correctly
    assert "- [x] added `src/测试文件.py` (Coverage: 50%)" in result
    assert "- [ ] modified `src/файл.py`" in result


def test_create_test_selection_comment_with_removed_status():
    """Test creating a comment specifically with removed status files."""
    branch_name = "removed-files"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/deleted_file.py",
            "checked": True,
            "coverage_info": "",
            "status": "removed",
        },
        {
            "path": "src/another_deleted.py",
            "checked": False,
            "coverage_info": " (Coverage: 80%)",
            "status": "removed",
        },
    ]

    result = create_test_selection_comment(checklist, branch_name)

    # Verify removed files are handled correctly
    assert "- [x] removed `src/deleted_file.py`" in result
    assert "- [ ] removed `src/another_deleted.py` (Coverage: 80%)" in result


def test_create_test_selection_comment_with_single_item():
    """Test creating a comment with exactly one checklist item."""
    branch_name = "single-item"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/single.py",
            "checked": True,
            "coverage_info": " (Coverage: 95%)",
            "status": "modified",
        }
    ]

    result = create_test_selection_comment(checklist, branch_name)

    # Verify single item is handled correctly
    assert "- [x] modified `src/single.py` (Coverage: 95%)" in result
    assert TEST_SELECTION_COMMENT_IDENTIFIER in result
    assert "- [ ] Yes, manage tests" in result


def test_create_test_selection_comment_line_endings():
    """Test that the comment uses consistent line endings."""
    branch_name = "line-endings"
    checklist: list[FileChecklistItem] = []

    result = create_test_selection_comment(checklist, branch_name)

    # Verify consistent line endings (should use \n)
    assert "\r\n" not in result  # No Windows line endings
    assert result.count("\n") > 0  # Has Unix line endings


def test_create_test_selection_comment_with_edge_case_coverage():
    """Test creating a comment with edge case coverage values."""
    branch_name = "edge-cases"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/edge1.py",
            "checked": True,
            "coverage_info": " (Coverage: 1%)",
            "status": "modified",
        },
        {
            "path": "src/edge2.py",
            "checked": False,
            "coverage_info": " (Coverage: 99%)",
            "status": "added",
        },
    ]

    result = create_test_selection_comment(checklist, branch_name)

    # Verify edge case coverage values are handled correctly
    assert "- [x] modified `src/edge1.py` (Coverage: 1%)" in result
    assert "- [ ] added `src/edge2.py` (Coverage: 99%)" in result


def test_create_test_selection_comment_with_large_checklist():
    """Test creating a comment with a large number of checklist items."""
    branch_name = "large-checklist"
    checklist: list[FileChecklistItem] = []

    # Create a large checklist with 20 items
    for i in range(20):
        checklist.append(
            {
                "path": f"src/file_{i:02d}.py",
                "checked": i % 3 == 0,  # Every third item checked
                "coverage_info": (
                    f" (Coverage: {i * 5}%)" if i < 20 else " (Coverage: 100%)"
                ),
                "status": "modified" if i % 2 == 0 else "added",
            }
        )

    result = create_test_selection_comment(checklist, branch_name)

    # Verify all items are present
    for i in range(20):
        checkbox = "[x]" if i % 3 == 0 else "[ ]"
        status = "modified" if i % 2 == 0 else "added"
        coverage = f" (Coverage: {i * 5}%)" if i < 20 else " (Coverage: 100%)"
        expected_line = f"- {checkbox} {status} `src/file_{i:02d}.py`{coverage}"
        assert expected_line in result

    # Verify structure is still intact
    assert TEST_SELECTION_COMMENT_IDENTIFIER in result
    assert "- [ ] Yes, manage tests" in result
    assert SETTINGS_LINKS in result


def test_file_checklist_item_type_validation():
    """Test that FileChecklistItem TypedDict structure is correctly defined."""
    # This test validates the TypedDict structure
    valid_item: FileChecklistItem = {
        "path": "src/test.py",
        "checked": True,
        "coverage_info": " (Coverage: 50%)",
        "status": "modified",
    }

    # Verify all required keys are present
    assert "path" in valid_item
    assert "checked" in valid_item
    assert "coverage_info" in valid_item
    assert "status" in valid_item

    # Verify types
    assert isinstance(valid_item["path"], str)
    assert isinstance(valid_item["checked"], bool)
    assert isinstance(valid_item["coverage_info"], str)
    assert valid_item["status"] in ["added", "modified", "removed"]


def test_create_test_selection_comment_with_none_branch_name():
    """Test creating a comment with None branch name (edge case)."""
    # This tests robustness when branch_name might be None
    checklist: list[FileChecklistItem] = []

    # This should not crash even with None branch name
    with patch(
        "services.webhook.utils.create_test_selection_comment.create_reset_command_message"
    ) as mock_reset:
        mock_reset.return_value = "MOCK_RESET_COMMAND"
        result = create_test_selection_comment(checklist, None)  # type: ignore

        # Verify the reset command was called with None
        mock_reset.assert_called_once_with(None)
        assert "MOCK_RESET_COMMAND" in result


def test_create_test_selection_comment_with_empty_string_branch_name():
    """Test creating a comment with empty string branch name."""
    checklist: list[FileChecklistItem] = []

    with patch(
        "services.webhook.utils.create_test_selection_comment.create_reset_command_message"
    ) as mock_reset:
        mock_reset.return_value = "MOCK_RESET_COMMAND"
        result = create_test_selection_comment(checklist, "")

        # Verify the reset command was called with empty string
        mock_reset.assert_called_once_with("")
        assert "MOCK_RESET_COMMAND" in result


def test_create_test_selection_comment_with_whitespace_in_coverage():
    """Test creating a comment with various whitespace patterns in coverage info."""
    branch_name = "whitespace-test"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/file1.py",
            "checked": True,
            "coverage_info": "   (Coverage: 50%)   ",  # Leading and trailing spaces
            "status": "modified",
        },
        {
            "path": "src/file2.py",
            "checked": False,
            "coverage_info": "\t(Coverage: 75%)\t",  # Tabs
            "status": "added",
        },
        {
            "path": "src/file3.py",
            "checked": True,
            "coverage_info": "\n(Coverage: 25%)\n",  # Newlines
            "status": "modified",
        },
    ]

    result = create_test_selection_comment(checklist, branch_name)

    # Verify whitespace is preserved as-is (no trimming in the function)
    assert "- [x] modified `src/file1.py`   (Coverage: 50%)   " in result
    assert "- [ ] added `src/file2.py`\t(Coverage: 75%)\t" in result
    assert "- [x] modified `src/file3.py`\n(Coverage: 25%)\n" in result


def test_create_test_selection_comment_with_very_long_branch_name():
    """Test creating a comment with a very long branch name."""
    # Create a very long branch name (common in some workflows)
    long_branch_name = "feature/very-long-branch-name-that-might-be-generated-by-automated-systems-" + "x" * 100
    checklist: list[FileChecklistItem] = []

    with patch(
        "services.webhook.utils.create_test_selection_comment.create_reset_command_message"
    ) as mock_reset:
        mock_reset.return_value = "MOCK_RESET_COMMAND"
        result = create_test_selection_comment(checklist, long_branch_name)

        # Verify the reset command was called with the long branch name
        mock_reset.assert_called_once_with(long_branch_name)
        assert "MOCK_RESET_COMMAND" in result


def test_create_test_selection_comment_with_special_branch_characters():
    """Test creating a comment with special characters in branch name."""
    special_branch_names = [
        "feature/issue-#123",
        "hotfix/bug@urgent",
        "release/v1.2.3-beta",
        "feature/user&admin",
        "bugfix/fix%encoding",
    ]

    for branch_name in special_branch_names:
        checklist: list[FileChecklistItem] = []

        with patch(
            "services.webhook.utils.create_test_selection_comment.create_reset_command_message"
        ) as mock_reset:
            mock_reset.return_value = f"MOCK_RESET_COMMAND_{branch_name}"
            result = create_test_selection_comment(checklist, branch_name)

            # Verify the reset command was called with the special branch name
            mock_reset.assert_called_once_with(branch_name)
            assert f"MOCK_RESET_COMMAND_{branch_name}" in result


def test_create_test_selection_comment_return_type():
    """Test that the function returns a string."""
    branch_name = "test-branch"
    checklist: list[FileChecklistItem] = []

    result = create_test_selection_comment(checklist, branch_name)

    # Verify return type
    assert isinstance(result, str)
    assert len(result) > 0


def test_create_test_selection_comment_immutability():
    """Test that the function doesn't modify the input checklist."""
    original_checklist = [
        {
            "path": "src/main.py",
            "checked": True,
            "coverage_info": " (85% coverage)",
            "status": "modified"
        }
    ]
    checklist_copy = original_checklist.copy()

    create_test_selection_comment(checklist_copy, "feature/test-branch")

    # Verify the original checklist wasn't modified
    assert checklist_copy == original_checklist


def test_create_test_selection_comment_performance_with_large_data():
    """Test performance with a very large checklist (stress test)."""
    branch_name = "performance-test"

    # Create a large checklist (100 items)
    checklist: list[FileChecklistItem] = []
    for i in range(100):
        checklist.append({
            "path": f"src/module_{i//10}/submodule_{i%10}/file_{i:03d}.py",
            "checked": i % 3 == 0,
            "coverage_info": f" ({50 + i % 50}% coverage)",
            "status": "modified" if i % 2 == 0 else "added"
        })

    branch_name = "feature/performance-test"

    # Measure execution time
    import time
    start_time = time.time()
    result = create_test_selection_comment(checklist, branch_name)
    end_time = time.time()

    # Should complete within reasonable time (less than 1 second for 100 items)
    assert end_time - start_time < 1.0
    assert isinstance(result, str)
    assert len(result) > 0
