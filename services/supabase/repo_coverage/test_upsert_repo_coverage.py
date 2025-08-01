from unittest.mock import patch, MagicMock
import pytest
from schemas.supabase.fastapi.schema_public_latest import RepoCoverageInsert
from services.supabase.repo_coverage.upsert_repo_coverage import upsert_repo_coverage


@pytest.fixture
def mock_supabase():
    """Fixture to provide a mocked supabase client."""
    with patch("services.supabase.repo_coverage.upsert_repo_coverage.supabase") as mock:
        yield mock


@pytest.fixture
def sample_coverage_data():
    """Fixture providing sample RepoCoverageInsert data."""
    return RepoCoverageInsert(
        owner_id=123456,
        owner_name="test-owner",
        repo_id=789012,
        repo_name="test-repo",
        branch_name="main",
        created_by="test-user",
        line_coverage=85.5,
        statement_coverage=82.3,
        function_coverage=90.0,
        branch_coverage=75.8,
        primary_language="python"
    )


@pytest.fixture
def minimal_coverage_data():
    """Fixture providing minimal required RepoCoverageInsert data."""
    return RepoCoverageInsert(
        owner_id=123456,
        owner_name="test-owner",
        repo_id=789012,
        repo_name="test-repo",
        branch_name="main",
        created_by="test-user"
    )


def test_upsert_repo_coverage_success(mock_supabase, sample_coverage_data):
    """Test successful upsert operation with complete data."""
    # Arrange
    mock_result = MagicMock()
    mock_result.data = [{"id": 1, "owner_id": 123456, "repo_id": 789012}]
    
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
    
    # Act
    result = upsert_repo_coverage(sample_coverage_data)
    
    # Assert
    mock_supabase.table.assert_called_once_with("repo_coverage")
    mock_supabase.table.return_value.insert.assert_called_once()
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()
    
    # Verify the data passed to insert
    insert_call_args = mock_supabase.table.return_value.insert.call_args[0][0]
    assert insert_call_args["owner_id"] == 123456
    assert insert_call_args["owner_name"] == "test-owner"
    assert insert_call_args["repo_id"] == 789012
    assert insert_call_args["repo_name"] == "test-repo"
    assert insert_call_args["branch_name"] == "main"
    assert insert_call_args["created_by"] == "test-user"
    assert insert_call_args["line_coverage"] == 85.5
    assert insert_call_args["statement_coverage"] == 82.3
    assert insert_call_args["function_coverage"] == 90.0
    assert insert_call_args["branch_coverage"] == 75.8
    assert insert_call_args["primary_language"] == "python"
    
    assert result == [{"id": 1, "owner_id": 123456, "repo_id": 789012}]


def test_upsert_repo_coverage_minimal_data(mock_supabase, minimal_coverage_data):
    """Test upsert operation with minimal required data."""
    # Arrange
    mock_result = MagicMock()
    mock_result.data = [{"id": 2, "owner_id": 123456, "repo_id": 789012}]
    
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
    
    # Act
    result = upsert_repo_coverage(minimal_coverage_data)
    
    # Assert
    mock_supabase.table.assert_called_once_with("repo_coverage")
    
    # Verify the data passed to insert excludes None values
    insert_call_args = mock_supabase.table.return_value.insert.call_args[0][0]
    assert insert_call_args["owner_id"] == 123456
    assert insert_call_args["owner_name"] == "test-owner"
    assert insert_call_args["repo_id"] == 789012
    assert insert_call_args["repo_name"] == "test-repo"
    assert insert_call_args["branch_name"] == "main"
    assert insert_call_args["created_by"] == "test-user"
    
    # Optional fields should not be present when None
    assert "line_coverage" not in insert_call_args
    assert "statement_coverage" not in insert_call_args
    assert "function_coverage" not in insert_call_args
    assert "branch_coverage" not in insert_call_args
    assert "primary_language" not in insert_call_args
    
    assert result == [{"id": 2, "owner_id": 123456, "repo_id": 789012}]


