import json
from datetime import datetime
from unittest.mock import Mock, patch
import requests

from services.supabase.usage.count_completed_unique_requests import count_completed_unique_requests


def test_count_completed_unique_requests_with_valid_data():
    """Test successful count with valid data"""
    mock_data = [
        {
            "owner_type": "Organization",
            "owner_name": "gitautoai",
            "repo_name": "gitauto",
            "issue_number": 123,
        },
        {
            "owner_type": "User",
            "owner_name": "john",
            "repo_name": "project",
            "issue_number": 456,
        },
    ]

    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = ((None, mock_data), None)

        start_date = datetime(2023, 1, 1, 0, 0, 0)
        result = count_completed_unique_requests(installation_id=12345, start_date=start_date)

        expected = {
            "Organization/gitautoai/gitauto#123",
            "User/john/project#456",
        }
        assert result == expected
        
        mock_supabase.table.assert_called_once_with("usage")
        mock_table.select.assert_called_once_with("owner_type, owner_name, repo_name, issue_number")
        mock_table.gt.assert_called_once_with("created_at", start_date)
        mock_table.eq.assert_any_call("installation_id", 12345)
        mock_table.eq.assert_any_call("is_completed", True)
        mock_table.in_.assert_called_once_with(
            "trigger",
            [
                "issue_comment",
                "issue_label",
                "pull_request",
            ],
        )
        mock_table.execute.assert_called_once()


def test_count_completed_unique_requests_with_empty_data():
    """Test count with empty data"""
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = ((None, []), None)

        start_date = datetime(2023, 1, 1, 0, 0, 0)
        result = count_completed_unique_requests(installation_id=12345, start_date=start_date)

        assert result == set()


def test_count_completed_unique_requests_with_duplicate_requests():
    """Test count with duplicate requests (should be deduplicated)"""
    mock_data = [
        {
            "owner_type": "Organization",
            "owner_name": "gitautoai",
            "repo_name": "gitauto",
            "issue_number": 123,
        },
        {
            "owner_type": "Organization",
            "owner_name": "gitautoai",
            "repo_name": "gitauto",
            "issue_number": 123,
        },
        {
            "owner_type": "User",
            "owner_name": "john",
            "repo_name": "project",
            "issue_number": 456,
        },
    ]

    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = ((None, mock_data), None)

        start_date = datetime(2023, 1, 1, 0, 0, 0)
        result = count_completed_unique_requests(installation_id=12345, start_date=start_date)

        expected = {
            "Organization/gitautoai/gitauto#123",
            "User/john/project#456",
        }
        assert result == expected
        assert len(result) == 2  # Should be deduplicated


def test_count_completed_unique_requests_with_single_record():
    """Test count with single record"""
    mock_data = [
        {
            "owner_type": "Organization",
            "owner_name": "gitautoai",
            "repo_name": "gitauto",
            "issue_number": 123,
        },
    ]

    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = ((None, mock_data), None)

        start_date = datetime(2023, 1, 1, 0, 0, 0)
        result = count_completed_unique_requests(installation_id=12345, start_date=start_date)

        expected = {"Organization/gitautoai/gitauto#123"}
        assert result == expected


def test_count_completed_unique_requests_with_zero_installation_id():
    """Test count with zero installation_id"""
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = ((None, []), None)

        start_date = datetime(2023, 1, 1, 0, 0, 0)
        result = count_completed_unique_requests(installation_id=0, start_date=start_date)

        assert result == set()
        mock_table.eq.assert_any_call("installation_id", 0)


def test_count_completed_unique_requests_with_negative_installation_id():
    """Test count with negative installation_id"""
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = ((None, []), None)

        start_date = datetime(2023, 1, 1, 0, 0, 0)
        result = count_completed_unique_requests(installation_id=-1, start_date=start_date)

        assert result == set()
        mock_table.eq.assert_any_call("installation_id", -1)


def test_count_completed_unique_requests_with_large_installation_id():
    """Test count with large installation_id"""
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = ((None, []), None)

        start_date = datetime(2023, 1, 1, 0, 0, 0)
        result = count_completed_unique_requests(installation_id=999999999, start_date=start_date)

        assert result == set()
        mock_table.eq.assert_any_call("installation_id", 999999999)


def test_count_completed_unique_requests_with_different_start_dates():
    """Test count with different start dates"""
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = ((None, []), None)

        # Test with different start dates
        start_dates = [
            datetime(2020, 1, 1, 0, 0, 0),
            datetime(2023, 6, 15, 12, 30, 45),
            datetime(2024, 12, 31, 23, 59, 59),
        ]

        for start_date in start_dates:
            result = count_completed_unique_requests(installation_id=12345, start_date=start_date)
            assert result == set()
            mock_table.gt.assert_called_with("created_at", start_date)


