from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from services.supabase.llm_requests.clear_old_content import clear_old_content


@patch("services.supabase.llm_requests.clear_old_content.supabase")
def test_clear_old_content_success(mock_supabase):
    mock_result = Mock()
    mock_result.data = [{"id": 1}, {"id": 2}]
    mock_supabase.table.return_value.update.return_value.lt.return_value.execute.return_value = (
        mock_result
    )

    result = clear_old_content(retention_days=14)

    assert result == [{"id": 1}, {"id": 2}]
    mock_supabase.table.assert_called_once_with("llm_requests")
    mock_supabase.table.return_value.update.assert_called_once_with(
        {"input_content": "", "output_content": ""}
    )


@patch("services.supabase.llm_requests.clear_old_content.supabase")
def test_clear_old_content_with_custom_retention_days(mock_supabase):
    mock_result = Mock()
    mock_result.data = [{"id": 3}]
    mock_supabase.table.return_value.update.return_value.lt.return_value.execute.return_value = (
        mock_result
    )

    result = clear_old_content(retention_days=30)

    assert result == [{"id": 3}]
    mock_supabase.table.assert_called_once_with("llm_requests")


@patch("services.supabase.llm_requests.clear_old_content.supabase")
def test_clear_old_content_with_zero_retention_days(mock_supabase):
    mock_result = Mock()
    mock_result.data = [{"id": 4}]
    mock_supabase.table.return_value.update.return_value.lt.return_value.execute.return_value = (
        mock_result
    )

    result = clear_old_content(retention_days=0)

    assert result == [{"id": 4}]
    mock_supabase.table.assert_called_once_with("llm_requests")


@patch("services.supabase.llm_requests.clear_old_content.supabase")
def test_clear_old_content_with_large_retention_days(mock_supabase):
    mock_result = Mock()
    mock_result.data = []
    mock_supabase.table.return_value.update.return_value.lt.return_value.execute.return_value = (
        mock_result
    )

    result = clear_old_content(retention_days=365)

    assert result is None
    mock_supabase.table.assert_called_once_with("llm_requests")


@patch("services.supabase.llm_requests.clear_old_content.supabase")
def test_clear_old_content_empty_result(mock_supabase):
    mock_result = Mock()
    mock_result.data = []
    mock_supabase.table.return_value.update.return_value.lt.return_value.execute.return_value = (
        mock_result
    )

    result = clear_old_content(retention_days=14)

    assert result is None


@patch("services.supabase.llm_requests.clear_old_content.supabase")
def test_clear_old_content_none_data(mock_supabase):
    mock_result = Mock()
    mock_result.data = None
    mock_supabase.table.return_value.update.return_value.lt.return_value.execute.return_value = (
        mock_result
    )

    result = clear_old_content(retention_days=14)

    assert result is None


@patch("services.supabase.llm_requests.clear_old_content.supabase")
def test_clear_old_content_database_error(mock_supabase):
    mock_supabase.table.return_value.update.return_value.lt.return_value.execute.side_effect = (
        Exception("Database error")
    )

    result = clear_old_content(retention_days=14)

    assert result is None


@patch("services.supabase.llm_requests.clear_old_content.supabase")
def test_clear_old_content_default_retention_days(mock_supabase):
    mock_result = Mock()
    mock_result.data = [{"id": 5}]
    mock_supabase.table.return_value.update.return_value.lt.return_value.execute.return_value = (
        mock_result
    )

    result = clear_old_content()

    assert result == [{"id": 5}]
    mock_supabase.table.assert_called_once_with("llm_requests")
    mock_supabase.table.return_value.update.assert_called_once_with(
        {"input_content": "", "output_content": ""}
    )
