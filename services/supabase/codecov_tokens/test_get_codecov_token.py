from unittest.mock import Mock, patch

from services.supabase.codecov_tokens.get_codecov_token import get_codecov_token


@patch("services.supabase.codecov_tokens.get_codecov_token.supabase")
def test_get_codecov_token_success(mock_supabase):
    mock_response = Mock()
    mock_response.data = {"token": "test_codecov_token_12345"}
    mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
        mock_response
    )

    result = get_codecov_token(owner_id=123)

    assert result == "test_codecov_token_12345"
    mock_supabase.table.assert_called_once_with("codecov_tokens")
    mock_supabase.table.return_value.select.assert_called_once_with("token")
    mock_supabase.table.return_value.select.return_value.eq.assert_called_once_with(
        "owner_id", 123
    )


@patch("services.supabase.codecov_tokens.get_codecov_token.supabase")
def test_get_codecov_token_not_found(mock_supabase):
    mock_response = Mock()
    mock_response.data = None
    mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
        mock_response
    )

    result = get_codecov_token(owner_id=999)

    assert result is None
