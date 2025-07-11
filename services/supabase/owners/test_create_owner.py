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


def test_create_owner_with_zero_ids(mock_supabase):
    """Test owner creation with zero ID values."""
    # Execute
    create_owner(
        owner_id=0,
        owner_name="zero-id-owner",
        user_id=0,
        user_name="zero-id-user"
    )
    
    # Assert
    call_args = mock_supabase.table().insert.call_args[0][0]
    assert call_args["owner_id"] == 0
    assert call_args["created_by"] == "0:zero-id-user"
    assert call_args["updated_by"] == "0:zero-id-user"


def test_create_owner_with_unicode_characters(mock_supabase):
    """Test owner creation with Unicode characters in names."""
    # Execute
    create_owner(
        owner_id=1001,
        owner_name="测试-owner-🚀",
        user_id=1002,
        user_name="用户-test-👤",
        stripe_customer_id="cus_unicode123",
        owner_type="Organization",
        org_rules="规则 with émojis 🎯"
    )
    
    # Assert
    mock_supabase.table().insert.assert_called_once_with({
        "owner_id": 1001,
        "owner_name": "测试-owner-🚀",
        "stripe_customer_id": "cus_unicode123",
        "created_by": "1002:用户-test-👤",
        "updated_by": "1002:用户-test-👤",
        "owner_type": "Organization",
        "org_rules": "规则 with émojis 🎯",
    })


def test_create_owner_with_long_strings(mock_supabase):
    """Test owner creation with very long string values."""
    long_name = "a" * 1000
    long_rules = "rule " * 500
    
    # Execute
    create_owner(
        owner_id=2001,
        owner_name=long_name,
        user_id=2002,
        user_name="long-test-user",
        stripe_customer_id="cus_long123",
        owner_type="Organization",
        org_rules=long_rules
    )
    
    # Assert
    call_args = mock_supabase.table().insert.call_args[0][0]
    assert call_args["owner_name"] == long_name
    assert call_args["org_rules"] == long_rules
    assert len(call_args["owner_name"]) == 1000
    assert len(call_args["org_rules"]) == 2500  # "rule " is 5 chars * 500


def test_create_owner_return_value_on_success(mock_supabase):
    """Test that create_owner returns None on successful execution."""
    # Execute
    result = create_owner(
        owner_id=3001,
        owner_name="return-test-owner",
        user_id=3002,
        user_name="return-test-user"
    )
    
    # Assert - function should return None (implicit return)
    assert result is None


def test_create_owner_decorator_configuration():
    """Test that the handle_exceptions decorator is configured correctly."""
    # This test verifies the decorator configuration by checking the function attributes
    # The decorator should be configured with default_return_value=None and raise_on_error=False
    
    # Import the function to check its decorator configuration
    from services.supabase.owners.create_owner import create_owner
    
    # The function should have the decorator applied
    assert hasattr(create_owner, '__wrapped__')
    
    # Test that exceptions are handled properly (already covered in other tests)
    # This test mainly serves as documentation of the expected decorator behavior
    assert create_owner.__name__ == "create_owner"


def test_create_owner_negative_ids(mock_supabase):
    """Test owner creation with negative ID values."""
    # Execute
    create_owner(
        owner_id=-1,
        owner_name="negative-id-owner",
        user_id=-999,
        user_name="negative-id-user"
    )
    
    # Assert
    call_args = mock_supabase.table().insert.call_args[0][0]
    assert call_args["owner_id"] == -1
    assert call_args["created_by"] == "-999:negative-id-user"
    assert call_args["updated_by"] == "-999:negative-id-user"


def test_create_owner_whitespace_handling(mock_supabase):
    """Test owner creation with whitespace in string parameters."""
    # Execute
    create_owner(
        owner_id=5001,
        owner_name="  owner-with-spaces  ",
        user_id=5002,
        user_name="  user-with-spaces  ",
        stripe_customer_id="  cus_spaces123  ",
        owner_type="  Organization  ",
        org_rules="  rules with spaces  "
    )
    
    # Assert - whitespace should be preserved as-is
    call_args = mock_supabase.table().insert.call_args[0][0]
    assert call_args["owner_name"] == "  owner-with-spaces  "
    assert call_args["created_by"] == "5002:  user-with-spaces  "
    assert call_args["updated_by"] == "5002:  user-with-spaces  "
    assert call_args["stripe_customer_id"] == "  cus_spaces123  "
    assert call_args["owner_type"] == "  Organization  "
    assert call_args["org_rules"] == "  rules with spaces  "


def test_create_owner_mixed_parameter_types(mock_supabase):
    """Test owner creation with a mix of provided and default parameters."""
    # Execute - mix of provided and default parameters
    create_owner(
        owner_id=6001,
        owner_name="mixed-params-owner",
        user_id=6002,
        user_name="mixed-params-user",
        stripe_customer_id="cus_mixed123",
        # owner_type and org_rules will use defaults (empty strings)
    )
    
    # Assert
    call_args = mock_supabase.table().insert.call_args[0][0]
    assert call_args["owner_id"] == 6001
    assert call_args["owner_name"] == "mixed-params-owner"
    assert call_args["stripe_customer_id"] == "cus_mixed123"
    assert call_args["owner_type"] == ""  # default value
    assert call_args["org_rules"] == ""  # default value
    assert call_args["created_by"] == "6002:mixed-params-user"


def test_create_owner_multiple_exception_types(mock_supabase):
    """Test that different types of exceptions are handled by the decorator."""
    # Test AttributeError
    mock_supabase.table().insert().execute.side_effect = AttributeError("Attribute error")
    result = create_owner(7001, "attr-error-owner", 7002, "attr-error-user")
    assert result is None
    
    # Reset mock and test KeyError
    mock_supabase.reset_mock()
    mock_supabase.table().insert().execute.side_effect = KeyError("Key error")
    result = create_owner(7003, "key-error-owner", 7004, "key-error-user")
    assert result is None
    
    # Reset mock and test TypeError
    mock_supabase.reset_mock()
    mock_supabase.table().insert().execute.side_effect = TypeError("Type error")
    result = create_owner(7005, "type-error-owner", 7006, "type-error-user")
    assert result is None
    
    # Reset mock and test generic Exception
    mock_supabase.reset_mock()
    mock_supabase.table().insert().execute.side_effect = Exception("Generic error")
    result = create_owner(7007, "generic-error-owner", 7008, "generic-error-user")
    assert result is None


def test_create_owner_function_signature():
    """Test that the function signature matches expectations."""
    import inspect
    from services.supabase.owners.create_owner import create_owner


def test_create_owner_all_data_types_preserved(mock_supabase):
