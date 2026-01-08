# pylint: disable=redefined-outer-name

# Standard imports
from unittest.mock import patch, MagicMock

# Third party imports
import pytest

# Local imports
from schemas.supabase.types import CoveragesInsert
from services.supabase.coverages.upsert_coverages import upsert_coverages


@pytest.fixture
def mock_supabase():
    """Mock the supabase client."""
    with patch("services.supabase.coverages.upsert_coverages.supabase") as mock:
        yield mock


@pytest.fixture
def sample_coverage_record():
    """Create a sample coverage record for testing."""
    record: CoveragesInsert = {
        "repo_id": 123,
        "full_path": "src/test.py",
        "owner_id": 456,
        "level": "file",
        "line_coverage": 85.5,
        "function_coverage": 90.0,
        "branch_coverage": 75.0,
        "created_by": "test_user",
        "updated_by": "test_user",
    }
    return record


@pytest.fixture
def sample_coverage_records(sample_coverage_record):
    """Create multiple sample coverage records for testing."""
    second_record: CoveragesInsert = {
        "repo_id": 123,
        "full_path": "src/another.py",
        "owner_id": 456,
        "level": "file",
        "line_coverage": 70.0,
        "function_coverage": 80.0,
        "branch_coverage": 65.0,
        "created_by": "test_user",
        "updated_by": "test_user",
    }
    return [sample_coverage_record, second_record]


