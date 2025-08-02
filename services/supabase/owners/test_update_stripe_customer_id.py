from unittest.mock import MagicMock, patch

import pytest

from services.supabase.owners.update_stripe_customer_id import update_stripe_customer_id


@pytest.fixture
def mock_supabase():
    """Mock supabase client for testing."""
    with patch("services.supabase.owners.update_stripe_customer_id.supabase") as mock:
        # Setup the method chain properly
        mock_execute_result = MagicMock()
        mock_execute = MagicMock(return_value=mock_execute_result)
        mock_eq = MagicMock()
        mock_eq.execute = mock_execute
        mock_update = MagicMock()
        mock_update.eq = MagicMock(return_value=mock_eq)
        mock_table = MagicMock()
        mock_table.update = MagicMock(return_value=mock_update)
        mock.table = MagicMock(return_value=mock_table)
        yield mock


def test_update_stripe_customer_id_success(mock_supabase):
    """Test successful update of stripe customer ID."""
    # Execute
    result = update_stripe_customer_id(
        owner_id=123456, stripe_customer_id="cus_test123"
    )

    # Assert
    mock_supabase.table.assert_called_once_with("owners")
    mock_supabase.table().update.assert_called_once_with(
        {"stripe_customer_id": "cus_test123"}
    )
    mock_supabase.table().update().eq.assert_called_once_with("owner_id", 123456)
    mock_supabase.table().update().eq().execute.assert_called_once()
    assert result is None


def test_update_stripe_customer_id_with_empty_string(mock_supabase):
    """Test update with empty string stripe customer ID."""
    # Execute
    result = update_stripe_customer_id(owner_id=789, stripe_customer_id="")

    # Assert
    mock_supabase.table.assert_called_once_with("owners")
    mock_supabase.table().update.assert_called_once_with({"stripe_customer_id": ""})
    mock_supabase.table().update().eq.assert_called_once_with("owner_id", 789)
    mock_supabase.table().update().eq().execute.assert_called_once()
    assert result is None


def test_update_stripe_customer_id_with_long_customer_id(mock_supabase):
    """Test update with very long stripe customer ID."""
    long_customer_id = "cus_" + "a" * 100

    # Execute
    result = update_stripe_customer_id(
        owner_id=456, stripe_customer_id=long_customer_id
    )

    # Assert
    mock_supabase.table().update.assert_called_once_with(
        {"stripe_customer_id": long_customer_id}
    )
    mock_supabase.table().update().eq.assert_called_once_with("owner_id", 456)
    assert result is None


def test_update_stripe_customer_id_with_special_characters(mock_supabase):
    """Test update with special characters in stripe customer ID."""
    special_customer_id = "cus_test-123_special!@#$%"

    # Execute
    result = update_stripe_customer_id(
        owner_id=999, stripe_customer_id=special_customer_id
    )

    # Assert
    mock_supabase.table().update.assert_called_once_with(
        {"stripe_customer_id": special_customer_id}
    )
    mock_supabase.table().update().eq.assert_called_once_with("owner_id", 999)
    assert result is None


def test_update_stripe_customer_id_with_unicode_characters(mock_supabase):
    """Test update with unicode characters in stripe customer ID."""
    unicode_customer_id = "cus_test_ñáéíóú_123"

    # Execute
    result = update_stripe_customer_id(
        owner_id=111, stripe_customer_id=unicode_customer_id
    )

    # Assert
    mock_supabase.table().update.assert_called_once_with(
        {"stripe_customer_id": unicode_customer_id}
    )
    mock_supabase.table().update().eq.assert_called_once_with("owner_id", 111)
    assert result is None


def test_update_stripe_customer_id_with_zero_owner_id(mock_supabase):
    """Test update with zero owner ID."""
    # Execute
    result = update_stripe_customer_id(owner_id=0, stripe_customer_id="cus_zero123")

    # Assert
    mock_supabase.table().update().eq.assert_called_once_with("owner_id", 0)
    assert result is None


def test_update_stripe_customer_id_with_negative_owner_id(mock_supabase):
    """Test update with negative owner ID."""
    # Execute
    result = update_stripe_customer_id(
        owner_id=-1, stripe_customer_id="cus_negative123"
    )

    # Assert
    mock_supabase.table().update().eq.assert_called_once_with("owner_id", -1)
    assert result is None


def test_update_stripe_customer_id_with_large_owner_id(mock_supabase):
    """Test update with very large owner ID."""
    large_owner_id = 999999999999

    # Execute
    result = update_stripe_customer_id(
        owner_id=large_owner_id, stripe_customer_id="cus_large123"
    )

    # Assert
    mock_supabase.table().update().eq.assert_called_once_with(
        "owner_id", large_owner_id
    )
    assert result is None


def test_update_stripe_customer_id_supabase_exception_handled(mock_supabase):
    """Test that Supabase exceptions are handled by the decorator."""
    # Setup - make execute() raise an exception
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.side_effect = Exception(
        "Database error"
    )

    # Execute - should not raise exception due to handle_exceptions decorator
    result = update_stripe_customer_id(owner_id=666, stripe_customer_id="cus_error123")

    # Assert - should return None due to handle_exceptions decorator
    assert result is None
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.assert_called_once()


