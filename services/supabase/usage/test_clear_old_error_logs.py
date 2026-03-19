from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from constants.supabase import SUPABASE_BATCH_SIZE
from services.supabase.usage.clear_old_error_logs import clear_old_error_logs


@patch("services.supabase.usage.clear_old_error_logs.supabase")
@patch("services.supabase.usage.clear_old_error_logs.datetime")
def test_clear_old_error_logs_single_batch(mock_datetime, mock_supabase):
    fixed_now = datetime(2025, 12, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_now
    expected_cutoff = (fixed_now - timedelta(days=14)).isoformat()

    mock_select_result = Mock()
    mock_select_result.data = [{"id": 1}, {"id": 2}, {"id": 3}]

    mock_table = Mock()
    mock_select = Mock()
    mock_lt_select = Mock()
    mock_neq = Mock()
    mock_limit = Mock()
    mock_update = Mock()
    mock_in = Mock()

    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.lt.return_value = mock_lt_select
    mock_lt_select.neq.return_value = mock_neq
    mock_neq.limit.return_value = mock_limit
    mock_limit.execute.side_effect = [mock_select_result, Mock(data=[])]

    mock_table.update.return_value = mock_update
    mock_update.in_.return_value = mock_in
    mock_in.execute.return_value = Mock(data=[])

    result = clear_old_error_logs()

    assert result == 3
    mock_table.select.assert_called_with("id")
    mock_select.lt.assert_called_with("created_at", expected_cutoff)
    mock_lt_select.neq.assert_called_with("original_error_log", "")
    mock_neq.limit.assert_called_with(SUPABASE_BATCH_SIZE)
    mock_table.update.assert_called_with(
        {"original_error_log": "", "minimized_error_log": ""}
    )
    mock_update.in_.assert_called_with("id", [1, 2, 3])


@patch("services.supabase.usage.clear_old_error_logs.supabase")
@patch("services.supabase.usage.clear_old_error_logs.datetime")
def test_clear_old_error_logs_no_records(mock_datetime, mock_supabase):
    fixed_now = datetime(2025, 12, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_now

    mock_table = Mock()
    mock_select = Mock()
    mock_lt_select = Mock()
    mock_neq = Mock()
    mock_limit = Mock()

    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.lt.return_value = mock_lt_select
    mock_lt_select.neq.return_value = mock_neq
    mock_neq.limit.return_value = mock_limit
    mock_limit.execute.return_value = Mock(data=[])

    result = clear_old_error_logs()

    assert result == 0
    mock_table.update.assert_not_called()


@patch("services.supabase.usage.clear_old_error_logs.supabase")
@patch("services.supabase.usage.clear_old_error_logs.datetime")
def test_clear_old_error_logs_custom_retention_days(mock_datetime, mock_supabase):
    fixed_now = datetime(2025, 12, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_now
    retention_days = 30
    expected_cutoff = (fixed_now - timedelta(days=retention_days)).isoformat()

    mock_select_result = Mock()
    mock_select_result.data = [{"id": 1}]

    mock_table = Mock()
    mock_select = Mock()
    mock_lt_select = Mock()
    mock_neq = Mock()
    mock_limit = Mock()
    mock_update = Mock()
    mock_in = Mock()

    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.lt.return_value = mock_lt_select
    mock_lt_select.neq.return_value = mock_neq
    mock_neq.limit.return_value = mock_limit
    mock_limit.execute.side_effect = [mock_select_result, Mock(data=[])]

    mock_table.update.return_value = mock_update
    mock_update.in_.return_value = mock_in
    mock_in.execute.return_value = Mock(data=[])

    result = clear_old_error_logs(retention_days=retention_days)

    assert result == 1
    mock_select.lt.assert_called_with("created_at", expected_cutoff)
