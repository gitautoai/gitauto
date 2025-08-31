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

def test_create_test_selection_comment_mixed_coverage_info(mock_reset_command):
    """Test creating a comment with mixed coverage info scenarios."""
    branch_name = "mixed-coverage"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/with_coverage.py",
            "checked": True,
            "coverage_info": " (Coverage: 85%)",
            "status": "modified",
        },
        {
            "path": "src/without_coverage.py",
            "checked": False,
            "coverage_info": "",
            "status": "added",
        },
        {
            "path": "src/zero_coverage.py",
            "checked": True,
            "coverage_info": " (Coverage: 0%)",
            "status": "modified",
        },
    ]

    result = create_test_selection_comment(checklist, branch_name)

    # Verify different coverage scenarios are handled correctly
    assert "- [x] modified `src/with_coverage.py` (Coverage: 85%)" in result
    assert "- [ ] added `src/without_coverage.py`" in result
    assert "- [x] modified `src/zero_coverage.py` (Coverage: 0%)" in result
    mock_reset_command.assert_called_once_with(branch_name)


def test_create_test_selection_comment_long_file_paths(mock_reset_command):
    """Test creating a comment with very long file paths."""
    branch_name = "long-paths"
    long_path = "src/very/deep/nested/directory/structure/with/many/levels/file.py"
    checklist: list[FileChecklistItem] = [
        {
            "path": long_path,
            "checked": True,
            "coverage_info": " (Coverage: 42%)",
            "status": "added",
        }
    ]

    result = create_test_selection_comment(checklist, branch_name)

    # Verify long paths are handled correctly
    assert f"- [x] added `{long_path}` (Coverage: 42%)" in result
    mock_reset_command.assert_called_once_with(branch_name)


def test_create_test_selection_comment_multiple_same_status(mock_reset_command):
    """Test creating a comment with multiple files having the same status."""
    branch_name = "same-status"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/file1.py",
            "checked": True,
            "coverage_info": " (Coverage: 10%)",
            "status": "modified",
        },
        {
            "path": "src/file2.py",
            "checked": False,
            "coverage_info": " (Coverage: 20%)",
            "status": "modified",
        },
        {
            "path": "src/file3.py",
            "checked": True,
            "coverage_info": " (Coverage: 30%)",
            "status": "modified",
        },
    ]

    result = create_test_selection_comment(checklist, branch_name)

    # Verify all files with same status are included
    assert "- [x] modified `src/file1.py` (Coverage: 10%)" in result
    assert "- [ ] modified `src/file2.py` (Coverage: 20%)" in result
    assert "- [x] modified `src/file3.py` (Coverage: 30%)" in result
    mock_reset_command.assert_called_once_with(branch_name)


def test_create_test_selection_comment_all_unchecked(mock_reset_command):
    """Test creating a comment where all items are unchecked."""
    branch_name = "all-unchecked"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/file1.py",
            "checked": False,
            "coverage_info": " (Coverage: 50%)",
            "status": "added",
        },
        {
            "path": "src/file2.py",
            "checked": False,
            "coverage_info": "",
            "status": "removed",
        },
    ]

    result = create_test_selection_comment(checklist, branch_name)

    # Verify all items are unchecked
    assert "- [ ] added `src/file1.py` (Coverage: 50%)" in result
    assert "- [ ] removed `src/file2.py`" in result
    mock_reset_command.assert_called_once_with(branch_name)


def test_create_test_selection_comment_all_checked(mock_reset_command):
    """Test creating a comment where all items are checked."""
    branch_name = "all-checked"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/file1.py",
            "checked": True,
            "coverage_info": " (Coverage: 75%)",
            "status": "modified",
        },
        {
            "path": "src/file2.py",
            "checked": True,
            "coverage_info": " (Coverage: 90%)",
            "status": "added",
        },
    ]

    result = create_test_selection_comment(checklist, branch_name)

    # Verify all items are checked
    assert "- [x] modified `src/file1.py` (Coverage: 75%)" in result
    assert "- [x] added `src/file2.py` (Coverage: 90%)" in result
    mock_reset_command.assert_called_once_with(branch_name)


def test_file_checklist_item_type():
    """Test that FileChecklistItem TypedDict structure is correctly defined."""
    # This test ensures the TypedDict is properly structured
    item: FileChecklistItem = {
        "path": "test/path.py",
        "checked": True,
        "coverage_info": " (Coverage: 100%)",


def test_create_test_selection_comment_branch_name_with_special_chars(mock_reset_command):
    """Test creating a comment with branch names containing special characters."""
    branch_name = "feature/test-branch_with.special@chars"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/test.py",
            "checked": True,
            "coverage_info": "",
            "status": "added",
        }
    ]

    result = create_test_selection_comment(checklist, branch_name)

    # Verify the branch name is passed correctly to reset command
    mock_reset_command.assert_called_once_with(branch_name)
    assert "- [x] added `src/test.py`" in result


def test_create_test_selection_comment_single_item(mock_reset_command):
    """Test creating a comment with exactly one checklist item."""
    branch_name = "single-item"
    checklist: list[FileChecklistItem] = [
        {
            "path": "src/single.py",
            "checked": False,
            "coverage_info": " (Coverage: 25%)",
            "status": "modified",
        }
    ]

    result = create_test_selection_comment(checklist, branch_name)

    # Verify single item is handled correctly
    assert "- [ ] modified `src/single.py` (Coverage: 25%)" in result
    assert TEST_SELECTION_COMMENT_IDENTIFIER in result
    assert "- [ ] Yes, manage tests" in result
    mock_reset_command.assert_called_once_with(branch_name)


def test_create_test_selection_comment_structure_consistency():
    """Test that the comment structure is consistent regardless of input."""
    branch_name = "structure-test"
    
    # Test with different checklist sizes
    test_cases = [
        [],  # Empty
        [{"path": "file1.py", "checked": True, "coverage_info": "", "status": "added"}],  # Single
        [  # Multiple
            {"path": "file1.py", "checked": True, "coverage_info": "", "status": "added"},
            {"path": "file2.py", "checked": False, "coverage_info": " (Coverage: 50%)", "status": "modified"},
        ]
    ]
    
    for checklist in test_cases:
        result = create_test_selection_comment(checklist, branch_name)
        lines = result.split('\n')
        
        # Verify consistent structure elements are always present
        assert lines[0] == TEST_SELECTION_COMMENT_IDENTIFIER
        assert lines[1] == ""
        assert lines[2] == "Select files to manage tests for (create, update, or remove):"
        assert lines[3] == ""
        
        # Find the "Yes, manage tests" line - it should always be present
        yes_manage_line = next((line for line in lines if "Yes, manage tests" in line), None)
        assert yes_manage_line == "- [ ] Yes, manage tests"
        
        # Verify SETTINGS_LINKS is always at the end
        assert lines[-1] == SETTINGS_LINKS