class TestUpsertCoverages:
    """Test cases for upsert_coverages function."""

    def test_upsert_coverages_empty_list_returns_none(self, mock_supabase):
        """Test that empty coverage records list returns None."""
        # Arrange
        coverage_records = []

        # Act
        result = upsert_coverages(coverage_records)

        # Assert
        assert result is None
        mock_supabase.table.assert_not_called()

    def test_upsert_coverages_single_record_success(
        self, mock_supabase, sample_coverage_record
    ):
        """Test successful upsert with single coverage record."""
        # Arrange
        coverage_records = [sample_coverage_record]
        mock_result = MagicMock()
        mock_result.data = [{"id": 1, "repo_id": 123, "full_path": "src/test.py"}]

        mock_supabase.table.return_value.upsert.return_value.execute.return_value = (
            mock_result
        )

        # Act
        result = upsert_coverages(coverage_records)

        # Assert
        assert result == mock_result.data
        mock_supabase.table.assert_called_once_with("coverages")
        mock_supabase.table.return_value.upsert.assert_called_once_with(
            coverage_records, on_conflict="repo_id,full_path", default_to_null=False
        )
        mock_supabase.table.return_value.upsert.return_value.execute.assert_called_once()

    def test_upsert_coverages_multiple_records_success(
        self, mock_supabase, sample_coverage_records
    ):
        """Test successful upsert with multiple coverage records."""
        # Arrange
        mock_result = MagicMock()
        mock_result.data = [
            {"id": 1, "repo_id": 123, "full_path": "src/test.py"},
            {"id": 2, "repo_id": 123, "full_path": "src/another.py"},
        ]

        mock_supabase.table.return_value.upsert.return_value.execute.return_value = (
            mock_result
        )

        # Act
        result = upsert_coverages(sample_coverage_records)

        # Assert
        assert result == mock_result.data
        mock_supabase.table.assert_called_once_with("coverages")
        mock_supabase.table.return_value.upsert.assert_called_once_with(
            sample_coverage_records,
            on_conflict="repo_id,full_path",
            default_to_null=False,
        )
        mock_supabase.table.return_value.upsert.return_value.execute.assert_called_once()

    def test_upsert_coverages_with_conflict_resolution(
        self, mock_supabase, sample_coverage_record
    ):
        """Test that upsert uses correct conflict resolution parameters."""
        # Arrange
        coverage_records = [sample_coverage_record]
        mock_result = MagicMock()
        mock_result.data = [{"id": 1, "repo_id": 123, "full_path": "src/test.py"}]

        mock_supabase.table.return_value.upsert.return_value.execute.return_value = (
            mock_result
        )

        # Act
        upsert_coverages(coverage_records)

        # Assert
        mock_supabase.table.return_value.upsert.assert_called_once_with(
            coverage_records, on_conflict="repo_id,full_path", default_to_null=False
        )

    def test_upsert_coverages_returns_result_data(
        self, mock_supabase, sample_coverage_record
    ):
        """Test that function returns result.data from the database operation."""
        # Arrange
        coverage_records = [sample_coverage_record]
        expected_data = [
            {
                "id": 1,
                "repo_id": 123,
                "full_path": "src/test.py",
                "line_coverage": 85.5,
                "function_coverage": 90.0,
                "branch_coverage": 75.0,
            }
        ]
        mock_result = MagicMock()
        mock_result.data = expected_data

        mock_supabase.table.return_value.upsert.return_value.execute.return_value = (
            mock_result
        )

        # Act
        result = upsert_coverages(coverage_records)

        # Assert
        assert result == expected_data

    def test_upsert_coverages_empty_result_data(
        self, mock_supabase, sample_coverage_record
    ):
        """Test handling when result.data is empty."""
        # Arrange
        coverage_records = [sample_coverage_record]
        mock_result = MagicMock()
        mock_result.data = []

        mock_supabase.table.return_value.upsert.return_value.execute.return_value = (
            mock_result
        )

        # Act
        result = upsert_coverages(coverage_records)

        # Assert
        assert result == []

    def test_upsert_coverages_none_result_data(
        self, mock_supabase, sample_coverage_record
    ):
        """Test handling when result.data is None."""
        # Arrange
        coverage_records = [sample_coverage_record]
        mock_result = MagicMock()
        mock_result.data = None

        mock_supabase.table.return_value.upsert.return_value.execute.return_value = (
            mock_result
        )

        # Act
        result = upsert_coverages(coverage_records)

        # Assert
        assert result is None

    def test_upsert_coverages_method_chaining(
        self, mock_supabase, sample_coverage_record
    ):
        """Test that the method chaining works correctly."""
        # Arrange
        coverage_records = [sample_coverage_record]
        mock_table = MagicMock()
        mock_upsert = MagicMock()
        MagicMock()
        mock_result = MagicMock()
        mock_result.data = [{"id": 1}]

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = mock_result

        # Act
        result = upsert_coverages(coverage_records)

        # Assert
        mock_supabase.table.assert_called_once_with("coverages")
        mock_table.upsert.assert_called_once_with(
            coverage_records, on_conflict="repo_id,full_path", default_to_null=False
        )
        mock_upsert.execute.assert_called_once()
        assert result == mock_result.data

    @patch("services.supabase.coverages.upsert_coverages.handle_exceptions")
    def test_upsert_coverages_has_exception_handler(
        self, mock_handle_exceptions, sample_coverage_record
    ):
        """Test that the function is decorated with handle_exceptions."""
        # Arrange

        # The decorator should have been applied during import
        # We can verify by checking if the function has the expected behavior

        # Act & Assert
        # This test verifies that the decorator was applied during module import
        # The actual exception handling behavior is tested by the decorator itself
        assert hasattr(upsert_coverages, "__wrapped__")

    def test_upsert_coverages_with_various_coverage_types(self, mock_supabase):
        """Test upsert with different types of coverage data."""
        # Arrange
        coverage_records: list[CoveragesInsert] = [
            {
                "repo_id": 123,
                "full_path": "src/file1.py",
                "owner_id": 456,
                "level": "file",
                "line_coverage": 100.0,
                "function_coverage": None,
                "branch_coverage": 0.0,
                "created_by": "test_user",
                "updated_by": "test_user",
            },
            {
                "repo_id": 123,
                "full_path": "src/file2.py",
                "owner_id": 456,
                "level": "directory",
                "line_coverage": None,
                "function_coverage": 50.5,
                "branch_coverage": None,
                "created_by": "test_user",
                "updated_by": "test_user",
            },
        ]
        mock_result = MagicMock()
        mock_result.data = [{"id": 1}, {"id": 2}]

        mock_supabase.table.return_value.upsert.return_value.execute.return_value = (
            mock_result
        )

        # Act
        result = upsert_coverages(coverage_records)

        # Assert
        assert result == mock_result.data
        mock_supabase.table.return_value.upsert.assert_called_once_with(
            coverage_records, on_conflict="repo_id,full_path", default_to_null=False
        )

    def test_upsert_coverages_with_different_repo_ids(self, mock_supabase):
        """Test upsert with coverage records from different repositories."""
        # Arrange
        coverage_records: list[CoveragesInsert] = [
            {
                "repo_id": 123,
                "full_path": "src/test.py",
                "owner_id": 456,
                "level": "file",
                "line_coverage": 85.0,
                "created_by": "user1",
                "updated_by": "user1",
            },
            {
                "repo_id": 789,
                "full_path": "src/test.py",  # Same path, different repo
                "owner_id": 456,
                "level": "file",
                "line_coverage": 90.0,
                "created_by": "user2",
                "updated_by": "user2",
            },
        ]
        mock_result = MagicMock()
        mock_result.data = [{"id": 1}, {"id": 2}]

        mock_supabase.table.return_value.upsert.return_value.execute.return_value = (
            mock_result
        )

        # Act
        result = upsert_coverages(coverage_records)

        # Assert
        assert result == mock_result.data
        mock_supabase.table.return_value.upsert.assert_called_once_with(
            coverage_records, on_conflict="repo_id,full_path", default_to_null=False
        )

    def test_upsert_coverages_preserves_input_data_structure(
        self, mock_supabase, sample_coverage_records
    ):
        """Test that the function doesn't modify the input data structure."""
        # Arrange
        original_records = [record.copy() for record in sample_coverage_records]
        mock_result = MagicMock()
        mock_result.data = [{"id": 1}, {"id": 2}]

        mock_supabase.table.return_value.upsert.return_value.execute.return_value = (
            mock_result
        )

        # Act
        upsert_coverages(sample_coverage_records)

        # Assert
        assert sample_coverage_records == original_records

    def test_upsert_coverages_table_name_is_correct(
        self, mock_supabase, sample_coverage_record
    ):
        """Test that the correct table name is used."""
        # Arrange
        coverage_records = [sample_coverage_record]
        mock_result = MagicMock()
        mock_result.data = [{"id": 1}]

        mock_supabase.table.return_value.upsert.return_value.execute.return_value = (
            mock_result
        )

        # Act
        upsert_coverages(coverage_records)

        # Assert
        mock_supabase.table.assert_called_once_with("coverages")

    def test_upsert_coverages_default_to_null_parameter(
        self, mock_supabase, sample_coverage_record
    ):
        """Test that default_to_null parameter is set correctly."""
        # Arrange
        coverage_records = [sample_coverage_record]
        mock_result = MagicMock()
        mock_result.data = [{"id": 1}]

        mock_supabase.table.return_value.upsert.return_value.execute.return_value = (
            mock_result
        )

        # Act
        upsert_coverages(coverage_records)

        # Assert
        mock_supabase.table.return_value.upsert.assert_called_once_with(
            coverage_records, on_conflict="repo_id,full_path", default_to_null=False
        )

    def test_upsert_coverages_large_dataset(self, mock_supabase):
        """Test upsert with a large number of coverage records."""
        # Arrange
        coverage_records = []
        for i in range(100):
            coverage_records.append(
                {
                    "repo_id": 123,
                    "full_path": f"src/file_{i}.py",
                    "owner_id": 456,
                    "level": "file",
                    "line_coverage": float(i),
                    "function_coverage": float(i + 10),
                    "branch_coverage": float(i + 20),
                    "created_by": "test_user",
                    "updated_by": "test_user",
                }
            )

        mock_result = MagicMock()
        mock_result.data = [{"id": i} for i in range(1, 101)]

        mock_supabase.table.return_value.upsert.return_value.execute.return_value = (
            mock_result
        )

        # Act
        result = upsert_coverages(coverage_records)

        # Assert
        assert result == mock_result.data
        assert result is not None and len(result) == 100
        mock_supabase.table.return_value.upsert.assert_called_once_with(
            coverage_records, on_conflict="repo_id,full_path", default_to_null=False
        )
