from unittest.mock import patch, MagicMock

import pytest
import requests

from services.github.workflow_runs.get_failed_step_log_file_name import (
    get_failed_step_log_file_name,
)


@pytest.fixture
def mock_successful_response():
    """Fixture providing a successful API response with failed step."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "jobs": [
            {
                "name": "build",
                "steps": [
                    {"number": 1, "name": "Set up job", "conclusion": "success"},
                    {"number": 2, "name": "Run tests", "conclusion": "failure"},
                    {"number": 3, "name": "Clean up", "conclusion": "skipped"},
                ],
            }
        ]
    }
    return mock_response


@pytest.fixture
def mock_no_failed_steps_response():
    """Fixture providing a response with no failed steps."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "jobs": [
            {
                "name": "build",
                "steps": [
                    {"number": 1, "name": "Set up job", "conclusion": "success"},
                    {"number": 2, "name": "Run tests", "conclusion": "success"},
                ],
            }
        ]
    }
    return mock_response


@pytest.fixture
def mock_404_response():
    """Fixture providing a 404 Not Found response."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    return mock_response


@pytest.fixture
def mock_headers(test_token):
    """Fixture providing mock headers."""
    return {"Authorization": f"Bearer {test_token}"}


def test_get_failed_step_log_file_name_success(
    mock_successful_response, mock_headers, test_owner, test_repo, test_token
):
    """Test successful retrieval of failed step log file name."""
    # Arrange
    run_id = 12345
    expected_filename = "build/2_Run tests.txt"

    # Act
    with patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_successful_response
        result = get_failed_step_log_file_name(
            test_owner, test_repo, run_id, test_token
        )

    # Assert
    mock_create_headers.assert_called_once_with(token=test_token)
    mock_get.assert_called_once()
    assert (
        mock_get.call_args[1]["url"]
        == f"https://api.github.com/repos/{test_owner}/{test_repo}/actions/runs/{run_id}/jobs"
    )
    assert mock_get.call_args[1]["headers"] == mock_headers
    assert mock_get.call_args[1]["timeout"] == 120
    mock_successful_response.raise_for_status.assert_called_once()
    mock_successful_response.json.assert_called_once()
    assert result == expected_filename


def test_get_failed_step_log_file_name_no_failed_steps(
    mock_no_failed_steps_response, mock_headers, test_owner, test_repo, test_token
):
    """Test handling when no failed steps are found."""
    # Arrange
    run_id = 12345

    # Act
    with patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_no_failed_steps_response
        result = get_failed_step_log_file_name(
            test_owner, test_repo, run_id, test_token
        )

    # Assert
    mock_get.assert_called_once()
    mock_no_failed_steps_response.raise_for_status.assert_called_once()
    mock_no_failed_steps_response.json.assert_called_once()
    assert result is None


def test_get_failed_step_log_file_name_404_not_found(
    mock_404_response, mock_headers, test_owner, test_repo, test_token
):
    """Test handling of 404 Not Found response."""
    # Arrange
    run_id = 12345

    # Act
    with patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_404_response
        result = get_failed_step_log_file_name(
            test_owner, test_repo, run_id, test_token
        )

    # Assert
    mock_get.assert_called_once()
    mock_404_response.raise_for_status.assert_not_called()
    mock_404_response.json.assert_not_called()
    assert result == 404


def test_get_failed_step_log_file_name_404_without_not_found_text(
    mock_headers, test_owner, test_repo, test_token
):
    """Test handling of 404 response without 'Not Found' in text."""
    # Arrange
    run_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Some other error message"
    mock_response.json.return_value = {
        "jobs": [
            {
                "name": "test",
                "steps": [
                    {"number": 1, "name": "Failed step", "conclusion": "failure"}
                ],
            }
        ]
    }

    # Act
    with patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_response
        result = get_failed_step_log_file_name(
            test_owner, test_repo, run_id, test_token
        )

    # Assert
    mock_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    assert result == "test/1_Failed step.txt"


def test_get_failed_step_log_file_name_multiple_jobs_first_failed(
    test_owner, test_repo, test_token
):
    """Test with multiple jobs where first job has failed step."""
    # Arrange
    run_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "jobs": [
            {
                "name": "lint",
                "steps": [
                    {"number": 1, "name": "Setup", "conclusion": "success"},
                    {"number": 2, "name": "Run linter", "conclusion": "failure"},
                ],
            },
            {
                "name": "test",
                "steps": [{"number": 1, "name": "Run tests", "conclusion": "failure"}],
            },
        ]
    }

    # Act
    with patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.create_headers"
    ):
        mock_get.return_value = mock_response
        result = get_failed_step_log_file_name(
            test_owner, test_repo, run_id, test_token
        )

    # Assert - should return first failed step found
    assert result == "lint/2_Run linter.txt"


def test_get_failed_step_log_file_name_missing_job_name(
    test_owner, test_repo, test_token
):
    """Test handling when job name is missing."""
    # Arrange
    run_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "jobs": [
            {"steps": [{"number": 1, "name": "Failed step", "conclusion": "failure"}]}
        ]
    }

    # Act
    with patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.create_headers"
    ):
        mock_get.return_value = mock_response
        result = get_failed_step_log_file_name(
            test_owner, test_repo, run_id, test_token
        )

    # Assert - should use default job name
    assert result == "unknown_job/1_Failed step.txt"


def test_get_failed_step_log_file_name_empty_jobs_list(
    test_owner, test_repo, test_token
):
    """Test handling when jobs list is empty."""
    # Arrange
    run_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"jobs": []}

    # Act
    with patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.create_headers"
    ):
        mock_get.return_value = mock_response
        result = get_failed_step_log_file_name(
            test_owner, test_repo, run_id, test_token
        )

    # Assert
    assert result is None


def test_get_failed_step_log_file_name_missing_jobs_key(
    test_owner, test_repo, test_token
):
    """Test handling when 'jobs' key is missing from response."""
    # Arrange
    run_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"other_field": "value"}

    # Act
    with patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.create_headers"
    ):
        mock_get.return_value = mock_response
        result = get_failed_step_log_file_name(
            test_owner, test_repo, run_id, test_token
        )

    # Assert
    assert result is None


def test_get_failed_step_log_file_name_url_construction(
    test_owner, test_repo, test_token
):
    """Test correct URL construction for the API call."""
    # Arrange
    owner = test_owner
    repo = test_repo
    run_id = 67890
    token = test_token
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"jobs": []}

    # Act
    with patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.GITHUB_API_URL",
        "https://api.github.test",
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {token}"}
        mock_get.return_value = mock_response
        get_failed_step_log_file_name(owner, repo, run_id, token)

    # Assert
    mock_get.assert_called_once()
    assert (
        mock_get.call_args[1]["url"]
        == f"https://api.github.test/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
    )


def test_get_failed_step_log_file_name_timeout_parameter(
    test_owner, test_repo, test_token
):
    """Test that the timeout parameter is correctly passed to the request."""
    # Arrange
    run_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"jobs": []}

    # Act
    with patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.TIMEOUT", 60
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}
        mock_get.return_value = mock_response
        get_failed_step_log_file_name(test_owner, test_repo, run_id, test_token)

    # Assert
    mock_get.assert_called_once()
    assert mock_get.call_args[1]["timeout"] == 60


def test_get_failed_step_log_file_name_http_error(test_owner, test_repo, test_token):
    """Test handling of HTTP error when retrieving workflow run jobs."""
    # Arrange
    run_id = 12345
    http_error = requests.HTTPError("500 Internal Server Error")
    mock_error_response = MagicMock()
    mock_error_response.status_code = 500
    mock_error_response.reason = "Internal Server Error"
    mock_error_response.text = "Server error"
    http_error.response = mock_error_response

    # Act & Assert - function doesn't have handle_exceptions decorator, so it should raise
    with patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}
        mock_get.return_value.raise_for_status.side_effect = http_error

        with pytest.raises(requests.HTTPError):
            get_failed_step_log_file_name(test_owner, test_repo, run_id, test_token)

        mock_get.assert_called_once()


def test_get_failed_step_log_file_name_missing_step_fields(
    test_owner, test_repo, test_token
):
    """Test handling when step fields are missing."""
    # Arrange
    run_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "jobs": [
            {
                "name": "test",
                "steps": [
                    {
                        # Missing number and name fields
                        "conclusion": "failure"
                    }
                ],
            }
        ]
    }

    # Act
    with patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.create_headers"
    ):
        mock_get.return_value = mock_response
        result = get_failed_step_log_file_name(
            test_owner, test_repo, run_id, test_token
        )

    # Assert - should handle missing fields gracefully
    assert result == "test/None_None.txt"


def test_get_failed_step_log_file_name_missing_steps_key(
    test_owner, test_repo, test_token
):
    """Test handling when 'steps' key is missing from job."""
    # Arrange
    run_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "jobs": [
            {
                "name": "test"
                # Missing steps key
            }
        ]
    }

    # Act
    with patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.create_headers"
    ):
        mock_get.return_value = mock_response
        result = get_failed_step_log_file_name(
            test_owner, test_repo, run_id, test_token
        )

    # Assert
    assert result is None


def test_get_failed_step_log_file_name_empty_steps_list(
    test_owner, test_repo, test_token
):
    """Test handling when steps list is empty."""
    # Arrange
    run_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"jobs": [{"name": "test", "steps": []}]}

    # Act
    with patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_failed_step_log_file_name.create_headers"
    ):
        mock_get.return_value = mock_response
        result = get_failed_step_log_file_name(
            test_owner, test_repo, run_id, test_token
        )

    # Assert
    assert result is None
