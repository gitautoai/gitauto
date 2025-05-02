import pytest
from unittest import mock

from services.supabase.owners.create_owner import create_owner
from tests.constants import OWNER


@pytest.fixture
def mock_supabase():
    with mock.patch("services.supabase.owners.create_owner.supabase") as mock_supabase:
        yield mock_supabase


def test_create_owner_success(mock_supabase):
    # Setup
    owner_id = 123
    owner_name = OWNER
    user_id = 456
    user_name = "testuser"
    stripe_customer_id = "cus_123456"
    owner_type = "Organization"
    org_rules = "Some rules"

    # Configure mock
    mock_execute = mock.MagicMock()
    mock_execute.data = [{"owner_id": owner_id}]
    mock_insert = mock.MagicMock()
    mock_insert.execute.return_value = mock_execute
    mock_table = mock.MagicMock()
    mock_table.insert.return_value = mock_insert
    mock_supabase.table.return_value = mock_table

    # Execute
    result = create_owner(
        owner_id=owner_id,
        owner_name=owner_name,
        user_id=user_id,
        user_name=user_name,
        stripe_customer_id=stripe_customer_id,
        owner_type=owner_type,
        org_rules=org_rules,
    )

    # Assert
    assert result is True
    mock_supabase.table.assert_called_once_with("owners")
    mock_table.insert.assert_called_once_with(
        {
            "owner_id": owner_id,
            "owner_name": owner_name,
            "stripe_customer_id": stripe_customer_id,
            "created_by": f"{user_id}:{user_name}",
            "updated_by": f"{user_id}:{user_name}",
            "owner_type": owner_type,
            "org_rules": org_rules,
        }
    )
    mock_insert.execute.assert_called_once()


def test_create_owner_with_default_values(mock_supabase):
    # Setup
    owner_id = 123
    owner_name = OWNER
    user_id = 456
    user_name = "testuser"

    # Configure mock
    mock_execute = mock.MagicMock()
    mock_execute.data = [{"owner_id": owner_id}]
    mock_insert = mock.MagicMock()
    mock_insert.execute.return_value = mock_execute
    mock_table = mock.MagicMock()
    mock_table.insert.return_value = mock_insert
    mock_supabase.table.return_value = mock_table

    # Execute
    result = create_owner(
        owner_id=owner_id,
        owner_name=owner_name,
        user_id=user_id,
        user_name=user_name,
    )

    # Assert
    assert result is True
    mock_supabase.table.assert_called_once_with("owners")
    mock_table.insert.assert_called_once_with(
        {
            "owner_id": owner_id,
            "owner_name": owner_name,
            "stripe_customer_id": "",
            "created_by": f"{user_id}:{user_name}",
            "updated_by": f"{user_id}:{user_name}",
            "owner_type": "",
            "org_rules": "",
        }
    )
    mock_insert.execute.assert_called_once()


def test_create_owner_failure_empty_data(mock_supabase):
    # Setup
    owner_id = 123
    owner_name = OWNER
    user_id = 456
    user_name = "testuser"

    # Configure mock to return None for data
    mock_execute = mock.MagicMock()
    mock_execute.data = None
    mock_insert = mock.MagicMock()
    mock_insert.execute.return_value = mock_execute
    mock_table = mock.MagicMock()
    mock_table.insert.return_value = mock_insert
    mock_supabase.table.return_value = mock_table

    # Execute
    result = create_owner(
        owner_id=owner_id,
        owner_name=owner_name,
        user_id=user_id,
        user_name=user_name,
    )

    # Assert
    assert result is False
    mock_supabase.table.assert_called_once_with("owners")
    mock_insert.execute.assert_called_once()


def test_create_owner_exception_handling(mock_supabase):
    # Setup
    owner_id = 123
    owner_name = OWNER
    user_id = 456
    user_name = "testuser"

    # Configure mock to raise an exception
    mock_supabase.table.side_effect = Exception("Database error")

    # Execute
    result = create_owner(
        owner_id=owner_id,
        owner_name=owner_name,
        user_id=user_id,
        user_name=user_name,
    )

    # Assert - should return True because of the default_return_value in the decorator
    assert result is True
    mock_supabase.table.assert_called_once_with("owners")


def test_create_owner_http_error(mock_supabase):
    # Setup
    owner_id = 123
    owner_name = OWNER
    user_id = 456
    user_name = "testuser"

    # Configure mock to raise an HTTPError
    import requests
    response_mock = mock.MagicMock()
    response_mock.status_code = 400
    response_mock.reason = "Bad Request"
    response_mock.text = "Invalid input"
    http_error = requests.exceptions.HTTPError("400 Client Error", response=response_mock)
    mock_supabase.table.side_effect = http_error

    # Execute
    result = create_owner(
        owner_id=owner_id,
        owner_name=owner_name,
        user_id=user_id,
        user_name=user_name,
    )

    # Assert - should return True because of the default_return_value in the decorator
    assert result is True
    mock_supabase.table.assert_called_once_with("owners")