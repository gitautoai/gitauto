import io
import zipfile
from unittest.mock import patch, MagicMock

import pytest
import requests

from services.github.workflow_runs.get_workflow_run_logs import get_workflow_run_logs


@pytest.fixture
def mock_zip_content():
    """Fixture providing mock zip file content with log files."""
    # Create a mock zip file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add various log files
        zf.writestr("0_build.txt", "2024-10-18T23:27:40.6602932Z Build started\n2024-10-18T23:27:41.1234567Z Build completed")
        zf.writestr("build/system.txt", "2024-10-18T23:27:40.6602932Z System info\n2024-10-18T23:27:41.1234567Z System ready")
        zf.writestr("build/1_Set up job.txt", "2024-10-18T23:27:40.6602932Z Setting up job\n2024-10-18T23:27:41.1234567Z Job setup complete")
        zf.writestr("build/2_Run actions_checkout@v4.txt", "2024-10-18T23:27:40.6602932Z Checking out code\n2024-10-18T23:27:41.1234567Z Checkout complete")
        zf.writestr("build/6_Run pytest.txt", "2024-10-18T23:27:40.6602932Z Running pytest\n2024-10-18T23:27:41.1234567Z Test failed with error\n2024-10-18T23:27:42.1234567Z Exit code: 1")
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


@pytest.fixture
def mock_successful_response(mock_zip_content):
    """Fixture providing a successful API response with zip content."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = mock_zip_content
    return mock_response


@pytest.fixture
def mock_404_response():
    """Fixture providing a 404 Not Found response."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    return mock_response


