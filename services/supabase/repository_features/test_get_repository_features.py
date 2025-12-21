from unittest.mock import MagicMock, patch

from services.supabase.repository_features.get_repository_features import (
    get_repository_features,
)


@patch("services.supabase.repository_features.get_repository_features.supabase")
def test_get_repository_features_success(mock_supabase):
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()

    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.execute.return_value = MagicMock(
        data=[
            {
                "id": 1,
                "owner_id": 12345,
                "repo_id": 123456,
                "repo_name": "test-repo",
                "auto_merge": True,
                "auto_merge_only_test_files": False,
                "merge_method": "squash",
                "created_at": "2025-01-01T00:00:00Z",
                "created_by": "system",
                "updated_at": "2025-01-01T00:00:00Z",
                "updated_by": "system",
            }
        ]
    )

    result = get_repository_features(repo_id=123456)

    assert result is not None
    assert result["repo_id"] == 123456
    assert result["auto_merge"] is True
    assert result["merge_method"] == "squash"
    mock_supabase.table.assert_called_once_with("repository_features")
    mock_table.select.assert_called_once_with("*")
    mock_select.eq.assert_called_once_with("repo_id", 123456)


@patch("services.supabase.repository_features.get_repository_features.supabase")
def test_get_repository_features_not_found(mock_supabase):
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()

    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.execute.return_value = MagicMock(data=[])

    result = get_repository_features(repo_id=999999)

    assert result is None


@patch("services.supabase.repository_features.get_repository_features.supabase")
def test_get_repository_features_handles_error(mock_supabase):
    mock_supabase.table.side_effect = Exception("Database error")

    result = get_repository_features(repo_id=123456)

    assert result is None
