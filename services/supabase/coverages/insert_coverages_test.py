from unittest.mock import patch, MagicMock
import pytest
from datetime import datetime

from schemas.supabase.fastapi.schema_public_latest import Coverages
from services.supabase.coverages.insert_coverages import insert_coverages


@pytest.fixture
def mock_supabase():
    """Fixture to provide a mocked supabase client."""
    with patch("services.supabase.coverages.insert_coverages.supabase") as mock:
        yield mock


@pytest.fixture
def sample_coverage_record():
    """Fixture to provide a sample coverage record."""
    return Coverages(
        id=1,
        branch_coverage=85.5,
        branch_name="main",
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        created_by="test_user",
        file_size=1024,
        full_path="src/example.py",
        function_coverage=90.0,
        github_issue_url="https://github.com/owner/repo/issues/123",
        is_excluded_from_testing=False,
        level="file",
        line_coverage=88.2,
        owner_id=12345,
        package_name="example_package",
        path_coverage=92.1,
        primary_language="python",
        repo_id=67890,
        statement_coverage=87.3,
        uncovered_branches="1,5,10",
        uncovered_functions="func1,func2",
        uncovered_lines="15,20,25",
        updated_at=datetime(2023, 1, 1, 12, 0, 0),
        updated_by="test_user"
    )


@pytest.fixture
def minimal_coverage_record():
    """Fixture to provide a minimal coverage record with only required fields."""
    return Coverages(
        id=2,
        branch_name="develop",
        created_at=datetime(2023, 1, 2, 10, 0, 0),
        created_by="minimal_user",
        full_path="src/minimal.py",
        level="file",
        owner_id=54321,
        repo_id=98765,
        updated_at=datetime(2023, 1, 2, 10, 0, 0),
        updated_by="minimal_user"
    )


def test_insert_coverages_successful_insertion(mock_supabase, sample_coverage_record):
    """Test successful coverage record insertion."""
    # Setup mock response
    mock_result = MagicMock()
    mock_result.data = [{"id": 1, "full_path": "src/example.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
    
    # Execute function
    result = insert_coverages(sample_coverage_record)
    
    # Verify behavior
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(sample_coverage_record)
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()
    
    # Verify result
    assert result == [{"id": 1, "full_path": "src/example.py"}]


def test_insert_coverages_with_minimal_record(mock_supabase, minimal_coverage_record):
    """Test insertion with minimal required fields."""
    # Setup mock response
    mock_result = MagicMock()
    mock_result.data = [{"id": 2, "full_path": "src/minimal.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
    
    # Execute function
    result = insert_coverages(minimal_coverage_record)
    
    # Verify behavior
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(minimal_coverage_record)
    
    # Verify result
    assert result == [{"id": 2, "full_path": "src/minimal.py"}]


def test_insert_coverages_empty_data_response(mock_supabase, sample_coverage_record):
    """Test handling of empty data response."""
    # Setup mock response with empty data
    mock_result = MagicMock()
    mock_result.data = []
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
    
    # Execute function
    result = insert_coverages(sample_coverage_record)
    
    # Verify result
    assert result == []


def test_insert_coverages_none_data_response(mock_supabase, sample_coverage_record):
    """Test handling of None data response."""
    # Setup mock response with None data
    mock_result = MagicMock()
    mock_result.data = None
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
    
    # Execute function
    result = insert_coverages(sample_coverage_record)
    
    # Verify result
    assert result is None


def test_insert_coverages_multiple_records_response(mock_supabase, sample_coverage_record):
    """Test handling of multiple records in response."""
    # Setup mock response with multiple records
    mock_result = MagicMock()
    mock_result.data = [
        {"id": 1, "full_path": "src/example1.py"},
        {"id": 2, "full_path": "src/example2.py"}
    ]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
    
    # Execute function
    result = insert_coverages(sample_coverage_record)
    
    # Verify result
    assert result == [
        {"id": 1, "full_path": "src/example1.py"},
        {"id": 2, "full_path": "src/example2.py"}
    ]


def test_insert_coverages_exception_handling(mock_supabase, sample_coverage_record):
    """Test exception handling returns None due to decorator."""
    # Setup mock to raise exception
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("Database error")
    
    # Execute function
    result = insert_coverages(sample_coverage_record)
    
    # Verify result (decorator should return None on exception)
    assert result is None


def test_insert_coverages_attribute_error_handling(mock_supabase, sample_coverage_record):
    """Test handling of AttributeError."""
    # Setup mock to raise AttributeError
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = AttributeError("Missing attribute")
    
    # Execute function
    result = insert_coverages(sample_coverage_record)
    
    # Verify result
    assert result is None


def test_insert_coverages_key_error_handling(mock_supabase, sample_coverage_record):
    """Test handling of KeyError."""
    # Setup mock to raise KeyError
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = KeyError("Missing key")
    
    # Execute function
    result = insert_coverages(sample_coverage_record)
    
    # Verify result
    assert result is None


def test_insert_coverages_type_error_handling(mock_supabase, sample_coverage_record):
    """Test handling of TypeError."""
    # Setup mock to raise TypeError
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = TypeError("Type mismatch")
    
    # Execute function
    result = insert_coverages(sample_coverage_record)
    
    # Verify result
    assert result is None


def test_insert_coverages_method_chaining(mock_supabase, sample_coverage_record):
    """Test that the method chaining is called in correct order."""
    # Setup mock
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()
    mock_result = MagicMock()
    mock_result.data = [{"id": 1}]
    
    mock_supabase.table.return_value = mock_table
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = mock_result
    
    # Execute function
    result = insert_coverages(sample_coverage_record)
    
    # Verify method chaining
    mock_supabase.table.assert_called_once_with("coverages")
    mock_table.insert.assert_called_once_with(sample_coverage_record)
    mock_insert.execute.assert_called_once()
    
    # Verify result
    assert result == [{"id": 1}]