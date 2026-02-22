# pylint: disable=import-outside-toplevel
import json
import os
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
import requests

from services.supabase.usage.count_unique_requests import (
    count_unique_requests,
)


def test_count_unique_requests_with_valid_data():
    """Test successful count with valid data"""
    mock_data = [
        {
            "owner_type": "Organization",
            "owner_name": "gitautoai",
            "repo_name": "gitauto",
            "pr_number": 123,
        },
        {
            "owner_type": "User",
            "owner_name": "john_doe",
            "repo_name": "my_repo",
            "pr_number": 456,
        },
    ]

    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_response = Mock()
        mock_response.data = mock_data
        mock_table.execute.return_value = mock_response

        start_date = datetime(2023, 1, 1)
        result = count_unique_requests(123, start_date)

        expected = {"Organization/gitautoai/gitauto#123", "User/john_doe/my_repo#456"}
        assert result == expected

        # Verify the query was built correctly
        mock_supabase.table.assert_called_once_with("usage")
        mock_table.select.assert_called_once_with(
            "owner_type, owner_name, repo_name, pr_number"
        )
        mock_table.gt.assert_not_called()
        mock_table.eq.assert_any_call("installation_id", 123)
        mock_table.in_.assert_called_once_with(
            "trigger",
            [
                "dashboard",
                "issue_comment",
                "issue_label",
                "manual",
                "pull_request",
                "schedule",
                "unknown",
            ],
        )
        mock_table.execute.assert_called_once()


def test_count_unique_requests_with_duplicate_data():
    """Test that duplicate requests are properly deduplicated"""
    mock_data = [
        {
            "owner_type": "Organization",
            "owner_name": "gitautoai",
            "repo_name": "gitauto",
            "pr_number": 123,
        },
        {
            "owner_type": "Organization",
            "owner_name": "gitautoai",
            "repo_name": "gitauto",
            "pr_number": 123,
        },
        {
            "owner_type": "User",
            "owner_name": "john_doe",
            "repo_name": "my_repo",
            "pr_number": 456,
        },
    ]

    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_response = Mock()
        mock_response.data = mock_data
        mock_table.execute.return_value = mock_response

        start_date = datetime(2023, 1, 1)
        result = count_unique_requests(123, start_date)

        # Should only have 2 unique requests despite 3 records
        expected = {"Organization/gitautoai/gitauto#123", "User/john_doe/my_repo#456"}
        assert result == expected
        assert len(result) == 2


def test_count_unique_requests_with_empty_data():
    """Test with empty data response"""
    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_response = Mock()
        mock_response.data = []
        mock_table.execute.return_value = mock_response

        start_date = datetime(2023, 1, 1)
        result = count_unique_requests(123, start_date)

        assert result == set()


def test_count_unique_requests_with_none_data():
    """Test with None data response - should return empty set due to exception handling"""
    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_response = Mock()
        mock_response.data = None
        mock_table.execute.return_value = mock_response

        start_date = datetime(2023, 1, 1)
        result = count_unique_requests(123, start_date)

        assert result == set()


def test_count_unique_requests_with_zero_installation_id():
    """Test with zero installation_id"""
    mock_data = [
        {
            "owner_type": "Organization",
            "owner_name": "test_org",
            "repo_name": "test_repo",
            "pr_number": 1,
        }
    ]

    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_response = Mock()
        mock_response.data = mock_data
        mock_table.execute.return_value = mock_response

        start_date = datetime(2023, 1, 1)
        result = count_unique_requests(0, start_date)

        expected = {"Organization/test_org/test_repo#1"}
        assert result == expected
        mock_table.eq.assert_any_call("installation_id", 0)


def test_count_unique_requests_with_negative_installation_id():
    """Test with negative installation_id"""
    mock_data = [
        {
            "owner_type": "User",
            "owner_name": "negative_user",
            "repo_name": "negative_repo",
            "pr_number": 999,
        }
    ]

    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_response = Mock()
        mock_response.data = mock_data
        mock_table.execute.return_value = mock_response

        start_date = datetime(2023, 1, 1)
        result = count_unique_requests(-1, start_date)

        expected = {"User/negative_user/negative_repo#999"}
        assert result == expected
        mock_table.eq.assert_any_call("installation_id", -1)


