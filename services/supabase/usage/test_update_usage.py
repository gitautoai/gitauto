import json
from unittest.mock import Mock, patch
import requests

from services.supabase.usage.update_usage import update_usage


def test_update_usage_success_with_all_parameters():
    mock_response = Mock()
    mock_response.data = [{"id": 1}]

    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response

        result = update_usage(
            usage_id=123,
            token_input=100,
            token_output=200,
            total_seconds=300,
            is_completed=True,
            pr_number=456,
            retry_workflow_id_hash_pairs=["hash1", "hash2"],
            original_error_log="Original error log content",
            minimized_error_log="Minimized error log content",
            lambda_log_group="/aws/lambda/pr-agent-prod",
            lambda_log_stream="2025/09/04/pr-agent-prod[$LATEST]841315c5",
            lambda_request_id="17921070-5cb6-43ee-8d2e-b5161ae89729",
            is_test_passed=True,
            is_merged=False,
        )

        assert result is None
        mock_supabase.table.assert_called_once_with(table_name="usage")
        mock_table.update.assert_called_once_with(
            json={
                "token_input": 100,
                "token_output": 200,
                "total_seconds": 300,
                "is_completed": True,
                "pr_number": 456,
                "retry_workflow_id_hash_pairs": ["hash1", "hash2"],
                "original_error_log": "Original error log content",
                "minimized_error_log": "Minimized error log content",
                "lambda_log_group": "/aws/lambda/pr-agent-prod",
                "lambda_log_stream": "2025/09/04/pr-agent-prod[$LATEST]841315c5",
                "lambda_request_id": "17921070-5cb6-43ee-8d2e-b5161ae89729",
                "is_test_passed": True,
                "is_merged": False,
            }
        )
        mock_table.eq.assert_called_once_with(column="id", value=123)
        mock_table.execute.assert_called_once()


def test_update_usage_success_with_default_parameters():
    mock_response = Mock()
    mock_response.data = [{"id": 1}]

    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response

        result = update_usage(
            usage_id=123, token_input=100, token_output=200, total_seconds=300
        )

        assert result is None
        mock_table.update.assert_called_once_with(
            json={
                "token_input": 100,
                "token_output": 200,
                "total_seconds": 300,
            }
        )


def test_update_usage_with_is_completed_false():
    mock_response = Mock()
    mock_response.data = [{"id": 1}]

    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response

        result = update_usage(
            usage_id=123,
            token_input=100,
            token_output=200,
            total_seconds=300,
            is_completed=False,
        )

        assert result is None
        mock_table.update.assert_called_once_with(
            json={
                "token_input": 100,
                "token_output": 200,
                "total_seconds": 300,
                "is_completed": False,
            }
        )


def test_update_usage_with_zero_values():
    mock_response = Mock()
    mock_response.data = [{"id": 1}]

    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response

        result = update_usage(
            usage_id=0, token_input=0, token_output=0, total_seconds=0, pr_number=0
        )

        assert result is None
        mock_table.eq.assert_called_once_with(column="id", value=0)
        mock_table.update.assert_called_once_with(
            json={
                "token_input": 0,
                "token_output": 0,
                "total_seconds": 0,
                "pr_number": 0,
            }
        )


def test_update_usage_with_negative_values():
    mock_response = Mock()
    mock_response.data = [{"id": 1}]

    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response

        result = update_usage(
            usage_id=-1,
            token_input=-10,
            token_output=-20,
            total_seconds=-30,
            pr_number=-5,
        )

        assert result is None
        mock_table.eq.assert_called_once_with(column="id", value=-1)
        mock_table.update.assert_called_once_with(
            json={
                "token_input": -10,
                "token_output": -20,
                "total_seconds": -30,
                "pr_number": -5,
            }
        )


def test_update_usage_with_large_values():
    mock_response = Mock()
    mock_response.data = [{"id": 1}]

    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response

        result = update_usage(
            usage_id=999999999,
            token_input=888888888,
            token_output=777777777,
            total_seconds=666666666,
            pr_number=555555555,
        )

        assert result is None
        mock_table.eq.assert_called_once_with(column="id", value=999999999)
        mock_table.update.assert_called_once_with(
            json={
                "token_input": 888888888,
                "token_output": 777777777,
                "total_seconds": 666666666,
                "pr_number": 555555555,
            }
        )


