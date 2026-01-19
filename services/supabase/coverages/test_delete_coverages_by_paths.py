from unittest.mock import MagicMock, patch

from services.supabase.coverages.delete_coverages_by_paths import (
    delete_coverages_by_paths,
)


def test_delete_coverages_by_paths_deletes_matching_records():
    with patch(
        "services.supabase.coverages.delete_coverages_by_paths.supabase"
    ) as mock_supabase:
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.delete.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = MagicMock(
            data=[{"full_path": "deleted/file.py"}]
        )

        result = delete_coverages_by_paths(
            owner_id=123,
            repo_id=456,
            file_paths=["deleted/file.py"],
        )

        mock_supabase.table.assert_called_once_with("coverages")
        mock_table.delete.assert_called_once()
        mock_table.eq.assert_any_call("owner_id", 123)
        mock_table.eq.assert_any_call("repo_id", 456)
        mock_table.in_.assert_called_once_with("full_path", ["deleted/file.py"])
        assert result == [{"full_path": "deleted/file.py"}]


def test_delete_coverages_by_paths_returns_none_for_empty_list():
    result = delete_coverages_by_paths(
        owner_id=123,
        repo_id=456,
        file_paths=[],
    )

    assert result is None


def test_delete_coverages_by_paths_handles_multiple_files():
    with patch(
        "services.supabase.coverages.delete_coverages_by_paths.supabase"
    ) as mock_supabase:
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.delete.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = MagicMock(
            data=[
                {"full_path": "deleted/file1.py"},
                {"full_path": "deleted/file2.py"},
            ]
        )

        result = delete_coverages_by_paths(
            owner_id=123,
            repo_id=456,
            file_paths=["deleted/file1.py", "deleted/file2.py"],
        )

        mock_table.in_.assert_called_once_with(
            "full_path", ["deleted/file1.py", "deleted/file2.py"]
        )
        assert result is not None
        assert len(result) == 2
