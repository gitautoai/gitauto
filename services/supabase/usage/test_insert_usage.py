# pylint: disable=import-outside-toplevel
import json
from unittest.mock import Mock, MagicMock
import requests

from services.supabase.usage.insert_usage import Trigger, insert_usage


def _mock_response(data):
    mock = MagicMock()
    mock.data = data
    return mock


def test_insert_usage_success_with_all_parameters():
    from unittest.mock import patch

    mock_supabase = MagicMock()
    mock_table = Mock()
    mock_supabase.table.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.execute.return_value = _mock_response([{"id": 123}])

    with patch("services.supabase.usage.insert_usage.supabase", mock_supabase):
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


def test_insert_usage_success_without_pr_number():
    from unittest.mock import patch

    mock_supabase = MagicMock()
    mock_table = Mock()
    mock_supabase.table.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.execute.return_value = _mock_response([{"id": 123}])

    with patch("services.supabase.usage.insert_usage.supabase", mock_supabase):
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


def test_insert_usage_with_zero_values():
    from unittest.mock import patch

    mock_supabase = MagicMock()
    mock_table = Mock()
    mock_supabase.table.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.execute.return_value = _mock_response([{"id": 0}])

    with patch("services.supabase.usage.insert_usage.supabase", mock_supabase):
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


def test_insert_usage_with_different_triggers():
    from unittest.mock import patch

    triggers: list[Trigger] = [
        "issue_label",
        "issue_comment",
        "review_comment",
        "test_failure",
        "pr_checkbox",
        "pr_merge",
    ]

    mock_supabase = MagicMock()
    mock_table = Mock()
    mock_supabase.table.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.execute.return_value = _mock_response([{"id": 123}])

    with patch("services.supabase.usage.insert_usage.supabase", mock_supabase):
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
    from unittest.mock import patch

    mock_supabase = MagicMock()
    mock_supabase.table.side_effect = Exception("Database error")

    with patch("services.supabase.usage.insert_usage.supabase", mock_supabase):
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
    from unittest.mock import patch

    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.reason = "Internal Server Error"
    mock_response.text = "Server error"

    http_error = requests.exceptions.HTTPError(response=mock_response)

    mock_supabase = MagicMock()
    mock_supabase.table.side_effect = http_error

    with patch("services.supabase.usage.insert_usage.supabase", mock_supabase):
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
    from unittest.mock import patch

    mock_supabase = MagicMock()
    mock_supabase.table.side_effect = json.JSONDecodeError("JSON error", "", 0)

    with patch("services.supabase.usage.insert_usage.supabase", mock_supabase):
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
    from unittest.mock import patch

    mock_supabase = MagicMock()
    mock_table = Mock()
    mock_supabase.table.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.execute.side_effect = Exception("Execute error")

    with patch("services.supabase.usage.insert_usage.supabase", mock_supabase):
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
