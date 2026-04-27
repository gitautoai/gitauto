from unittest.mock import MagicMock, patch

from services.supabase.credits.check_purchase_exists import check_purchase_exists


@patch("services.supabase.credits.check_purchase_exists.supabase")
def test_returns_true_when_purchase_exists(mock_supabase):
    mock_result = MagicMock()
    mock_result.data = [{"id": 1}]
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = (
        mock_result
    )

    assert check_purchase_exists(platform="github", owner_id=123) is True


@patch("services.supabase.credits.check_purchase_exists.supabase")
def test_returns_false_when_no_purchase(mock_supabase):
    mock_result = MagicMock()
    mock_result.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = (
        mock_result
    )

    assert check_purchase_exists(platform="github", owner_id=456) is False


@patch("services.supabase.credits.check_purchase_exists.supabase")
def test_queries_credits_table_with_purchase_type(mock_supabase):
    mock_result = MagicMock()
    mock_result.data = []
    mock_table = mock_supabase.table.return_value
    mock_select = mock_table.select.return_value
    mock_eq1 = mock_select.eq.return_value
    mock_eq2 = mock_eq1.eq.return_value
    mock_eq3 = mock_eq2.eq.return_value
    mock_eq3.limit.return_value.execute.return_value = mock_result

    check_purchase_exists(platform="github", owner_id=789)

    mock_supabase.table.assert_called_with("credits")
    mock_table.select.assert_called_with("id")
    mock_select.eq.assert_called_with("platform", "github")
    mock_eq1.eq.assert_called_with("owner_id", 789)
    mock_eq2.eq.assert_called_with("transaction_type", "purchase")
