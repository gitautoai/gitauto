import json
from unittest.mock import Mock, patch
import requests

from services.supabase.usage.insert_usage import insert_usage


def test_insert_usage_success_with_all_parameters():
    """Test successful usage insertion with all parameters provided"""
    with patch("services.supabase.usage.insert_usage.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = ([None, [{"id": 123}]], None)

        result = insert_usage(
            owner_id=1,
            owner_type="Organization",
            owner_name="test_org",
            repo_id=2,
            repo_name="test_repo",
            issue_number=3,
            user_id=4,
            installation_id=5,
            source="test",
            trigger="issue_label",
            pr_number=6,
        )

        assert result == 123
        mock_supabase.table.assert_called_once_with(table_name="usage")
        mock_table.insert.assert_called_once_with(
            json={
                "owner_id": 1,
                "owner_type": "Organization",
                "owner_name": "test_org",
                "repo_id": 2,
                "repo_name": "test_repo",
                "issue_number": 3,
                "user_id": 4,
                "installation_id": 5,
                "source": "test",
                "trigger": "issue_label",
                "pr_number": 6,
                "is_test_passed": False,
                "lambda_log_group": None,
                "lambda_log_stream": None,
                "lambda_request_id": None,
            }
        )
        mock_table.execute.assert_called_once()


def test_insert_usage_success_without_pr_number():
    """Test successful usage insertion without pr_number"""
    with patch("services.supabase.usage.insert_usage.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = ([None, [{"id": 123}]], None)

        result = insert_usage(
            owner_id=1,
            owner_type="Organization",
            owner_name="test_org",
            repo_id=2,
            repo_name="test_repo",
            issue_number=3,
            user_id=4,
            installation_id=5,
            source="test",
            trigger="issue_label",
        )

        assert result == 123
        mock_table.insert.assert_called_once_with(
            json={
                "owner_id": 1,
                "owner_type": "Organization",
                "owner_name": "test_org",
                "repo_id": 2,
                "repo_name": "test_repo",
                "issue_number": 3,
                "user_id": 4,
                "installation_id": 5,
                "source": "test",
                "trigger": "issue_label",
                "pr_number": None,
                "is_test_passed": False,
                "lambda_log_group": None,
                "lambda_log_stream": None,
                "lambda_request_id": None,
            }
        )


def test_insert_usage_with_zero_values():
    """Test usage insertion with zero values"""
    with patch("services.supabase.usage.insert_usage.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = ([None, [{"id": 0}]], None)

        result = insert_usage(
            owner_id=0,
            owner_type="Organization",
            owner_name="test_org",
            repo_id=0,
            repo_name="test_repo",
            issue_number=0,
            user_id=0,
            installation_id=0,
            source="test",
            trigger="issue_label",
            pr_number=0,
        )

        assert result == 0
        mock_table.insert.assert_called_once_with(
            json={
                "owner_id": 0,
                "owner_type": "Organization",
                "owner_name": "test_org",
                "repo_id": 0,
                "repo_name": "test_repo",
                "issue_number": 0,
                "user_id": 0,
                "installation_id": 0,
                "source": "test",
                "trigger": "issue_label",
                "pr_number": 0,
                "is_test_passed": False,
                "lambda_log_group": None,
                "lambda_log_stream": None,
                "lambda_request_id": None,
            }
        )


def test_insert_usage_with_different_triggers():
    """Test usage insertion with different valid triggers"""
    triggers = [
        "issue_label",
        "issue_comment",
        "review_comment",
        "test_failure",
        "pr_checkbox",
        "pr_merge",
    ]

    with patch("services.supabase.usage.insert_usage.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = ([None, [{"id": 123}]], None)

        for trigger in triggers:
            result = insert_usage(
                owner_id=1,
                owner_type="Organization",
                owner_name="test_org",
                repo_id=2,
                repo_name="test_repo",
                issue_number=3,
                user_id=4,
                installation_id=5,
                source="test",
                trigger=trigger,
            )

            assert result == 123


def test_insert_usage_with_exception():
    """Test usage insertion when supabase raises an exception"""
    with patch("services.supabase.usage.insert_usage.supabase") as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database error")

        result = insert_usage(
            owner_id=1,
            owner_type="Organization",
            owner_name="test_org",
            repo_id=2,
            repo_name="test_repo",
            issue_number=3,
            user_id=4,
            installation_id=5,
            source="test",
            trigger="issue_label",
        )

        assert result is None


def test_insert_usage_with_http_error():
    """Test usage insertion when HTTP error is raised"""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.reason = "Internal Server Error"
    mock_response.text = "Server error"

    http_error = requests.exceptions.HTTPError(response=mock_response)

    with patch("services.supabase.usage.insert_usage.supabase") as mock_supabase:
        mock_supabase.table.side_effect = http_error

        result = insert_usage(
            owner_id=1,
            owner_type="Organization",
            owner_name="test_org",
            repo_id=2,
            repo_name="test_repo",
            issue_number=3,
            user_id=4,
            installation_id=5,
            source="test",
            trigger="issue_label",
        )

        assert result is None


def test_insert_usage_with_json_decode_error():
    """Test usage insertion when JSONDecodeError is raised"""
    with patch("services.supabase.usage.insert_usage.supabase") as mock_supabase:
        mock_supabase.table.side_effect = json.JSONDecodeError("JSON error", "", 0)

        result = insert_usage(
            owner_id=1,
            owner_type="Organization",
            owner_name="test_org",
            repo_id=2,
            repo_name="test_repo",
            issue_number=3,
            user_id=4,
            installation_id=5,
            source="test",
            trigger="issue_label",
        )

        assert result is None


def test_insert_usage_execute_exception():
    """Test usage insertion when execute method raises an exception"""
    with patch("services.supabase.usage.insert_usage.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.side_effect = Exception("Execute error")

        result = insert_usage(
            owner_id=1,
            owner_type="Organization",
            owner_name="test_org",
            repo_id=2,
            repo_name="test_repo",
            issue_number=3,
            user_id=4,
            installation_id=5,
            source="test",
            trigger="issue_label",
        )

        assert result is None
