from unittest.mock import patch, MagicMock

import pytest
import requests

from services.github.workflow_runs.cancel_workflow_run import cancel_workflow_run
from tests.constants import OWNER, REPO, TOKEN


def test_cancel_workflow_run_success():
    """Test successful cancellation of a workflow run."""
    # Arrange
    run_id = 12345
    mock_response = MagicMock()

    # Act
    with patch("services.github.workflow_runs.cancel_workflow_run.post") as mock_post, \
         patch("services.github.workflow_runs.cancel_workflow_run.create_headers") as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_post.return_value = mock_response
        result = cancel_workflow_run(OWNER, REPO, run_id, TOKEN)

    # Assert
    mock_create_headers.assert_called_once_with(token=TOKEN, media_type="")
    mock_post.assert_called_once()
    assert mock_post.call_args[1]["url"] == f"https://api.github.com/repos/{OWNER}/{REPO}/actions/runs/{run_id}/cancel"
    assert mock_post.call_args[1]["headers"] == {"Authorization": f"Bearer {TOKEN}"}
    assert mock_post.call_args[1]["timeout"] == 120
    assert result is None


def test_cancel_workflow_run_http_error():
    """Test handling of HTTP error when cancelling a workflow run."""
    # Arrange
    run_id = 12345
    http_error = requests.HTTPError("404 Not Found")
    mock_error_response = MagicMock()
    mock_error_response.status_code = 404
    mock_error_response.reason = "Not Found"
    mock_error_response.text = "Workflow run not found"
    mock_error_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Used": "1"
    }
    http_error.response = mock_error_response

    # Act
    with patch("services.github.workflow_runs.cancel_workflow_run.post") as mock_post, \
         patch("services.github.workflow_runs.cancel_workflow_run.create_headers") as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_post.side_effect = http_error
        result = cancel_workflow_run(OWNER, REPO, run_id, TOKEN)

    # Assert
    mock_post.assert_called_once()
    assert result is None


def test_cancel_workflow_run_request_exception():
    """Test handling of request exception when cancelling a workflow run."""
    # Arrange
    run_id = 12345

    # Act
    with patch("services.github.workflow_runs.cancel_workflow_run.post") as mock_post, \
         patch("services.github.workflow_runs.cancel_workflow_run.create_headers") as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_post.side_effect = requests.RequestException("Connection error")
        result = cancel_workflow_run(OWNER, REPO, run_id, TOKEN)

    # Assert
    mock_post.assert_called_once()
    assert result is None


def test_cancel_workflow_run_rate_limit_exceeded():
    """Test handling of rate limit exceeded error when cancelling a workflow run."""
    # Arrange
    run_id = 12345
    http_error = requests.HTTPError("403 Forbidden")
    mock_error_response = MagicMock()
    mock_error_response.status_code = 403
    mock_error_response.reason = "Forbidden"
    mock_error_response.text = "API rate limit exceeded"
    mock_error_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Used": "5000",
        "X-RateLimit-Reset": "1000000010"  # 10 seconds from mock time
    }
    http_error.response = mock_error_response

    # Act
    with patch("services.github.workflow_runs.cancel_workflow_run.post") as mock_post, \
         patch("services.github.workflow_runs.cancel_workflow_run.create_headers") as mock_create_headers, \
         patch("time.sleep") as mock_sleep, \
         patch("time.time", return_value=1000000000):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        
        # First call raises rate limit error, second call succeeds
        mock_success_response = MagicMock()
        mock_post.side_effect = [http_error, mock_success_response]
        
        result = cancel_workflow_run(OWNER, REPO, run_id, TOKEN)

    # Assert
    assert mock_post.call_count == 2
    mock_sleep.assert_called_once_with(15)  # 10 seconds + 5 buffer
    assert result is None


def test_cancel_workflow_run_secondary_rate_limit():
    """Test handling of secondary rate limit when cancelling a workflow run."""
    # Arrange
    run_id = 12345
    http_error = requests.HTTPError("403 Forbidden")
    mock_error_response = MagicMock()
    mock_error_response.status_code = 403
    mock_error_response.reason = "Forbidden"
    mock_error_response.text = "You have exceeded a secondary rate limit"
    mock_error_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4990",
        "X-RateLimit-Used": "10",
        "Retry-After": "30"
    }
    http_error.response = mock_error_response

    # Act
    with patch("services.github.workflow_runs.cancel_workflow_run.post") as mock_post, \
         patch("services.github.workflow_runs.cancel_workflow_run.create_headers") as mock_create_headers, \
         patch("time.sleep") as mock_sleep:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        
        # First call raises secondary rate limit error, second call succeeds
        mock_success_response = MagicMock()
        mock_post.side_effect = [http_error, mock_success_response]
        
        result = cancel_workflow_run(OWNER, REPO, run_id, TOKEN)

    # Assert
    assert mock_post.call_count == 2
    mock_sleep.assert_called_once_with(30)
    assert result is None


def test_cancel_workflow_run_url_construction():
    """Test correct URL construction for the API call."""
    # Arrange
    owner = "test-owner"
    repo = "test-repo"
    run_id = 67890
    token = "test-token"
    mock_response = MagicMock()

    # Act
    with patch("services.github.workflow_runs.cancel_workflow_run.post") as mock_post, \
         patch("services.github.workflow_runs.cancel_workflow_run.create_headers") as mock_create_headers, \
         patch("services.github.workflow_runs.cancel_workflow_run.GITHUB_API_URL", "https://api.github.test"):
        mock_create_headers.return_value = {"Authorization": f"Bearer {token}"}
        mock_post.return_value = mock_response
        cancel_workflow_run(owner, repo, run_id, token)

    # Assert
    mock_post.assert_called_once()
    assert mock_post.call_args[1]["url"] == f"https://api.github.test/repos/{owner}/{repo}/actions/runs/{run_id}/cancel"


def test_cancel_workflow_run_timeout_parameter():
    """Test that the timeout parameter is correctly passed to the request."""
    # Arrange
    run_id = 12345
    mock_response = MagicMock()

    # Act
    with patch("services.github.workflow_runs.cancel_workflow_run.post") as mock_post, \
         patch("services.github.workflow_runs.cancel_workflow_run.create_headers") as mock_create_headers, \
         patch("services.github.workflow_runs.cancel_workflow_run.TIMEOUT", 60):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_post.return_value = mock_response
        cancel_workflow_run(OWNER, REPO, run_id, TOKEN)

    # Assert
    mock_post.assert_called_once()
    assert mock_post.call_args[1]["timeout"] == 60