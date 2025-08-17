"""Unit tests for get_circleci_build_logs using mocked data."""

import json
from unittest.mock import patch, Mock

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

    # Load mock build data and modify status
    with open("payloads/circleci/build_16.json", "r", encoding=UTF8) as f:
        mock_build_data = json.load(f)
    
    mock_build_data["status"] = "infrastructure_fail"

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
def test_get_build_logs_timedout_status(mock_get):
    """Test getting logs from a build with timedout status."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    # Load mock build data and modify status
    with open("payloads/circleci/build_16.json", "r", encoding=UTF8) as f:
        mock_build_data = json.load(f)
    
    mock_build_data["status"] = "timedout"

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
def test_get_build_logs_no_output_url(mock_get):
    """Test getting logs when action has no output_url."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    # Create mock build data with failed action but no output_url
    mock_build_data = {
        "status": "failed",
        "steps": [
            {
                "name": "Test Step",
                "actions": [
                    {
                        "status": "failed",
                        "output_url": None  # No output URL
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
def test_get_build_logs_log_request_fails(mock_get):
    """Test when log output request fails."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    # Create mock build data with failed action and output_url
    mock_build_data = {
        "status": "failed",
        "steps": [
            {
                "name": "Test Step",
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
        else:  # output_url request fails
            mock_response.status_code = 500
        return mock_response

    mock_get.side_effect = mock_get_side_effect

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert result == "No error logs found in CircleCI build."


@patch("services.circleci.get_build_logs.get")
def test_get_build_logs_non_list_log_data(mock_get):
    """Test when log data is not a list."""
    project_slug = "test/project/slug"
    build_number = 16
    token = "test-token"

    # Create mock build data
    mock_build_data = {
        "status": "failed",
        "steps": [
            {
                "name": "Test Step",
                "actions": [
                    {
                        "status": "failed",
                        "output_url": "https://example.com/logs"
                    }
                ]
            }
        ]
    }

    # Mock log data as string instead of list
    mock_log_data = "Error log as string"

