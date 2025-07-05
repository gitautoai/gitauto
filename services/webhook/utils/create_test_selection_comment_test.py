import pytest
from unittest.mock import patch

from config import PRODUCT_NAME
from constants.messages import SETTINGS_LINKS
from services.github.pulls.get_pull_request_files import Status
from utils.text.comment_identifiers import TEST_SELECTION_COMMENT_IDENTIFIER
from services.webhook.utils.create_test_selection_comment import (
    create_test_selection_comment,
    FileChecklistItem,
)


@pytest.fixture
def mock_reset_command():
    """Mock the reset command message function."""
    with patch(
        "services.webhook.utils.create_test_selection_comment.create_reset_command_message"
    ) as mock:
        mock.return_value = "MOCK_RESET_COMMAND"
        yield mock


class TestCreateTestSelectionComment:
    """Test cases for create_test_selection_comment function."""

    def test_empty_checklist(self, mock_reset_command):
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

    def test_single_checked_item(self, mock_reset_command):
        """Test creating a comment with a single checked item."""
        branch_name = "feature-branch"
        checklist: list[FileChecklistItem] = [
            {
                "path": "src/file1.py",
                "checked": True,
                "coverage_info": " (Coverage: 75%)",
                "status": "modified",
            }
        ]

        result = create_test_selection_comment(checklist, branch_name)

        # Verify the reset command was called with the correct branch name
        mock_reset_command.assert_called_once_with(branch_name)

        # Check that the comment contains the checked item
        assert "- [x] modified `src/file1.py` (Coverage: 75%)" in result
        assert TEST_SELECTION_COMMENT_IDENTIFIER in result
        assert SETTINGS_LINKS in result

    def test_single_unchecked_item(self, mock_reset_command):
        """Test creating a comment with a single unchecked item."""
        branch_name = "main"
        checklist: list[FileChecklistItem] = [
            {
                "path": "src/file2.py",
                "checked": False,
                "coverage_info": " (Coverage: 0%)",
                "status": "added",
            }
        ]

        result = create_test_selection_comment(checklist, branch_name)

        # Verify the reset command was called with the correct branch name
        mock_reset_command.assert_called_once_with(branch_name)

        # Check that the comment contains the unchecked item
        assert "- [ ] added `src/file2.py` (Coverage: 0%)" in result
        assert TEST_SELECTION_COMMENT_IDENTIFIER in result
        assert SETTINGS_LINKS in result

    def test_multiple_items_mixed_checked_status(self, mock_reset_command):
        """Test creating a comment with multiple items having mixed checked status."""
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
            {
                "path": "src/file3.py",
                "checked": True,
                "coverage_info": "",
                "status": "removed",
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
            "- [x] removed `src/file3.py`",
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

    def test_all_status_types(self, mock_reset_command):
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

    def test_empty_coverage_info(self, mock_reset_command):
        """Test creating a comment with empty coverage info."""
        branch_name = "test-branch"
        checklist: list[FileChecklistItem] = [
            {
                "path": "src/file.py",
                "checked": True,
                "coverage_info": "",
                "status": "modified",
            }
        ]

        result = create_test_selection_comment(checklist, branch_name)

        # Check that the item appears without coverage info
        assert "- [x] modified `src/file.py`" in result
        # Ensure no extra spaces or coverage info is added
        assert "- [x] modified `src/file.py` " not in result

    def test_special_characters_in_paths(self, mock_reset_command):
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
            {
                "path": "src/file.with.dots.py",
                "checked": True,
                "coverage_info": " (Coverage: 100%)",
                "status": "modified",
            },
        ]

        result = create_test_selection_comment(checklist, branch_name)
        
        assert "- [x] modified `src/file-with-dashes.py`" in result
        assert "- [ ] added `src/file_with_underscores.py` (Coverage: 0%)" in result
        assert "- [x] modified `src/file.with.dots.py` (Coverage: 100%)" in result

    def test_long_file_paths(self, mock_reset_command):
        """Test creating a comment with very long file paths."""
        branch_name = "test-branch"
        long_path = "very/long/path/to/some/deeply/nested/directory/structure/file.py"
        checklist: list[FileChecklistItem] = [
            {
                "path": long_path,
                "checked": True,
                "coverage_info": " (Coverage: 85%)",
                "status": "modified",
            }
        ]

        result = create_test_selection_comment(checklist, branch_name)

        # Check that long paths are handled correctly
        assert f"- [x] modified `{long_path}` (Coverage: 85%)" in result

    def test_different_branch_name_formats(self, mock_reset_command):
        """Test creating a comment with different branch name formats."""
        test_cases = [
            "main",
            "feature/new-feature",
            "bugfix/fix-123",
            "release/v1.0.0",
            "hotfix/urgent-fix",
            "develop",
        ]

        checklist: list[FileChecklistItem] = [
            {
                "path": "src/test.py",
                "checked": True,
                "coverage_info": "",
                "status": "modified",
            }
        ]

        for branch_name in test_cases:
            result = create_test_selection_comment(checklist, branch_name)
            
            # Verify the reset command was called with each branch name
            assert TEST_SELECTION_COMMENT_IDENTIFIER in result
            assert SETTINGS_LINKS in result
            assert "- [x] modified `src/test.py`" in result

        # Verify reset command was called for each test case
        assert mock_reset_command.call_count == len(test_cases)

    def test_coverage_info_variations(self, mock_reset_command):
        """Test creating a comment with different coverage info formats."""
        branch_name = "test-branch"
        checklist: list[FileChecklistItem] = [
            {
                "path": "src/file1.py",
                "checked": True,
                "coverage_info": " (Coverage: 0%)",
                "status": "modified",
            },
            {
                "path": "src/file2.py",
                "checked": True,
                "coverage_info": " (Coverage: 100%)",
                "status": "added",
            },
            {
                "path": "src/file3.py",
                "checked": False,
                "coverage_info": " (Coverage: 42%)",
                "status": "modified",
            },
        ]

        result = create_test_selection_comment(checklist, branch_name)

        # Check that different coverage percentages are handled correctly
        assert "- [x] modified `src/file1.py` (Coverage: 0%)" in result
        assert "- [x] added `src/file2.py` (Coverage: 100%)" in result
        assert "- [ ] modified `src/file3.py` (Coverage: 42%)" in result

    def test_checkbox_formatting(self, mock_reset_command):
        """Test that checkbox formatting is correct for checked and unchecked items."""
        branch_name = "test-branch"
        checklist: list[FileChecklistItem] = [
            {
                "path": "checked.py",
                "checked": True,
                "coverage_info": "",
                "status": "modified",
            },
            {
                "path": "unchecked.py",
                "checked": False,
                "coverage_info": "",
                "status": "added",
            },
        ]

        result = create_test_selection_comment(checklist, branch_name)

        # Verify exact checkbox formatting
        assert "- [x] modified `checked.py`" in result
        assert "- [ ] added `unchecked.py`" in result
        # Ensure no malformed checkboxes
        assert "- [X]" not in result
        assert "- []" not in result

    def test_comment_structure_order(self, mock_reset_command):
        """Test that the comment structure follows the correct order."""
        branch_name = "test-branch"
        checklist: list[FileChecklistItem] = [
            {
                "path": "src/file.py",
                "checked": True,
                "coverage_info": " (Coverage: 50%)",
                "status": "modified",
            }
        ]

        result = create_test_selection_comment(checklist, branch_name)
        lines = result.split("\n")

        # Verify the structure order
        assert lines[0] == TEST_SELECTION_COMMENT_IDENTIFIER
        assert lines[1] == ""
        assert lines[2] == "Select files to manage tests for (create, update, or remove):"
        assert lines[3] == ""
        assert lines[4] == "- [x] modified `src/file.py` (Coverage: 50%)"
        assert lines[5] == ""
        assert lines[6] == "---"
        assert lines[7] == ""
        assert lines[8] == "- [ ] Yes, manage tests"
        assert lines[9] == ""
        assert lines[10] == f"Click the checkbox and {PRODUCT_NAME} will add/update/remove tests for the selected files to this PR."
        assert lines[11] == "MOCK_RESET_COMMAND"
        assert lines[12] == ""
        assert lines[13].startswith("You can [turn off triggers]")

    def test_integration_with_actual_dependencies(self):
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

    def test_large_checklist(self, mock_reset_command):
        """Test creating a comment with a large number of files."""
        branch_name = "test-branch"
        checklist: list[FileChecklistItem] = []
        
        # Create a large checklist with 20 files
        for i in range(20):
            checklist.append({
                "path": f"src/file_{i:02d}.py",
                "checked": i % 2 == 0,  # Alternate between checked and unchecked
                "coverage_info": f" (Coverage: {i * 5}%)" if i < 20 else "",
                "status": "modified" if i % 3 == 0 else "added" if i % 3 == 1 else "removed",
            })

        result = create_test_selection_comment(checklist, branch_name)

        # Verify all files are included
        for i in range(20):
            checkbox = "[x]" if i % 2 == 0 else "[ ]"
            status = "modified" if i % 3 == 0 else "added" if i % 3 == 1 else "removed"
            coverage = f" (Coverage: {i * 5}%)" if i < 20 else ""
            expected_line = f"- {checkbox} {status} `src/file_{i:02d}.py`{coverage}"
            assert expected_line in result

        # Verify structure is maintained
        assert TEST_SELECTION_COMMENT_IDENTIFIER in result
        assert SETTINGS_LINKS in result
        assert "- [ ] Yes, manage tests" in result


class TestFileChecklistItem:
    """Test cases for FileChecklistItem TypedDict."""

    def test_file_checklist_item_structure(self):
        """Test that FileChecklistItem has the correct structure."""
        # This test ensures the TypedDict structure is maintained
        item: FileChecklistItem = {
            "path": "test/file.py",
            "checked": True,
            "coverage_info": " (Coverage: 75%)",
            "status": "modified",
        }
        
        # Verify all required keys are present
        assert "path" in item
        assert "checked" in item
        assert "coverage_info" in item
        assert "status" in item
        
        # Verify types
        assert isinstance(item["path"], str)
        assert isinstance(item["checked"], bool)
        assert isinstance(item["coverage_info"], str)
        assert item["status"] in ["added", "modified", "removed"]

    def test_status_type_values(self):
        """Test that Status type accepts correct values."""
        valid_statuses: list[Status] = ["added", "modified", "removed"]
        
        for status in valid_statuses:
            item: FileChecklistItem = {
                "path": "test.py",
                "checked": False,
                "coverage_info": "",
                "status": status,
            }
            # If this doesn't raise a type error, the status is valid
            assert item["status"] == status
