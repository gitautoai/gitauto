from unittest.mock import MagicMock, patch

from services.supabase.circleci_tokens.get_circleci_token import get_circleci_token


def test_get_circleci_token_returns_token_when_found():
    mock_result = MagicMock()
    mock_result.data = {"token": "circleci_test_token_123"}

    with patch(
        "services.supabase.circleci_tokens.get_circleci_token.supabase"
    ) as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            mock_result
        )
        result = get_circleci_token(owner_id=12345)

    assert result == "circleci_test_token_123"


def test_get_circleci_token_returns_none_when_not_found():
    mock_result = MagicMock()
    mock_result.data = None

    with patch(
        "services.supabase.circleci_tokens.get_circleci_token.supabase"
    ) as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            mock_result
        )
        result = get_circleci_token(owner_id=12345)

    assert result is None


def test_get_circleci_token_returns_none_on_exception():
    with patch(
        "services.supabase.circleci_tokens.get_circleci_token.supabase"
    ) as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database error")
        result = get_circleci_token(owner_id=12345)

    assert result is None
