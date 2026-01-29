from unittest.mock import Mock, patch

from services.supabase.repositories.get_repository_by_name import get_repository_by_name


def test_get_repository_by_name_success():
    mock_result = Mock()
    mock_result.data = {
        "id": 1,
        "repo_id": 123456,
        "repo_name": "test-repo",
        "owner_id": 789,
        "target_branch": "main",
    }

    with patch(
        "services.supabase.repositories.get_repository_by_name.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_maybe_single = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.maybe_single.return_value = mock_maybe_single
        mock_maybe_single.execute.return_value = mock_result

        result = get_repository_by_name(owner_id=789, repo_name="test-repo")

        assert result is not None
        assert isinstance(result, dict)
        assert result["repo_id"] == 123456
        assert result["repo_name"] == "test-repo"
        assert result["owner_id"] == 789
        assert result["target_branch"] == "main"

        mock_supabase.table.assert_called_once_with("repositories")
        mock_table.select.assert_called_once_with("*")
        mock_select.eq.assert_called_once_with("owner_id", 789)
        mock_eq1.eq.assert_called_once_with("repo_name", "test-repo")
        mock_eq2.maybe_single.assert_called_once()
        mock_maybe_single.execute.assert_called_once()


def test_get_repository_by_name_not_found():
    mock_result = Mock()
    mock_result.data = None

    with patch(
        "services.supabase.repositories.get_repository_by_name.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_maybe_single = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.maybe_single.return_value = mock_maybe_single
        mock_maybe_single.execute.return_value = mock_result

        result = get_repository_by_name(owner_id=789, repo_name="nonexistent-repo")

        assert result is None


def test_get_repository_by_name_exception_handling():
    with patch(
        "services.supabase.repositories.get_repository_by_name.supabase"
    ) as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database connection error")

        result = get_repository_by_name(owner_id=789, repo_name="test-repo")

        assert result is None


def test_get_repository_by_name_queries_by_both_owner_and_name():
    mock_result = Mock()
    mock_result.data = {"repo_name": "test-repo", "owner_id": 789}

    with patch(
        "services.supabase.repositories.get_repository_by_name.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_maybe_single = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.maybe_single.return_value = mock_maybe_single
        mock_maybe_single.execute.return_value = mock_result

        result = get_repository_by_name(owner_id=789, repo_name="test-repo")

        mock_select.eq.assert_called_once_with("owner_id", 789)
        mock_eq1.eq.assert_called_once_with("repo_name", "test-repo")
        assert result is not None
