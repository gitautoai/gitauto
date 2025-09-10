from unittest.mock import patch
import pytest
from config import PRODUCT_NAME
from constants.messages import SETTINGS_LINKS
from utils.text.comment_identifiers import TEST_SELECTION_COMMENT_IDENTIFIER
from services.webhook.utils.create_test_selection_comment import (
    create_test_selection_comment,
    FileChecklistItem,
)


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
    # This test ensures the TypedDict is properly structured
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


def test_create_test_selection_comment_with_empty_path():
    """Test creating a comment with edge case values that might cause issues."""
    branch_name = "edge-case-branch"
    checklist: list[FileChecklistItem] = [
        {
            "path": "",  # Empty path
            "checked": False,
            "coverage_info": "",
            "status": "added",
        },
    ]
    
    result = create_test_selection_comment(checklist, branch_name)
    
    # Should handle empty path gracefully
    assert "- [ ] added ``" in result
    assert TEST_SELECTION_COMMENT_IDENTIFIER in result


def test_create_test_selection_comment_with_whitespace_paths():
    """Test creating a comment with paths containing whitespace."""
    branch_name = "whitespace-test"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/file with spaces.py",
            "checked": True,
            "coverage_info": " (Coverage: 75%)",
            "status": "modified",
        },
        {
            "path": "src/file\twith\ttabs.py",
            "checked": False,
            "coverage_info": "",
            "status": "added",
        },
    ]
    
    result = create_test_selection_comment(checklist, branch_name)
    
    # Verify whitespace in paths is preserved
    assert "- [x] modified `src/file with spaces.py` (Coverage: 75%)" in result
    assert "- [ ] added `src/file\twith\ttabs.py`" in result


def test_create_test_selection_comment_with_extreme_branch_names():
    """Test creating a comment with various branch name formats."""
    test_cases = [
        "feature/very-long-branch-name-with-many-hyphens-and-descriptive-text",
        "hotfix/123-urgent-fix",
        "release/v1.2.3",
        "bugfix/issue-#456",
        "main",
        "develop",
    ]
    
    for branch_name in test_cases:
        result = create_test_selection_comment([], branch_name)
        
        # Verify branch name is included in the reset command
        assert branch_name in result
        assert TEST_SELECTION_COMMENT_IDENTIFIER in result


def test_create_test_selection_comment_with_special_coverage_formats():
    """Test creating a comment with various coverage info formats."""
    branch_name = "coverage-formats"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/file1.py",
            "checked": True,
            "coverage_info": " (No coverage data)",
            "status": "added",
        },
        {
            "path": "src/file2.py",
            "checked": False,
            "coverage_info": " (Coverage: N/A)",
            "status": "modified",
        },
        {
            "path": "src/file3.py",
            "checked": True,
            "coverage_info": " (Test file)",
            "status": "added",
        },
    ]
    
    result = create_test_selection_comment(checklist, branch_name)
    
    # Verify all coverage formats are handled correctly
    assert "- [x] added `src/file1.py` (No coverage data)" in result
    assert "- [ ] modified `src/file2.py` (Coverage: N/A)" in result
    assert "- [x] added `src/file3.py` (Test file)" in result


def test_create_test_selection_comment_output_format_consistency():
    """Test that the output format is consistent and well-formed."""
    branch_name = "format-test"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/example.py",
            "checked": True,
            "coverage_info": " (Coverage: 80%)",
            "status": "modified",
        }
    ]
    
    result = create_test_selection_comment(checklist, branch_name)
    lines = result.split("\n")
    
    # Verify the structure is well-formed
    assert lines[0] == TEST_SELECTION_COMMENT_IDENTIFIER
    assert lines[1] == ""  # Empty line after identifier
    assert lines[2] == "Select files to manage tests for (create, update, or remove):"
    assert lines[3] == ""  # Empty line after instruction
    assert lines[4] == "- [x] modified `src/example.py` (Coverage: 80%)"
    assert lines[5] == ""  # Empty line before separator
    assert lines[6] == "---"
    assert lines[7] == ""  # Empty line after separator
    assert lines[8] == "- [ ] Yes, manage tests"
    assert lines[9] == ""  # Empty line after checkbox
