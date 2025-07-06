import pytest
from unittest.mock import patch

from services.github.pulls.get_pull_request_files import FileChange
from services.webhook.utils.create_file_checklist import create_file_checklist
from services.webhook.utils.create_test_selection_comment import FileChecklistItem


@pytest.fixture
def mock_is_excluded_from_testing():
    """Mock the is_excluded_from_testing function."""
    with patch(
        "services.webhook.utils.create_file_checklist.is_excluded_from_testing"
    ) as mock:
        mock.return_value = False  # Default to not excluded
        yield mock


@pytest.fixture
def sample_file_changes():
    """Sample file changes for testing."""
    return [
        {"filename": "src/file1.py", "status": "modified"},
        {"filename": "src/file2.py", "status": "added"},
        {"filename": "src/file3.py", "status": "removed"},
    ]


@pytest.fixture
def sample_coverage_data():
    """Sample coverage data for testing."""
    return {
        "src/file1.py": {
            "line_coverage": 75.0,
            "function_coverage": 80.0,
            "branch_coverage": 65.0,
        },
        "src/file2.py": {
            "line_coverage": 0.0,
            "function_coverage": None,
            "branch_coverage": None,
        },
    }


class TestCreateFileChecklist:
    """Test cases for create_file_checklist function."""

    def test_empty_file_changes(self, mock_is_excluded_from_testing):
        """Test creating a checklist with empty file changes."""
        file_changes = []
        coverage_data = {}
        
        result = create_file_checklist(file_changes, coverage_data)
        
        assert result == []
        mock_is_excluded_from_testing.assert_not_called()

    def test_single_file_change_no_coverage(self, mock_is_excluded_from_testing):
        """Test creating a checklist with a single file change and no coverage data."""
        file_changes = [{"filename": "src/test.py", "status": "added"}]
        coverage_data = {}
        
        result = create_file_checklist(file_changes, coverage_data)
        
        assert len(result) == 1
        assert result[0]["path"] == "src/test.py"
        assert result[0]["status"] == "added"
        assert result[0]["checked"] is True  # Not excluded by default
        assert result[0]["coverage_info"] == ""
        
        mock_is_excluded_from_testing.assert_called_once_with(
            filename="src/test.py", coverage_data=coverage_data
        )

    def test_single_file_change_with_coverage(self, mock_is_excluded_from_testing):
        """Test creating a checklist with a single file change and coverage data."""
        file_changes = [{"filename": "src/test.py", "status": "modified"}]
        coverage_data = {
            "src/test.py": {
                "line_coverage": 85.0,
                "function_coverage": 90.0,
                "branch_coverage": 75.0,
            }
        }
        
        result = create_file_checklist(file_changes, coverage_data)
        
        assert len(result) == 1
        assert result[0]["path"] == "src/test.py"
        assert result[0]["status"] == "modified"
        assert result[0]["checked"] is True
        assert result[0]["coverage_info"] == " (Line: 85.0%, Function: 90.0%, Branch: 75.0%)"

    def test_file_excluded_from_testing(self, mock_is_excluded_from_testing):
        """Test creating a checklist with a file excluded from testing."""
        mock_is_excluded_from_testing.return_value = True
        
        file_changes = [{"filename": "src/excluded.py", "status": "added"}]
        coverage_data = {}
        
        result = create_file_checklist(file_changes, coverage_data)
        
        assert len(result) == 1
        assert result[0]["path"] == "src/excluded.py"
        assert result[0]["checked"] is False  # Excluded files are unchecked

    def test_multiple_files_mixed_coverage(self, mock_is_excluded_from_testing, sample_file_changes, sample_coverage_data):
        """Test creating a checklist with multiple files and mixed coverage data."""
        result = create_file_checklist(sample_file_changes, sample_coverage_data)
        
        assert len(result) == 3
        
        # First file with full coverage data
        assert result[0]["path"] == "src/file1.py"
        assert result[0]["status"] == "modified"
        assert result[0]["checked"] is True
        assert result[0]["coverage_info"] == " (Line: 75.0%, Function: 80.0%, Branch: 65.0%)"
        
        # Second file with partial coverage data
        assert result[1]["path"] == "src/file2.py"
        assert result[1]["status"] == "added"
        assert result[1]["checked"] is True
        assert result[1]["coverage_info"] == " (Line: 0.0%)"
        
        # Third file with no coverage data
        assert result[2]["path"] == "src/file3.py"
        assert result[2]["status"] == "removed"
        assert result[2]["checked"] is True
        assert result[2]["coverage_info"] == ""

    def test_coverage_data_with_none_values(self, mock_is_excluded_from_testing):
        """Test creating a checklist with coverage data containing None values."""
        file_changes = [{"filename": "src/test.py", "status": "modified"}]
        coverage_data = {
            "src/test.py": {
                "line_coverage": None,
                "function_coverage": None,
                "branch_coverage": None,
            }
        }
        
        result = create_file_checklist(file_changes, coverage_data)
        
        assert len(result) == 1
        assert result[0]["coverage_info"] == ""

    def test_partial_coverage_data(self, mock_is_excluded_from_testing):
        """Test creating a checklist with partial coverage data."""
        file_changes = [
            {"filename": "src/test1.py", "status": "modified"},
            {"filename": "src/test2.py", "status": "added"},
            {"filename": "src/test3.py", "status": "removed"},
        ]
        coverage_data = {
            "src/test1.py": {
                "line_coverage": 50.0,
                "function_coverage": None,
                "branch_coverage": None,
            },
            "src/test2.py": {
                "line_coverage": None,
                "function_coverage": 75.0,
                "branch_coverage": None,
            },
            "src/test3.py": {
                "line_coverage": None,
                "function_coverage": None,
                "branch_coverage": 90.0,
            },
        }
        
        result = create_file_checklist(file_changes, coverage_data)
        
        assert len(result) == 3
        assert result[0]["coverage_info"] == " (Line: 50.0%)"
        assert result[1]["coverage_info"] == " (Function: 75.0%)"
        assert result[2]["coverage_info"] == " (Branch: 90.0%)"

    def test_all_status_types(self, mock_is_excluded_from_testing):
        """Test creating a checklist with all possible status types."""
        file_changes = [
            {"filename": "src/added.py", "status": "added"},
            {"filename": "src/modified.py", "status": "modified"},
            {"filename": "src/removed.py", "status": "removed"},
        ]
        coverage_data = {}
        
        result = create_file_checklist(file_changes, coverage_data)
        
        assert len(result) == 3
        assert result[0]["status"] == "added"
        assert result[1]["status"] == "modified"
        assert result[2]["status"] == "removed"

    def test_return_type_is_list_of_file_checklist_items(self, mock_is_excluded_from_testing):
        """Test that the function returns a list of FileChecklistItem objects."""
        file_changes = [FileChange(filename="src/test.py", status="added")]
        coverage_data = {}
        
        result = create_file_checklist(file_changes, coverage_data)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], dict)
        
        # Verify it has all required keys for FileChecklistItem
        required_keys = {"path", "checked", "coverage_info", "status"}
        assert set(result[0].keys()) == required_keys

    def test_special_characters_in_filenames(self, mock_is_excluded_from_testing):
        """Test creating a checklist with filenames containing special characters."""
        file_changes = [
            FileChange(filename="src/file-with-dashes.py", status="modified"),
            FileChange(filename="src/file_with_underscores.py", status="added"),
            FileChange(filename="src/file.with.dots.py", status="removed"),
        ]
        coverage_data = {}
        
        result = create_file_checklist(file_changes, coverage_data)
        
        assert len(result) == 3
        assert result[0]["path"] == "src/file-with-dashes.py"
        assert result[1]["path"] == "src/file_with_underscores.py"
        assert result[2]["path"] == "src/file.with.dots.py"

    def test_large_number_of_files(self, mock_is_excluded_from_testing):
        """Test creating a checklist with a large number of files."""
        file_changes = [
            FileChange(filename=f"src/file_{i:03d}.py", status="modified")
            for i in range(100)
        ]
        coverage_data = {}
        
        result = create_file_checklist(file_changes, coverage_data)
        
        assert len(result) == 100
        assert all(item["status"] == "modified" for item in result)
        assert all(item["checked"] is True for item in result)
        assert mock_is_excluded_from_testing.call_count == 100
