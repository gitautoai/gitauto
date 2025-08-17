from unittest.mock import MagicMock, patch
import pytest

from services.supabase.get_circleci_token import get_circleci_token


@pytest.fixture
def mock_supabase():
    """Mock supabase client for testing."""
    with patch("services.supabase.get_circleci_token.supabase") as mock:
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
    owner_id = 123456
    expected_token = "circle-ci-token-123"
    
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = {
        "token": expected_token
    }
    
    result = get_circleci_token(owner_id)
    
    assert result == expected_token
    mock_supabase.table.assert_called_once_with("circleci_tokens")
    mock_supabase.table().select.assert_called_once_with("token")
    mock_supabase.table().select().eq.assert_called_once_with("owner_id", owner_id)


def test_get_circleci_token_not_found(mock_supabase):
    """Test when no CircleCI token is found for the owner."""
    owner_id = 789
    
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = None
    
    result = get_circleci_token(owner_id)
    
    assert result is None
    mock_supabase.table.assert_called_once_with("circleci_tokens")


def test_get_circleci_token_empty_data(mock_supabase):
    """Test when response data is empty dict."""
    owner_id = 456
    
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = {}
    
    result = get_circleci_token(owner_id)
    
    assert result is None


def test_get_circleci_token_with_zero_owner_id(mock_supabase):
    """Test with zero owner ID."""
    owner_id = 0
    expected_token = "token-for-zero-owner"
    
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = {
        "token": expected_token
    }
    
    result = get_circleci_token(owner_id)
    
    assert result == expected_token
    mock_supabase.table().select().eq.assert_called_once_with("owner_id", 0)


def test_get_circleci_token_exception_handling(mock_supabase):
    """Test that exceptions are handled by the decorator."""
    owner_id = 123
    
    mock_supabase.table().select().eq().maybe_single().execute.side_effect = Exception("Database error")
    
    result = get_circleci_token(owner_id)
    
    assert result is None


@pytest.mark.parametrize("owner_id,expected_token", [
    (123456, "token-123"),
    (0, "token-zero"),
    (999999999, "token-large"),
])
def test_get_circleci_token_parametrized(mock_supabase, owner_id, expected_token):
    """Test function with various parameter combinations."""
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = {
        "token": expected_token
    }
    
    result = get_circleci_token(owner_id)
    
    assert result == expected_token
    mock_supabase.table().select().eq.assert_called_once_with("owner_id", owner_id)


def test_get_circleci_token_table_name(mock_supabase):
    """Test that the correct table name is used."""
    owner_id = 123
    
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = None
    
    get_circleci_token(owner_id)
    
    mock_supabase.table.assert_called_once_with("circleci_tokens")


def test_get_circleci_token_select_field(mock_supabase):
    """Test that only the token field is selected."""
    owner_id = 123
    
    mock_supabase.table().select().eq().maybe_single().execute.return_value.data = None
    
    get_circleci_token(owner_id)
    
    mock_supabase.table().select.assert_called_once_with("token")