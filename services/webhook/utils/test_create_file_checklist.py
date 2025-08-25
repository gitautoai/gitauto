from unittest.mock import patch
from datetime import datetime
from typing import cast
import pytest
from schemas.supabase.types import Coverages
from services.github.pulls.get_pull_request_files import FileChange
from services.webhook.utils.create_file_checklist import create_file_checklist


def create_file_change(filename: str, status: str = "modified") -> FileChange:
    """Helper function to create a FileChange object."""
    return {"filename": filename, "status": status}


def create_coverage_data(
    filename: str,
    line_coverage: float | None = None,
    function_coverage: float | None = None,
    branch_coverage: float | None = None,
    is_excluded: bool = False,
    **overrides,
) -> Coverages:
    """Helper function to create coverage data."""
    base_data = {
        "id": 1,
        "owner_id": 123,
        "repo_id": 456,
        "primary_language": "python",
        "package_name": "test_package",
        "level": "file",
        "full_path": filename,
        "statement_coverage": 80.0,
        "function_coverage": function_coverage,
        "branch_coverage": branch_coverage,
        "path_coverage": 60.0,
        "line_coverage": line_coverage,
        "uncovered_lines": "1,2,3",
        "created_at": datetime.now(),
        "created_by": "testuser",
        "updated_at": datetime.now(),
        "updated_by": "testuser",
        "github_issue_url": None,
        "uncovered_functions": "func1,func2",
        "uncovered_branches": "branch1,branch2",
        "branch_name": "main",
        "file_size": 1000,
        "is_excluded_from_testing": is_excluded,
    }
    base_data.update(overrides)
    return cast(Coverages, base_data)


@pytest.fixture
def mock_is_excluded_from_testing():
    """Mock the is_excluded_from_testing function."""
    with patch(
        "services.webhook.utils.create_file_checklist.is_excluded_from_testing"
    ) as mock:
        yield mock


