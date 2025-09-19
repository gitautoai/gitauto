from unittest.mock import Mock, patch

from services.supabase.usage.get_usage_by_pr import get_usage_by_pr


def test_get_usage_by_pr_success():
    with patch("services.supabase.usage.get_usage_by_pr.supabase") as mock_supabase:
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_eq3 = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.eq.return_value = mock_eq3
        mock_eq3.execute.return_value = Mock(data=[{"id": 1}, {"id": 2}])

        result = get_usage_by_pr(owner_id=123, repo_id=456, pr_number=789)

        assert result == [{"id": 1}, {"id": 2}]
        mock_supabase.table.assert_called_once_with("usage")
        mock_table.select.assert_called_once_with("id")
        mock_select.eq.assert_called_once_with("owner_id", 123)
        mock_eq1.eq.assert_called_once_with("repo_id", 456)
        mock_eq2.eq.assert_called_once_with("pr_number", 789)


def test_get_usage_by_pr_empty_result():
    with patch("services.supabase.usage.get_usage_by_pr.supabase") as mock_supabase:
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_eq3 = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.eq.return_value = mock_eq3
        mock_eq3.execute.return_value = Mock(data=[])

        result = get_usage_by_pr(owner_id=123, repo_id=456, pr_number=789)

        assert result == []


def test_get_usage_by_pr_with_exception():
    with patch("services.supabase.usage.get_usage_by_pr.supabase") as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database error")

        result = get_usage_by_pr(owner_id=123, repo_id=456, pr_number=789)

        assert result == []