def test_upsert_repo_coverage_exclude_none_values(mock_supabase):
    """Test that model_dump excludes None values correctly."""
    # Arrange
    coverage_data = RepoCoverageInsert(
        owner_id=123456,
        owner_name="test-owner",
        repo_id=789012,
        repo_name="test-repo",
        branch_name="main",
        created_by="test-user",
        line_coverage=None,  # Explicitly set to None
        statement_coverage=50.0,
        function_coverage=None,  # Explicitly set to None
        branch_coverage=60.0,
        primary_language=None  # Explicitly set to None
    )
    
    mock_result = MagicMock()
    mock_result.data = [{"id": 3}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
    
    # Act
    result = upsert_repo_coverage(coverage_data)
    
    # Assert
    insert_call_args = mock_supabase.table.return_value.insert.call_args[0][0]
    
    # None values should be excluded
    assert "line_coverage" not in insert_call_args
    assert "function_coverage" not in insert_call_args
    assert "primary_language" not in insert_call_args
    
    # Non-None values should be included
    assert insert_call_args["statement_coverage"] == 50.0
    assert insert_call_args["branch_coverage"] == 60.0
    
    assert result == [{"id": 3}]


def test_upsert_repo_coverage_empty_result_data(mock_supabase, sample_coverage_data):
    """Test handling when supabase returns empty data."""
    # Arrange
    mock_result = MagicMock()
    mock_result.data = []
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
    
    # Act
    result = upsert_repo_coverage(sample_coverage_data)
    
    # Assert
    assert result == []


def test_upsert_repo_coverage_none_result_data(mock_supabase, sample_coverage_data):
    """Test handling when supabase returns None data."""
    # Arrange
    mock_result = MagicMock()
    mock_result.data = None
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
    
    # Act
    result = upsert_repo_coverage(sample_coverage_data)
    
    # Assert
    assert result is None


def test_upsert_repo_coverage_handles_exception(mock_supabase, sample_coverage_data):
    """Test that function handles exceptions gracefully due to @handle_exceptions decorator."""
    # Arrange
    mock_supabase.table.side_effect = Exception("Database connection error")
    
    # Act
    result = upsert_repo_coverage(sample_coverage_data)
    
    # Assert
    # Function should return None due to @handle_exceptions decorator with default_return_value=None
    assert result is None
    mock_supabase.table.assert_called_once_with("repo_coverage")


def test_upsert_repo_coverage_supabase_chain_exception(mock_supabase, sample_coverage_data):
    """Test exception handling when supabase chain operations fail."""
    # Arrange
    mock_supabase.table.return_value.insert.side_effect = Exception("Insert operation failed")
    
    # Act
    result = upsert_repo_coverage(sample_coverage_data)
    
    # Assert
    assert result is None
    mock_supabase.table.assert_called_once_with("repo_coverage")
    mock_supabase.table.return_value.insert.assert_called_once()


def test_upsert_repo_coverage_execute_exception(mock_supabase, sample_coverage_data):
    """Test exception handling when execute operation fails."""
    # Arrange
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("Execute failed")
    
    # Act
    result = upsert_repo_coverage(sample_coverage_data)
    
    # Assert
    assert result is None
    mock_supabase.table.assert_called_once_with("repo_coverage")
    mock_supabase.table.return_value.insert.assert_called_once()
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_upsert_repo_coverage_with_zero_coverage_values(mock_supabase):
    """Test upsert operation with zero coverage values."""
    # Arrange
    coverage_data = RepoCoverageInsert(
        owner_id=123456,
        owner_name="test-owner",
        repo_id=789012,
        repo_name="test-repo",
        branch_name="main",
        created_by="test-user",
        line_coverage=0.0,
        statement_coverage=0.0,
        function_coverage=0.0,
        branch_coverage=0.0,
        primary_language="javascript"
    )
    
    mock_result = MagicMock()
    mock_result.data = [{"id": 4, "line_coverage": 0.0}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
    
    # Act
    result = upsert_repo_coverage(coverage_data)
    
    # Assert
    insert_call_args = mock_supabase.table.return_value.insert.call_args[0][0]
    assert insert_call_args["line_coverage"] == 0.0
    assert insert_call_args["statement_coverage"] == 0.0
    assert insert_call_args["function_coverage"] == 0.0
    assert insert_call_args["branch_coverage"] == 0.0
    assert insert_call_args["primary_language"] == "javascript"
    
    assert result == [{"id": 4, "line_coverage": 0.0}]