def test_count_completed_unique_requests_with_special_characters():
    """Test count with special characters in names"""
    mock_data = [
        {
            "owner_type": "Organization",
            "owner_name": "test-org_123",
            "repo_name": "my-repo.test",
            "issue_number": 456,
        },
        {
            "owner_type": "User",
            "owner_name": "user@domain",
            "repo_name": "repo_with_underscores",
            "issue_number": 789,
        },
    ]

    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = ((None, mock_data), None)

        start_date = datetime(2023, 1, 1, 0, 0, 0)
        result = count_completed_unique_requests(installation_id=12345, start_date=start_date)

        expected = {
            "Organization/test-org_123/my-repo.test#456",
            "User/user@domain/repo_with_underscores#789",
        }
        assert result == expected


def test_count_completed_unique_requests_with_exception():
    """Test count when supabase raises an exception"""
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database error")

        start_date = datetime(2023, 1, 1, 0, 0, 0)
        result = count_completed_unique_requests(installation_id=12345, start_date=start_date)

        assert result == set()


def test_count_completed_unique_requests_with_attribute_error():
    """Test count when AttributeError is raised"""
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_supabase.table.side_effect = AttributeError("Attribute error")

        start_date = datetime(2023, 1, 1, 0, 0, 0)
        result = count_completed_unique_requests(installation_id=12345, start_date=start_date)

        assert result == set()


def test_count_completed_unique_requests_with_key_error():
    """Test count when KeyError is raised"""
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_supabase.table.side_effect = KeyError("Key error")

        start_date = datetime(2023, 1, 1, 0, 0, 0)
        result = count_completed_unique_requests(installation_id=12345, start_date=start_date)

        assert result == set()


def test_count_completed_unique_requests_with_type_error():
    """Test count when TypeError is raised"""
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_supabase.table.side_effect = TypeError("Type error")

        start_date = datetime(2023, 1, 1, 0, 0, 0)
        result = count_completed_unique_requests(installation_id=12345, start_date=start_date)

        assert result == set()


def test_count_completed_unique_requests_with_json_decode_error():
    """Test count when JSONDecodeError is raised"""
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_supabase.table.side_effect = json.JSONDecodeError("JSON error", "", 0)

        start_date = datetime(2023, 1, 1, 0, 0, 0)
        result = count_completed_unique_requests(installation_id=12345, start_date=start_date)

        assert result == set()


def test_count_completed_unique_requests_with_http_error_500():
    """Test count when HTTP 500 error is raised"""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.reason = "Internal Server Error"
    mock_response.text = "Server error"

    http_error = requests.exceptions.HTTPError(response=mock_response)

    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_supabase.table.side_effect = http_error

        start_date = datetime(2023, 1, 1, 0, 0, 0)
        result = count_completed_unique_requests(installation_id=12345, start_date=start_date)

        assert result == set()


def test_count_completed_unique_requests_with_http_error_409():
    """Test count when HTTP 409 Conflict error is raised"""
    mock_response = Mock()
    mock_response.status_code = 409
    mock_response.reason = "Conflict"
    mock_response.text = "Conflict error"

    http_error = requests.exceptions.HTTPError(response=mock_response)

    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_supabase.table.side_effect = http_error

        start_date = datetime(2023, 1, 1, 0, 0, 0)
        result = count_completed_unique_requests(installation_id=12345, start_date=start_date)

        assert result == set()


def test_count_completed_unique_requests_with_execute_exception():
    """Test count when execute method raises an exception"""
    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.side_effect = Exception("Execute error")

        start_date = datetime(2023, 1, 1, 0, 0, 0)
        result = count_completed_unique_requests(installation_id=12345, start_date=start_date)

        assert result == set()


def test_count_completed_unique_requests_with_missing_fields():
    """Test count when records have missing fields"""
    mock_data = [
        {
            "owner_type": "Organization",
            "owner_name": "gitautoai",
            "repo_name": "gitauto",
            # Missing issue_number
        },
        {
            "owner_type": "User",
            # Missing owner_name
            "repo_name": "project",
            "issue_number": 456,
        },
    ]

    with patch("services.supabase.usage.count_completed_unique_requests.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.gt.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = ((None, mock_data), None)

        start_date = datetime(2023, 1, 1, 0, 0, 0)
        result = count_completed_unique_requests(installation_id=12345, start_date=start_date)

        # Should return empty set due to missing fields causing KeyError
        assert result == set()