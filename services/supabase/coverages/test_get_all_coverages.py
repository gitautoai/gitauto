from unittest.mock import MagicMock, patch

import pytest

from services.supabase.coverages.get_all_coverages import get_all_coverages, PAGE_SIZE


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


def _setup_mock_chain(mock_supabase_client, results):
    """Helper to set up the mock chain for paginated queries.
    results: list of lists, one per page call."""
    chain = (
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value.order.return_value.range.return_value
    )
    mock_results = []
    for data in results:
        mock_result = MagicMock()
        mock_result.data = data
        mock_results.append(mock_result)
    chain.execute.side_effect = mock_results


def test_get_all_coverages_returns_coverage_list(
    mock_supabase_client, sample_coverage_data
):
    _setup_mock_chain(mock_supabase_client, [sample_coverage_data])

    result = get_all_coverages(platform="github", owner_id=789, repo_id=123)

    assert len(result) == 2
    assert result[0]["full_path"] == "src/main.py"
    assert result[1]["full_path"] == "src/utils.py"
    mock_supabase_client.table.assert_called_with("coverages")


def test_get_all_coverages_returns_empty_list_when_no_data(mock_supabase_client):
    _setup_mock_chain(mock_supabase_client, [[]])

    result = get_all_coverages(platform="github", owner_id=789, repo_id=123)

    assert not result


def test_get_all_coverages_returns_empty_list_when_data_is_none(mock_supabase_client):
    _setup_mock_chain(mock_supabase_client, [None])

    result = get_all_coverages(platform="github", owner_id=789, repo_id=123)

    assert not result


def test_get_all_coverages_exception_handling(mock_supabase_client):
    mock_supabase_client.table.side_effect = Exception("Database error")

    result = get_all_coverages(platform="github", owner_id=789, repo_id=123)

    assert not result


def test_get_all_coverages_paginates_when_more_than_page_size(mock_supabase_client):
    """When result count equals PAGE_SIZE, fetch next page until fewer results."""
    page1 = [{"id": i, "full_path": f"file_{i}.py"} for i in range(PAGE_SIZE)]
    page2 = [{"id": PAGE_SIZE, "full_path": "last_file.py"}]
    _setup_mock_chain(mock_supabase_client, [page1, page2])

    result = get_all_coverages(platform="github", owner_id=789, repo_id=123)

    assert len(result) == PAGE_SIZE + 1
    assert result[-1]["full_path"] == "last_file.py"


def test_get_all_coverages_stops_on_empty_second_page(mock_supabase_client):
    """When first page is exactly PAGE_SIZE but second page is empty, stop."""
    page1 = [{"id": i, "full_path": f"file_{i}.py"} for i in range(PAGE_SIZE)]
    _setup_mock_chain(mock_supabase_client, [page1, []])

    result = get_all_coverages(platform="github", owner_id=789, repo_id=123)

    assert len(result) == PAGE_SIZE
