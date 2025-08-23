from unittest.mock import patch, MagicMock
import pytest
from datetime import datetime

from schemas.supabase.fastapi.schema_public_latest import RepoCoverageInsert
from services.supabase.repo_coverage.upsert_repo_coverage import upsert_repo_coverage


@pytest.fixture
def sample_repo_coverage_data():
    """Fixture providing sample RepoCoverageInsert data."""
    return RepoCoverageInsert(
        branch_name="main",
        created_by="test-user",
        owner_id=123456,
        owner_name="test-owner",
        repo_id=789012,
        repo_name="test-repo",
        branch_coverage=85.5,
        function_coverage=90.0,
        line_coverage=88.2,
        statement_coverage=87.8,
        primary_language="Python",
        created_at=datetime(2023, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def minimal_repo_coverage_data():
    """Fixture providing minimal required RepoCoverageInsert data."""
    return RepoCoverageInsert(
        branch_name="develop",
        created_by="minimal-user",
        owner_id=111111,
        owner_name="minimal-owner",
        repo_id=222222,
        repo_name="minimal-repo",
    )


@pytest.fixture
def mock_supabase_client():
    """Fixture to mock the supabase client."""
    with patch("services.supabase.repo_coverage.upsert_repo_coverage.supabase") as mock:
        yield mock


class TestUpsertRepoCoverage:
    def test_successful_upsert_with_full_data(
        self, mock_supabase_client, sample_repo_coverage_data
    ):
        """Test successful upsert operation with complete data."""
        # Setup
        expected_data = [{"id": 1, "repo_name": "test-repo"}]
        mock_result = MagicMock()
        mock_result.data = expected_data

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = (
            mock_result
        )

        # Execute
        result = upsert_repo_coverage(sample_repo_coverage_data)

        # Verify
        assert result == expected_data
        mock_supabase_client.table.assert_called_once_with("repo_coverage")

        # Verify the insert was called with model_dump(exclude_none=True)
        expected_insert_data = sample_repo_coverage_data.model_dump(exclude_none=True)
        mock_supabase_client.table.return_value.insert.assert_called_once_with(
            expected_insert_data
        )
        mock_supabase_client.table.return_value.insert.return_value.execute.assert_called_once()

    def test_successful_upsert_with_minimal_data(
        self, mock_supabase_client, minimal_repo_coverage_data
    ):
        """Test successful upsert operation with minimal required data."""
        # Setup
        expected_data = [{"id": 2, "repo_name": "minimal-repo"}]
        mock_result = MagicMock()
        mock_result.data = expected_data

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = (
            mock_result
        )

        # Execute
        result = upsert_repo_coverage(minimal_repo_coverage_data)

        # Verify
        assert result == expected_data
        mock_supabase_client.table.assert_called_once_with("repo_coverage")

        # Verify the insert was called with model_dump(exclude_none=True)
        expected_insert_data = minimal_repo_coverage_data.model_dump(exclude_none=True)
        mock_supabase_client.table.return_value.insert.assert_called_once_with(
            expected_insert_data
        )
        mock_supabase_client.table.return_value.insert.return_value.execute.assert_called_once()

    def test_upsert_with_none_values_excluded(self, mock_supabase_client):
        """Test that None values are properly excluded from the insert data."""
        # Setup
        coverage_data = RepoCoverageInsert(
            branch_name="feature-branch",
            created_by="test-user",
            owner_id=123456,
            owner_name="test-owner",
            repo_id=789012,
            repo_name="test-repo",
            branch_coverage=None,  # This should be excluded
            function_coverage=None,  # This should be excluded
            line_coverage=75.0,
            statement_coverage=None,  # This should be excluded
            primary_language=None,  # This should be excluded
        )

        expected_data = [{"id": 3, "repo_name": "test-repo"}]
        mock_result = MagicMock()
        mock_result.data = expected_data

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = (
            mock_result
        )

        # Execute
        result = upsert_repo_coverage(coverage_data)

        # Verify
        assert result == expected_data

        # Verify that None values were excluded
        call_args = mock_supabase_client.table.return_value.insert.call_args[0][0]
        assert "branch_coverage" not in call_args
        assert "function_coverage" not in call_args
        assert "statement_coverage" not in call_args
        assert "primary_language" not in call_args
        assert call_args["line_coverage"] == 75.0

    def test_empty_result_data(self, mock_supabase_client, sample_repo_coverage_data):
        """Test handling of empty result data."""
        # Setup
        mock_result = MagicMock()
        mock_result.data = []

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = (
            mock_result
        )

        # Execute
        result = upsert_repo_coverage(sample_repo_coverage_data)

        # Verify
        assert result == []
        mock_supabase_client.table.assert_called_once_with("repo_coverage")

    def test_null_result_data(self, mock_supabase_client, sample_repo_coverage_data):
        """Test handling of null result data."""
        # Setup
        mock_result = MagicMock()
        mock_result.data = None

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = (
            mock_result
        )

        # Execute
        result = upsert_repo_coverage(sample_repo_coverage_data)

        # Verify
        assert result is None
        mock_supabase_client.table.assert_called_once_with("repo_coverage")

    def test_exception_handling_returns_none(
        self, mock_supabase_client, sample_repo_coverage_data
    ):
        """Test that exceptions are handled and None is returned as default."""
        # Setup - make the supabase call raise an exception
        mock_supabase_client.table.side_effect = Exception("Database connection error")

        # Execute
        result = upsert_repo_coverage(sample_repo_coverage_data)

        # Verify - should return None due to handle_exceptions decorator
        assert result is None

    def test_supabase_operation_chain(
        self, mock_supabase_client, sample_repo_coverage_data
    ):
        """Test the complete supabase operation chain."""
        # Setup
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [{"id": 1}]

        mock_supabase_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_result

        # Execute
        result = upsert_repo_coverage(sample_repo_coverage_data)

        # Verify the complete chain
        mock_supabase_client.table.assert_called_once_with("repo_coverage")
        mock_table.insert.assert_called_once()
        mock_insert.execute.assert_called_once()
        assert result == [{"id": 1}]
