from unittest.mock import patch, MagicMock

import pytest
from schemas.supabase.fastapi.schema_public_latest import Coverages
from services.supabase.coverages.insert_coverages import insert_coverages


@pytest.fixture
def mock_supabase():
    """Fixture to provide a mocked supabase client."""
    with patch("services.supabase.coverages.insert_coverages.supabase") as mock:
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()
        
        mock.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute
        
        yield mock


@pytest.fixture
def sample_coverage_record():
    """Fixture to provide a sample coverage record."""
    return Coverages(
        id=1,
        created_by="test_user",
        full_path="services/test/example.py",
        level="file",
        owner_id=123,
        repo_id=456,
        updated_by="test_user",
        line_coverage=85.5,
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00",
        branch_coverage=75.0,
        function_coverage=90.0,
        statement_coverage=88.0,
        branch_name="main",
        primary_language="python",
        uncovered_lines="10,15,20",
        uncovered_branches="5,8",
        uncovered_functions="helper_function",
        file_size=1024,
        github_issue_url="https://github.com/owner/repo/issues/123"
    )


def test_insert_coverages_successful_insertion(mock_supabase, sample_coverage_record):
    """Test successful coverage record insertion."""
    expected_data = [{"id": 1, "full_path": "services/test/example.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = expected_data
    
    result = insert_coverages(sample_coverage_record)
    
    assert result == expected_data
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(sample_coverage_record)
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_returns_empty_data(mock_supabase, sample_coverage_record):
    """Test insertion returns empty data."""
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = []
    
    result = insert_coverages(sample_coverage_record)
    
    assert result == []
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(sample_coverage_record)
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_returns_none_data(mock_supabase, sample_coverage_record):
    """Test insertion returns None data."""
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = None
    
    result = insert_coverages(sample_coverage_record)
    
    assert result is None
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(sample_coverage_record)
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_with_minimal_required_fields(mock_supabase):
    """Test insertion with only required fields."""
    minimal_record = Coverages(
        id=2,
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00",
        created_by="minimal_user",
        full_path="minimal/path.py",
        level="file",
        owner_id=1,
        repo_id=2,
        updated_by="minimal_user"
    )
    expected_data = [{"id": 2, "full_path": "minimal/path.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = expected_data
    
    result = insert_coverages(minimal_record)
    
    assert result == expected_data
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(minimal_record)
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_with_all_optional_fields(mock_supabase):
    """Test insertion with all optional fields populated."""
    comprehensive_record = Coverages(
        id=3,
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00",
        created_by="comprehensive_user",
        full_path="comprehensive/path.py",
        level="function",
        owner_id=999,
        repo_id=888,
        updated_by="comprehensive_user",
        branch_coverage=95.5,
        branch_name="feature-branch",
        file_size=2048,
        function_coverage=98.0,
        github_issue_url="https://github.com/test/repo/issues/456",
        is_excluded_from_testing=False,
        line_coverage=92.3,
        package_name="test.package",
        path_coverage=89.7,
        primary_language="typescript",
        statement_coverage=94.1,
        uncovered_branches="1,3,7",
        uncovered_functions="unused_helper,deprecated_method",
        uncovered_lines="25,30,35,40"
    )
    expected_data = [{"id": 3, "full_path": "comprehensive/path.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = expected_data
    
    result = insert_coverages(comprehensive_record)
    
    assert result == expected_data
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(comprehensive_record)
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_handles_supabase_exception(mock_supabase, sample_coverage_record):
    """Test that exceptions are handled by the decorator and return None."""
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("Database error")
    
    result = insert_coverages(sample_coverage_record)
    
    assert result is None
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(sample_coverage_record)
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_handles_table_exception(mock_supabase, sample_coverage_record):
    """Test that table method exceptions are handled."""
    mock_supabase.table.side_effect = Exception("Table access error")
    
    result = insert_coverages(sample_coverage_record)
    
    assert result is None
    mock_supabase.table.assert_called_once_with("coverages")


def test_insert_coverages_handles_insert_exception(mock_supabase, sample_coverage_record):
    """Test that insert method exceptions are handled."""
    mock_supabase.table.return_value.insert.side_effect = Exception("Insert error")
    
    result = insert_coverages(sample_coverage_record)
    
    assert result is None
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(sample_coverage_record)


def test_insert_coverages_with_zero_coverage_values(mock_supabase):
    """Test insertion with zero coverage values."""
    zero_coverage_record = Coverages(
        id=4,
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00",
        created_by="zero_user",
        full_path="zero/coverage.py",
        level="file",
        owner_id=100,
        repo_id=200,
        updated_by="zero_user",
        line_coverage=0.0,
        branch_coverage=0.0,
        function_coverage=0.0,
        statement_coverage=0.0
    )
    expected_data = [{"id": 4, "full_path": "zero/coverage.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = expected_data
    
    result = insert_coverages(zero_coverage_record)
    
    assert result == expected_data
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(zero_coverage_record)
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_with_perfect_coverage_values(mock_supabase):
    """Test insertion with perfect coverage values."""
    perfect_coverage_record = Coverages(
        id=5,
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00",
        created_by="perfect_user",
        full_path="perfect/coverage.py",
        level="file",
        owner_id=300,
        repo_id=400,
        updated_by="perfect_user",
        line_coverage=100.0,
        branch_coverage=100.0,
        function_coverage=100.0,
        statement_coverage=100.0
    )
    expected_data = [{"id": 5, "full_path": "perfect/coverage.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = expected_data
    
    result = insert_coverages(perfect_coverage_record)
    
    assert result == expected_data
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(perfect_coverage_record)
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()
