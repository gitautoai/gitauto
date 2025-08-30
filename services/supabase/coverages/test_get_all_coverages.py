# Standard imports
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest

# Local imports
from services.supabase.coverages.get_all_coverages import get_all_coverages


@pytest.fixture
def mock_supabase_client():
    """Fixture to provide a mocked supabase client."""
    with patch("services.supabase.coverages.get_all_coverages.supabase") as mock:
        yield mock


@pytest.fixture
def sample_coverage_data():
    """Fixture providing sample coverage data."""
    return [
        {
            "id": 1,
            "full_path": "src/main.py",
            "repo_id": 123,
            "level": "file",
            "statement_coverage": 85.5,
            "function_coverage": 90.0,
            "branch_coverage": 75.0,
            "line_coverage": 85.5,
            "owner_id": 456,
            "branch_name": "main",
            "created_by": "user1",
            "updated_by": "user1",
            "file_size": 1024,
            "language": "python",
            "package_name": None,
            "github_issue_url": None,
            "is_excluded_from_testing": False,
            "uncovered_lines": "10,15,20",
            "uncovered_functions": "func1,func2",
            "uncovered_branches": "branch1,branch2",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        },
        {
            "id": 2,
            "full_path": "src/utils.py",
            "repo_id": 123,
            "level": "file",
            "statement_coverage": 95.0,
            "function_coverage": 100.0,
            "branch_coverage": 90.0,
            "line_coverage": 95.0,
            "owner_id": 456,
            "branch_name": "main",
            "created_by": "user1",
            "updated_by": "user1",
            "file_size": 512,
            "language": "python",
            "package_name": None,
            "github_issue_url": None,
            "is_excluded_from_testing": False,
            "uncovered_lines": "5",
            "uncovered_functions": "",
            "uncovered_branches": "branch3",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        },
    ]


def test_get_all_coverages_returns_coverage_list_when_data_exists(
    mock_supabase_client, sample_coverage_data
):
    """Test that get_all_coverages returns a list of Coverages when data exists."""
    # Setup mock
    mock_result = MagicMock()
    mock_result.data = sample_coverage_data
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = (
        mock_result
    )

    # Execute
    result = get_all_coverages(repo_id=123)

    # Verify
    assert result is not None
    assert len(result) == 2
    assert all(isinstance(item, dict) for item in result)
    assert result[0]["full_path"] == "src/main.py"
    assert result[1]["full_path"] == "src/utils.py"

    # Verify the correct query was made
    mock_supabase_client.table.assert_called_once_with("coverages")
    mock_supabase_client.table.return_value.select.assert_called_once_with("*")
    mock_supabase_client.table.return_value.select.return_value.eq.assert_called_with(
        "repo_id", 123
    )
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.assert_called_with(
        "level", "file"
    )
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.assert_called_once_with(
        "statement_coverage,file_size,full_path", desc=False
    )


def test_get_all_coverages_returns_empty_list_when_no_data_exists(mock_supabase_client):
    """Test that get_all_coverages returns empty list when no data exists."""
    # Setup mock
    mock_result = MagicMock()
    mock_result.data = []
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = (
        mock_result
    )

    # Execute
    result = get_all_coverages(repo_id=123)

    # Verify
    assert result == []

    # Verify the correct query was made
    mock_supabase_client.table.assert_called_once_with("coverages")
    mock_supabase_client.table.return_value.select.assert_called_once_with("*")
    mock_supabase_client.table.return_value.select.return_value.eq.assert_called_with(
        "repo_id", 123
    )
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.assert_called_with(
        "level", "file"
    )
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.assert_called_once_with(
        "statement_coverage,file_size,full_path", desc=False
    )


def test_get_all_coverages_returns_empty_list_when_data_is_none(mock_supabase_client):
    """Test that get_all_coverages returns empty list when result.data is None."""
    # Setup mock
    mock_result = MagicMock()
    mock_result.data = None
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = (
        mock_result
    )

    # Execute
    result = get_all_coverages(repo_id=123)

    # Verify
    assert result == []


