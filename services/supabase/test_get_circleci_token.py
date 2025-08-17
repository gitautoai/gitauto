"""Test for get_circleci_token function."""

from unittest.mock import Mock, patch

from services.supabase.get_circleci_token import get_circleci_token


@patch("services.supabase.get_circleci_token.supabase")
def test_get_circleci_token_exists(mock_supabase):
    """Test getting CircleCI token when it exists."""
    # Mock the chain of calls
    mock_table = Mock()
    mock_select = Mock()
    mock_eq = Mock()
    mock_maybe_single = Mock()

    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.maybe_single.return_value = mock_maybe_single

    # Mock successful response with token
    mock_response = Mock()
    mock_response.data = {"token": "test-circleci-token-123"}
    mock_maybe_single.execute.return_value = mock_response

    result = get_circleci_token(owner_id=12345)

    assert result == "test-circleci-token-123"
    mock_supabase.table.assert_called_once_with("circleci_tokens")
    mock_table.select.assert_called_once_with("token")
    mock_select.eq.assert_called_once_with("owner_id", 12345)


@patch("services.supabase.get_circleci_token.supabase")
def test_get_circleci_token_not_exists(mock_supabase):
    """Test getting CircleCI token when it doesn't exist."""
    # Mock the chain of calls
    mock_table = Mock()
    mock_select = Mock()
    mock_eq = Mock()
    mock_maybe_single = Mock()

    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.maybe_single.return_value = mock_maybe_single

    # Mock response with no data
    mock_response = Mock()
    mock_response.data = None
    mock_maybe_single.execute.return_value = mock_response

    result = get_circleci_token(owner_id=99999)

    assert result is None
    mock_supabase.table.assert_called_once_with("circleci_tokens")


@patch("services.supabase.get_circleci_token.supabase")
def test_get_circleci_token_exception(mock_supabase):
    """Test getting CircleCI token when an exception occurs."""
    # Mock to raise an exception
    mock_supabase.table.side_effect = Exception("Database error")

    result = get_circleci_token(owner_id=12345)

    # Should return None due to @handle_exceptions
    assert result is None
