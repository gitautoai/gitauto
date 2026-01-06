from unittest.mock import patch, MagicMock

import pytest

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
            "owner_id": 456,
        },
        {
            "id": 2,
            "full_path": "src/utils.py",
            "repo_id": 123,
            "level": "file",
            "statement_coverage": 95.0,
            "owner_id": 456,
        },
    ]


def test_get_all_coverages_returns_coverage_list(
    mock_supabase_client, sample_coverage_data
):
    """Test that get_all_coverages returns a list of Coverages when data exists."""
    mock_result = MagicMock()
    mock_result.data = sample_coverage_data
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = (
        mock_result
    )

    result = get_all_coverages(owner_id=789, repo_id=123)

    assert result is not None
    assert len(result) == 2
    assert result[0]["full_path"] == "src/main.py"
    assert result[1]["full_path"] == "src/utils.py"
    mock_supabase_client.table.assert_called_once_with("coverages")


def test_get_all_coverages_returns_empty_list_when_no_data(mock_supabase_client):
    """Test that get_all_coverages returns empty list when no data exists."""
    mock_result = MagicMock()
    mock_result.data = []
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = (
        mock_result
    )

    result = get_all_coverages(owner_id=789, repo_id=123)

    assert result == []


def test_get_all_coverages_returns_empty_list_when_data_is_none(mock_supabase_client):
    """Test that get_all_coverages returns empty list when result.data is None."""
    mock_result = MagicMock()
    mock_result.data = None
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = (
        mock_result
    )

    result = get_all_coverages(owner_id=789, repo_id=123)

    assert result == []


def test_get_all_coverages_exception_handling(mock_supabase_client):
    """Test that get_all_coverages handles exceptions gracefully."""
    mock_supabase_client.table.side_effect = Exception("Database error")

    result = get_all_coverages(owner_id=789, repo_id=123)

    assert result == []
