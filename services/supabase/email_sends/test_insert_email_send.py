from unittest.mock import MagicMock, patch

import pytest
from postgrest.exceptions import APIError

from services.supabase.email_sends.insert_email_send import insert_email_send


@pytest.fixture
def mock_supabase_client():
    with patch("services.supabase.email_sends.insert_email_send.supabase") as mock:
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()

        mock.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute

        yield mock, mock_execute


def test_insert_email_send_success(mock_supabase_client):
    mock, mock_execute = mock_supabase_client
    mock_execute.data = [
        {
            "id": 1,
            "owner_id": 12345,
            "owner_name": "test-user",
            "email_type": "uninstall",
            "created_at": "2025-12-18T00:00:00",
        }
    ]

    result = insert_email_send(
        platform="github",
        owner_id=12345,
        owner_name="test-user",
        email_type="uninstall",
    )

    assert result is True
    mock.table.assert_called_once_with("email_sends")
    mock.table.return_value.insert.assert_called_once_with(
        {
            "platform": "github",
            "owner_id": 12345,
            "owner_name": "test-user",
            "email_type": "uninstall",
        }
    )
    mock.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_email_send_duplicate(mock_supabase_client):
    _, mock_execute = mock_supabase_client
    mock_execute.data = []

    result = insert_email_send(
        platform="github",
        owner_id=12345,
        owner_name="test-user",
        email_type="uninstall",
    )

    assert result is False


def test_insert_email_send_duplicate_key_error_returns_false(mock_supabase_client):
    mock, _ = mock_supabase_client
    api_error = APIError(
        {"code": "23505", "message": "duplicate key value violates unique constraint"}
    )
    mock.table.return_value.insert.return_value.execute.side_effect = api_error

    result = insert_email_send(
        platform="github",
        owner_id=12345,
        owner_name="test-user",
        email_type="uninstall",
    )

    assert result is False


def test_insert_email_send_exception_returns_none(mock_supabase_client):
    """DB errors return None so the email dedup is skipped (only False = duplicate)."""
    mock, _ = mock_supabase_client
    mock.table.return_value.insert.return_value.execute.side_effect = Exception(
        "Database error"
    )

    result = insert_email_send(
        platform="github",
        owner_id=12345,
        owner_name="test-user",
        email_type="uninstall",
    )

    assert result is None


def test_insert_email_send_postgrest_server_error_returns_none(mock_supabase_client):
    """PostgREST 502/500 returns None so the email dedup is skipped."""
    mock, _ = mock_supabase_client
    api_error = APIError({"code": "502", "message": "JSON could not be generated"})
    mock.table.return_value.insert.return_value.execute.side_effect = api_error

    result = insert_email_send(
        platform="github",
        owner_id=12345,
        owner_name="test-user",
        email_type="uninstall",
    )

    assert result is None
