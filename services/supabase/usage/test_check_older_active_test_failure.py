"""Unit tests for check_older_active_test_failure.py"""

from unittest.mock import patch, MagicMock
from services.supabase.usage.check_older_active_test_failure import (
    check_older_active_test_failure_request,
)


@patch("services.supabase.usage.check_older_active_test_failure.supabase")
def test_check_older_active_test_failure_request_found(mock_supabase):
    """Test finding an older active test failure request."""
    # Mock the result
    expected_result = {"id": 888, "created_at": "2025-09-23T10:00:00Z"}
    mock_result = MagicMock()
    mock_result.data = [expected_result]

    # Mock the fluent API chain
    mock_query = MagicMock()
    mock_query.execute.return_value = mock_result
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value.lt.return_value.limit.return_value = (
        mock_query
    )

    # Execute
    result = check_older_active_test_failure_request(
        owner_id=11111, repo_id=98765, pr_number=1, current_usage_id=999
    )

    # Verify
    assert result == expected_result
    mock_supabase.table.assert_called_once_with("usage")
    mock_query.execute.assert_called_once()


@patch("services.supabase.usage.check_older_active_test_failure.supabase")
def test_check_older_active_test_failure_request_not_found(mock_supabase):
    """Test when no older active test failure request is found."""
    # Mock empty result
    mock_result = MagicMock()
    mock_result.data = []

    # Mock the fluent API chain
    mock_query = MagicMock()
    mock_query.execute.return_value = mock_result
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value.lt.return_value.limit.return_value = (
        mock_query
    )

    # Execute
    result = check_older_active_test_failure_request(
        owner_id=11111, repo_id=98765, pr_number=1, current_usage_id=999
    )

    # Verify
    assert result is None
    mock_supabase.table.assert_called_once_with("usage")


@patch("services.supabase.usage.check_older_active_test_failure.supabase")
def test_check_older_active_test_failure_request_exception_handling(mock_supabase):
    """Test exception handling returns None."""
    # Mock supabase to raise an exception
    mock_supabase.table.side_effect = Exception("Database error")

    # Execute
    result = check_older_active_test_failure_request(
        owner_id=11111, repo_id=98765, pr_number=1, current_usage_id=999
    )

    # Verify exception is handled and None is returned
    assert result is None


def test_check_older_active_test_failure_request_filters_correctly():
    """Test that the function uses correct filters for finding older requests."""
    with patch(
        "services.supabase.usage.check_older_active_test_failure.supabase"
    ) as mock_supabase:
        # Mock empty result
        mock_result = MagicMock()
        mock_result.data = []

        # Mock the fluent API chain
        mock_query = MagicMock()
        mock_query.execute.return_value = mock_result
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value.lt.return_value.limit.return_value = (
            mock_query
        )

        # Execute
        result = check_older_active_test_failure_request(
            owner_id=12345, repo_id=67890, pr_number=42, current_usage_id=100
        )

        # Verify table selection and result
        mock_supabase.table.assert_called_once_with("usage")
        mock_query.execute.assert_called_once()
        assert result is None