def test_get_all_coverages_with_different_repo_id(
    mock_supabase_client, sample_coverage_data
):
    """Test that get_all_coverages works with different repo_id values."""
    # Setup mock
    mock_result = MagicMock()
    mock_result.data = sample_coverage_data
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = (
        mock_result
    )

    # Execute with different repo_id
    result = get_all_coverages(repo_id=999)

    # Verify
    assert result is not None
    assert len(result) == 2

    # Verify the correct repo_id was used in the query
    mock_supabase_client.table.return_value.select.return_value.eq.assert_called_with(
        "repo_id", 999
    )


def test_get_all_coverages_with_zero_repo_id(mock_supabase_client):
    """Test that get_all_coverages handles zero repo_id correctly."""
    # Setup mock
    mock_result = MagicMock()
    mock_result.data = []
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = (
        mock_result
    )

    # Execute
    result = get_all_coverages(repo_id=0)

    # Verify
    assert result == []

    # Verify the correct repo_id was used in the query
    mock_supabase_client.table.return_value.select.return_value.eq.assert_called_with(
        "repo_id", 0
    )


def test_get_all_coverages_with_negative_repo_id(mock_supabase_client):
    """Test that get_all_coverages handles negative repo_id correctly."""
    # Setup mock
    mock_result = MagicMock()
    mock_result.data = []
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = (
        mock_result
    )

    # Execute
    result = get_all_coverages(repo_id=-1)

    # Verify
    assert result == []

    # Verify the correct repo_id was used in the query
    mock_supabase_client.table.return_value.select.return_value.eq.assert_called_with(
        "repo_id", -1
    )


def test_get_all_coverages_single_item_result(mock_supabase_client):
    """Test that get_all_coverages handles single item results correctly."""
    # Setup mock with single item
    single_item = [
        {
            "id": 1,
            "full_path": "src/single.py",
            "repo_id": 123,
            "level": "file",
            "statement_coverage": 50.0,
            "function_coverage": 60.0,
            "branch_coverage": 40.0,
            "line_coverage": 50.0,
            "owner_id": 456,
            "branch_name": "main",
            "created_by": "user1",
            "updated_by": "user1",
        }
    ]
    mock_result = MagicMock()
    mock_result.data = single_item
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = (
        mock_result
    )

    # Execute
    result = get_all_coverages(repo_id=123)

    # Verify
    assert result is not None
    assert len(result) == 1
    assert result[0]["full_path"] == "src/single.py"
    assert result[0]["statement_coverage"] == 50.0


def test_get_all_coverages_exception_handling(mock_supabase_client):
    """Test that get_all_coverages handles exceptions gracefully due to @handle_exceptions decorator."""
    # Setup mock to raise an exception
    mock_supabase_client.table.side_effect = Exception("Database connection error")

    # Execute
    result = get_all_coverages(repo_id=123)

    # Verify that the decorator returns the default value (empty list) on exception
    assert result == []


@pytest.mark.parametrize("repo_id", [1, 100, 999999, 2147483647])
def test_get_all_coverages_with_various_repo_ids(mock_supabase_client, repo_id):
    """Test that get_all_coverages works with various valid repo_id values."""
    # Setup mock
    mock_result = MagicMock()
    mock_result.data = []
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = (
        mock_result
    )

    # Execute
    result = get_all_coverages(repo_id=repo_id)

    # Verify
    assert result == []
    mock_supabase_client.table.return_value.select.return_value.eq.assert_called_with(
        "repo_id", repo_id
    )


def test_get_all_coverages_query_chain_structure(mock_supabase_client):
    """Test that get_all_coverages builds the correct query chain structure."""
    # Setup mock
    mock_result = MagicMock()
    mock_result.data = []
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = (
        mock_result
    )

    # Execute
    get_all_coverages(repo_id=123)
    assert (
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.called
    )
    assert (
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.called
    )
    # Verify the complete query chain was called correctly
    mock_supabase_client.table.assert_called_once_with("coverages")
    assert mock_supabase_client.table.return_value.select.called
    assert mock_supabase_client.table.return_value.select.return_value.eq.called
    assert (
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.called
    )
