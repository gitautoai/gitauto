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

def test_create_test_selection_comment_with_large_checklist():
    """Test creating a comment with a large number of files."""
    branch_name = "large-checklist-branch"
    # Create a checklist with 20 items
    checklist: list[FileChecklistItem] = [
        {
            "path": f"src/file{i}.py",
            "checked": i % 2 == 0,  # Alternate between checked and unchecked
            "coverage_info": f" (Coverage: {i * 5}%)",
            "status": "modified" if i % 3 == 0 else "added" if i % 3 == 1 else "removed",
        }
        for i in range(1, 21)
    ]

    result = create_test_selection_comment(checklist, branch_name)

    # Verify the comment contains all files
    for i in range(1, 21):
        checkbox = "[x]" if i % 2 == 0 else "[ ]"
        status = "modified" if i % 3 == 0 else "added" if i % 3 == 1 else "removed"
        assert f"- {checkbox} {status} `src/file{i}.py` (Coverage: {i * 5}%)" in result

    # Verify other parts of the comment
    assert TEST_SELECTION_COMMENT_IDENTIFIER in result
    assert "- [ ] Yes, manage tests" in result
    assert SETTINGS_LINKS in result


def test_create_test_selection_comment_with_empty_path_or_coverage():
    """Test creating a comment with empty path or coverage info."""
    branch_name = "empty-fields-branch"
    checklist: list[FileChecklistItem] = [
        {
            "path": "",  # Empty path
            "checked": True,
            "coverage_info": " (Coverage: 50%)",
            "status": "modified",
        },
        {
            "path": "src/file.py",
            "checked": False,
            "coverage_info": "",  # Empty coverage info
            "status": "added",
        },
    ]

    result = create_test_selection_comment(checklist, branch_name)

    assert "- [x] modified `` (Coverage: 50%)" in result
    assert "- [ ] added `src/file.py`" in result


def test_create_test_selection_comment_with_complex_branch_name():
    """Test creating a comment with complex branch name formats."""
    complex_branch_names = [
        "feature/user-auth#123",
        "bugfix/issue-456_hotfix",
        "release/v1.2.3+build.456",
    ]

    for branch_name in complex_branch_names:
        result = create_test_selection_comment([], branch_name)
        assert branch_name in result  # Branch name should be in the reset command
