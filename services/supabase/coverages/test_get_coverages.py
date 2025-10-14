# pylint: disable=redefined-outer-name

# Standard imports
import logging
import os
from unittest.mock import Mock, patch

# Third-party imports
import pytest
# Local imports
from services.supabase.client import supabase
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
            "language": "python",
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
            "language": "python",
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
        mock_result = Mock()
        mock_result.data = sample_coverage_data
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 123
        filenames = ["src/main.py", "src/utils.py"]

        result = get_coverages(repo_id=repo_id, filenames=filenames)

        assert isinstance(result, dict)
        assert len(result) == 2
        assert "src/main.py" in result
        assert "src/utils.py" in result
        assert result["src/main.py"]["line_coverage"] == 85.5
        assert result["src/utils.py"]["line_coverage"] == 95.0

        mock_supabase_chain.select.assert_called_once_with("*")
        mock_supabase_chain.eq.assert_called_once_with("repo_id", repo_id)
        mock_supabase_chain.in_.assert_called_once_with("full_path", filenames)
        mock_supabase_chain.execute.assert_called_once()

    def test_get_coverages_empty_filenames_list(self, mock_supabase_chain):
        """Test that empty filenames list returns empty dictionary without database query."""
        repo_id = 123
        filenames = []

        result = get_coverages(repo_id=repo_id, filenames=filenames)

        assert not result
        mock_supabase_chain.execute.assert_not_called()

    def test_get_coverages_no_data_found(self, mock_supabase_chain):
        """Test when no coverage data is found in the database."""
        mock_result = Mock()
        mock_result.data = []
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 123
        filenames = ["src/nonexistent.py"]

        result = get_coverages(repo_id=repo_id, filenames=filenames)

        assert not result
        mock_supabase_chain.execute.assert_called_once()

    def test_get_coverages_none_data(self, mock_supabase_chain):
        """Test when result.data is None."""
        mock_result = Mock()
        mock_result.data = None
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 123
        filenames = ["src/test.py"]

        result = get_coverages(repo_id=repo_id, filenames=filenames)

        assert not result
        mock_supabase_chain.execute.assert_called_once()

    def test_get_coverages_single_file(self, mock_supabase_chain, sample_coverage_data):
        """Test coverage retrieval for a single file."""
        single_file_data = [sample_coverage_data[0]]
        mock_result = Mock()
        mock_result.data = single_file_data
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 123
        filenames = ["src/main.py"]

        result = get_coverages(repo_id=repo_id, filenames=filenames)

        assert len(result) == 1
        assert "src/main.py" in result
        assert result["src/main.py"]["id"] == 1
        assert result["src/main.py"]["line_coverage"] == 85.5

    def test_get_coverages_multiple_files(
        self, mock_supabase_chain, sample_coverage_data
    ):
        """Test coverage retrieval for multiple files."""
        mock_result = Mock()
        mock_result.data = sample_coverage_data
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 123
        filenames = ["src/main.py", "src/utils.py", "src/nonexistent.py"]

        result = get_coverages(repo_id=repo_id, filenames=filenames)

        assert len(result) == 2
        assert "src/main.py" in result
        assert "src/utils.py" in result
        assert "src/nonexistent.py" not in result

    def test_get_coverages_with_different_repo_id(
        self, mock_supabase_chain, sample_coverage_data
    ):
        """Test coverage retrieval with different repo_id values."""
        mock_result = Mock()
        mock_result.data = sample_coverage_data
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 999
        filenames = ["src/main.py"]

        result = get_coverages(repo_id=repo_id, filenames=filenames)

        assert len(result) == 2
        mock_supabase_chain.eq.assert_called_once_with("repo_id", repo_id)

    def test_get_coverages_with_special_file_paths(self, mock_supabase_chain):
        """Test coverage retrieval with special characters in file paths."""
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

        result = get_coverages(repo_id=repo_id, filenames=filenames)

        assert len(result) == 1
        assert "src/file with spaces.py" in result
        assert result["src/file with spaces.py"]["line_coverage"] == 80.0

    def test_get_coverages_with_zero_coverage(self, mock_supabase_chain):
        """Test coverage retrieval with zero coverage values."""
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

        result = get_coverages(repo_id=repo_id, filenames=filenames)

        assert len(result) == 1
        assert result["src/uncovered.py"]["line_coverage"] == 0.0
        assert result["src/uncovered.py"]["function_coverage"] == 0.0
        assert result["src/uncovered.py"]["branch_coverage"] == 0.0

    def test_get_coverages_with_full_coverage(self, mock_supabase_chain):
        """Test coverage retrieval with 100% coverage values."""
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

        result = get_coverages(repo_id=repo_id, filenames=filenames)

        assert len(result) == 1
        assert result["src/perfect.py"]["line_coverage"] == 100.0
        assert result["src/perfect.py"]["function_coverage"] == 100.0
        assert result["src/perfect.py"]["branch_coverage"] == 100.0

    def test_get_coverages_database_exception(self, mock_supabase_chain):
        """Test that database exceptions are handled gracefully due to handle_exceptions decorator."""
        mock_supabase_chain.execute.side_effect = Exception("Database connection error")

        repo_id = 123
        filenames = ["src/test.py"]

        result = get_coverages(repo_id=repo_id, filenames=filenames)

        assert not result

    def test_get_coverages_supabase_table_exception(self, mock_supabase):
        """Test that supabase.table exceptions are handled gracefully."""
        mock_supabase.table.side_effect = Exception("Table access error")

        repo_id = 123
        filenames = ["src/test.py"]

        result = get_coverages(repo_id=repo_id, filenames=filenames)

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
        mock_result = Mock()
        mock_result.data = []
        mock_supabase_chain.execute.return_value = mock_result

        result = get_coverages(repo_id=repo_id, filenames=filenames)

        assert not result
        mock_supabase_chain.eq.assert_called_once_with("repo_id", repo_id)
        mock_supabase_chain.in_.assert_called_once_with("full_path", filenames)

    def test_get_coverages_with_none_values_in_data(self, mock_supabase_chain):
        """Test coverage retrieval when some fields have None values."""
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

        result = get_coverages(repo_id=repo_id, filenames=filenames)

        assert len(result) == 1
        assert result["src/partial.py"]["line_coverage"] == 50.0
        assert result["src/partial.py"]["function_coverage"] is None
        assert result["src/partial.py"]["branch_coverage"] == 60.0
        assert result["src/partial.py"]["package_name"] is None

    def test_get_coverages_return_type_cast(
        self, mock_supabase_chain, sample_coverage_data
    ):
        """Test that the return values are properly cast to Coverages type."""
        mock_result = Mock()
        mock_result.data = sample_coverage_data
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 123
        filenames = ["src/main.py"]

        result = get_coverages(repo_id=repo_id, filenames=filenames)

        assert isinstance(result, dict)
        assert isinstance(result["src/main.py"], dict)
        assert "full_path" in result["src/main.py"]
        assert "line_coverage" in result["src/main.py"]

    def test_get_coverages_large_filenames_list(self, mock_supabase_chain):
        """Test coverage retrieval with a large number of filenames."""
        large_filenames = [f"src/file_{i}.py" for i in range(100)]
        mock_result = Mock()
        mock_result.data = []
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 123

        result = get_coverages(repo_id=repo_id, filenames=large_filenames)

        assert not result
        mock_supabase_chain.in_.assert_called_once_with("full_path", large_filenames)

    def test_get_coverages_duplicate_filenames(
        self, mock_supabase_chain, sample_coverage_data
    ):
        """Test coverage retrieval with duplicate filenames in the list."""
        mock_result = Mock()
        mock_result.data = [sample_coverage_data[0]]
        mock_supabase_chain.execute.return_value = mock_result

        repo_id = 123
        filenames = ["src/main.py", "src/main.py", "src/main.py"]

        result = get_coverages(repo_id=repo_id, filenames=filenames)

        assert len(result) == 1
        assert "src/main.py" in result
        mock_supabase_chain.in_.assert_called_once_with("full_path", filenames)

    def test_get_coverages_character_batching(self, mock_supabase):
        """Test that batching occurs based on character count."""
        long_filenames = [
            f"src/very/long/path/to/deeply/nested/component/with/many/extra/folders/to/exceed/the/character/limit/easily/file{i:04d}.tsx"
            for i in range(180)
        ]

        mock_chain = Mock()
        mock_supabase.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.in_.return_value = mock_chain

        mock_result = Mock()
        mock_result.data = []
        mock_chain.execute.return_value = mock_result

        repo_id = 123

        get_coverages(repo_id=repo_id, filenames=long_filenames)

        assert mock_chain.execute.call_count == 2
        assert mock_chain.in_.call_count == 2

        first_batch = mock_chain.in_.call_args_list[0][0][1]
        second_batch = mock_chain.in_.call_args_list[1][0][1]

        assert len(first_batch) + len(second_batch) == 180
        assert set(first_batch + second_batch) == set(long_filenames)

    def test_get_coverages_exact_character_limit(self, mock_supabase):
        """Test that we correctly handle queries near the 25,036 character limit."""
        mock_chain = Mock()
        mock_supabase.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.in_.return_value = mock_chain
        mock_result = Mock()
        mock_result.data = []
        mock_chain.execute.return_value = mock_result

        filenames_under = [
            "a" * 195 for _ in range(100)
        ]

        get_coverages(repo_id=123, filenames=filenames_under)
        assert mock_chain.execute.call_count == 1

        mock_chain.reset_mock()

        filenames_over = [
            "b" * 215 for _ in range(100)
        ]

        get_coverages(repo_id=123, filenames=filenames_over)
        assert mock_chain.execute.call_count == 2

    def test_get_coverages_agent_zx_scenario(self, mock_supabase):
        """Test the exact AGENT-ZX error scenario with many long filenames."""
        filenames = [
            "src/createGenericServer.ts",
            "src/features.ts",
            "src/global.ts",
            "src/index.ts",
            "src/raw-loader.d.ts",
            "src/resolvers.ts",
            "src/sentry.ts",
            "src/context/getSecrets.ts",
            "src/context/index.ts",
            "src/context/logger.ts",
            "src/context/mongodb.ts",
        ] + [f"src/context/amTrust/file{i:04d}.ts" for i in range(600)]

        mock_chain = Mock()
        mock_supabase.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.in_.return_value = mock_chain
        mock_result = Mock()
        mock_result.data = []
        mock_chain.execute.return_value = mock_result

        result = get_coverages(repo_id=297717337, filenames=filenames)

        assert mock_chain.execute.call_count == 2
        assert isinstance(result, dict)

    def test_get_coverages_mixed_filename_lengths(self, mock_supabase):
        """Test batching with mixed short and long filenames."""
        filenames = (
            ["a.py"] * 100
            + ["src/medium/path/file.js"] * 100
            + ["src/very/long/path/to/deeply/nested/component/file.tsx"]
            * 100
        )

        mock_chain = Mock()
        mock_supabase.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.in_.return_value = mock_chain
        mock_result = Mock()
        mock_result.data = []
        mock_chain.execute.return_value = mock_result

        result = get_coverages(repo_id=123, filenames=filenames)

        assert mock_chain.execute.call_count == 1
        assert isinstance(result, dict)

    def test_get_coverages_single_very_long_filename_exceeds_limit(self, mock_supabase):
        """Test edge case where a single filename exceeds the character limit."""
        very_long_filename = "src/" + "x" * 25000 + ".py"

        mock_chain = Mock()
        mock_supabase.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.in_.return_value = mock_chain
        mock_result = Mock()
        mock_result.data = []
        mock_chain.execute.return_value = mock_result

        result = get_coverages(repo_id=123, filenames=[very_long_filename])

        assert mock_chain.execute.call_count == 1
        assert isinstance(result, dict)
        mock_chain.in_.assert_called_once_with("full_path", [very_long_filename])

    def test_get_coverages_empty_batch_condition(self, mock_supabase):
        """Test the edge case where current_chars + filename_chars > MAX_CHARS but batch is empty."""
        long_filename = "src/" + "x" * 19950 + ".py"
        normal_filename = "src/normal.py"

        mock_chain = Mock()
        mock_supabase.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.in_.return_value = mock_chain
        mock_result = Mock()
        mock_result.data = []
        mock_chain.execute.return_value = mock_result

        result = get_coverages(repo_id=123, filenames=[long_filename, normal_filename])

        assert mock_chain.execute.call_count == 2
        assert isinstance(result, dict)

    def test_get_coverages_batch_reset_after_processing(self, mock_supabase):
        """Test that batch is properly reset after processing a batch."""
        batch1_files = [
            "src/" + "x" * 9950 + f"_{i}.py" for i in range(2)
        ]
        batch2_files = [
            "src/small.py"
        ]

        all_files = batch1_files + batch2_files

        mock_chain = Mock()
        mock_supabase.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.in_.return_value = mock_chain
        mock_result = Mock()
        mock_result.data = []
        mock_chain.execute.return_value = mock_result

        result = get_coverages(repo_id=123, filenames=all_files)

        assert mock_chain.execute.call_count == 2
        assert isinstance(result, dict)

        first_batch_call = mock_chain.in_.call_args_list[0][0][1]
        second_batch_call = mock_chain.in_.call_args_list[1][0][1]

        assert len(first_batch_call) == 1
        assert first_batch_call[0] == batch1_files[0]
        assert len(second_batch_call) == 2
        assert batch1_files[1] in second_batch_call
        assert "src/small.py" in second_batch_call

    def test_get_coverages_final_batch_processing(self, mock_supabase):
        """Test that the final batch is processed correctly when it exists."""
        filenames = [f"src/file_{i}.py" for i in range(10)]

        mock_chain = Mock()
        mock_supabase.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.in_.return_value = mock_chain
        mock_result = Mock()
        mock_result.data = []
        mock_chain.execute.return_value = mock_result

        result = get_coverages(repo_id=123, filenames=filenames)

        assert mock_chain.execute.call_count == 1
        assert isinstance(result, dict)
        mock_chain.in_.assert_called_once_with("full_path", filenames)

    def test_get_coverages_multiple_batches_with_data(
        self, mock_supabase, sample_coverage_data
    ):
        """Test that data from multiple batches is correctly combined."""
        long_filenames = [
            f"src/very/long/path/to/deeply/nested/component/with/many/extra/folders/to/exceed/the/character/limit/easily/file{i:04d}.tsx"
            for i in range(180)
        ]

        mock_chain = Mock()
        mock_supabase.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.in_.return_value = mock_chain

        batch1_data = [sample_coverage_data[0]]
        batch2_data = [sample_coverage_data[1]]

        mock_results = [Mock(), Mock()]
        mock_results[0].data = batch1_data
        mock_results[1].data = batch2_data
        mock_chain.execute.side_effect = mock_results

        result = get_coverages(repo_id=123, filenames=long_filenames)

        assert mock_chain.execute.call_count == 2
        assert len(result) == 2
        assert "src/main.py" in result
        assert "src/utils.py" in result

    def test_get_coverages_character_counting_accuracy(self, mock_supabase):
        """Test that character counting includes quotes and commas correctly."""
        filenames = [
            "a" * 100 for _ in range(190)
        ]

        mock_chain = Mock()
        mock_supabase.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.in_.return_value = mock_chain
        mock_result = Mock()
        mock_result.data = []
        mock_chain.execute.return_value = mock_result

        result = get_coverages(repo_id=123, filenames=filenames)

        assert mock_chain.execute.call_count == 1
        assert isinstance(result, dict)

    def test_get_coverages_overhead_calculation(self, mock_supabase):
        """Test that the OVERHEAD constant is properly accounted for in batching."""
        filenames = ["x" * 97 for _ in range(199)]

        mock_chain = Mock()
        mock_supabase.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.in_.return_value = mock_chain
        mock_result = Mock()
        mock_result.data = []
        mock_chain.execute.return_value = mock_result

        result = get_coverages(repo_id=123, filenames=filenames)

        assert mock_chain.execute.call_count == 1
        assert isinstance(result, dict)

    def test_get_coverages_batch_with_none_data_in_middle(self, mock_supabase):
        """Test that None data in middle batch doesn't affect final result."""
        long_filenames = [
            f"src/very/long/path/to/deeply/nested/component/with/many/extra/folders/to/exceed/the/character/limit/easily/file{i:04d}.tsx"
            for i in range(180)
        ]

        mock_chain = Mock()
        mock_supabase.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.in_.return_value = mock_chain

        mock_results = [Mock(), Mock()]
        mock_results[0].data = None
        mock_results[1].data = []
        mock_chain.execute.side_effect = mock_results

        result = get_coverages(repo_id=123, filenames=long_filenames)

        assert mock_chain.execute.call_count == 2
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_get_coverages_batch_with_empty_data_in_middle(self, mock_supabase):
        """Test that empty data in middle batch doesn't affect final result."""
        long_filenames = [
            f"src/very/long/path/to/deeply/nested/component/with/many/extra/folders/to/exceed/the/character/limit/easily/file{i:04d}.tsx"
            for i in range(180)
        ]

        mock_chain = Mock()
        mock_supabase.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.in_.return_value = mock_chain

        mock_results = [Mock(), Mock()]
        mock_results[0].data = []
        mock_results[1].data = []
        mock_chain.execute.side_effect = mock_results

        result = get_coverages(repo_id=123, filenames=long_filenames)

        assert mock_chain.execute.call_count == 2
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_get_coverages_exception_in_first_batch(self, mock_supabase):
        """Test that exception in first batch is handled gracefully."""
        long_filenames = [
            f"src/very/long/path/to/deeply/nested/component/with/many/extra/folders/to/exceed/the/character/limit/easily/file{i:04d}.tsx"
            for i in range(180)
        ]

        mock_chain = Mock()
        mock_supabase.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.in_.return_value = mock_chain
        mock_chain.execute.side_effect = Exception("Database error")

        result = get_coverages(repo_id=123, filenames=long_filenames)

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_get_coverages_exception_in_final_batch(self, mock_supabase):
        """Test that exception in final batch is handled gracefully."""
        long_filenames = [
            f"src/very/long/path/to/deeply/nested/component/with/many/extra/folders/to/exceed/the/character/limit/easily/file{i:04d}.tsx"
            for i in range(180)
        ]

        mock_chain = Mock()
        mock_supabase.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.in_.return_value = mock_chain

        mock_results = [Mock(), Exception("Database error in final batch")]
        mock_results[0].data = []
        mock_chain.execute.side_effect = mock_results

        result = get_coverages(repo_id=123, filenames=long_filenames)

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_get_coverages_all_batches_processed_in_loop(self, mock_supabase):
        """Test scenario where all files are processed in batches during the loop."""
        filenames = [
            "src/" + "x" * 9950 + f"_{i}.py" for i in range(4)
        ]

        mock_chain = Mock()
        mock_supabase.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.in_.return_value = mock_chain
        mock_result = Mock()
        mock_result.data = []
        mock_chain.execute.return_value = mock_result

        result = get_coverages(repo_id=123, filenames=filenames)

        assert mock_chain.execute.call_count == 4
        assert isinstance(result, dict)

    def test_get_coverages_final_batch_with_data(
        self, mock_supabase_chain, sample_coverage_data
    ):
        """Test that final batch correctly processes data."""
        mock_result = Mock()
        mock_result.data = sample_coverage_data
        mock_supabase_chain.execute.return_value = mock_result

        filenames = ["src/main.py", "src/utils.py"]

        result = get_coverages(repo_id=123, filenames=filenames)

        assert len(result) == 2
        assert "src/main.py" in result
        assert "src/utils.py" in result
        mock_supabase_chain.execute.assert_called_once()

    def test_get_coverages_final_batch_with_none_data(self, mock_supabase_chain):
        """Test that final batch handles None data correctly."""
        mock_result = Mock()
        mock_result.data = None
        mock_supabase_chain.execute.return_value = mock_result

        filenames = ["src/test.py"]

        result = get_coverages(repo_id=123, filenames=filenames)

        assert len(result) == 0
        mock_supabase_chain.execute.assert_called_once()

    def test_get_coverages_final_batch_with_empty_data(self, mock_supabase_chain):
        """Test that final batch handles empty data correctly."""
        mock_result = Mock()
        mock_result.data = []
        mock_supabase_chain.execute.return_value = mock_result

        filenames = ["src/test.py"]

        result = get_coverages(repo_id=123, filenames=filenames)

        assert len(result) == 0
        mock_supabase_chain.execute.assert_called_once()