class TestCreateFileChecklist:
    """Test cases for create_file_checklist function."""

    def test_empty_file_changes(self, mock_is_excluded_from_testing):
        """Test creating checklist with empty file changes."""
        # Arrange
        file_changes = []
        coverage_data = {}

        # Act
        result = create_file_checklist(file_changes, coverage_data)

        # Assert
        assert not result
        mock_is_excluded_from_testing.assert_not_called()

    def test_single_file_no_coverage_data(self, mock_is_excluded_from_testing):
        """Test creating checklist with single file and no coverage data."""
        # Arrange
        file_changes = [create_file_change("src/test.py", "added")]
        coverage_data = {}
        mock_is_excluded_from_testing.return_value = False

        # Act
        result = create_file_checklist(file_changes, coverage_data)

        # Assert
        assert len(result) == 1
        assert result[0]["path"] == "src/test.py"
        assert result[0]["checked"] is True
        assert result[0]["status"] == "added"
        assert result[0]["coverage_info"] == ""
        mock_is_excluded_from_testing.assert_called_once_with(
            filename="src/test.py", coverage_data=coverage_data
        )

    def test_single_file_excluded_from_testing(self, mock_is_excluded_from_testing):
        """Test creating checklist with file excluded from testing."""
        # Arrange
        file_changes = [create_file_change("src/excluded.py", "modified")]
        coverage_data = {}
        mock_is_excluded_from_testing.return_value = True

        # Act
        result = create_file_checklist(file_changes, coverage_data)

        # Assert
        assert len(result) == 1
        assert result[0]["path"] == "src/excluded.py"
        assert result[0]["checked"] is False  # Should be unchecked when excluded
        assert result[0]["status"] == "modified"
        assert result[0]["coverage_info"] == ""

    def test_single_file_with_all_coverage_types(self, mock_is_excluded_from_testing):
        """Test creating checklist with file having all coverage types."""
        # Arrange
        filename = "src/covered.py"
        file_changes = [create_file_change(filename, "modified")]
        coverage_data = {
            filename: create_coverage_data(
                filename,
                line_coverage=85.5,
                function_coverage=90.0,
                branch_coverage=75.0,
            )
        }
        mock_is_excluded_from_testing.return_value = False

        # Act
        result = create_file_checklist(file_changes, coverage_data)

        # Assert
        assert len(result) == 1
        assert result[0]["path"] == filename
        assert result[0]["checked"] is True
        assert result[0]["status"] == "modified"
        assert (
            result[0]["coverage_info"]
            == " (Line: 85.5%, Function: 90.0%, Branch: 75.0%)"
        )

    def test_single_file_with_partial_coverage_data(
        self, mock_is_excluded_from_testing
    ):
        """Test creating checklist with file having partial coverage data."""
        # Arrange
        filename = "src/partial.py"
        file_changes = [create_file_change(filename, "added")]
        coverage_data = {
            filename: create_coverage_data(
                filename,
                line_coverage=60.0,
                function_coverage=None,
                branch_coverage=80.0,
            )
        }
        mock_is_excluded_from_testing.return_value = False

        # Act
        result = create_file_checklist(file_changes, coverage_data)

        # Assert
        assert len(result) == 1
        assert result[0]["coverage_info"] == " (Line: 60.0%, Branch: 80.0%)"

    def test_single_file_with_only_line_coverage(self, mock_is_excluded_from_testing):
        """Test creating checklist with file having only line coverage."""
        # Arrange
        filename = "src/line_only.py"
        file_changes = [create_file_change(filename, "removed")]
        coverage_data = {
            filename: create_coverage_data(
                filename,
                line_coverage=42.5,
                function_coverage=None,
                branch_coverage=None,
            )
        }
        mock_is_excluded_from_testing.return_value = False

        # Act
        result = create_file_checklist(file_changes, coverage_data)

        # Assert
        assert len(result) == 1
        assert result[0]["coverage_info"] == " (Line: 42.5%)"

    def test_single_file_with_zero_coverage(self, mock_is_excluded_from_testing):
        """Test creating checklist with file having zero coverage."""
        # Arrange
        filename = "src/zero.py"
        file_changes = [create_file_change(filename, "modified")]
        coverage_data = {
            filename: create_coverage_data(
                filename, line_coverage=0.0, function_coverage=0.0, branch_coverage=0.0
            )
        }
        mock_is_excluded_from_testing.return_value = False

        # Act
        result = create_file_checklist(file_changes, coverage_data)

        # Assert
        assert len(result) == 1
        assert (
            result[0]["coverage_info"] == " (Line: 0.0%, Function: 0.0%, Branch: 0.0%)"
        )

    def test_single_file_with_all_none_coverage(self, mock_is_excluded_from_testing):
        """Test creating checklist with file having all None coverage values."""
        # Arrange
        filename = "src/none_coverage.py"
        file_changes = [create_file_change(filename, "added")]
        coverage_data = {
            filename: create_coverage_data(
                filename,
                line_coverage=None,
                function_coverage=None,
                branch_coverage=None,
            )
        }
        mock_is_excluded_from_testing.return_value = False

        # Act
        result = create_file_checklist(file_changes, coverage_data)

        # Assert
        assert len(result) == 1
        assert result[0]["coverage_info"] == ""  # No coverage info when all are None

    def test_multiple_files_mixed_scenarios(self, mock_is_excluded_from_testing):
        """Test creating checklist with multiple files in different scenarios."""
        # Arrange
        file_changes = [
            create_file_change("src/file1.py", "added"),
            create_file_change("src/file2.py", "modified"),
            create_file_change("src/file3.py", "removed"),
            create_file_change("src/file4.py", "modified"),
        ]
        coverage_data = {
            "src/file1.py": create_coverage_data("src/file1.py", line_coverage=85.0),
            "src/file2.py": create_coverage_data(
                "src/file2.py", line_coverage=60.0, function_coverage=70.0
            ),
            # file3.py has no coverage data
            "src/file4.py": create_coverage_data(
                "src/file4.py",
                line_coverage=None,
                function_coverage=None,
                branch_coverage=None,
            ),
        }

        # Mock different exclusion results for different files
        def mock_exclusion_side_effect(filename, coverage_data):
            return filename == "src/file2.py"  # Only file2 is excluded

        mock_is_excluded_from_testing.side_effect = mock_exclusion_side_effect

        # Act
        result = create_file_checklist(file_changes, coverage_data)

        # Assert
        assert len(result) == 4

        # file1.py - included, has coverage
        assert result[0]["path"] == "src/file1.py"
        assert result[0]["checked"] is True
        assert result[0]["status"] == "added"
        assert result[0]["coverage_info"] == " (Line: 85.0%)"

        # file2.py - excluded, has coverage
        assert result[1]["path"] == "src/file2.py"
        assert result[1]["checked"] is False
        assert result[1]["status"] == "modified"
        assert result[1]["coverage_info"] == " (Line: 60.0%, Function: 70.0%)"

        # file3.py - included, no coverage
        assert result[2]["path"] == "src/file3.py"
        assert result[2]["checked"] is True
        assert result[2]["status"] == "removed"
        assert result[2]["coverage_info"] == ""

        # file4.py - included, has coverage data but all None
        assert result[3]["path"] == "src/file4.py"
        assert result[3]["checked"] is True
        assert result[3]["status"] == "modified"
        assert result[3]["coverage_info"] == ""

    def test_all_file_statuses(self, mock_is_excluded_from_testing):
        """Test creating checklist with all possible file statuses."""
        # Arrange
        file_changes = [
            create_file_change("src/added.py", "added"),
            create_file_change("src/modified.py", "modified"),
            create_file_change("src/removed.py", "removed"),
        ]
        coverage_data = {}
        mock_is_excluded_from_testing.return_value = False

        # Act
        result = create_file_checklist(file_changes, coverage_data)

        # Assert
        assert len(result) == 3
        assert result[0]["status"] == "added"
        assert result[1]["status"] == "modified"
        assert result[2]["status"] == "removed"
        # All should be checked since none are excluded
        assert all(item["checked"] for item in result)

    def test_coverage_info_formatting_edge_cases(self, mock_is_excluded_from_testing):
        """Test coverage info formatting with edge cases."""
        # Arrange
        test_cases = [
            # (line, function, branch, expected_coverage_info)
            (100.0, 100.0, 100.0, " (Line: 100.0%, Function: 100.0%, Branch: 100.0%)"),
            (0.0, None, 50.0, " (Line: 0.0%, Branch: 50.0%)"),
            (None, 75.0, None, " (Function: 75.0%)"),
            (33.33, 66.67, 99.99, " (Line: 33.33%, Function: 66.67%, Branch: 99.99%)"),
        ]

        file_changes = []
        coverage_data = {}

        for i, (line, function, branch, _) in enumerate(test_cases):
            filename = f"src/test{i}.py"
            file_changes.append(create_file_change(filename, "modified"))
            coverage_data[filename] = create_coverage_data(
                filename,
                line_coverage=line,
                function_coverage=function,
                branch_coverage=branch,
            )

        mock_is_excluded_from_testing.return_value = False

        # Act
        result = create_file_checklist(file_changes, coverage_data)

        # Assert
        assert len(result) == len(test_cases)
        for i, (_, _, _, expected_info) in enumerate(test_cases):
            assert result[i]["coverage_info"] == expected_info

    def test_file_path_edge_cases(self, mock_is_excluded_from_testing):
        """Test creating checklist with various file path formats."""
        # Arrange
        file_changes = [
            create_file_change("simple.py", "added"),
            create_file_change("path/to/nested/file.py", "modified"),
            create_file_change("file-with-dashes.py", "removed"),
            create_file_change("file_with_underscores.py", "added"),
            create_file_change("file.with.dots.py", "modified"),
            create_file_change("UPPERCASE.PY", "added"),
            create_file_change("123numeric.py", "modified"),
        ]
        coverage_data = {}
        mock_is_excluded_from_testing.return_value = False

        # Act
        result = create_file_checklist(file_changes, coverage_data)

        # Assert
        assert len(result) == 7
        expected_paths = [
            "simple.py",
            "path/to/nested/file.py",
            "file-with-dashes.py",
            "file_with_underscores.py",
            "file.with.dots.py",
            "UPPERCASE.PY",
            "123numeric.py",
        ]
        for i, expected_path in enumerate(expected_paths):
            assert result[i]["path"] == expected_path

    def test_large_number_of_files(self, mock_is_excluded_from_testing):
        """Test creating checklist with a large number of files."""
        # Arrange
        num_files = 50
        file_changes = []
        coverage_data = {}

        for i in range(num_files):
            filename = f"src/file_{i:03d}.py"
            status = ["added", "modified", "removed"][i % 3]
            file_changes.append(create_file_change(filename, status))

            # Add coverage data for every other file
            if i % 2 == 0:
                coverage_data[filename] = create_coverage_data(
                    filename, line_coverage=float(i), function_coverage=float(i + 10)
                )

        mock_is_excluded_from_testing.return_value = False

        # Act
        result = create_file_checklist(file_changes, coverage_data)

        # Assert
        assert len(result) == num_files
        for i in range(num_files):
            assert result[i]["path"] == f"src/file_{i:03d}.py"
            assert result[i]["status"] == ["added", "modified", "removed"][i % 3]
            assert result[i]["checked"] is True  # All included since mock returns False

            # Check coverage info
            if i % 2 == 0:  # Files with coverage data
                expected_info = f" (Line: {float(i)}%, Function: {float(i + 10)}%)"
                assert result[i]["coverage_info"] == expected_info
            else:  # Files without coverage data
                assert result[i]["coverage_info"] == ""

    def test_coverage_data_with_file_not_in_changes(
        self, mock_is_excluded_from_testing
    ):
        """Test that coverage data for files not in changes is ignored."""
        # Arrange
        file_changes = [create_file_change("src/included.py", "modified")]
        coverage_data = {
            "src/included.py": create_coverage_data(
                "src/included.py", line_coverage=80.0
            ),
            "src/not_in_changes.py": create_coverage_data(
                "src/not_in_changes.py", line_coverage=90.0
            ),
        }
        mock_is_excluded_from_testing.return_value = False

        # Act
        result = create_file_checklist(file_changes, coverage_data)

        # Assert
        assert len(result) == 1
        assert result[0]["path"] == "src/included.py"
        assert result[0]["coverage_info"] == " (Line: 80.0%)"

    def test_is_excluded_from_testing_called_correctly(
        self, mock_is_excluded_from_testing
    ):
        """Test that is_excluded_from_testing is called with correct parameters."""
        # Arrange
        file_changes = [
            create_file_change("src/file1.py", "added"),
            create_file_change("src/file2.py", "modified"),
        ]
        coverage_data = {
            "src/file1.py": create_coverage_data("src/file1.py", line_coverage=50.0)
        }
        mock_is_excluded_from_testing.return_value = False

        # Act
        create_file_checklist(file_changes, coverage_data)

        # Assert
        assert mock_is_excluded_from_testing.call_count == 2
        mock_is_excluded_from_testing.assert_any_call(
            filename="src/file1.py", coverage_data=coverage_data
        )
        mock_is_excluded_from_testing.assert_any_call(
            filename="src/file2.py", coverage_data=coverage_data
        )

    def test_file_checklist_item_structure(self, mock_is_excluded_from_testing):
        """Test that returned FileChecklistItem has correct structure."""
        # Arrange
        file_changes = [create_file_change("src/test.py", "modified")]
        coverage_data = {
            "src/test.py": create_coverage_data("src/test.py", line_coverage=75.0)
        }
        mock_is_excluded_from_testing.return_value = False

        # Act
        result = create_file_checklist(file_changes, coverage_data)

        # Assert
        assert len(result) == 1
        item = result[0]

        # Check all required keys are present
        assert "path" in item
        assert "checked" in item
        assert "status" in item
        assert "coverage_info" in item

        # Check types
        assert isinstance(item["path"], str)
        assert isinstance(item["checked"], bool)
        assert isinstance(item["status"], str)
        assert isinstance(item["coverage_info"], str)

        # Check values
        assert item["path"] == "src/test.py"
        assert item["checked"] is True
        assert item["status"] == "modified"
        assert item["coverage_info"] == " (Line: 75.0%)"

    def test_integration_without_mocks(self):
        """Test the function with actual dependencies (integration test)."""
        # Arrange
        file_changes = [
            create_file_change("src/included.py", "added"),
            create_file_change("src/excluded.py", "modified"),
        ]
        coverage_data = {
            "src/included.py": create_coverage_data(
                "src/included.py", line_coverage=85.0, is_excluded=False
            ),
            "src/excluded.py": create_coverage_data(
                "src/excluded.py", function_coverage=90.0, is_excluded=True
            ),
        }

        # Act
        result = create_file_checklist(file_changes, coverage_data)

        # Assert
        assert len(result) == 2

        # included.py should be checked (not excluded)
        included_item = next(
            item for item in result if item["path"] == "src/included.py"
        )
        assert included_item["checked"] is True
        assert included_item["coverage_info"] == " (Line: 85.0%)"

        # excluded.py should be unchecked (excluded)
        excluded_item = next(
            item for item in result if item["path"] == "src/excluded.py"
        )
        assert excluded_item["checked"] is False
        assert excluded_item["coverage_info"] == " (Function: 90.0%)"
