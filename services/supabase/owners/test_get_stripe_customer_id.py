from unittest.mock import patch, MagicMock

import pytest

from services.supabase.owners.get_stripe_customer_id import get_stripe_customer_id


@pytest.fixture
def mock_supabase():
    """Fixture to provide a mocked supabase client."""
    with patch("services.supabase.owners.get_stripe_customer_id.supabase") as mock:
        yield mock


def test_get_stripe_customer_id_success(mock_supabase):
    """Test successful retrieval of stripe customer ID."""
    # Setup mock response
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.execute.return_value = (
        [None, [{"stripe_customer_id": "cus_test123"}]], 
        1
    )
    
    # Execute
    result = get_stripe_customer_id(owner_id=123456)
    
    # Verify
    assert result == "cus_test123"
    mock_supabase.table.assert_called_once_with(table_name="owners")
    mock_table.select.assert_called_once_with("stripe_customer_id")
    mock_select.eq.assert_called_once_with(column="owner_id", value=123456)
    mock_eq.execute.assert_called_once()


def test_get_stripe_customer_id_none_value(mock_supabase):
    """Test when stripe_customer_id is None in database."""
    # Setup mock response with None value
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.execute.return_value = (
        [None, [{"stripe_customer_id": None}]], 
        1
    )
    
    # Execute
    result = get_stripe_customer_id(owner_id=123456)
    
    # Verify
    assert result is None


def test_get_stripe_customer_id_empty_string(mock_supabase):
    """Test when stripe_customer_id is empty string."""
    # Setup mock response with empty string
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.execute.return_value = (
        [None, [{"stripe_customer_id": ""}]], 
        1
    )
    
    # Execute
    result = get_stripe_customer_id(owner_id=123456)
    
    # Verify
    assert result == ""


def test_get_stripe_customer_id_no_data(mock_supabase):
    """Test when no data is returned from database."""
    # Setup mock response with no data
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.execute.return_value = (None, 0)
    
    # Execute
    result = get_stripe_customer_id(owner_id=123456)
    
    # Verify
    assert result is None


def test_get_stripe_customer_id_empty_data_array(mock_supabase):
    """Test when data array is empty."""
    # Setup mock response with empty data array
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.execute.return_value = ([], 0)
    
    # Execute
    result = get_stripe_customer_id(owner_id=123456)
    
    # Verify
    assert result is None


def test_get_stripe_customer_id_insufficient_data_length(mock_supabase):
    """Test when data array has insufficient length."""
    # Setup mock response with insufficient data length
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.execute.return_value = ([None], 0)
    
    # Execute
    result = get_stripe_customer_id(owner_id=123456)
    
    # Verify
    assert result is None


def test_get_stripe_customer_id_none_second_element(mock_supabase):
    """Test when second element of data array is None."""
    # Setup mock response with None second element
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.execute.return_value = ([None, None], 0)
    
    # Execute
    result = get_stripe_customer_id(owner_id=123456)
    
    # Verify
    assert result is None


def test_get_stripe_customer_id_exception_handling(mock_supabase):
    """Test that exceptions are handled gracefully by the decorator."""
    # Setup mock to raise an exception
    mock_supabase.table.side_effect = Exception("Database connection error")
    
    # Execute
    result = get_stripe_customer_id(owner_id=123456)
    
    # Verify that the default return value is returned
    assert result is None


def test_get_stripe_customer_id_with_different_owner_ids(mock_supabase):
    """Test function with various owner ID values."""
    # Setup mock response
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.execute.return_value = (
        [None, [{"stripe_customer_id": "cus_different123"}]], 
        1
    )
    
    # Test with different owner IDs
    test_cases = [0, 1, 999999, 123456789]
    
    for owner_id in test_cases:
        result = get_stripe_customer_id(owner_id=owner_id)
        assert result == "cus_different123"
        
        # Verify the correct owner_id was passed
        calls = mock_select.eq.call_args_list
        assert any(call[1]["value"] == owner_id for call in calls)


def test_get_stripe_customer_id_multiple_records(mock_supabase):
    """Test when multiple records are returned (should use first one)."""
    # Setup mock response with multiple records
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.execute.return_value = (
        [None, [
            {"stripe_customer_id": "cus_first123"},
            {"stripe_customer_id": "cus_second456"}
        ]], 
        2
    )
    
    # Execute
    result = get_stripe_customer_id(owner_id=123456)
    
    # Verify that the first record is used
    assert result == "cus_first123"


def test_get_stripe_customer_id_long_customer_id(mock_supabase):
    """Test with a very long customer ID."""
    # Setup mock response with long customer ID
    long_customer_id = "cus_" + "a" * 100  # Very long customer ID
    
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.execute.return_value = (
        [None, [{"stripe_customer_id": long_customer_id}]], 
        1
    )
    
    # Execute
    result = get_stripe_customer_id(owner_id=123456)
    
    # Verify
    assert result == long_customer_id


@pytest.mark.parametrize("owner_id", [
    123456,
    0,
    -1,
    999999999,
])
def test_get_stripe_customer_id_parametrized_owner_ids(mock_supabase, owner_id):
    """Test function with various owner ID values using parametrize."""
    # Setup mock response
