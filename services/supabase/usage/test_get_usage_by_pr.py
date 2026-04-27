from unittest.mock import Mock, patch

from services.supabase.usage.get_usage_by_pr import get_usage_by_pr


def _build_chain(mock_supabase, data):
    mock_chain = Mock()
    mock_chain.data = data
    mock_supabase.table.return_value = mock_chain
    mock_chain.select.return_value = mock_chain
    mock_chain.eq.return_value = mock_chain
    mock_chain.execute.return_value = mock_chain
    return mock_chain


def test_get_usage_by_pr_success():
    with patch("services.supabase.usage.get_usage_by_pr.supabase") as mock_supabase:
        mock_chain = _build_chain(mock_supabase, [{"id": 1}, {"id": 2}])

        result = get_usage_by_pr(
            platform="github", owner_id=123, repo_id=456, pr_number=789
        )

        assert result == [{"id": 1}, {"id": 2}]
        mock_supabase.table.assert_called_once_with("usage")
        mock_chain.select.assert_called_once_with("id")
        mock_chain.eq.assert_any_call("platform", "github")
        mock_chain.eq.assert_any_call("owner_id", 123)
        mock_chain.eq.assert_any_call("repo_id", 456)
        mock_chain.eq.assert_any_call("pr_number", 789)


def test_get_usage_by_pr_empty_result():
    with patch("services.supabase.usage.get_usage_by_pr.supabase") as mock_supabase:
        _build_chain(mock_supabase, [])

        result = get_usage_by_pr(
            platform="github", owner_id=123, repo_id=456, pr_number=789
        )

        assert not result


def test_get_usage_by_pr_with_exception():
    with patch("services.supabase.usage.get_usage_by_pr.supabase") as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database error")

        result = get_usage_by_pr(
            platform="github", owner_id=123, repo_id=456, pr_number=789
        )

        assert not result
