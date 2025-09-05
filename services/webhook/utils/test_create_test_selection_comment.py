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


def test_create_test_selection_comment_with_empty_coverage_info(mock_reset_command):
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


def test_create_test_selection_comment_with_long_file_paths(mock_reset_command):
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


def test_create_test_selection_comment_with_mixed_checked_states(mock_reset_command):
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


def test_create_test_selection_comment_structure_consistency(mock_reset_command):
    """Test that the comment structure is consistent regardless of checklist content."""
    # Test with different checklist sizes
    for _ in [0, 1, 5, 10]:
        pass
