from unittest.mock import Mock, patch

from services.supabase.repositories.get_repository import get_repository


def test_get_repository_success():
    """Test get_repository returns correct repository data when found."""
    mock_result = Mock()
    mock_result.data = {
        "id": 1,
        "repo_id": 123456,
        "repo_name": "test-repo",
        "owner_id": 789,
        "created_by": "user:test",
        "updated_by": "user:test",
        "file_count": 100,
        "blank_lines": 50,
        "comment_lines": 30,
        "code_lines": 200,
        "target_branch": "main",
        "trigger_on_commit": True,
        "trigger_on_merged": False,
        "trigger_on_pr_change": True,
        "trigger_on_review_comment": False,
        "trigger_on_schedule": False,
        "trigger_on_test_failure": True,
        "schedule_execution_count": 0,
        "schedule_include_weekends": False,
        "schedule_interval_minutes": 60,
    }

    with patch(
        "services.supabase.repositories.get_repository.supabase"
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

        result = get_repository(owner_id=789, repo_id=123456)

        assert result is not None
        assert isinstance(result, dict)
        assert result["repo_id"] == 123456
        assert result["repo_name"] == "test-repo"
        assert result["owner_id"] == 789

        mock_supabase.table.assert_called_once_with("repositories")
        mock_table.select.assert_called_once_with("*")
        mock_select.eq.assert_called_once_with("owner_id", 789)
        mock_eq1.eq.assert_called_once_with("repo_id", 123456)
        mock_eq2.maybe_single.assert_called_once()
        mock_maybe_single.execute.assert_called_once()


def test_get_repository_not_found():
    """Test get_repository returns None when no data is found."""
    mock_result = Mock()
    mock_result.data = None

    with patch(
        "services.supabase.repositories.get_repository.supabase"
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

        result = get_repository(owner_id=789, repo_id=999999)

        assert result is None


def test_get_repository_exception_handling():
    """Test get_repository handles exceptions and returns None due to decorator."""
    with patch(
        "services.supabase.repositories.get_repository.supabase"
    ) as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database connection error")

        result = get_repository(owner_id=789, repo_id=123456)

        assert result is None


def test_get_repository_queries_by_both_owner_and_repo():
    """Test that get_repository queries by both owner_id and repo_id."""
    mock_result = Mock()
    mock_result.data = {"repo_id": 123456, "owner_id": 789}

    with patch(
        "services.supabase.repositories.get_repository.supabase"
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

        result = get_repository(owner_id=789, repo_id=123456)

        mock_select.eq.assert_called_once_with("owner_id", 789)
        mock_eq1.eq.assert_called_once_with("repo_id", 123456)
        assert result is not None
