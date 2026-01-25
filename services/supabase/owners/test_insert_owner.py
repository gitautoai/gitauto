# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import MagicMock, patch

import pytest

from services.supabase.owners.insert_owner import insert_owner


@pytest.fixture
def mock_supabase():
    with patch("services.supabase.owners.insert_owner.supabase") as mock:
        mock_execute_result = MagicMock()
        mock_execute = MagicMock(return_value=mock_execute_result)
        mock_insert = MagicMock()
        mock_insert.execute = mock_execute
        mock_table = MagicMock()
        mock_table.insert = MagicMock(return_value=mock_insert)
        mock.table = MagicMock(return_value=mock_table)
        yield mock


def test_insert_owner_with_stripe_customer_id(mock_supabase):
    insert_owner(
        owner_id=123,
        owner_name="test-owner",
        owner_type="Organization",
        user_id=456,
        user_name="test-user",
        stripe_customer_id="cus_test123",
    )

    mock_supabase.table.assert_called_once_with("owners")
    mock_supabase.table().insert.assert_called_once_with(
        {
            "owner_id": 123,
            "owner_name": "test-owner",
            "owner_type": "Organization",
            "stripe_customer_id": "cus_test123",
            "created_by": "456:test-user",
            "updated_by": "456:test-user",
        }
    )
    mock_supabase.table().insert().execute.assert_called_once()


def test_insert_owner_without_stripe_customer_id(mock_supabase):
    insert_owner(
        owner_id=789,
        owner_name="minimal-owner",
        owner_type="User",
        user_id=101,
        user_name="minimal-user",
        stripe_customer_id="",
    )

    mock_supabase.table.assert_called_once_with("owners")
    mock_supabase.table().insert.assert_called_once_with(
        {
            "owner_id": 789,
            "owner_name": "minimal-owner",
            "owner_type": "User",
            "stripe_customer_id": "",
            "created_by": "101:minimal-user",
            "updated_by": "101:minimal-user",
        }
    )


def test_insert_owner_exception_handled(mock_supabase):
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = (
        Exception("Database error")
    )

    result = insert_owner(
        owner_id=666,
        owner_name="error-owner",
        owner_type="Organization",
        user_id=777,
        user_name="error-user",
        stripe_customer_id="cus_123",
    )

    assert result is None