def test_update_usage_with_only_usage_id():
    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        result = update_usage(usage_id=123)

        assert result is None
        mock_supabase.table.assert_not_called()


def test_update_usage_with_none_values_filtered():
    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table

        result = update_usage(
            usage_id=123,
            token_input=100,
            token_output=None,
            is_completed=True,
            pr_number=None,
        )

        assert result is None
        mock_table.update.assert_called_once_with(
            json={
                "token_input": 100,
                "is_completed": True,
            }
        )


def test_update_usage_with_is_merged_only():
    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table

        result = update_usage(usage_id=123, is_merged=True)

        assert result is None
        mock_table.update.assert_called_once_with(json={"is_merged": True})


def test_update_usage_with_is_test_passed_only():
    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table

        result = update_usage(usage_id=123, is_test_passed=False)

        assert result is None
        mock_table.update.assert_called_once_with(json={"is_test_passed": False})


def test_update_usage_with_exception():
    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_supabase.table.side_effect = Exception("Database error")

        result = update_usage(
            usage_id=123, token_input=100, token_output=200, total_seconds=300
        )

        assert result is None


def test_update_usage_with_attribute_error():
    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_supabase.table.side_effect = AttributeError("Attribute error")

        result = update_usage(
            usage_id=123, token_input=100, token_output=200, total_seconds=300
        )

        assert result is None


def test_update_usage_with_key_error():
    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_supabase.table.side_effect = KeyError("Key error")

        result = update_usage(
            usage_id=123, token_input=100, token_output=200, total_seconds=300
        )

        assert result is None


def test_update_usage_with_type_error():
    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_supabase.table.side_effect = TypeError("Type error")

        result = update_usage(
            usage_id=123, token_input=100, token_output=200, total_seconds=300
        )

        assert result is None


def test_update_usage_with_json_decode_error():
    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_supabase.table.side_effect = json.JSONDecodeError("JSON error", "", 0)

        result = update_usage(
            usage_id=123, token_input=100, token_output=200, total_seconds=300
        )

        assert result is None


def test_update_usage_with_http_error_500():
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.reason = "Internal Server Error"
    mock_response.text = "Server error"

    http_error = requests.exceptions.HTTPError(response=mock_response)

    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_supabase.table.side_effect = http_error

        result = update_usage(
            usage_id=123, token_input=100, token_output=200, total_seconds=300
        )

        assert result is None


def test_update_usage_with_http_error_409():
    mock_response = Mock()
    mock_response.status_code = 409
    mock_response.reason = "Conflict"
    mock_response.text = "Conflict error"

    http_error = requests.exceptions.HTTPError(response=mock_response)

    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_supabase.table.side_effect = http_error

        result = update_usage(
            usage_id=123, token_input=100, token_output=200, total_seconds=300
        )

        assert result is None


def test_update_usage_with_http_error_422():
    mock_response = Mock()
    mock_response.status_code = 422
    mock_response.reason = "Unprocessable Entity"
    mock_response.text = "Validation error"

    http_error = requests.exceptions.HTTPError(response=mock_response)

    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_supabase.table.side_effect = http_error

        result = update_usage(
            usage_id=123, token_input=100, token_output=200, total_seconds=300
        )

        assert result is None


def test_update_usage_execute_exception():
    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.side_effect = Exception("Execute error")

        result = update_usage(
            usage_id=123, token_input=100, token_output=200, total_seconds=300
        )

        assert result is None


def test_update_usage_update_exception():
    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.side_effect = Exception("Update error")

        result = update_usage(
            usage_id=123, token_input=100, token_output=200, total_seconds=300
        )

        assert result is None


def test_update_usage_eq_exception():
    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.side_effect = Exception("Eq error")

        result = update_usage(
            usage_id=123, token_input=100, token_output=200, total_seconds=300
        )

        assert result is None


def test_update_usage_table_exception():
    with patch("services.supabase.usage.update_usage.supabase") as mock_supabase:
        mock_supabase.table.side_effect = Exception("Table error")

        result = update_usage(
            usage_id=123, token_input=100, token_output=200, total_seconds=300
        )

        assert result is None