def test_update_stripe_customer_id_table_method_called_correctly(mock_supabase):
    """Test that the correct table name is used."""
    # Execute
    update_stripe_customer_id(owner_id=111, stripe_customer_id="cus_table123")

    # Assert
    mock_supabase.table.assert_called_once_with("owners")


def test_update_stripe_customer_id_method_chaining(mock_supabase):
    """Test that the Supabase method chaining works correctly."""
    # Execute
    update_stripe_customer_id(owner_id=888, stripe_customer_id="cus_chain123")

    # Assert the complete chain
    mock_supabase.table.assert_called_once_with("owners")
    mock_supabase.table().update.assert_called_once()
    mock_supabase.table().update().eq.assert_called_once()
    mock_supabase.table().update().eq().execute.assert_called_once()


def test_update_stripe_customer_id_attribute_error_handled(mock_supabase):
    """Test that AttributeError is handled by the decorator."""
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.side_effect = AttributeError(
        "Attribute error"
    )
    result = update_stripe_customer_id(7001, "cus_error123")
    assert result is None


def test_update_stripe_customer_id_key_error_handled(mock_supabase):
    """Test that KeyError is handled by the decorator."""
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.side_effect = KeyError(
        "Key error"
    )
    result = update_stripe_customer_id(7003, "cus_error123")
    assert result is None


def test_update_stripe_customer_id_type_error_handled(mock_supabase):
    """Test that TypeError is handled by the decorator."""
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.side_effect = TypeError(
        "Type error"
    )
    result = update_stripe_customer_id(7005, "cus_error123")
    assert result is None


def test_update_stripe_customer_id_generic_exception_handled(mock_supabase):
    """Test that generic Exception is handled by the decorator."""
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.side_effect = Exception(
        "Generic error"
    )
    result = update_stripe_customer_id(7007, "cus_error123")
    assert result is None


def test_update_stripe_customer_id_decorator_configuration():
    """Test that the handle_exceptions decorator is configured correctly."""
    # This test verifies the decorator configuration by checking the function attributes
    # The decorator should be configured with default_return_value=None and raise_on_error=False

    # Import the function to check its decorator configuration
    from services.supabase.owners.update_stripe_customer_id import (
        update_stripe_customer_id,
    )

    # The function should have the decorator applied
    assert hasattr(update_stripe_customer_id, "__wrapped__")

    # Test that exceptions are handled properly (already covered in other tests)
    # This test mainly serves as documentation of the expected decorator behavior
    assert update_stripe_customer_id.__name__ == "update_stripe_customer_id"


def test_update_stripe_customer_id_whitespace_handling(mock_supabase):
    """Test update with whitespace in stripe customer ID."""
    customer_id_with_spaces = "  cus_spaces123  "

    # Execute
    result = update_stripe_customer_id(
        owner_id=5001, stripe_customer_id=customer_id_with_spaces
    )

    # Assert - whitespace should be preserved as-is
    mock_supabase.table().update.assert_called_once_with(
        {"stripe_customer_id": customer_id_with_spaces}
    )
    assert result is None


@pytest.mark.parametrize(
    "owner_id,stripe_customer_id",
    [
        (123456, "cus_test123"),
        (0, "cus_zero"),
        (-1, "cus_negative"),
        (999999999, "cus_large"),
        (42, ""),
        (100, "cus_special!@#$%"),
    ],
)
def test_update_stripe_customer_id_parametrized(
    mock_supabase, owner_id, stripe_customer_id
):
    """Test function with various parameter combinations using parametrize."""
    # Execute
    result = update_stripe_customer_id(
        owner_id=owner_id, stripe_customer_id=stripe_customer_id
    )

    # Assert
    mock_supabase.table().update.assert_called_once_with(
        {"stripe_customer_id": stripe_customer_id}
    )
    mock_supabase.table().update().eq.assert_called_once_with("owner_id", owner_id)
    assert result is None


def test_update_stripe_customer_id_function_signature():
    """Test that the function signature matches expectations."""
    import inspect
    from services.supabase.owners.update_stripe_customer_id import (
        update_stripe_customer_id,
    )

    # Get function signature
    sig = inspect.signature(update_stripe_customer_id)
    params = list(sig.parameters.keys())

    # Assert expected parameters are present
    expected_params = ["owner_id", "stripe_customer_id"]
    assert params == expected_params

    # Check that parameters don't have default values (both are required)
    for param_name in expected_params:
        param = sig.parameters[param_name]
        assert param.default == inspect.Parameter.empty


def test_update_stripe_customer_id_return_value_on_success(mock_supabase):
    """Test that update_stripe_customer_id returns None on successful execution."""
    # Execute
    result = update_stripe_customer_id(
        owner_id=3001, stripe_customer_id="cus_return123"
    )

    # Assert - function should return None (implicit return)
    assert result is None


def test_update_stripe_customer_id_update_data_structure(mock_supabase):
    """Test that the update data structure is correct."""
    stripe_customer_id = "cus_structure123"

    # Execute
    update_stripe_customer_id(owner_id=4001, stripe_customer_id=stripe_customer_id)

    # Assert - verify the exact structure of the update data
    call_args = mock_supabase.table().update.call_args[0][0]
    assert isinstance(call_args, dict)
    assert len(call_args) == 1
    assert "stripe_customer_id" in call_args
    assert call_args["stripe_customer_id"] == stripe_customer_id