def test_count_unique_requests_with_large_installation_id():
    """Test with large installation_id"""
    mock_data = [
        {
            "owner_type": "Organization",
            "owner_name": "large_org",
            "repo_name": "large_repo",
            "pr_number": 888888,
        }
    ]

    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_response = Mock()
        mock_response.data = mock_data
        mock_table.execute.return_value = mock_response

        start_date = datetime(2023, 1, 1)
        result = count_unique_requests(999999999, start_date)

        expected = {"Organization/large_org/large_repo#888888"}
        assert result == expected
        mock_table.eq.assert_any_call("installation_id", 999999999)


def test_count_unique_requests_with_special_characters():
    """Test with special characters in owner/repo names"""
    mock_data = [
        {
            "owner_type": "Organization",
            "owner_name": "org-with-dashes",
            "repo_name": "repo_with_underscores",
            "pr_number": 123,
        },
        {
            "owner_type": "User",
            "owner_name": "user.with.dots",
            "repo_name": "repo-with-dashes",
            "pr_number": 456,
        },
    ]

    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_response = Mock()
        mock_response.data = mock_data
        mock_table.execute.return_value = mock_response

        start_date = datetime(2023, 1, 1)
        result = count_unique_requests(123, start_date)

        expected = {
            "Organization/org-with-dashes/repo_with_underscores#123",
            "User/user.with.dots/repo-with-dashes#456",
        }
        assert result == expected


def test_count_unique_requests_with_exception():
    """Test when supabase raises an exception"""
    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database error")

        start_date = datetime(2023, 1, 1)
        result = count_unique_requests(123, start_date)

        # Should return default value (empty set) due to handle_exceptions decorator
        assert result == set()


def test_count_unique_requests_with_attribute_error():
    """Test when AttributeError is raised"""
    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_supabase.table.side_effect = AttributeError("Attribute error")

        start_date = datetime(2023, 1, 1)
        result = count_unique_requests(123, start_date)

        assert result == set()


def test_count_unique_requests_with_key_error():
    """Test when KeyError is raised"""
    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_supabase.table.side_effect = KeyError("Key error")

        start_date = datetime(2023, 1, 1)
        result = count_unique_requests(123, start_date)

        assert result == set()


def test_count_unique_requests_with_type_error():
    """Test when TypeError is raised"""
    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_supabase.table.side_effect = TypeError("Type error")

        start_date = datetime(2023, 1, 1)
        result = count_unique_requests(123, start_date)

        assert result == set()


def test_count_unique_requests_with_json_decode_error():
    """Test when JSONDecodeError is raised"""
    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_supabase.table.side_effect = json.JSONDecodeError("JSON error", "", 0)

        start_date = datetime(2023, 1, 1)
        result = count_unique_requests(123, start_date)

        assert result == set()


def test_count_unique_requests_with_http_error_500():
    """Test when HTTP 500 error is raised"""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.reason = "Internal Server Error"
    mock_response.text = "Server error"

    http_error = requests.exceptions.HTTPError(response=mock_response)

    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_supabase.table.side_effect = http_error

        start_date = datetime(2023, 1, 1)
        result = count_unique_requests(123, start_date)

        assert result == set()


def test_count_unique_requests_with_http_error_409():
    """Test when HTTP 409 Conflict error is raised"""
    mock_response = Mock()
    mock_response.status_code = 409
    mock_response.reason = "Conflict"
    mock_response.text = "Conflict error"

    http_error = requests.exceptions.HTTPError(response=mock_response)

    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_supabase.table.side_effect = http_error

        start_date = datetime(2023, 1, 1)
        result = count_unique_requests(123, start_date)

        assert result == set()


