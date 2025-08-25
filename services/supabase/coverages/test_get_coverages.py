# pylint: disable=redefined-outer-name

# Standard imports
from unittest.mock import patch, Mock

# Third-party imports
import pytest

# Local imports
from services.supabase.coverages.get_coverages import get_coverages


@pytest.fixture
def mock_supabase():
    """Fixture to mock the supabase client."""
    with patch("services.supabase.coverages.get_coverages.supabase") as mock:
        yield mock


@pytest.fixture
def sample_coverage_data():
    """Fixture providing sample coverage data."""
    return [
        {
            "id": 1,
            "full_path": "src/main.py",
            "repo_id": 123,
            "owner_id": 456,
            "line_coverage": 85.5,
            "function_coverage": 90.0,
            "branch_coverage": 75.0,
            "statement_coverage": 88.0,
            "level": "file",
            "branch_name": "main",
            "created_by": "test_user",
            "updated_by": "test_user",
            "primary_language": "python",
            "package_name": None,
            "github_issue_url": None,
            "is_excluded_from_testing": False,
            "uncovered_lines": "10,15,20",
            "uncovered_functions": "func1,func2",
            "uncovered_branches": "branch1,branch2",
            "file_size": 1024,
            "path_coverage": 80.0,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        },
        {
            "id": 2,
            "full_path": "src/utils.py",
            "repo_id": 123,
            "owner_id": 456,
            "line_coverage": 95.0,
            "function_coverage": 100.0,
            "branch_coverage": 85.0,
            "statement_coverage": 92.0,
            "level": "file",
            "branch_name": "main",
            "created_by": "test_user",
            "updated_by": "test_user",
            "primary_language": "python",
            "package_name": None,
            "github_issue_url": None,
            "is_excluded_from_testing": False,
            "uncovered_lines": "5",
            "uncovered_functions": None,
            "uncovered_branches": "branch3",
            "file_size": 512,
            "path_coverage": 90.0,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        },
    ]


@pytest.fixture
def mock_supabase_chain(mock_supabase):
    """Fixture to set up the complete supabase method chain."""
    mock_chain = Mock()
    mock_supabase.table.return_value = mock_chain
    mock_chain.select.return_value = mock_chain
    mock_chain.eq.return_value = mock_chain
    mock_chain.in_.return_value = mock_chain
    return mock_chain


