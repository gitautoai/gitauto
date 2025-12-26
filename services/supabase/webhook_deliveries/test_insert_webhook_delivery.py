from unittest.mock import MagicMock, patch

import pytest
from postgrest.exceptions import APIError

from services.supabase.webhook_deliveries.insert_webhook_delivery import (
    insert_webhook_delivery,
)


@pytest.fixture
def mock_supabase_client():
    with patch(
        "services.supabase.webhook_deliveries.insert_webhook_delivery.supabase"
    ) as mock:
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()

        mock.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute

        yield mock, mock_execute


def test_insert_webhook_delivery_success(mock_supabase_client):
    mock, mock_execute = mock_supabase_client
    mock_execute.data = [
        {
            "id": 1,
            "delivery_id": "abc-123",
            "event_name": "check_suite",
            "created_at": "2025-12-18T00:00:00",
        }
    ]

    result = insert_webhook_delivery(delivery_id="abc-123", event_name="check_suite")

    assert result is True
    mock.table.assert_called_once_with("webhook_deliveries")
    mock.table.return_value.insert.assert_called_once_with(
        {"delivery_id": "abc-123", "event_name": "check_suite"}
    )
    mock.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_webhook_delivery_duplicate(mock_supabase_client):
    _, mock_execute = mock_supabase_client
    mock_execute.data = []

    result = insert_webhook_delivery(delivery_id="abc-123", event_name="check_suite")

    assert result is False


def test_insert_webhook_delivery_duplicate_key_error_returns_false(
    mock_supabase_client,
):
    mock, _ = mock_supabase_client
    api_error = APIError(
        {"code": "23505", "message": "duplicate key value violates unique constraint"}
    )
    mock.table.return_value.insert.return_value.execute.side_effect = api_error

    result = insert_webhook_delivery(delivery_id="abc-123", event_name="check_suite")

    assert result is False


def test_insert_webhook_delivery_exception_returns_false(mock_supabase_client):
    mock, _ = mock_supabase_client
    mock.table.return_value.insert.return_value.execute.side_effect = Exception(
        "Database error"
    )

    result = insert_webhook_delivery(delivery_id="abc-123", event_name="check_suite")

    assert result is False
