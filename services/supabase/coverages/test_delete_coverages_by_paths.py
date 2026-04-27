import os
from unittest.mock import MagicMock, patch

import pytest
from postgrest.exceptions import APIError

from constants.supabase import SUPABASE_BATCH_SIZE
from services.supabase.client import supabase
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
            platform="github",
            owner_id=123,
            repo_id=456,
            file_paths=["deleted/file.py"],
        )

        mock_supabase.table.assert_called_once_with("coverages")
        mock_table.delete.assert_called_once()
        mock_table.eq.assert_any_call("platform", "github")
        mock_table.eq.assert_any_call("owner_id", 123)
        mock_table.eq.assert_any_call("repo_id", 456)
        mock_table.in_.assert_called_once_with("full_path", ["deleted/file.py"])
        assert result == [{"full_path": "deleted/file.py"}]


def test_delete_coverages_by_paths_returns_empty_list_for_empty_input():
    result = delete_coverages_by_paths(
        platform="github",
        owner_id=123,
        repo_id=456,
        file_paths=[],
    )

    assert not result


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
            platform="github",
            owner_id=123,
            repo_id=456,
            file_paths=["deleted/file1.py", "deleted/file2.py"],
        )

        mock_table.in_.assert_called_once_with(
            "full_path", ["deleted/file1.py", "deleted/file2.py"]
        )
        assert result is not None
        assert len(result) == 2


def test_delete_coverages_by_paths_batches_large_lists():
    with patch(
        "services.supabase.coverages.delete_coverages_by_paths.supabase"
    ) as mock_supabase:
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.delete.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[{"full_path": "file.py"}])

        file_paths = [f"path/to/file{i}.py" for i in range(SUPABASE_BATCH_SIZE + 50)]

        delete_coverages_by_paths(
            platform="github",
            owner_id=123,
            repo_id=456,
            file_paths=file_paths,
        )

        assert mock_table.in_.call_count == 2
        first_batch = mock_table.in_.call_args_list[0][0][1]
        second_batch = mock_table.in_.call_args_list[1][0][1]
        assert len(first_batch) == SUPABASE_BATCH_SIZE
        assert len(second_batch) == 50


class TestDeleteCoveragesByPathsIntegration:

    @pytest.mark.skipif(bool(os.getenv("CI")), reason="Skip integration tests in CI")
    def test_batch_size_within_supabase_url_limit(self):
        file_paths = [
            f"src/components/feature{i}/index.tsx" for i in range(SUPABASE_BATCH_SIZE)
        ]

        try:
            supabase.table("coverages").select("id").eq("repo_id", 999999).in_(
                "full_path", file_paths
            ).execute()
        except APIError as e:
            if "URI Too Long" in str(e) or "414" in str(e):
                pytest.fail(
                    f"SUPABASE_BATCH_SIZE={SUPABASE_BATCH_SIZE} causes URL length error."
                )

    @pytest.mark.skipif(bool(os.getenv("CI")), reason="Skip integration tests in CI")
    def test_delete_with_more_than_batch_size(self):
        file_paths_large = [
            f"src/components/feature{i}/index.tsx"
            for i in range(SUPABASE_BATCH_SIZE + 50)
        ]
        result = delete_coverages_by_paths(
            platform="github",
            owner_id=999999,
            repo_id=999999,
            file_paths=file_paths_large,
        )
        assert result is not None
