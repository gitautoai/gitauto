from unittest.mock import patch, MagicMock

import pytest
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
    """Fixture to provide a sample coverage record as a dictionary."""
    return {
        "created_by": "test_user",
        "full_path": "services/test/example.py",
        "level": "file",
        "owner_id": 123,
        "repo_id": 456,
        "updated_by": "test_user",
        "line_coverage": 85.5,
        "branch_coverage": 75.0,
        "function_coverage": 90.0,
        "statement_coverage": 88.0,
        "branch_name": "main",
        "language": "python",
        "uncovered_lines": "10,15,20",
        "uncovered_branches": "5,8",
        "uncovered_functions": "helper_function",
        "file_size": 1024,
        "github_issue_url": "https://github.com/owner/repo/issues/123",
    }


def test_insert_coverages_successful_insertion(mock_supabase, sample_coverage_record):
    """Test successful coverage record insertion."""
    expected_data = [{"id": 1, "full_path": "services/test/example.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = (
        expected_data
    )

    result = insert_coverages(sample_coverage_record)

    assert result == expected_data
    mock_supabase.table.assert_called_once_with("coverages")
    # Verify insert is called with dict() wrapper to convert TypedDict to plain dict
    mock_supabase.table.return_value.insert.assert_called_once_with(
        dict(sample_coverage_record)
    )
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_returns_empty_data(mock_supabase, sample_coverage_record):
    """Test insertion returns empty data."""
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = []

    result = insert_coverages(sample_coverage_record)

    assert result == []
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(
        sample_coverage_record
    )
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_returns_none_data(mock_supabase, sample_coverage_record):
    """Test insertion returns None data."""
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = (
        None
    )

    result = insert_coverages(sample_coverage_record)

    assert result is None
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(
        sample_coverage_record
    )
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_with_minimal_required_fields(mock_supabase):
    """Test insertion with only required fields."""
    minimal_record = {
        "created_by": "test_user",
        "full_path": "minimal/path.py",
        "level": "file",
        "owner_id": 1,
        "repo_id": 2,
        "updated_by": "test_user",
    }
    expected_data = [{"id": 2, "full_path": "minimal/path.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = (
        expected_data
    )

    result = insert_coverages(minimal_record)

    assert result == expected_data
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(minimal_record)
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_with_all_optional_fields(mock_supabase):
    """Test insertion with all optional fields populated."""
    comprehensive_record = {
        "created_by": "test_user",
        "full_path": "comprehensive/path.py",
        "level": "function",
        "owner_id": 999,
        "repo_id": 888,
        "updated_by": "test_user",
        "branch_coverage": 95.5,
        "branch_name": "feature-branch",
        "file_size": 2048,
        "function_coverage": 98.0,
        "github_issue_url": "https://github.com/test/repo/issues/456",
        "is_excluded_from_testing": False,
        "line_coverage": 92.3,
        "package_name": "test.package",
        "path_coverage": 89.7,
        "language": "typescript",
        "statement_coverage": 94.1,
        "uncovered_branches": "1,3,7",
        "uncovered_functions": "unused_helper,deprecated_method",
        "uncovered_lines": "25,30,35,40",
    }
    expected_data = [{"id": 3, "full_path": "comprehensive/path.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = (
        expected_data
    )

    result = insert_coverages(comprehensive_record)

    assert result == expected_data
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(
        comprehensive_record
    )
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_handles_supabase_exception(
    mock_supabase, sample_coverage_record
):
    """Test that exceptions are handled by the decorator and return None."""
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = (
        Exception("Database error")
    )

    result = insert_coverages(sample_coverage_record)

    assert result is None
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(
        sample_coverage_record
    )
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_handles_table_exception(
    mock_supabase, sample_coverage_record
):
    """Test that table method exceptions are handled."""
    mock_supabase.table.side_effect = Exception("Table access error")

    result = insert_coverages(sample_coverage_record)

    assert result is None
    mock_supabase.table.assert_called_once_with("coverages")


def test_insert_coverages_handles_insert_exception(
    mock_supabase, sample_coverage_record
):
    """Test that insert method exceptions are handled."""
    mock_supabase.table.return_value.insert.side_effect = Exception("Insert error")

    result = insert_coverages(sample_coverage_record)

    assert result is None
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(
        sample_coverage_record
    )


def test_insert_coverages_with_zero_coverage_values(mock_supabase):
    """Test insertion with zero coverage values."""
    zero_coverage_record = {
        "created_by": "test_user",
        "full_path": "zero/coverage.py",
        "level": "file",
        "owner_id": 100,
        "repo_id": 200,
        "updated_by": "test_user",
        "line_coverage": 0.0,
        "branch_coverage": 0.0,
        "function_coverage": 0.0,
        "statement_coverage": 0.0,
    }
    expected_data = [{"id": 4, "full_path": "zero/coverage.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = (
        expected_data
    )

    result = insert_coverages(zero_coverage_record)

    assert result == expected_data
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(
        zero_coverage_record
    )
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_with_perfect_coverage_values(mock_supabase):
    """Test insertion with perfect coverage values."""
    perfect_coverage_record = {
        "created_by": "test_user",
        "full_path": "perfect/coverage.py",
        "level": "file",
        "owner_id": 300,
        "repo_id": 400,
        "updated_by": "test_user",
        "line_coverage": 100.0,
        "branch_coverage": 100.0,
        "function_coverage": 100.0,
        "statement_coverage": 100.0,
    }
    expected_data = [{"id": 5, "full_path": "perfect/coverage.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = (
        expected_data
    )

    result = insert_coverages(perfect_coverage_record)

    assert result == expected_data
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(
        perfect_coverage_record
    )
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_with_none_values(mock_supabase):
    """Test insertion with None values for optional fields."""
    record_with_nones = {
        "created_by": "test_user",
        "full_path": "test/with_nones.py",
        "level": "file",
        "owner_id": 500,
        "repo_id": 600,
        "updated_by": "test_user",
        "line_coverage": None,
        "branch_coverage": None,
        "function_coverage": None,
        "statement_coverage": None,
        "uncovered_lines": None,
        "uncovered_branches": None,
        "uncovered_functions": None,
        "github_issue_url": None,
        "package_name": None,
        "language": None,
    }
    expected_data = [{"id": 6, "full_path": "test/with_nones.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = (
        expected_data
    )

    result = insert_coverages(record_with_nones)

    assert result == expected_data
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(record_with_nones)
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_with_string_coverage_values(mock_supabase):
    """Test insertion with string coverage values that could be converted."""
    string_coverage_record = {
        "created_by": "test_user",
        "full_path": "test/string_coverage.py",
        "level": "file",
        "owner_id": 700,
        "repo_id": 800,
        "updated_by": "test_user",
        "line_coverage": "85.5",
        "branch_coverage": "75.0",
        "function_coverage": "90.0",
        "statement_coverage": "88.0",
    }
    expected_data = [{"id": 7, "full_path": "test/string_coverage.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = (
        expected_data
    )

    result = insert_coverages(string_coverage_record)

    assert result == expected_data
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(
        string_coverage_record
    )
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_with_large_file_size(mock_supabase):
    """Test insertion with large file size."""
    large_file_record = {
        "created_by": "test_user",
        "full_path": "test/large_file.py",
        "level": "file",
        "owner_id": 900,
        "repo_id": 1000,
        "updated_by": "test_user",
        "file_size": 999999999,
        "line_coverage": 50.0,
        "branch_coverage": 45.0,
        "function_coverage": 60.0,
        "statement_coverage": 55.0,
    }
    expected_data = [{"id": 8, "full_path": "test/large_file.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = (
        expected_data
    )

    result = insert_coverages(large_file_record)

    assert result == expected_data
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(large_file_record)
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_with_boolean_exclusion_flag(mock_supabase):
    """Test insertion with boolean exclusion flag."""
    excluded_record = {
        "created_by": "test_user",
        "full_path": "test/excluded.py",
        "level": "file",
        "owner_id": 1100,
        "repo_id": 1200,
        "updated_by": "test_user",
        "is_excluded_from_testing": True,
        "line_coverage": 0.0,
        "branch_coverage": 0.0,
        "function_coverage": 0.0,
        "statement_coverage": 0.0,
    }
    expected_data = [{"id": 9, "full_path": "test/excluded.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = (
        expected_data
    )

    result = insert_coverages(excluded_record)

    assert result == expected_data
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(excluded_record)
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_with_special_characters_in_path(mock_supabase):
    """Test insertion with special characters in file path."""
    special_path_record = {
        "created_by": "test_user",
        "full_path": "test/special-chars_file@#$.py",
        "level": "file",
        "owner_id": 1300,
        "repo_id": 1400,
        "updated_by": "test_user",
        "line_coverage": 75.0,
        "branch_coverage": 70.0,
        "function_coverage": 80.0,
        "statement_coverage": 77.5,
    }
    expected_data = [{"id": 10, "full_path": "test/special-chars_file@#$.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = (
        expected_data
    )

    result = insert_coverages(special_path_record)

    assert result == expected_data
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(special_path_record)
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_with_empty_strings(mock_supabase):
    """Test insertion with empty strings for optional fields."""
    empty_strings_record = {
        "created_by": "test_user",
        "full_path": "test/empty_strings.py",
        "level": "file",
        "owner_id": 1500,
        "repo_id": 1600,
        "updated_by": "test_user",
        "uncovered_lines": "",
        "uncovered_branches": "",
        "uncovered_functions": "",
        "package_name": "",
        "language": "",
        "line_coverage": 100.0,
        "branch_coverage": 100.0,
        "function_coverage": 100.0,
        "statement_coverage": 100.0,
    }
    expected_data = [{"id": 11, "full_path": "test/empty_strings.py"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = (
        expected_data
    )

    result = insert_coverages(empty_strings_record)

    assert result == expected_data
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(
        empty_strings_record
    )
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_with_different_levels(mock_supabase):
    """Test insertion with different level values."""
    directory_record = {
        "created_by": "test_user",
        "full_path": "test/directory",
        "level": "directory",
        "owner_id": 1700,
        "repo_id": 1800,
        "updated_by": "test_user",
        "line_coverage": 65.0,
        "branch_coverage": 60.0,
        "function_coverage": 70.0,
        "statement_coverage": 67.5,
    }
    expected_data = [{"id": 12, "full_path": "test/directory"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = (
        expected_data
    )

    result = insert_coverages(directory_record)

    assert result == expected_data
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(directory_record)
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_coverages_with_repository_level(mock_supabase):
    """Test insertion with repository level."""
    repository_record = {
        "created_by": "test_user",
        "full_path": "All",
        "level": "repository",
        "owner_id": 1900,
        "repo_id": 2000,
        "updated_by": "test_user",
        "line_coverage": 80.0,
        "branch_coverage": 75.0,
        "function_coverage": 85.0,
        "statement_coverage": 82.5,
    }
    expected_data = [{"id": 13, "full_path": "All"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = (
        expected_data
    )

    result = insert_coverages(repository_record)

    assert result == expected_data
    mock_supabase.table.assert_called_once_with("coverages")
    mock_supabase.table.return_value.insert.assert_called_once_with(repository_record)
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()