def test_count_unique_requests_execute_exception():
    """Test when execute method raises an exception"""
    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.side_effect = Exception("Execute error")

        start_date = datetime(2023, 1, 1)
        result = count_unique_requests(123, start_date)

        assert result == set()


def test_count_unique_requests_with_malformed_data():
    """Test with malformed data missing required fields"""
    mock_data = [
        {
            "owner_type": "Organization",
            "owner_name": "gitautoai",
            # Missing repo_name and pr_number
        },
        {
            "owner_type": "User",
            "repo_name": "my_repo",
            "pr_number": 456,
            # Missing owner_name
        },
    ]

    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_response = Mock()
        mock_response.data = mock_data
        mock_table.execute.return_value = mock_response

        start_date = datetime(2023, 1, 1)
        result = count_unique_requests(123, start_date)

        # Should return empty set due to KeyError in processing
        assert result == set()


def test_count_unique_requests_with_different_start_dates():
    """Test with different start date formats"""
    mock_data = [
        {
            "owner_type": "Organization",
            "owner_name": "test_org",
            "repo_name": "test_repo",
            "pr_number": 1,
        }
    ]

    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_response = Mock()
        mock_response.data = mock_data
        mock_table.execute.return_value = mock_response

        # Test with different datetime formats
        start_dates = [
            datetime(2023, 1, 1, 0, 0, 0),
            datetime(2023, 12, 31, 23, 59, 59),
            datetime(2024, 6, 15, 12, 30, 45),
        ]

        for start_date in start_dates:
            result = count_unique_requests(123, start_date)
            expected = {"Organization/test_org/test_repo#1"}
            assert result == expected
            mock_table.gt.assert_not_called()


def test_count_unique_requests_with_single_record():
    """Test with single record"""
    mock_data = [
        {
            "owner_type": "Organization",
            "owner_name": "single_org",
            "repo_name": "single_repo",
            "pr_number": 42,
        }
    ]

    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_response = Mock()
        mock_response.data = mock_data
        mock_table.execute.return_value = mock_response

        start_date = datetime(2023, 1, 1)
        result = count_unique_requests(123, start_date)

        expected = {"Organization/single_org/single_repo#42"}
        assert result == expected
        assert len(result) == 1


def test_count_unique_requests_with_numeric_strings():
    """Test with numeric strings in owner/repo names"""
    mock_data = [
        {
            "owner_type": "Organization",
            "owner_name": "org123",
            "repo_name": "repo456",
            "pr_number": 789,
        },
        {
            "owner_type": "User",
            "owner_name": "user999",
            "repo_name": "project2023",
            "pr_number": 1,
        },
    ]

    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_response = Mock()
        mock_response.data = mock_data
        mock_table.execute.return_value = mock_response

        start_date = datetime(2023, 1, 1)
        result = count_unique_requests(123, start_date)

        expected = {"Organization/org123/repo456#789", "User/user999/project2023#1"}
        assert result == expected
        assert len(result) == 2


def test_count_unique_requests_query_parameters():
    """Test that all query parameters are correctly passed"""
    with patch(
        "services.supabase.usage.count_unique_requests.supabase"
    ) as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_response = Mock()
        mock_response.data = []
        mock_table.execute.return_value = mock_response

        start_date = datetime(2023, 1, 1)
        count_unique_requests(123, start_date)

        mock_supabase.table.assert_called_once_with("usage")
        mock_table.select.assert_called_once()
        mock_table.gt.assert_not_called()
        mock_table.eq.assert_any_call("installation_id", 123)


@pytest.mark.skipif(bool(os.environ.get("CI")), reason="Integration test")
def test_count_unique_requests_integration(test_installation_id):
    from datetime import timedelta
    from config import TZ

    start_date = datetime.now(TZ) - timedelta(days=365)
    result = count_unique_requests(test_installation_id, start_date)
    assert isinstance(result, set)
    for item in result:
        assert "/" in item
        assert "#" in item

    result = count_unique_requests(999999999, start_date)
    assert isinstance(result, set)
    assert len(result) == 0
