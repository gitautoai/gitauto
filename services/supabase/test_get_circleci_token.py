from unittest.mock import patch, MagicMock
import pytest

from services.supabase.get_circleci_token import get_circleci_token


@pytest.fixture
def mock_supabase():
    """Mock supabase client for testing."""
    with patch("services.supabase.get_circleci_token.supabase") as mock:
        # Setup the method chain properly
        mock_execute_result = MagicMock()
        mock_execute = MagicMock(return_value=mock_execute_result)
        mock_maybe_single = MagicMock()
        mock_maybe_single.execute = mock_execute
        mock_eq = MagicMock()
        mock_eq.maybe_single = MagicMock(return_value=mock_maybe_single)
        mock_select = MagicMock()
        mock_select.eq = MagicMock(return_value=mock_eq)
        mock_table = MagicMock()
        mock_table.select = MagicMock(return_value=mock_select)
        mock.table = MagicMock(return_value=mock_table)
        yield mock


def test_get_circleci_token_success(mock_supabase):
    """Test successful retrieval of CircleCI token."""
    # Setup
    expected_token = "test_circleci_token_123"
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = {
        "token": expected_token
    }
    
    # Execute
    result = get_circleci_token(owner_id=123456)
    
    # Assert
    assert result == expected_token
    mock_supabase.table.assert_called_once_with("circleci_tokens")
    mock_supabase.table().select.assert_called_once_with("token")
    mock_supabase.table().select().eq.assert_called_once_with("owner_id", 123456)
    mock_supabase.table().select().eq().maybe_single.assert_called_once()
    mock_supabase.table().select().eq().maybe_single().execute.assert_called_once()


def test_get_circleci_token_not_found(mock_supabase):
    """Test when no CircleCI token is found for the owner."""
    # Setup - no data returned
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = None
    
    # Execute
    result = get_circleci_token(owner_id=999999)
    
    # Assert
    assert result is None
    mock_supabase.table.assert_called_once_with("circleci_tokens")
    mock_supabase.table().select.assert_called_once_with("token")
    mock_supabase.table().select().eq.assert_called_once_with("owner_id", 999999)


def test_get_circleci_token_empty_data(mock_supabase):
    """Test when empty data is returned."""
    # Setup - empty data
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = {}
    
    # Execute
    result = get_circleci_token(owner_id=456789)
    
    # Assert
    assert result is None


def test_get_circleci_token_with_zero_owner_id(mock_supabase):
    """Test with zero owner ID."""
    # Setup
    expected_token = "token_for_zero_owner"
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = {
        "token": expected_token
    }
    
    # Execute
    result = get_circleci_token(owner_id=0)
    
    # Assert
    assert result == expected_token
    mock_supabase.table().select().eq.assert_called_once_with("owner_id", 0)


def test_get_circleci_token_with_negative_owner_id(mock_supabase):
    """Test with negative owner ID."""
    # Setup
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = None
    
    # Execute
    result = get_circleci_token(owner_id=-1)
    
    # Assert
    assert result is None
    mock_supabase.table().select().eq.assert_called_once_with("owner_id", -1)


def test_get_circleci_token_with_large_owner_id(mock_supabase):
    """Test with very large owner ID."""
    # Setup
    large_owner_id = 999999999999
    expected_token = "token_for_large_owner"
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = {
        "token": expected_token
    }
    
    # Execute
    result = get_circleci_token(owner_id=large_owner_id)
    
    # Assert
    assert result == expected_token
    mock_supabase.table().select().eq.assert_called_once_with("owner_id", large_owner_id)


def test_get_circleci_token_exception_handled(mock_supabase):
    """Test that exceptions are handled by the decorator."""
    # Setup - make execute() raise an exception
    mock_supabase.table().select().eq().maybe_single().execute.side_effect = Exception("Database error")
    
    # Execute - should not raise exception due to handle_exceptions decorator
    result = get_circleci_token(owner_id=666)
    
    # Assert - should return None due to handle_exceptions decorator
    assert result is None


def test_get_circleci_token_table_name():
    """Test that the correct table name is used."""
    with patch("services.supabase.get_circleci_token.supabase") as mock_supabase:
        mock_supabase.table().select().eq().maybe_single().execute.return_value.data = None
        
        get_circleci_token(owner_id=111)
        
        mock_supabase.table.assert_called_once_with("circleci_tokens")


def test_get_circleci_token_select_field():
    """Test that only the token field is selected."""
    with patch("services.supabase.get_circleci_token.supabase") as mock_supabase:
        mock_supabase.table().select().eq().maybe_single().execute.return_value.data = None
        
        get_circleci_token(owner_id=222)
        
        mock_supabase.table().select.assert_called_once_with("token")


@pytest.mark.parametrize("owner_id,expected_token", [
    (123, "token_123"),
    (456, "another_token_456"),
    (789, "special_token_789"),
    (0, "zero_token"),
    (999999999, "large_id_token"),
])
def test_get_circleci_token_parametrized(mock_supabase, owner_id, expected_token):
    """Test function with various owner IDs and tokens using parametrize."""
    # Setup
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = {
        "token": expected_token
    }
    
    # Execute
    result = get_circleci_token(owner_id=owner_id)
    
    # Assert
    assert result == expected_token
    mock_supabase.table().select().eq.assert_called_once_with("owner_id", owner_id)


def test_get_circleci_token_method_chaining(mock_supabase):
    """Test that the Supabase method chaining works correctly."""
    # Setup
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = None
    
    # Execute
    get_circleci_token(owner_id=888)
    
    # Assert the complete chain
    mock_supabase.table.assert_called_once_with("circleci_tokens")
    mock_supabase.table().select.assert_called_once()
    mock_supabase.table().select().eq.assert_called_once()
    mock_supabase.table().select().eq().maybe_single.assert_called_once()
    mock_supabase.table().select().eq().maybe_single().execute.assert_called_once()


def test_get_circleci_token_decorator_configuration():
    """Test that the handle_exceptions decorator is configured correctly."""
    # Import the function to check its decorator configuration
    from services.supabase.get_circleci_token import get_circleci_token
    
    # The function should have the decorator applied
    assert hasattr(get_circleci_token, "__wrapped__")
    assert get_circleci_token.__name__ == "get_circleci_token"


def test_get_circleci_token_return_value_structure(mock_supabase):
    """Test that the function returns the correct value structure."""
    # Setup with token
    expected_token = "test_token_structure"
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = {
        "token": expected_token,
        "other_field": "should_be_ignored"
    }
    
    # Execute
    result = get_circleci_token(owner_id=555)
    
    # Assert - should only return the token value, not the whole data object
    assert result == expected_token
    assert result != {"token": expected_token, "other_field": "should_be_ignored"}


def test_get_circleci_token_missing_token_field(mock_supabase):
    """Test when data exists but token field is missing."""
    # Setup - data exists but no token field
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = {
        "other_field": "some_value"
    }
    
    # Execute
    result = get_circleci_token(owner_id=777)
    
    # Assert - should return None when token field is missing
    assert result is None