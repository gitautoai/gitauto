# pylint: disable=redefined-outer-name
from unittest.mock import MagicMock, patch

from services.supabase.coverages.update_quality_checks import update_quality_checks


@patch("services.supabase.coverages.update_quality_checks.supabase")
def test_update_quality_checks_calls_supabase(mock_supabase: MagicMock):
    mock_table = MagicMock()
    mock_supabase.table.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.execute.return_value = MagicMock(data=[{"id": 1}])

    quality_checks = {
        "adversarial": {
            "null_undefined_inputs": {"status": "pass", "detail": ""},
        },
    }

    result = update_quality_checks(
        owner_id=123,
        repo_id=456,
        file_path="src/utils/foo.ts",
        impl_blob_sha="abc123",
        test_blob_sha="def456",
        checklist_hash="hash789",
        quality_checks=quality_checks,
        updated_by="testuser",
    )

    mock_supabase.table.assert_called_once_with("coverages")
    mock_table.update.assert_called_once()
    assert mock_table.eq.call_count == 3
    assert result == [{"id": 1}]


@patch("services.supabase.coverages.update_quality_checks.supabase")
def test_update_quality_checks_with_none_test_sha(mock_supabase: MagicMock):
    mock_table = MagicMock()
    mock_supabase.table.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.execute.return_value = MagicMock(data=[{"id": 1}])

    result = update_quality_checks(
        owner_id=123,
        repo_id=456,
        file_path="src/utils/foo.ts",
        impl_blob_sha="abc123",
        test_blob_sha=None,
        checklist_hash="hash789",
        quality_checks={"adversarial": {}},
        updated_by="testuser",
    )

    update_args = mock_table.update.call_args[0][0]
    assert update_args["test_blob_sha"] is None
    assert result == [{"id": 1}]
