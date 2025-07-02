# Standard imports
from unittest.mock import patch, MagicMock
import datetime

# Third party imports
import pytest

# Local imports
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
        created_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
        created_by="test_user",
        file_size=1024,
        full_path="src/example.py",
        function_coverage=90.0,
        github_issue_url="https://github.com/test/repo/issues/123",
        is_excluded_from_testing=False,
        level="file",
        line_coverage=88.2,
        owner_id=12345,
        package_name="test_package",
        path_coverage=92.1,
        primary_language="python",
        repo_id=67890,
        statement_coverage=87.3,
        uncovered_branches="10,15,20",
        uncovered_functions="func1,func2",
        uncovered_lines="5,10,15",
        updated_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
        updated_by="test_user"
    )


@pytest.fixture
def minimal_coverage_record():
    """Fixture to provide a minimal coverage record with only required fields."""
    return Coverages(
        id=2,
        branch_name="feature-branch",
        created_at=datetime.datetime(2024, 1, 2, 10, 0, 0),
        created_by="minimal_user",
        full_path="src/minimal.py",
        level="file",
        owner_id=54321,
        repo_id=98765,
        updated_at=datetime.datetime(2024, 1, 2, 10, 0, 0),
        updated_by="minimal_user"
    )


def test_insert_coverages_success(mock_supabase, sample_coverage_record):
    """Test successful insertion of coverage record."""
    # Setup mock response
    mock_result = MagicMock()
    mock_result.data = [{"id": 1, "full_path": "src/example.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
    
    # Call the function
    result = insert_coverages(sample_coverage_record)
    
    # Verify the result
    assert result == [{"id": 1, "full_path": "src/example.py"}]
    
    # Verify supabase calls
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(sample_coverage_record)
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_with_minimal_record(mock_supabase, minimal_coverage_record):
    """Test insertion with minimal coverage record."""
    # Setup mock response
    mock_result = MagicMock()
    mock_result.data = [{"id": 2, "full_path": "src/minimal.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
    
    # Call the function
    result = insert_coverages(minimal_coverage_record)
    
    # Verify the result
    assert result == [{"id": 2, "full_path": "src/minimal.py"}]
    
    # Verify supabase calls
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(minimal_coverage_record)


def test_insert_coverages_empty_response(mock_supabase, sample_coverage_record):
    """Test insertion when supabase returns empty data."""
    # Setup mock response with empty data
    mock_result = MagicMock()
    mock_result.data = []
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
    
    # Call the function
    result = insert_coverages(sample_coverage_record)
    
    # Verify the result is empty list
    assert result == []
    
    # Verify supabase calls
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(sample_coverage_record)


def test_insert_coverages_none_response(mock_supabase, sample_coverage_record):
    """Test insertion when supabase returns None data."""
    # Setup mock response with None data
    mock_result = MagicMock()
    mock_result.data = None
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
    
    # Call the function
    result = insert_coverages(sample_coverage_record)
    
    # Verify the result is None
    assert result is None
    
    # Verify supabase calls
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(sample_coverage_record)


def test_insert_coverages_with_supabase_exception(mock_supabase, sample_coverage_record):
    """Test insertion when supabase raises an exception."""
    # Setup mock to raise exception
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("Database error")
    
    # Call the function - should return None due to handle_exceptions decorator
    result = insert_coverages(sample_coverage_record)
    
    # Verify the result is None (default return value from decorator)
    assert result is None
    
    # Verify supabase calls were attempted
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(sample_coverage_record)


def test_insert_coverages_with_http_error(mock_supabase, sample_coverage_record):
    """Test insertion when supabase raises an HTTP error."""
    from requests.exceptions import HTTPError
    
    # Create a mock response for HTTPError
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.reason = "Internal Server Error"
    mock_response.text = "Database connection failed"
    
    # Create HTTPError with mock response
    http_error = HTTPError("HTTP 500 Error")
    http_error.response = mock_response
    
    # Setup mock to raise HTTPError
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = http_error
    
    # Call the function - should return None due to handle_exceptions decorator
    result = insert_coverages(sample_coverage_record)
    
    # Verify the result is None (default return value from decorator)
    assert result is None
    
    # Verify supabase calls were attempted
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(sample_coverage_record)


def test_insert_coverages_with_multiple_records_response(mock_supabase, sample_coverage_record):
    """Test insertion when supabase returns multiple records."""
    # Setup mock response with multiple records
    mock_result = MagicMock()
    mock_result.data = [
        {"id": 1, "full_path": "src/example.py"},
        {"id": 2, "full_path": "src/another.py"}
    ]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
    
    # Call the function
    result = insert_coverages(sample_coverage_record)
    
    # Verify the result contains multiple records
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[1]["id"] == 2
    
    # Verify supabase calls
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(sample_coverage_record)


def test_insert_coverages_with_complex_data_types(mock_supabase):
    """Test insertion with coverage record containing complex data types."""
    # Create coverage record with None values for optional fields
    coverage_record = Coverages(
        id=3,
        branch_coverage=None,  # Optional field as None
        branch_name="test-branch",
        created_at=datetime.datetime(2024, 1, 3, 14, 30, 0),
        created_by="complex_user",
        file_size=None,  # Optional field as None
        full_path="src/complex.py",
        function_coverage=None,  # Optional field as None
        github_issue_url=None,  # Optional field as None
        is_excluded_from_testing=None,  # Optional field as None
        level="file",
        line_coverage=None,  # Optional field as None
        owner_id=11111,
        package_name=None,  # Optional field as None
        path_coverage=None,  # Optional field as None
        primary_language=None,  # Optional field as None
        repo_id=22222,
        statement_coverage=None,  # Optional field as None
        uncovered_branches=None,  # Optional field as None
        uncovered_functions=None,  # Optional field as None
        uncovered_lines=None,  # Optional field as None
        updated_at=datetime.datetime(2024, 1, 3, 14, 30, 0),
        updated_by="complex_user"
    )
    
    # Setup mock response
    mock_result = MagicMock()
    mock_result.data = [{"id": 3, "full_path": "src/complex.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
    
    # Call the function
    result = insert_coverages(coverage_record)
    
    # Verify the result
    assert result == [{"id": 3, "full_path": "src/complex.py"}]
    
    # Verify supabase calls
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(coverage_record)