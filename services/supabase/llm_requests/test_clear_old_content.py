from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from services.supabase.llm_requests.clear_old_content import clear_old_content


@patch("services.supabase.llm_requests.clear_old_content.supabase")
@patch("services.supabase.llm_requests.clear_old_content.datetime")
def test_clear_old_content_success_default_retention(mock_datetime, mock_supabase):
    """Test successful clearing of old content with default retention days (14)."""
    fixed_now = datetime(2025, 12, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_now
    expected_cutoff = (fixed_now - timedelta(days=14)).isoformat()

    mock_result = Mock()
    mock_result.data = [
        {"id": 1, "created_at": "2025-11-10T12:00:00"},
        {"id": 2, "created_at": "2025-11-11T12:00:00"},
    ]

    mock_table = Mock()
    mock_update = Mock()
    mock_lt = Mock()

    mock_supabase.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.lt.return_value = mock_lt
    mock_lt.execute.return_value = mock_result

    result = clear_old_content()

    assert result == mock_result.data
    mock_supabase.table.assert_called_with("llm_requests")
    mock_table.update.assert_called_with({"input_content": "", "output_content": ""})
    mock_update.lt.assert_called_with("created_at", expected_cutoff)
    mock_lt.execute.assert_called_once()


@patch("services.supabase.llm_requests.clear_old_content.supabase")
@patch("services.supabase.llm_requests.clear_old_content.datetime")
def test_clear_old_content_custom_retention_days(mock_datetime, mock_supabase):
    """Test clearing old content with custom retention days."""
    fixed_now = datetime(2025, 12, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_now
    retention_days = 30
    expected_cutoff = (fixed_now - timedelta(days=retention_days)).isoformat()

    mock_result = Mock()
    mock_result.data = [{"id": 3, "created_at": "2025-10-15T12:00:00"}]

    mock_table = Mock()
    mock_update = Mock()
    mock_lt = Mock()

    mock_supabase.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.lt.return_value = mock_lt
    mock_lt.execute.return_value = mock_result

    result = clear_old_content(retention_days=retention_days)

    assert result == mock_result.data
    mock_supabase.table.assert_called_with("llm_requests")
    mock_update.lt.assert_called_with("created_at", expected_cutoff)


@patch("services.supabase.llm_requests.clear_old_content.supabase")
@patch("services.supabase.llm_requests.clear_old_content.datetime")
def test_clear_old_content_no_data_to_clear(mock_datetime, mock_supabase):
    """Test when no old content is found to clear."""
    fixed_now = datetime(2025, 12, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_now

    mock_result = Mock()
    mock_result.data = []

    mock_table = Mock()
    mock_update = Mock()
    mock_lt = Mock()

    mock_supabase.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.lt.return_value = mock_lt
    mock_lt.execute.return_value = mock_result

    result = clear_old_content()

    assert result is None
    mock_supabase.table.assert_called_with("llm_requests")


@patch("services.supabase.llm_requests.clear_old_content.supabase")
@patch("services.supabase.llm_requests.clear_old_content.datetime")
def test_clear_old_content_result_data_is_none(mock_datetime, mock_supabase):
    """Test when result.data is None."""
    fixed_now = datetime(2025, 12, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_now

    mock_result = Mock()
    mock_result.data = None

    mock_table = Mock()
    mock_update = Mock()
    mock_lt = Mock()

    mock_supabase.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.lt.return_value = mock_lt
    mock_lt.execute.return_value = mock_result

    result = clear_old_content()

    assert result is None
    mock_supabase.table.assert_called_with("llm_requests")


@patch("services.supabase.llm_requests.clear_old_content.supabase")
@patch("services.supabase.llm_requests.clear_old_content.datetime")
def test_clear_old_content_zero_retention_days(mock_datetime, mock_supabase):
    """Test clearing content with zero retention days (clear all)."""
    fixed_now = datetime(2025, 12, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_now
    expected_cutoff = fixed_now.isoformat()

    mock_result = Mock()
    mock_result.data = [{"id": 4}, {"id": 5}]

    mock_table = Mock()
    mock_update = Mock()
    mock_lt = Mock()

    mock_supabase.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.lt.return_value = mock_lt
    mock_lt.execute.return_value = mock_result

    result = clear_old_content(retention_days=0)

    assert result == mock_result.data
    mock_supabase.table.assert_called_with("llm_requests")
    mock_update.lt.assert_called_with("created_at", expected_cutoff)


@patch("services.supabase.llm_requests.clear_old_content.supabase")
@patch("services.supabase.llm_requests.clear_old_content.datetime")
def test_clear_old_content_large_retention_days(mock_datetime, mock_supabase):
    """Test clearing content with large retention days (e.g., 365 days)."""
    fixed_now = datetime(2025, 12, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_now

    mock_result = Mock()
    mock_result.data = [{"id": 7}]

    mock_table = Mock()
    mock_update = Mock()
    mock_lt = Mock()

    mock_supabase.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.lt.return_value = mock_lt
    mock_lt.execute.return_value = mock_result

    result = clear_old_content(retention_days=365)

    assert result == mock_result.data
    mock_supabase.table.assert_called_with("llm_requests")


@patch("services.supabase.llm_requests.clear_old_content.supabase")
@patch("services.supabase.llm_requests.clear_old_content.datetime")
def test_clear_old_content_negative_retention_days(mock_datetime, mock_supabase):
    """Test clearing content with negative retention days (future dates - edge case)."""
    fixed_now = datetime(2025, 12, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_now
    expected_cutoff = (fixed_now - timedelta(days=-7)).isoformat()

    mock_result = Mock()
    mock_result.data = []

    mock_table = Mock()
    mock_update = Mock()
    mock_lt = Mock()

    mock_supabase.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.lt.return_value = mock_lt
    mock_lt.execute.return_value = mock_result

    result = clear_old_content(retention_days=-7)

    assert result is None
    mock_supabase.table.assert_called_with("llm_requests")
    mock_update.lt.assert_called_with("created_at", expected_cutoff)


@patch("services.supabase.llm_requests.clear_old_content.supabase")
@patch("services.supabase.llm_requests.clear_old_content.datetime")
def test_clear_old_content_database_exception(mock_datetime, mock_supabase):
    """Test handling of database exceptions (decorator should catch and return None)."""
    fixed_now = datetime(2025, 12, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_now

    mock_table = Mock()
    mock_supabase.table.return_value = mock_table
    mock_table.update.side_effect = Exception("Database connection error")

    result = clear_old_content()

    assert result is None
    mock_supabase.table.assert_called_with("llm_requests")


@patch("services.supabase.llm_requests.clear_old_content.supabase")
@patch("services.supabase.llm_requests.clear_old_content.datetime")
def test_clear_old_content_attribute_error(mock_datetime, mock_supabase):
    """Test handling of AttributeError (decorator should catch and return None)."""
    fixed_now = datetime(2025, 12, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_now

    mock_table = Mock()
    mock_update = Mock()
    mock_lt = Mock()

    mock_supabase.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.lt.return_value = mock_lt
    mock_lt.execute.side_effect = AttributeError(
        "'NoneType' object has no attribute 'data'"
    )

    result = clear_old_content()

    assert result is None
    mock_supabase.table.assert_called_with("llm_requests")


@patch("services.supabase.llm_requests.clear_old_content.supabase")
@patch("services.supabase.llm_requests.clear_old_content.datetime")
def test_clear_old_content_type_error(mock_datetime, mock_supabase):
    """Test handling of TypeError (decorator should catch and return None)."""
    fixed_now = datetime(2025, 12, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_now

    mock_table = Mock()
    mock_update = Mock()

    mock_supabase.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.lt.side_effect = TypeError("Invalid type for comparison")

    result = clear_old_content()

    assert result is None
    mock_supabase.table.assert_called_with("llm_requests")


@patch("services.supabase.llm_requests.clear_old_content.supabase")
@patch("services.supabase.llm_requests.clear_old_content.datetime")
def test_clear_old_content_key_error(mock_datetime, mock_supabase):
    """Test handling of KeyError (decorator should catch and return None)."""
    fixed_now = datetime(2025, 12, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_now

    mock_table = Mock()
    mock_update = Mock()
    mock_lt = Mock()

    mock_supabase.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.lt.return_value = mock_lt
    mock_lt.execute.side_effect = KeyError("created_at")

    result = clear_old_content()

    assert result is None
    mock_supabase.table.assert_called_with("llm_requests")


@patch("services.supabase.llm_requests.clear_old_content.supabase")
@patch("services.supabase.llm_requests.clear_old_content.datetime")
def test_clear_old_content_single_record(mock_datetime, mock_supabase):
    """Test clearing a single old record."""
    fixed_now = datetime(2025, 12, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_now

    mock_result = Mock()
    mock_result.data = [{"id": 100, "created_at": "2025-11-01T12:00:00"}]

    mock_table = Mock()
    mock_update = Mock()
    mock_lt = Mock()

    mock_supabase.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.lt.return_value = mock_lt
    mock_lt.execute.return_value = mock_result

    result = clear_old_content()

    assert result is not None
    assert result == mock_result.data
    assert len(result) == 1
    mock_supabase.table.assert_called_with("llm_requests")


@patch("services.supabase.llm_requests.clear_old_content.supabase")
@patch("services.supabase.llm_requests.clear_old_content.datetime")
def test_clear_old_content_multiple_records(mock_datetime, mock_supabase):
    """Test clearing multiple old records."""
    fixed_now = datetime(2025, 12, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_now

    mock_result = Mock()
    mock_result.data = [
        {"id": 1, "created_at": "2025-11-01T12:00:00"},
        {"id": 2, "created_at": "2025-11-05T12:00:00"},
        {"id": 3, "created_at": "2025-11-10T12:00:00"},
    ]

    mock_table = Mock()
    mock_update = Mock()
    mock_lt = Mock()

    mock_supabase.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.lt.return_value = mock_lt
    mock_lt.execute.return_value = mock_result

    result = clear_old_content()

    assert result is not None
    assert result == mock_result.data
    assert len(result) == 3
    mock_supabase.table.assert_called_with("llm_requests")


@patch("services.supabase.llm_requests.clear_old_content.supabase")
@patch("services.supabase.llm_requests.clear_old_content.datetime")
def test_clear_old_content_verifies_update_payload(mock_datetime, mock_supabase):
    """Test that the update payload contains correct empty strings."""
    fixed_now = datetime(2025, 12, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_now

    mock_result = Mock()
    mock_result.data = [{"id": 1}]

    mock_table = Mock()
    mock_update = Mock()
    mock_lt = Mock()

    mock_supabase.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.lt.return_value = mock_lt
    mock_lt.execute.return_value = mock_result

    result = clear_old_content()

    mock_table.update.assert_called_once_with(
        {"input_content": "", "output_content": ""}
    )
    assert result == mock_result.data


@patch("services.supabase.llm_requests.clear_old_content.supabase")
@patch("services.supabase.llm_requests.clear_old_content.datetime")
def test_clear_old_content_verifies_cutoff_calculation(mock_datetime, mock_supabase):
    """Test that the cutoff date is calculated correctly."""
    fixed_now = datetime(2025, 12, 15, 10, 30, 45)
    mock_datetime.now.return_value = fixed_now
    retention_days = 7
    expected_cutoff = (fixed_now - timedelta(days=retention_days)).isoformat()

    mock_result = Mock()
    mock_result.data = [{"id": 1}]

    mock_table = Mock()
    mock_update = Mock()
    mock_lt = Mock()

    mock_supabase.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.lt.return_value = mock_lt
    mock_lt.execute.return_value = mock_result

    result = clear_old_content(retention_days=retention_days)

    mock_update.lt.assert_called_once_with("created_at", expected_cutoff)
    assert result == mock_result.data
