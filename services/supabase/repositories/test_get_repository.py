from unittest.mock import Mock, patch

from services.supabase.repositories.get_repository import get_repository


def _build_chain(mock_supabase, data):
    mock_chain = Mock()
    mock_chain.data = data
    mock_supabase.table.return_value = mock_chain
    mock_chain.select.return_value = mock_chain
    mock_chain.eq.return_value = mock_chain
    mock_chain.maybe_single.return_value = mock_chain
    mock_chain.execute.return_value = mock_chain
    return mock_chain


def test_get_repository_success():
    """Test get_repository returns correct repository data when found."""
    data = {
        "id": 1,
        "repo_id": 123456,
        "repo_name": "test-repo",
        "owner_id": 789,
        "created_by": "user:test",
        "updated_by": "user:test",
        "file_count": 100,
        "code_lines": 200,
        "target_branch": "main",
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
        mock_chain = _build_chain(mock_supabase, data)

        result = get_repository(platform="github", owner_id=789, repo_id=123456)

        assert result is not None
        assert isinstance(result, dict)
        assert result["repo_id"] == 123456
        assert result["repo_name"] == "test-repo"
        assert result["owner_id"] == 789

        mock_supabase.table.assert_called_once_with("repositories")
        mock_chain.select.assert_called_once_with("*")
        mock_chain.eq.assert_any_call("platform", "github")
        mock_chain.eq.assert_any_call("owner_id", 789)
        mock_chain.eq.assert_any_call("repo_id", 123456)
        mock_chain.maybe_single.assert_called_once()
        mock_chain.execute.assert_called_once()


def test_get_repository_not_found():
    """Test get_repository returns None when no data is found."""
    with patch(
        "services.supabase.repositories.get_repository.supabase"
    ) as mock_supabase:
        _build_chain(mock_supabase, None)

        result = get_repository(platform="github", owner_id=789, repo_id=999999)

        assert result is None


def test_get_repository_exception_handling():
    """Test get_repository handles exceptions and returns None due to decorator."""
    with patch(
        "services.supabase.repositories.get_repository.supabase"
    ) as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database connection error")

        result = get_repository(platform="github", owner_id=789, repo_id=123456)

        assert result is None


def test_get_repository_queries_by_both_owner_and_repo():
    """Test that get_repository queries by both owner_id and repo_id."""
    with patch(
        "services.supabase.repositories.get_repository.supabase"
    ) as mock_supabase:
        mock_chain = _build_chain(mock_supabase, {"repo_id": 123456, "owner_id": 789})

        result = get_repository(platform="github", owner_id=789, repo_id=123456)

        mock_chain.eq.assert_any_call("platform", "github")
        mock_chain.eq.assert_any_call("owner_id", 789)
        mock_chain.eq.assert_any_call("repo_id", 123456)
        assert result is not None
