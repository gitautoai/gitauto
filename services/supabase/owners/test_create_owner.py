from unittest.mock import MagicMock, patch

import pytest

from services.supabase.owners.create_owner import create_owner


@pytest.fixture
def mock_supabase():
    """Mock supabase client for testing."""
    with patch("services.supabase.owners.create_owner.supabase") as mock:
        # Setup the chain: supabase.table().insert().execute()
        mock_execute = MagicMock()
        mock_insert = MagicMock()
        mock_insert.execute.return_value = mock_execute
        mock_table = MagicMock()
        mock_table.insert.return_value = mock_insert
        mock.table.return_value = mock_table
        yield mock


def test_create_owner_success_with_all_parameters(mock_supabase):
    """Test successful owner creation with all parameters provided."""
    # Execute
    create_owner(
        owner_id=123,
        owner_name="test-owner",
        user_id=456,
        user_name="test-user",
        stripe_customer_id="cus_test123",
        owner_type="Organization",
        org_rules="test rules"
    )
    
    # Assert
    mock_supabase.table.assert_called_once_with("owners")
    mock_supabase.table().insert.assert_called_once_with({
        "owner_id": 123,
        "owner_name": "test-owner",
        "stripe_customer_id": "cus_test123",
        "created_by": "456:test-user",
        "updated_by": "456:test-user",
        "owner_type": "Organization",
        "org_rules": "test rules",
    })
    mock_supabase.table().insert().execute.assert_called_once()


def test_create_owner_success_with_required_parameters_only(mock_supabase):
    """Test successful owner creation with only required parameters."""
    # Execute
    create_owner(
        owner_id=789,
        owner_name="minimal-owner",
        user_id=101,
        user_name="minimal-user"
    )
    
    # Assert
    mock_supabase.table.assert_called_once_with("owners")
    mock_supabase.table().insert.assert_called_once_with({
        "owner_id": 789,
        "owner_name": "minimal-owner",
        "stripe_customer_id": "",
        "created_by": "101:minimal-user",
        "updated_by": "101:minimal-user",
        "owner_type": "",
        "org_rules": "",
    })
    mock_supabase.table().insert().execute.assert_called_once()


def test_create_owner_with_empty_optional_parameters(mock_supabase):
    """Test owner creation with explicitly empty optional parameters."""
    # Execute
    create_owner(
        owner_id=999,
        owner_name="empty-optional-owner",
        user_id=202,
        user_name="empty-user",
        stripe_customer_id="",
        owner_type="",
        org_rules=""
    )
    
    # Assert
    mock_supabase.table().insert.assert_called_once_with({
        "owner_id": 999,
        "owner_name": "empty-optional-owner",
        "stripe_customer_id": "",
        "created_by": "202:empty-user",
        "updated_by": "202:empty-user",
        "owner_type": "",
        "org_rules": "",
    })


def test_create_owner_user_id_string_conversion(mock_supabase):
    """Test that user_id is properly converted to string in created_by and updated_by fields."""
    # Execute
    create_owner(
        owner_id=555,
        owner_name="string-test-owner",
        user_id=777,
        user_name="string-test-user"
    )
    
    # Assert - verify user_id is converted to string and concatenated properly
    call_args = mock_supabase.table().insert.call_args[0][0]
    assert call_args["created_by"] == "777:string-test-user"
    assert call_args["updated_by"] == "777:string-test-user"
    assert isinstance(call_args["created_by"], str)
    assert isinstance(call_args["updated_by"], str)


def test_create_owner_with_special_characters_in_names(mock_supabase):
    """Test owner creation with special characters in names."""
    # Execute
    create_owner(
        owner_id=333,
        owner_name="test-owner-with-dashes_and_underscores",
        user_id=444,
        user_name="test.user@example.com",
        stripe_customer_id="cus_special123",
        owner_type="User",
        org_rules="Rules with special chars: !@#$%^&*()"
    )
    
    # Assert
    mock_supabase.table().insert.assert_called_once_with({
        "owner_id": 333,
        "owner_name": "test-owner-with-dashes_and_underscores",
        "stripe_customer_id": "cus_special123",
        "created_by": "444:test.user@example.com",
        "updated_by": "444:test.user@example.com",
        "owner_type": "User",
        "org_rules": "Rules with special chars: !@#$%^&*()",
    })


def test_create_owner_supabase_exception_handled(mock_supabase):
    """Test that Supabase exceptions are handled by the decorator."""
    # Setup - make execute() raise an exception
    mock_supabase.table().insert().execute.side_effect = Exception("Database error")
    
    # Execute - should not raise exception due to handle_exceptions decorator
    result = create_owner(
        owner_id=666,
        owner_name="error-owner",
        user_id=777,
        user_name="error-user"
    )
    
    # Assert - should return None due to handle_exceptions decorator
    assert result is None
    mock_supabase.table().insert().execute.assert_called_once()


def test_create_owner_table_method_called_correctly(mock_supabase):
    """Test that the correct table name is used."""
    # Execute
    create_owner(
        owner_id=111,
        owner_name="table-test-owner",
        user_id=222,
        user_name="table-test-user"
    )
    
    # Assert
    mock_supabase.table.assert_called_once_with("owners")


def test_create_owner_method_chaining(mock_supabase):
    """Test that the Supabase method chaining works correctly."""
    # Execute
    create_owner(
        owner_id=888,
        owner_name="chain-test-owner",
        user_id=999,
        user_name="chain-test-user"
    )
    
    # Assert the complete chain
    mock_supabase.table.assert_called_once_with("owners")
    mock_supabase.table().insert.assert_called_once()
    mock_supabase.table().insert().execute.assert_called_once()


def test_create_owner_with_large_ids(mock_supabase):
    """Test owner creation with large ID values."""
    # Execute
    create_owner(
        owner_id=999999999999,
        owner_name="large-id-owner",
        user_id=888888888888,
        user_name="large-id-user"
    )
    
    # Assert
    call_args = mock_supabase.table().insert.call_args[0][0]
    assert call_args["owner_id"] == 999999999999
    assert call_args["created_by"] == "888888888888:large-id-user"
    assert call_args["updated_by"] == "888888888888:large-id-user"
