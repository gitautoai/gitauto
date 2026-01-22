# pylint: disable=redefined-outer-name
from unittest.mock import MagicMock, patch

import pytest

from services.supabase.coverages.exclude_from_testing import exclude_from_testing


@pytest.fixture
def mock_supabase():
    with patch("services.supabase.coverages.exclude_from_testing.supabase") as mock:
        yield mock


class TestExcludeFromTesting:
    def test_exclude_from_testing_success(self, mock_supabase):
        mock_result = MagicMock()
        mock_result.data = [{"id": 1, "is_excluded_from_testing": True}]
        mock_supabase.table.return_value.upsert.return_value.execute.return_value = (
            mock_result
        )

        result = exclude_from_testing(
            owner_id=123,
            repo_id=456,
            full_path="src/generated/file.ts",
            branch_name="main",
            exclusion_reason="ai_no_testable_logic",
            updated_by="test_user",
        )

        assert result == mock_result.data
        mock_supabase.table.assert_called_once_with("coverages")
        mock_supabase.table.return_value.upsert.assert_called_once_with(
            {
                "owner_id": 123,
                "repo_id": 456,
                "full_path": "src/generated/file.ts",
                "branch_name": "main",
                "level": "file",
                "created_by": "test_user",
                "is_excluded_from_testing": True,
                "exclusion_reason": "ai_no_testable_logic",
                "updated_by": "test_user",
            },
            on_conflict="repo_id,full_path",
            default_to_null=False,
        )

    def test_exclude_from_testing_various_reasons(self, mock_supabase):
        mock_result = MagicMock()
        mock_result.data = [{"id": 1}]
        mock_supabase.table.return_value.upsert.return_value.execute.return_value = (
            mock_result
        )

        reasons = [
            "not code file",
            "test file",
            "type file",
            "migration file",
            "empty file",
            "only exports",
            "generated code",
        ]

        for reason in reasons:
            result = exclude_from_testing(
                owner_id=123,
                repo_id=456,
                full_path=f"src/{reason}.ts",
                branch_name="main",
                exclusion_reason=reason,
                updated_by="test_user",
            )
            assert result is not None
