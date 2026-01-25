# pylint: disable=unused-argument
from unittest.mock import patch

from services.supabase.coverages.delete_stale_coverages import delete_stale_coverages


def test_deletes_stale_files():
    with patch(
        "services.supabase.coverages.delete_stale_coverages.get_all_coverages"
    ) as mock_all_cov, patch(
        "services.supabase.coverages.delete_stale_coverages.delete_coverages_by_paths"
    ) as mock_delete:
        mock_all_cov.return_value = [
            {"full_path": "src/main.py"},
            {"full_path": "src/deleted.py"},
        ]

        result = delete_stale_coverages(
            owner_id=123,
            repo_id=456,
            current_files={"src/main.py"},
        )

        assert result == 1
        mock_delete.assert_called_once_with(
            owner_id=123, repo_id=456, file_paths=["src/deleted.py"]
        )


def test_no_stale_files():
    with patch(
        "services.supabase.coverages.delete_stale_coverages.get_all_coverages"
    ) as mock_all_cov, patch(
        "services.supabase.coverages.delete_stale_coverages.delete_coverages_by_paths"
    ) as mock_delete:
        mock_all_cov.return_value = [
            {"full_path": "src/main.py"},
        ]

        result = delete_stale_coverages(
            owner_id=123,
            repo_id=456,
            current_files={"src/main.py"},
        )

        assert result == 0
        mock_delete.assert_not_called()