class TestGetCoveragesIntegration:
    """Integration tests that hit the actual Supabase database."""

    @pytest.mark.skipif(bool(os.getenv("CI")), reason="Skip integration tests in CI")
    def test_find_exact_character_limit(self):
        """Integration test to find the exact character limit for Supabase queries."""
        logging.disable(logging.ERROR)

        try:
            low, high = 20000, 30000
            max_working = 0

            while low <= high:
                mid = (low + high) // 2

                overhead = 60
                filename_length = mid - overhead
                filename = "x" * filename_length

                try:
                    supabase.table("coverages").select("*").eq("repo_id", 999999).in_(
                        "full_path", [filename]
                    ).execute()
                    max_working = mid
                    low = mid + 1
                except Exception as e:
                    if (
                        "400" in str(e)
                        or "Bad Request" in str(e)
                        or "JSON could not be generated" in str(e)
                        or "APIError" in str(e)
                    ):
                        high = mid - 1
                    else:
                        high = mid - 1

            assert (
                25000 <= max_working <= 26000
            ), f"Expected limit around 25,036, got {max_working}"

        finally:
            logging.disable(logging.NOTSET)

    @pytest.mark.skipif(bool(os.getenv("CI")), reason="Skip integration tests in CI")
    def test_get_coverages_with_realistic_large_batch(self):
        """Test that get_coverages can handle realistic large batches from real repos."""
        filenames = [
            "src/createGenericServer.ts",
            "src/features.ts",
            "src/global.ts",
            "src/index.ts",
            "src/raw-loader.d.ts",
            "src/resolvers.ts",
            "src/sentry.ts",
            "src/context/getSecrets.ts",
            "src/context/index.ts",
            "src/context/logger.ts",
            "src/context/mongodb.ts",
        ] + [
            f"src/context/amTrust/file{i}.ts" for i in range(100)
        ]

        result = get_coverages(repo_id=999999, filenames=filenames)
        assert isinstance(result, dict)