@pytest.fixture
def mock_404_response_without_not_found():
    """Fixture providing a 404 response without 'Not Found' in text."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Some other error message"
    return mock_response


@pytest.fixture
def mock_headers(test_token):
    """Fixture providing mock headers."""
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {test_token}",
        "User-Agent": "GitAuto",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def test_get_workflow_run_logs_success(
    mock_successful_response, mock_headers, test_owner, test_repo, test_token
):
    """Test successful retrieval of workflow run logs."""
    # Arrange
    run_id = 12345
    failed_step_fname = "build/6_Run pytest.txt"
    expected_content = "```GitHub Check Run Log: build/6_Run pytest.txt\nRunning pytest\nTest failed with error\nExit code: 1\n```"

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_logs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_logs.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_run_logs.get_failed_step_log_file_name"
    ) as mock_get_failed_step:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_successful_response
        mock_get_failed_step.return_value = failed_step_fname
        
        result = get_workflow_run_logs(test_owner, test_repo, run_id, test_token)

    # Assert
    mock_create_headers.assert_called_once_with(media_type="", token=test_token)
    mock_get.assert_called_once()
    assert (
        mock_get.call_args[1]["url"]
        == f"https://api.github.com/repos/{test_owner}/{test_repo}/actions/runs/{run_id}/logs"
    )
    assert mock_get.call_args[1]["headers"] == mock_headers
    assert mock_get.call_args[1]["timeout"] == 120
    mock_successful_response.raise_for_status.assert_called_once()
    mock_get_failed_step.assert_called_once_with(
        owner=test_owner, repo=test_repo, run_id=run_id, token=test_token
    )
    assert result == expected_content


def test_get_workflow_run_logs_404_not_found(
    mock_404_response, mock_headers, test_owner, test_repo, test_token
):
    """Test handling of 404 Not Found response."""
    # Arrange
    run_id = 12345

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_logs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_logs.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_run_logs.get_failed_step_log_file_name"
    ) as mock_get_failed_step:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_404_response
        
        result = get_workflow_run_logs(test_owner, test_repo, run_id, test_token)

    # Assert
    mock_get.assert_called_once()
    mock_404_response.raise_for_status.assert_not_called()
    mock_get_failed_step.assert_not_called()
    assert result == 404


def test_get_workflow_run_logs_404_without_not_found_text(
    mock_404_response_without_not_found, mock_headers, test_owner, test_repo, test_token, mock_zip_content
):
    """Test handling of 404 response without 'Not Found' in text."""
    # Arrange
    run_id = 12345
    failed_step_fname = "build/6_Run pytest.txt"
    mock_404_response_without_not_found.content = mock_zip_content
    expected_content = "```GitHub Check Run Log: build/6_Run pytest.txt\nRunning pytest\nTest failed with error\nExit code: 1\n```"

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_logs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_logs.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_run_logs.get_failed_step_log_file_name"
    ) as mock_get_failed_step:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_404_response_without_not_found
        mock_get_failed_step.return_value = failed_step_fname
        
        result = get_workflow_run_logs(test_owner, test_repo, run_id, test_token)

    # Assert
    mock_get.assert_called_once()
    mock_404_response_without_not_found.raise_for_status.assert_called_once()
    mock_get_failed_step.assert_called_once_with(
        owner=test_owner, repo=test_repo, run_id=run_id, token=test_token
    )
    assert result == expected_content


def test_get_workflow_run_logs_failed_step_not_found(
    mock_successful_response, mock_headers, test_owner, test_repo, test_token
):
    """Test handling when failed step log file name is not found."""
    # Arrange
    run_id = 12345
    failed_step_fname = 404

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_logs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_logs.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_run_logs.get_failed_step_log_file_name"
    ) as mock_get_failed_step:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_successful_response
        mock_get_failed_step.return_value = failed_step_fname
        
        result = get_workflow_run_logs(test_owner, test_repo, run_id, test_token)

    # Assert
    mock_get.assert_called_once()
    mock_successful_response.raise_for_status.assert_called_once()
    mock_get_failed_step.assert_called_once_with(
        owner=test_owner, repo=test_repo, run_id=run_id, token=test_token
    )
    assert result == 404


def test_get_workflow_run_logs_failed_step_none(
    mock_successful_response, mock_headers, test_owner, test_repo, test_token
):
    """Test handling when get_failed_step_log_file_name returns None."""
    # Arrange
    run_id = 12345
    failed_step_fname = None

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_logs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_logs.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_run_logs.get_failed_step_log_file_name"
    ) as mock_get_failed_step:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_successful_response
        mock_get_failed_step.return_value = failed_step_fname
        
        result = get_workflow_run_logs(test_owner, test_repo, run_id, test_token)

    # Assert
    mock_get.assert_called_once()
    mock_successful_response.raise_for_status.assert_called_once()
    mock_get_failed_step.assert_called_once()
    assert result is None


def test_get_workflow_run_logs_failed_step_file_not_in_zip(
    mock_successful_response, mock_headers, test_owner, test_repo, test_token
):
    """Test handling when failed step log file is not found in zip."""
    # Arrange
    run_id = 12345
    failed_step_fname = "build/7_Nonexistent step.txt"  # This file doesn't exist in the zip

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_logs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_logs.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_run_logs.get_failed_step_log_file_name"
    ) as mock_get_failed_step:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_successful_response
        mock_get_failed_step.return_value = failed_step_fname
        
        result = get_workflow_run_logs(test_owner, test_repo, run_id, test_token)

    # Assert
    mock_get.assert_called_once()
    mock_successful_response.raise_for_status.assert_called_once()
    mock_get_failed_step.assert_called_once_with(
        owner=test_owner, repo=test_repo, run_id=run_id, token=test_token
    )
    assert result is None


def test_get_workflow_run_logs_empty_zip(
    mock_headers, test_owner, test_repo, test_token
):
    """Test handling when zip file is empty."""
    # Arrange
    run_id = 12345
    failed_step_fname = "build/6_Run pytest.txt"
    
    # Create empty zip content
    empty_zip_buffer = io.BytesIO()
    with zipfile.ZipFile(empty_zip_buffer, 'w', zipfile.ZIP_DEFLATED):
        pass  # Create empty zip
    empty_zip_buffer.seek(0)
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = empty_zip_buffer.getvalue()

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_logs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_logs.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_run_logs.get_failed_step_log_file_name"
    ) as mock_get_failed_step:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_response
        mock_get_failed_step.return_value = failed_step_fname
        
        result = get_workflow_run_logs(test_owner, test_repo, run_id, test_token)

    # Assert
    mock_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_get_failed_step.assert_called_once_with(
        owner=test_owner, repo=test_repo, run_id=run_id, token=test_token
    )
    assert result is None


def test_get_workflow_run_logs_short_log_lines(
    mock_headers, test_owner, test_repo, test_token
):
    """Test handling of log lines shorter than 29 characters."""
    # Arrange
    run_id = 12345
    failed_step_fname = "build/6_Run pytest.txt"
    
    # Create zip with short log lines
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("build/6_Run pytest.txt", "Short line\nAnother short\n2024-10-18T23:27:40.6602932Z Normal line")
    zip_buffer.seek(0)
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = zip_buffer.getvalue()
    
    expected_content = "```GitHub Check Run Log: build/6_Run pytest.txt\nShort line\nAnother short\nNormal line\n```"

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_logs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_logs.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_run_logs.get_failed_step_log_file_name"
    ) as mock_get_failed_step:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_response
        mock_get_failed_step.return_value = failed_step_fname
        
        result = get_workflow_run_logs(test_owner, test_repo, run_id, test_token)

    # Assert
    assert result == expected_content


def test_get_workflow_run_logs_exactly_29_char_lines(
    mock_headers, test_owner, test_repo, test_token
):
    """Test handling of log lines exactly 29 characters long."""
    # Arrange
    run_id = 12345
    failed_step_fname = "build/6_Run pytest.txt"
    
    # Create zip with exactly 29 character lines
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("build/6_Run pytest.txt", "2024-10-18T23:27:40.6602932Z \n2024-10-18T23:27:40.6602932Z Test line")
    zip_buffer.seek(0)
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = zip_buffer.getvalue()
    
    expected_content = "```GitHub Check Run Log: build/6_Run pytest.txt\n2024-10-18T23:27:40.6602932Z \nTest line\n```"

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_logs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_logs.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_run_logs.get_failed_step_log_file_name"
    ) as mock_get_failed_step:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_response
        mock_get_failed_step.return_value = failed_step_fname
        
        result = get_workflow_run_logs(test_owner, test_repo, run_id, test_token)

    # Assert
    assert result == expected_content


def test_get_workflow_run_logs_timestamp_removal_verification(
    mock_headers, test_owner, test_repo, test_token
):
    """Test that exactly 29 characters are removed from each line (not 28 as comment suggests)."""
    # Arrange
    run_id = 12345
    failed_step_fname = "build/6_Run pytest.txt"
    
    # Create zip with specific timestamp format
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # The timestamp format is exactly 29 characters: "2024-10-18T23:27:40.6602932Z "
        log_content = "2024-10-18T23:27:40.6602932Z This should remain\n2024-10-18T23:27:41.1234567Z This should also remain"
        zf.writestr("build/6_Run pytest.txt", log_content)
    zip_buffer.seek(0)
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = zip_buffer.getvalue()
    
    expected_content = "```GitHub Check Run Log: build/6_Run pytest.txt\nThis should remain\nThis should also remain\n```"

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_logs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_logs.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_run_logs.get_failed_step_log_file_name"
    ) as mock_get_failed_step:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_response
        mock_get_failed_step.return_value = failed_step_fname
        
        result = get_workflow_run_logs(test_owner, test_repo, run_id, test_token)

    # Assert
    assert result == expected_content


def test_get_workflow_run_logs_url_construction(
    mock_successful_response, test_owner, test_repo, test_token
):
    """Test correct URL construction for the API call."""
    # Arrange
    owner = test_owner
    repo = test_repo
    run_id = 67890
    token = test_token
    failed_step_fname = "build/6_Run pytest.txt"

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_logs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_logs.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_run_logs.get_failed_step_log_file_name"
    ) as mock_get_failed_step, patch(
        "services.github.workflow_runs.get_workflow_run_logs.GITHUB_API_URL",
        "https://api.github.test",
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {token}"}
        mock_get.return_value = mock_successful_response
        mock_get_failed_step.return_value = failed_step_fname
        
        get_workflow_run_logs(owner, repo, run_id, token)

    # Assert
    mock_get.assert_called_once()
    assert (
        mock_get.call_args[1]["url"]
        == f"https://api.github.test/repos/{owner}/{repo}/actions/runs/{run_id}/logs"
    )


def test_get_workflow_run_logs_timeout_parameter(
    mock_successful_response, test_owner, test_repo, test_token
):
    """Test that the timeout parameter is correctly passed to the request."""
    # Arrange
    run_id = 12345
    failed_step_fname = "build/6_Run pytest.txt"

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_logs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_logs.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_run_logs.get_failed_step_log_file_name"
    ) as mock_get_failed_step, patch(
        "services.github.workflow_runs.get_workflow_run_logs.TIMEOUT", 60
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {test_token}"}
        mock_get.return_value = mock_successful_response
        mock_get_failed_step.return_value = failed_step_fname
        
        get_workflow_run_logs(test_owner, test_repo, run_id, test_token)

    # Assert
    mock_get.assert_called_once()
    assert mock_get.call_args[1]["timeout"] == 60


def test_get_workflow_run_logs_http_error_after_404_check(
    mock_headers, test_owner, test_repo, test_token
):
    """Test handling of HTTP error after 404 check passes."""
    # Arrange
    run_id = 12345
    http_error = requests.HTTPError("500 Internal Server Error")
    mock_error_response = MagicMock()
    mock_error_response.status_code = 500
    mock_error_response.reason = "Internal Server Error"
    mock_error_response.text = "Server error"
    mock_error_response.raise_for_status.side_effect = http_error
    http_error.response = mock_error_response

    # Act - function has handle_exceptions decorator, so it should return default value
    with patch(
        "services.github.workflow_runs.get_workflow_run_logs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_logs.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_error_response
        
        result = get_workflow_run_logs(test_owner, test_repo, run_id, test_token)

    # Assert - should return default value from handle_exceptions decorator
    mock_get.assert_called_once()
    mock_error_response.raise_for_status.assert_called_once()
    assert result == ""  # default_return_value from handle_exceptions decorator


def test_get_workflow_run_logs_invalid_zip_content(
    mock_headers, test_owner, test_repo, test_token
):
    """Test handling of invalid zip content."""
    # Arrange
    run_id = 12345
    failed_step_fname = "build/6_Run pytest.txt"
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"invalid zip content"

    # Act - function has handle_exceptions decorator, so it should return default value
    with patch(
        "services.github.workflow_runs.get_workflow_run_logs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_logs.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_run_logs.get_failed_step_log_file_name"
    ) as mock_get_failed_step:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_response
        mock_get_failed_step.return_value = failed_step_fname
        
        result = get_workflow_run_logs(test_owner, test_repo, run_id, test_token)

    # Assert - should return default value from handle_exceptions decorator
    mock_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_get_failed_step.assert_called_once_with(
        owner=test_owner, repo=test_repo, run_id=run_id, token=test_token
    )
    assert result == ""  # default_return_value from handle_exceptions decorator


def test_get_workflow_run_logs_different_log_file_names(
    mock_headers, test_owner, test_repo, test_token
):
    """Test with different log file name patterns."""
    # Arrange
    run_id = 12345
    failed_step_fname = "test/3_Custom step name.txt"
    
    # Create zip with the specific log file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("0_build.txt", "2024-10-18T23:27:40.6602932Z Build log")
        zf.writestr("test/system.txt", "2024-10-18T23:27:40.6602932Z System log")
        zf.writestr("test/3_Custom step name.txt", "2024-10-18T23:27:40.6602932Z Custom step executed\n2024-10-18T23:27:41.1234567Z Step completed")
    zip_buffer.seek(0)
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = zip_buffer.getvalue()
    
    expected_content = "```GitHub Check Run Log: test/3_Custom step name.txt\nCustom step executed\nStep completed\n```"

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_logs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_logs.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_run_logs.get_failed_step_log_file_name"
    ) as mock_get_failed_step:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_response
        mock_get_failed_step.return_value = failed_step_fname
        
        result = get_workflow_run_logs(test_owner, test_repo, run_id, test_token)

    # Assert
    assert result == expected_content


def test_get_workflow_run_logs_unicode_content(
    mock_headers, test_owner, test_repo, test_token
):
    """Test handling of unicode content in log files."""
    # Arrange
    run_id = 12345
    failed_step_fname = "build/6_Run pytest.txt"
    
    # Create zip with unicode content
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        unicode_content = "2024-10-18T23:27:40.6602932Z Test with unicode: 测试 🚀 ñáéíóú"
        zf.writestr("build/6_Run pytest.txt", unicode_content.encode('utf-8'))
    zip_buffer.seek(0)
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = zip_buffer.getvalue()
    
    expected_content = "```GitHub Check Run Log: build/6_Run pytest.txt\nTest with unicode: 测试 🚀 ñáéíóú\n```"

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_logs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_logs.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_run_logs.get_failed_step_log_file_name"
    ) as mock_get_failed_step:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_response
        mock_get_failed_step.return_value = failed_step_fname
        
        result = get_workflow_run_logs(test_owner, test_repo, run_id, test_token)

    # Assert
    assert result == expected_content


def test_get_workflow_run_logs_empty_log_file(
    mock_headers, test_owner, test_repo, test_token
):
    """Test handling of empty log file."""
    # Arrange
    run_id = 12345
    failed_step_fname = "build/6_Run pytest.txt"
    
    # Create zip with empty log file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("build/6_Run pytest.txt", "")
    zip_buffer.seek(0)
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = zip_buffer.getvalue()
    
    expected_content = "```GitHub Check Run Log: build/6_Run pytest.txt\n\n```"

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_logs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_logs.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_run_logs.get_failed_step_log_file_name"
    ) as mock_get_failed_step:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_response
        mock_get_failed_step.return_value = failed_step_fname
        
        result = get_workflow_run_logs(test_owner, test_repo, run_id, test_token)

    # Assert
    assert result == expected_content


def test_get_workflow_run_logs_single_line_log(
    mock_headers, test_owner, test_repo, test_token
):
    """Test handling of single line log file."""
    # Arrange
    run_id = 12345
    failed_step_fname = "build/6_Run pytest.txt"
    
    # Create zip with single line log file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("build/6_Run pytest.txt", "2024-10-18T23:27:40.6602932Z Single line log")
    zip_buffer.seek(0)
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = zip_buffer.getvalue()
    
    expected_content = "```GitHub Check Run Log: build/6_Run pytest.txt\nSingle line log\n```"

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_logs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_logs.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_run_logs.get_failed_step_log_file_name"
    ) as mock_get_failed_step:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_response
        mock_get_failed_step.return_value = failed_step_fname
        
        result = get_workflow_run_logs(test_owner, test_repo, run_id, test_token)

    # Assert
    assert result == expected_content