class TestGetCoverages:
    def test_get_coverages_success_with_data(
        self, mock_supabase_chain, sample_coverage_data
    ):
        """Test successful coverage retrieval when data exists."""
        # Setup
        mock_result = Mock()
        mock_result.data = sample_coverage_data
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 123
        filenames = ["src/main.py", "src/utils.py"]

        # Execute
        result = get_coverages(repo_id=repo_id, filenames=filenames)

        # Verify
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "src/main.py" in result
        assert "src/utils.py" in result
        assert result["src/main.py"]["line_coverage"] == 85.5
        assert result["src/utils.py"]["line_coverage"] == 95.0

        # Verify database query was constructed correctly
        mock_supabase_chain.select.assert_called_once_with("*")
        mock_supabase_chain.eq.assert_called_once_with("repo_id", repo_id)
        mock_supabase_chain.in_.assert_called_once_with("full_path", filenames)
        mock_supabase_chain.execute.assert_called_once()

    def test_get_coverages_empty_filenames_list(self, mock_supabase_chain):
        """Test that empty filenames list returns empty dictionary without database query."""
        # Setup
        repo_id = 123
        filenames = []

        # Execute
        result = get_coverages(repo_id=repo_id, filenames=filenames)

        # Verify
        assert not result

        # Verify no database query was made
        mock_supabase_chain.execute.assert_not_called()

    def test_get_coverages_no_data_found(self, mock_supabase_chain):
        """Test when no coverage data is found in the database."""
        # Setup
        mock_result = Mock()
        mock_result.data = []
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 123
        filenames = ["src/nonexistent.py"]

        # Execute
        result = get_coverages(repo_id=repo_id, filenames=filenames)

        # Verify
        assert not result
        mock_supabase_chain.execute.assert_called_once()

    def test_get_coverages_none_data(self, mock_supabase_chain):
        """Test when result.data is None."""
        # Setup
        mock_result = Mock()
        mock_result.data = None
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 123
        filenames = ["src/test.py"]

        # Execute
        result = get_coverages(repo_id=repo_id, filenames=filenames)

        # Verify
        assert not result
        mock_supabase_chain.execute.assert_called_once()

    def test_get_coverages_single_file(self, mock_supabase_chain, sample_coverage_data):
        """Test coverage retrieval for a single file."""
        # Setup
        single_file_data = [sample_coverage_data[0]]
        mock_result = Mock()
        mock_result.data = single_file_data
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 123
        filenames = ["src/main.py"]

        # Execute
        result = get_coverages(repo_id=repo_id, filenames=filenames)

        # Verify
        assert len(result) == 1
        assert "src/main.py" in result
        assert result["src/main.py"]["id"] == 1
        assert result["src/main.py"]["line_coverage"] == 85.5

    def test_get_coverages_multiple_files(
        self, mock_supabase_chain, sample_coverage_data
    ):
        """Test coverage retrieval for multiple files."""
        # Setup
        mock_result = Mock()
        mock_result.data = sample_coverage_data
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 123
        filenames = ["src/main.py", "src/utils.py", "src/nonexistent.py"]

        # Execute
        result = get_coverages(repo_id=repo_id, filenames=filenames)

        # Verify
        assert len(result) == 2  # Only files with data are returned
        assert "src/main.py" in result
        assert "src/utils.py" in result
        assert "src/nonexistent.py" not in result

    def test_get_coverages_with_different_repo_id(
        self, mock_supabase_chain, sample_coverage_data
    ):
        """Test coverage retrieval with different repo_id values."""
        # Setup
        mock_result = Mock()
        mock_result.data = sample_coverage_data
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 999
        filenames = ["src/main.py"]

        # Execute
        result = get_coverages(repo_id=repo_id, filenames=filenames)

        # Verify
        assert len(result) == 2
        mock_supabase_chain.eq.assert_called_once_with("repo_id", repo_id)

    def test_get_coverages_with_special_file_paths(self, mock_supabase_chain):
        """Test coverage retrieval with special characters in file paths."""
        # Setup
        special_data = [
            {
                "id": 1,
                "full_path": "src/file with spaces.py",
                "repo_id": 123,
                "line_coverage": 80.0,
                "function_coverage": 85.0,
                "branch_coverage": 75.0,
            }
        ]
        mock_result = Mock()
        mock_result.data = special_data
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 123
        filenames = [
            "src/file with spaces.py",
            "src/file-with-dashes.py",
            "src/file_with_underscores.py",
        ]

        # Execute
        result = get_coverages(repo_id=repo_id, filenames=filenames)

        # Verify
        assert len(result) == 1
        assert "src/file with spaces.py" in result
        assert result["src/file with spaces.py"]["line_coverage"] == 80.0

    def test_get_coverages_with_zero_coverage(self, mock_supabase_chain):
        """Test coverage retrieval with zero coverage values."""
        # Setup
        zero_coverage_data = [
            {
                "id": 1,
                "full_path": "src/uncovered.py",
                "repo_id": 123,
                "line_coverage": 0.0,
                "function_coverage": 0.0,
                "branch_coverage": 0.0,
                "statement_coverage": 0.0,
            }
        ]
        mock_result = Mock()
        mock_result.data = zero_coverage_data
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 123
        filenames = ["src/uncovered.py"]

        # Execute
        result = get_coverages(repo_id=repo_id, filenames=filenames)

        # Verify
        assert len(result) == 1
        assert result["src/uncovered.py"]["line_coverage"] == 0.0
        assert result["src/uncovered.py"]["function_coverage"] == 0.0
        assert result["src/uncovered.py"]["branch_coverage"] == 0.0

    def test_get_coverages_with_full_coverage(self, mock_supabase_chain):
        """Test coverage retrieval with 100% coverage values."""
        # Setup
        full_coverage_data = [
            {
                "id": 1,
                "full_path": "src/perfect.py",
                "repo_id": 123,
                "line_coverage": 100.0,
                "function_coverage": 100.0,
                "branch_coverage": 100.0,
                "statement_coverage": 100.0,
            }
        ]
        mock_result = Mock()
        mock_result.data = full_coverage_data
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 123
        filenames = ["src/perfect.py"]

        # Execute
        result = get_coverages(repo_id=repo_id, filenames=filenames)

        # Verify
        assert len(result) == 1
        assert result["src/perfect.py"]["line_coverage"] == 100.0
        assert result["src/perfect.py"]["function_coverage"] == 100.0
        assert result["src/perfect.py"]["branch_coverage"] == 100.0

    def test_get_coverages_database_exception(self, mock_supabase_chain):
        """Test that database exceptions are handled gracefully due to handle_exceptions decorator."""
        # Setup
        mock_supabase_chain.execute.side_effect = Exception("Database connection error")

        repo_id = 123
        filenames = ["src/test.py"]

        # Execute
        result = get_coverages(repo_id=repo_id, filenames=filenames)

        # Verify - should return empty dict due to handle_exceptions decorator
        assert not result

    def test_get_coverages_supabase_table_exception(self, mock_supabase):
        """Test that supabase.table exceptions are handled gracefully."""
        # Setup
        mock_supabase.table.side_effect = Exception("Table access error")

        repo_id = 123
        filenames = ["src/test.py"]

        # Execute
        result = get_coverages(repo_id=repo_id, filenames=filenames)

        # Verify - should return empty dict due to handle_exceptions decorator
        assert not result

    @pytest.mark.parametrize(
        "repo_id,filenames",
        [
            (1, ["file1.py"]),
            (999999, ["very/deep/nested/file.py"]),
            (0, ["root.py"]),
            (123, ["src/file1.py", "src/file2.py", "src/file3.py"]),
        ],
    )
    def test_get_coverages_with_various_parameters(
        self, mock_supabase_chain, repo_id, filenames
    ):
        """Test get_coverages with various parameter combinations."""
        # Setup
        mock_result = Mock()
        mock_result.data = []
        mock_supabase_chain.execute.return_value = mock_result

        # Execute
        result = get_coverages(repo_id=repo_id, filenames=filenames)

        # Verify
        assert not result
        mock_supabase_chain.eq.assert_called_once_with("repo_id", repo_id)
        mock_supabase_chain.in_.assert_called_once_with("full_path", filenames)

    def test_get_coverages_with_none_values_in_data(self, mock_supabase_chain):
        """Test coverage retrieval when some fields have None values."""
        # Setup
        data_with_nones = [
            {
                "id": 1,
                "full_path": "src/partial.py",
                "repo_id": 123,
                "line_coverage": 50.0,
                "function_coverage": None,
                "branch_coverage": 60.0,
                "statement_coverage": None,
                "package_name": None,
                "github_issue_url": None,
                "uncovered_lines": None,
                "uncovered_functions": None,
                "uncovered_branches": None,
            }
        ]
        mock_result = Mock()
        mock_result.data = data_with_nones
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 123
        filenames = ["src/partial.py"]

        # Execute
        result = get_coverages(repo_id=repo_id, filenames=filenames)

        # Verify
        assert len(result) == 1
        assert result["src/partial.py"]["line_coverage"] == 50.0
        assert result["src/partial.py"]["function_coverage"] is None
        assert result["src/partial.py"]["branch_coverage"] == 60.0
        assert result["src/partial.py"]["package_name"] is None

    def test_get_coverages_return_type_cast(
        self, mock_supabase_chain, sample_coverage_data
    ):
        """Test that the return values are properly cast to Coverages type."""
        # Setup
        mock_result = Mock()
        mock_result.data = sample_coverage_data
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 123
        filenames = ["src/main.py"]

        # Execute
        result = get_coverages(repo_id=repo_id, filenames=filenames)

        # Verify the result structure (cast function doesn't change runtime behavior)
        assert isinstance(result, dict)
        assert isinstance(result["src/main.py"], dict)  # At runtime, it's still a dict
        assert "full_path" in result["src/main.py"]
        assert "line_coverage" in result["src/main.py"]

    def test_get_coverages_large_filenames_list(self, mock_supabase_chain):
        """Test coverage retrieval with a large number of filenames."""
        # Setup
        large_filenames = [f"src/file_{i}.py" for i in range(100)]
        mock_result = Mock()
        mock_result.data = []
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 123

        # Execute
        result = get_coverages(repo_id=repo_id, filenames=large_filenames)

        # Verify
        assert not result
        mock_supabase_chain.in_.assert_called_once_with("full_path", large_filenames)

    def test_get_coverages_duplicate_filenames(
        self, mock_supabase_chain, sample_coverage_data
    ):
        """Test coverage retrieval with duplicate filenames in the list."""
        # Setup
        mock_result = Mock()
        mock_result.data = [sample_coverage_data[0]]  # Only one record
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 123
        filenames = ["src/main.py", "src/main.py", "src/main.py"]  # Duplicates

        # Execute
        result = get_coverages(repo_id=repo_id, filenames=filenames)

        # Verify
        assert len(result) == 1  # Should only have one entry despite duplicates
        assert "src/main.py" in result
        mock_supabase_chain.in_.assert_called_once_with("full_path", filenames)
