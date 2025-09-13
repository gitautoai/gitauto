"""Unit tests for get_circleci_build_logs using mocked data."""

import json
from unittest.mock import patch, Mock
import pytest
import requests

from config import UTF8
from services.circleci.get_build_logs import get_circleci_build_logs


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_with_valid_token(mock_get):
    """Test getting build logs with valid token and project slug."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    # Load mock build data
    with open("payloads/circleci/build_16.json", "r", encoding=UTF8) as f:
        mock_build_data = json.load(f)

    # Load mock log entries
    with open("payloads/circleci/log_entries.json", "r", encoding=UTF8) as f:
        mock_log_data = json.load(f)

    def mock_get_side_effect(url, **_kwargs):
        mock_response = Mock()
        if "/project/" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = mock_build_data
        else:  # output_url request
            mock_response.status_code = 200
            mock_response.json.return_value = mock_log_data
        return mock_response

    mock_get.side_effect = mock_get_side_effect

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert isinstance(result, str)
    assert "CircleCI Build Log" in result


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_without_token(mock_get):
    """Test getting build logs without token."""
    project_slug = "test/project/slug"
    build_number = 16

    mock_response = Mock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    result = get_circleci_build_logs(project_slug, build_number, "")

    assert result == 404


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_with_invalid_build_number(mock_get):
    """Test getting build logs with invalid build number."""
    project_slug = "test/project/slug"
    build_number = 99999
    token = "test-token"

    mock_response = Mock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert result == 404


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_successful_build(mock_get):
    """Test getting logs from a successful build (should return None)."""
    project_slug = "test/project/slug"
    build_number = 15
    token = "test-token"

    # Load successful build data
    with open("payloads/circleci/build_15.json", "r", encoding=UTF8) as f:
        mock_build_data = json.load(f)

    # Modify to be successful
    mock_build_data["status"] = "success"
    mock_build_data["failed"] = False

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_build_data
    mock_get.return_value = mock_response

    result = get_circleci_build_logs(project_slug, build_number, token)

    # Successful build should return None (no error logs)
    assert result is None


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_authentication_failed(mock_get):
    """Test getting build logs with authentication failure."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "invalid-token"

    mock_response = Mock()
    mock_response.status_code = 401
    mock_get.return_value = mock_response

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert result == "CircleCI authentication failed. Please check your token."


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_infrastructure_fail_status(mock_get):
    """Test getting logs from a build with infrastructure_fail status."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    mock_build_data = {
        "status": "infrastructure_fail",
        "failed": True,
        "steps": [
            {
                "name": "Test Step",
                "actions": [
                    {
                        "status": "infrastructure_fail",
                        "output_url": "https://example.com/logs"
                    }
                ]
            }
        ]
    }

    mock_log_data = [{"message": "Infrastructure failure occurred", "time": "2025-01-01T00:00:00Z", "type": "out"}]

    def mock_get_side_effect(url, **_kwargs):
        mock_response = Mock()
        if "/project/" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = mock_build_data
        else:  # output_url request
            mock_response.status_code = 200
            mock_response.json.return_value = mock_log_data
        return mock_response

    mock_get.side_effect = mock_get_side_effect

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert isinstance(result, str)
    assert "CircleCI Build Log: Test Step" in result
    assert "Infrastructure failure occurred" in result


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_timedout_status(mock_get):
    """Test getting logs from a build with timedout status."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    mock_build_data = {
        "status": "timedout",
        "failed": True,
        "steps": [
            {
                "name": "Timeout Step",
                "actions": [
                    {
                        "status": "timedout",
                        "output_url": "https://example.com/logs"
                    }
                ]
            }
        ]
    }

    mock_log_data = [{"message": "Build timed out", "time": "2025-01-01T00:00:00Z", "type": "out"}]

    def mock_get_side_effect(url, **_kwargs):
        mock_response = Mock()
        if "/project/" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = mock_build_data
        else:  # output_url request
            mock_response.status_code = 200
            mock_response.json.return_value = mock_log_data
        return mock_response

    mock_get.side_effect = mock_get_side_effect

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert isinstance(result, str)
    assert "CircleCI Build Log: Timeout Step" in result
    assert "Build timed out" in result


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_no_steps(mock_get):
    """Test getting logs from a build with no steps."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    mock_build_data = {
        "status": "failed",
        "failed": True,
        "steps": []
    }

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_build_data
    mock_get.return_value = mock_response

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert result == "No error logs found in CircleCI build."


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_no_actions(mock_get):
    """Test getting logs from a build with steps but no actions."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    mock_build_data = {
        "status": "failed",
        "failed": True,
        "steps": [
            {
                "name": "Empty Step",
                "actions": []
            }
        ]
    }

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_build_data
    mock_get.return_value = mock_response

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert result == "No error logs found in CircleCI build."


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_no_failed_actions(mock_get):
    """Test getting logs from a build with successful actions only."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    mock_build_data = {
        "status": "failed",
        "failed": True,
        "steps": [
            {
                "name": "Success Step",
                "actions": [
                    {
                        "status": "success",
                        "output_url": "https://example.com/logs"
                    }
                ]
            }
        ]
    }

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_build_data
    mock_get.return_value = mock_response

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert result == "No error logs found in CircleCI build."


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_no_output_url(mock_get):
    """Test getting logs from a failed action without output_url."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    mock_build_data = {
        "status": "failed",
        "failed": True,
        "steps": [
            {
                "name": "Failed Step",
                "actions": [
                    {
                        "status": "failed",
                        "output_url": None
                    }
                ]
            }
        ]
    }

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_build_data
    mock_get.return_value = mock_response

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert result == "No error logs found in CircleCI build."


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_log_request_failed(mock_get):
    """Test getting logs when log request fails."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    mock_build_data = {
        "status": "failed",
        "failed": True,
        "steps": [
            {
                "name": "Failed Step",
                "actions": [
                    {
                        "status": "failed",
                        "output_url": "https://example.com/logs"
                    }
                ]
            }
        ]
    }

    def mock_get_side_effect(url, **_kwargs):
        mock_response = Mock()
        if "/project/" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = mock_build_data
        else:  # output_url request
            mock_response.status_code = 500
        return mock_response

    mock_get.side_effect = mock_get_side_effect

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert result == "No error logs found in CircleCI build."


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_non_list_log_data(mock_get):
    """Test getting logs when log data is not a list."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    mock_build_data = {
        "status": "failed",
        "failed": True,
        "steps": [
            {
                "name": "Failed Step",
                "actions": [
                    {
                        "status": "failed",
                        "output_url": "https://example.com/logs"
                    }
                ]
            }
        ]
    }

    mock_log_data = "This is a string log instead of list"

    def mock_get_side_effect(url, **_kwargs):
        mock_response = Mock()
        if "/project/" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = mock_build_data
        else:  # output_url request
            mock_response.status_code = 200
            mock_response.json.return_value = mock_log_data
        return mock_response

    mock_get.side_effect = mock_get_side_effect

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert isinstance(result, str)
    assert "CircleCI Build Log: Failed Step" in result
    assert "This is a string log instead of list" in result


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_non_dict_log_entries(mock_get):
    """Test getting logs when log entries are not dictionaries."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    mock_build_data = {
        "status": "failed",
        "failed": True,
        "steps": [
            {
                "name": "Failed Step",
                "actions": [
                    {
                        "status": "failed",
                        "output_url": "https://example.com/logs"
                    }
                ]
            }
        ]
    }

    mock_log_data = ["string entry", 123, {"message": "dict entry", "time": "2025-01-01T00:00:00Z", "type": "out"}]

    def mock_get_side_effect(url, **_kwargs):
        mock_response = Mock()
        if "/project/" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = mock_build_data
        else:  # output_url request
            mock_response.status_code = 200
            mock_response.json.return_value = mock_log_data
        return mock_response

    mock_get.side_effect = mock_get_side_effect

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert isinstance(result, str)
    assert "CircleCI Build Log: Failed Step" in result
    assert "string entry" in result
    assert "123" in result
    assert "dict entry" in result


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_carriage_return_cleanup(mock_get):
    """Test that carriage returns are properly cleaned up in log messages."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    mock_build_data = {
        "status": "failed",
        "failed": True,
        "steps": [
            {
                "name": "Failed Step",
                "actions": [
                    {
                        "status": "failed",
                        "output_url": "https://example.com/logs"
                    }
                ]
            }
        ]
    }

    mock_log_data = [
        {
            "message": "Line 1\r\nLine 2\rLine 3",
            "time": "2025-01-01T00:00:00Z",
            "type": "out"
        }
    ]

    def mock_get_side_effect(url, **_kwargs):
        mock_response = Mock()
        if "/project/" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = mock_build_data
        else:  # output_url request
            mock_response.status_code = 200
            mock_response.json.return_value = mock_log_data
        return mock_response

    mock_get.side_effect = mock_get_side_effect

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert isinstance(result, str)
    assert "Line 1\nLine 2\nLine 3" in result
    assert "\r" not in result


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_multiple_failed_actions_only_first_processed(mock_get):
    """Test that only the first failed action per step is processed."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    mock_build_data = {
        "status": "failed",
        "failed": True,
        "steps": [
            {
                "name": "Multi-Action Step",
                "actions": [
                    {
                        "status": "failed",
                        "output_url": "https://example.com/logs1"
                    },
                    {
                        "status": "failed",
                        "output_url": "https://example.com/logs2"
                    }
                ]
            }
        ]
    }

    call_count = 0

    def mock_get_side_effect(url, **_kwargs):
        nonlocal call_count
        mock_response = Mock()
        if "/project/" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = mock_build_data
        else:  # output_url request
            call_count += 1
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"message": f"Log from action {call_count}", "time": "2025-01-01T00:00:00Z", "type": "out"}
            ]
        return mock_response

    mock_get.side_effect = mock_get_side_effect

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert isinstance(result, str)
    assert "Log from action 1" in result
    assert "Log from action 2" not in result
    # Only one log request should be made (first failed action)
    assert call_count == 1


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_multiple_steps_with_logs(mock_get):
    """Test getting logs from multiple steps with failed actions."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    mock_build_data = {
        "status": "failed",
        "failed": True,
        "steps": [
            {
                "name": "Step 1",
                "actions": [
                    {
                        "status": "failed",
                        "output_url": "https://example.com/logs1"
                    }
                ]
            },
            {
                "name": "Step 2",
                "actions": [
                    {
                        "status": "failed",
                        "output_url": "https://example.com/logs2"
                    }
                ]
            }
        ]
    }

    call_count = 0

    def mock_get_side_effect(url, **_kwargs):
        nonlocal call_count
        mock_response = Mock()
        if "/project/" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = mock_build_data
        else:  # output_url request
            call_count += 1
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"message": f"Log from step {call_count}", "time": "2025-01-01T00:00:00Z", "type": "out"}
            ]
        return mock_response

    mock_get.side_effect = mock_get_side_effect

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert isinstance(result, str)
    assert "CircleCI Build Log: Step 1" in result
    assert "CircleCI Build Log: Step 2" in result
    assert "Log from step 1" in result
    assert "Log from step 2" in result
    # Two separate log sections should be joined with double newlines
    assert "\n\n" in result


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_missing_step_name(mock_get):
    """Test getting logs from a step without a name."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    mock_build_data = {
        "status": "failed",
        "failed": True,
        "steps": [
            {
                "actions": [
                    {
                        "status": "failed",
                        "output_url": "https://example.com/logs"
                    }
                ]
            }
        ]
    }

    mock_log_data = [{"message": "Log message", "time": "2025-01-01T00:00:00Z", "type": "out"}]

    def mock_get_side_effect(url, **_kwargs):
        mock_response = Mock()
        if "/project/" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = mock_build_data
        else:  # output_url request
            mock_response.status_code = 200
            mock_response.json.return_value = mock_log_data
        return mock_response

    mock_get.side_effect = mock_get_side_effect

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert isinstance(result, str)
    assert "CircleCI Build Log: Unknown Step" in result
    assert "Log message" in result


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_http_error_raises_for_status(mock_get):
    """Test that HTTP errors are handled by the decorator."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = requests.HTTPError("Server Error")
    mock_get.return_value = mock_response

    # The handle_exceptions decorator should catch this and return None
    result = get_circleci_build_logs(project_slug, build_number, token)

    assert result is None


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_missing_steps_key(mock_get):
    """Test getting logs from build data without steps key."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    mock_build_data = {
        "status": "failed",
        "failed": True
        # Missing "steps" key
    }

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_build_data
    mock_get.return_value = mock_response

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert result == "No error logs found in CircleCI build."


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_missing_actions_key(mock_get):
    """Test getting logs from step without actions key."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    mock_build_data = {
        "status": "failed",
        "failed": True,
        "steps": [
            {
                "name": "Step without actions"
                # Missing "actions" key
            }
        ]
    }

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_build_data
    mock_get.return_value = mock_response

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert result == "No error logs found in CircleCI build."


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_empty_log_message(mock_get):
    """Test getting logs with empty message."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    mock_build_data = {
        "status": "failed",
        "failed": True,
        "steps": [
            {
                "name": "Failed Step",
                "actions": [
                    {
                        "status": "failed",
                        "output_url": "https://example.com/logs"
                    }
                ]
            }
        ]
    }

    mock_log_data = [
        {
            "message": "",
            "time": "2025-01-01T00:00:00Z",
            "type": "out"
        },
        {
            "time": "2025-01-01T00:00:00Z",
            "type": "out"
            # Missing "message" key
        }
    ]

    def mock_get_side_effect(url, **_kwargs):
        mock_response = Mock()
        if "/project/" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = mock_build_data
        else:  # output_url request
            mock_response.status_code = 200
            mock_response.json.return_value = mock_log_data
        return mock_response

    mock_get.side_effect = mock_get_side_effect

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert isinstance(result, str)
    assert "CircleCI Build Log: Failed Step" in result
    # Should handle empty messages gracefully