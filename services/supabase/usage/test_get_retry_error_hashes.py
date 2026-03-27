from unittest.mock import Mock, patch
from services.supabase.usage.get_retry_error_hashes import get_retry_error_hashes


def _setup_mock_table(mock_supabase, mock_response):
    mock_table = Mock()
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    # .not_.is_() chain: not_ is a property returning a filter builder, is_() continues the chain
    mock_table.not_.is_.return_value = mock_table
    mock_table.execute.return_value = mock_response
    return mock_table


def test_get_retry_error_hashes_aggregates_from_all_records():
    mock_response = Mock()
    mock_response.data = [
        {"retry_error_hashes": ["hash1", "hash2"]},
        {"retry_error_hashes": ["hash3"]},
        {"retry_error_hashes": ["hash2", "hash4"]},
    ]

    with patch(
        "services.supabase.usage.get_retry_error_hashes.supabase"
    ) as mock_supabase:
        mock_table = _setup_mock_table(mock_supabase, mock_response)

        result = get_retry_error_hashes(123, 456, 789)

        assert result == ["hash1", "hash2", "hash3", "hash4"]
        mock_supabase.table.assert_called_once_with("usage")
        mock_table.select.assert_called_once_with("retry_error_hashes")
        assert mock_table.eq.call_count == 3
        mock_table.eq.assert_any_call("owner_id", 123)
        mock_table.eq.assert_any_call("repo_id", 456)
        mock_table.eq.assert_any_call("pr_number", 789)
        mock_table.not_.is_.assert_called_once_with("retry_error_hashes", "null")


def test_get_retry_error_hashes_with_single_record():
    mock_response = Mock()
    mock_response.data = [{"retry_error_hashes": ["hash1", "hash2", "hash3"]}]

    with patch(
        "services.supabase.usage.get_retry_error_hashes.supabase"
    ) as mock_supabase:
        _setup_mock_table(mock_supabase, mock_response)

        result = get_retry_error_hashes(123, 456, 789)

        assert result == ["hash1", "hash2", "hash3"]


def test_get_retry_error_hashes_with_empty_response_data():
    mock_response = Mock()
    mock_response.data = []

    with patch(
        "services.supabase.usage.get_retry_error_hashes.supabase"
    ) as mock_supabase:
        _setup_mock_table(mock_supabase, mock_response)

        result = get_retry_error_hashes(123, 456, 789)

        assert not result


def test_get_retry_error_hashes_with_none_response_data():
    mock_response = Mock()
    mock_response.data = None

    with patch(
        "services.supabase.usage.get_retry_error_hashes.supabase"
    ) as mock_supabase:
        _setup_mock_table(mock_supabase, mock_response)

        result = get_retry_error_hashes(123, 456, 789)

        assert not result


def test_get_retry_error_hashes_with_empty_hashes_in_records():
    mock_response = Mock()
    mock_response.data = [
        {"retry_error_hashes": []},
        {"retry_error_hashes": ["hash1"]},
    ]

    with patch(
        "services.supabase.usage.get_retry_error_hashes.supabase"
    ) as mock_supabase:
        _setup_mock_table(mock_supabase, mock_response)

        result = get_retry_error_hashes(123, 456, 789)

        assert result == ["hash1"]


def test_get_retry_error_hashes_deduplicates_across_records():
    mock_response = Mock()
    mock_response.data = [
        {"retry_error_hashes": ["hash1", "hash2"]},
        {"retry_error_hashes": ["hash1", "hash2"]},
        {"retry_error_hashes": ["hash1", "hash3"]},
    ]

    with patch(
        "services.supabase.usage.get_retry_error_hashes.supabase"
    ) as mock_supabase:
        _setup_mock_table(mock_supabase, mock_response)

        result = get_retry_error_hashes(123, 456, 789)

        assert result == ["hash1", "hash2", "hash3"]


def test_get_retry_error_hashes_with_exception():
    with patch(
        "services.supabase.usage.get_retry_error_hashes.supabase"
    ) as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database error")

        result = get_retry_error_hashes(123, 456, 789)

        assert not result


def test_get_retry_error_hashes_with_missing_key():
    mock_response = Mock()
    mock_response.data = [{}]

    with patch(
        "services.supabase.usage.get_retry_error_hashes.supabase"
    ) as mock_supabase:
        _setup_mock_table(mock_supabase, mock_response)

        result = get_retry_error_hashes(123, 456, 789)

        assert not result


def test_get_retry_error_hashes_with_execute_exception():
    with patch(
        "services.supabase.usage.get_retry_error_hashes.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.not_.is_.return_value = mock_table
        mock_table.execute.side_effect = Exception("Execute error")

        result = get_retry_error_hashes(123, 456, 789)

        assert not result
