import pytest
from unittest.mock import patch, Mock
from services.github.actions_manager import (
    get_failed_step_log_file_name,
    get_workflow_run_path,
    get_workflow_run_logs
)


@patch('services.github.actions_manager.requests.get')
def test_get_failed_step_log_file_name(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "jobs": [
            {
                "name": "build",
                "steps": [
                    {"conclusion": "success", "number": 1, "name": "checkout"},
                    {"conclusion": "failure", "number": 2, "name": "test"}
                ]
            }
        ]
    }
    mock_get.return_value = mock_response

    result = get_failed_step_log_file_name("owner", "repo", 123, "token")
    assert result == "build/2_test.txt"


@patch('services.github.actions_manager.requests.get')
def test_get_workflow_run_path(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"path": "/path/to/workflow"}
    mock_get.return_value = mock_response

    result = get_workflow_run_path("owner", "repo", 123, "token")
    assert result == "/path/to/workflow"


@patch('services.github.actions_manager.requests.get')
@patch('services.github.actions_manager.get_failed_step_log_file_name')
def test_get_workflow_run_logs(mock_get_failed_step, mock_get):
    mock_get_failed_step.return_value = "build/2_test.txt"

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = b""  # Simulate zip file content
    mock_get.return_value = mock_response

    with patch('zipfile.ZipFile') as MockZipFile:
        mock_zip = MockZipFile.return_value.__enter__.return_value
        mock_zip.namelist.return_value = ["build/2_test.txt"]
        mock_zip.open.return_value.__enter__.return_value.read.return_value = b"2024-10-18T23:27:40.6602932Z log content"

        result = get_workflow_run_logs("owner", "repo", 123, "token")
        assert result == "```GitHub Check Run Log: build/2_test.txt\nlog content\n```"
