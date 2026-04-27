from unittest.mock import Mock, patch

from services.supabase.repositories.get_repository_by_name import get_repository_by_name


def _build_chain(mock_supabase, data):
    mock_chain = Mock()
    mock_chain.data = data
    mock_supabase.table.return_value = mock_chain
    mock_chain.select.return_value = mock_chain
    mock_chain.eq.return_value = mock_chain
    mock_chain.maybe_single.return_value = mock_chain
    mock_chain.execute.return_value = mock_chain
    return mock_chain


def test_get_repository_by_name_success():
    data = {
        "id": 1,
        "repo_id": 123456,
        "repo_name": "test-repo",
        "owner_id": 789,
        "target_branch": "main",
    }

    with patch(
        "services.supabase.repositories.get_repository_by_name.supabase"
    ) as mock_supabase:
        mock_chain = _build_chain(mock_supabase, data)

        result = get_repository_by_name(
            platform="github", owner_id=789, repo_name="test-repo"
        )

        assert result is not None
        assert isinstance(result, dict)
        assert result["repo_id"] == 123456
        assert result["repo_name"] == "test-repo"
        assert result["owner_id"] == 789
        assert result["target_branch"] == "main"

        mock_supabase.table.assert_called_once_with("repositories")
        mock_chain.select.assert_called_once_with("*")
        mock_chain.eq.assert_any_call("platform", "github")
        mock_chain.eq.assert_any_call("owner_id", 789)
        mock_chain.eq.assert_any_call("repo_name", "test-repo")
        mock_chain.maybe_single.assert_called_once()
        mock_chain.execute.assert_called_once()


def test_get_repository_by_name_not_found():
    with patch(
        "services.supabase.repositories.get_repository_by_name.supabase"
    ) as mock_supabase:
        _build_chain(mock_supabase, None)

        result = get_repository_by_name(
            platform="github", owner_id=789, repo_name="nonexistent-repo"
        )

        assert result is None


def test_get_repository_by_name_exception_handling():
    with patch(
        "services.supabase.repositories.get_repository_by_name.supabase"
    ) as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database connection error")

        result = get_repository_by_name(
            platform="github", owner_id=789, repo_name="test-repo"
        )

        assert result is None


def test_get_repository_by_name_queries_by_both_owner_and_name():
    with patch(
        "services.supabase.repositories.get_repository_by_name.supabase"
    ) as mock_supabase:
        mock_chain = _build_chain(
            mock_supabase, {"repo_name": "test-repo", "owner_id": 789}
        )

        result = get_repository_by_name(
            platform="github", owner_id=789, repo_name="test-repo"
        )

        mock_chain.eq.assert_any_call("platform", "github")
        mock_chain.eq.assert_any_call("owner_id", 789)
        mock_chain.eq.assert_any_call("repo_name", "test-repo")
        assert result is not None
