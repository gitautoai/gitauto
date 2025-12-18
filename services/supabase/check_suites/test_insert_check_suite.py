from unittest.mock import MagicMock, patch

import pytest
from services.supabase.check_suites.insert_check_suite import insert_check_suite


@pytest.fixture
def mock_supabase_client():
    with patch("services.supabase.check_suites.insert_check_suite.supabase") as mock:
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()

        mock.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute

        yield mock, mock_execute


def test_insert_check_suite_success(mock_supabase_client):
    mock, mock_execute = mock_supabase_client
    mock_execute.data = [{"check_suite_id": 12345, "created_at": "2025-12-18T00:00:00"}]

    result = insert_check_suite(check_suite_id=12345)

    assert result is True
    mock.table.assert_called_once_with("check_suites")
    mock.table.return_value.insert.assert_called_once_with({"check_suite_id": 12345})
    mock.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_check_suite_duplicate(mock_supabase_client):
    _, mock_execute = mock_supabase_client
    mock_execute.data = []

    result = insert_check_suite(check_suite_id=12345)

    assert result is False


def test_insert_check_suite_exception_returns_false(mock_supabase_client):
    mock, _ = mock_supabase_client
    mock.table.return_value.insert.return_value.execute.side_effect = Exception(
        "Database error"
    )

    result = insert_check_suite(check_suite_id=12345)

    assert result is False
