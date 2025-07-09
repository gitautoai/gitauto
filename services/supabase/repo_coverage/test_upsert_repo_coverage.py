from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

from schemas.supabase.fastapi.schema_public_latest import RepoCoverageInsert
from services.supabase.repo_coverage.upsert_repo_coverage import upsert_repo_coverage


@pytest.fixture
def mock_supabase():
    """Fixture to provide a mocked supabase client."""
    with patch("services.supabase.repo_coverage.upsert_repo_coverage.supabase") as mock:
        # Create a mock result object
        mock_result = MagicMock()
        mock_result.data = []
        
        # Set up the method chain
        mock.table.return_value.insert.return_value.execute.return_value = mock_result
        
        yield mock


@pytest.fixture
def sample_coverage_data():
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
        primary_language="python"
    )


@pytest.fixture
def minimal_coverage_data():
    """Fixture providing minimal required RepoCoverageInsert data."""
    return RepoCoverageInsert(
        branch_name="develop",
        created_by="minimal-user",
        owner_id=111111,
        owner_name="minimal-owner",
        repo_id=222222,
        repo_name="minimal-repo"
    )


def test_upsert_repo_coverage_successful_insert(mock_supabase, sample_coverage_data):
    """Test successful repository coverage upsert operation."""
    # Arrange
    expected_data = [{"id": 1, "repo_id": 789012, "branch_name": "main"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = expected_data
    
    # Act
    result = upsert_repo_coverage(sample_coverage_data)
    
    # Assert
    assert result == expected_data
    mock_supabase.table.assert_called_with("repo_coverage")


def test_upsert_repo_coverage_with_minimal_data(mock_supabase, minimal_coverage_data):
    """Test upsert with minimal required fields only."""
    # Arrange
    expected_data = [{"id": 2, "repo_id": 222222, "branch_name": "develop"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = expected_data
    
    # Act
    result = upsert_repo_coverage(minimal_coverage_data)
    
    # Assert
    assert result == expected_data


def test_upsert_repo_coverage_model_dump_called_correctly(mock_supabase, sample_coverage_data):
    """Test that model_dump is called with exclude_none=True."""
    # Arrange
    expected_data = [{"id": 3}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = expected_data
    
    # Act
    with patch.object(sample_coverage_data, 'model_dump') as mock_model_dump:
        mock_model_dump.return_value = {"test": "data"}
        result = upsert_repo_coverage(sample_coverage_data)
    
    # Assert
    mock_model_dump.assert_called_once_with(exclude_none=True)
    mock_supabase.table.return_value.insert.assert_called_with({"test": "data"})


def test_upsert_repo_coverage_empty_result_data(mock_supabase, sample_coverage_data):
    """Test behavior when supabase returns empty data."""
    # Arrange
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = []
    
    # Act
    result = upsert_repo_coverage(sample_coverage_data)
    
    # Assert
    assert result == []


def test_upsert_repo_coverage_none_result_data(mock_supabase, sample_coverage_data):
    """Test behavior when supabase returns None data."""
    # Arrange
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = None
    
    # Act
    result = upsert_repo_coverage(sample_coverage_data)
    
    # Assert
    assert result is None


def test_upsert_repo_coverage_with_all_optional_fields(mock_supabase):
    """Test upsert with all optional fields populated."""
    # Arrange
    coverage_data = RepoCoverageInsert(
        id=999,
        branch_name="feature-branch",
        created_by="full-user",
        owner_id=333333,
        owner_name="full-owner",
        repo_id=444444,
        repo_name="full-repo",
        branch_coverage=95.5,
        created_at=datetime.now(),
        function_coverage=98.0,
        line_coverage=92.3,
        primary_language="javascript",
        statement_coverage=94.1
    )
    expected_data = [{"id": 999, "branch_name": "feature-branch"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = expected_data
    
    # Act
    result = upsert_repo_coverage(coverage_data)
    
    # Assert
    assert result == expected_data


def test_upsert_repo_coverage_exception_handling_returns_none(mock_supabase, sample_coverage_data):
    """Test that exceptions are handled and None is returned."""
    # Arrange
    mock_supabase.table.side_effect = Exception("Database connection error")
    
    # Act
    result = upsert_repo_coverage(sample_coverage_data)
    
    # Assert
    assert result is None


def test_upsert_repo_coverage_supabase_insert_exception(mock_supabase, sample_coverage_data):
    """Test handling of supabase insert exceptions."""
    # Arrange
    mock_supabase.table.return_value.insert.side_effect = Exception("Insert failed")
    
    # Act
    result = upsert_repo_coverage(sample_coverage_data)
    
    # Assert
    assert result is None


def test_upsert_repo_coverage_supabase_execute_exception(mock_supabase, sample_coverage_data):
    """Test handling of supabase execute exceptions."""
    # Arrange
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("Execute failed")
    
    # Act
    result = upsert_repo_coverage(sample_coverage_data)
    
    # Assert
    assert result is None


def test_upsert_repo_coverage_with_zero_coverage_values(mock_supabase):
    """Test upsert with zero coverage values."""
    # Arrange
    coverage_data = RepoCoverageInsert(
        branch_name="zero-coverage",
        created_by="zero-user",
        owner_id=555555,
        owner_name="zero-owner",
        repo_id=666666,
        repo_name="zero-repo",
        branch_coverage=0.0,
        function_coverage=0.0,
        line_coverage=0.0,
        statement_coverage=0.0
    )
    expected_data = [{"id": 4, "line_coverage": 0.0}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = expected_data
    
    # Act
    result = upsert_repo_coverage(coverage_data)
    
    # Assert
    assert result == expected_data


def test_upsert_repo_coverage_with_perfect_coverage(mock_supabase):
    """Test upsert with 100% coverage values."""
    # Arrange
    coverage_data = RepoCoverageInsert(
        branch_name="perfect-coverage",
        created_by="perfect-user",
        owner_id=777777,
        owner_name="perfect-owner",
        repo_id=888888,
        repo_name="perfect-repo",
        branch_coverage=100.0,
        function_coverage=100.0,
        line_coverage=100.0,
        statement_coverage=100.0
    )
    expected_data = [{"id": 5, "line_coverage": 100.0}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = expected_data
    
    # Act
    result = upsert_repo_coverage(coverage_data)
    
    # Assert
    assert result == expected_data