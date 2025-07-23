from unittest.mock import patch, MagicMock

import pytest
import requests

from services.github.workflow_runs.get_workflow_run_path import get_workflow_run_path
from tests.constants import OWNER, REPO, TOKEN


@pytest.fixture
def mock_successful_response():
    """Fixture providing a successful API response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"path": ".github/workflows/test.yml"}
    return mock_response


@pytest.fixture
def mock_404_response():
    """Fixture providing a 404 Not Found response."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    return mock_response


@pytest.fixture
def mock_headers():
    """Fixture providing mock headers."""
    return {"Authorization": f"Bearer {TOKEN}"}


def test_get_workflow_run_path_success(mock_successful_response, mock_headers):
    """Test successful retrieval of workflow run path."""
    # Arrange
    run_id = 12345
    expected_path = ".github/workflows/test.yml"

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_path.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_path.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_successful_response
        result = get_workflow_run_path(OWNER, REPO, run_id, TOKEN)

    # Assert
    mock_create_headers.assert_called_once_with(token=TOKEN)
    mock_get.assert_called_once()
    assert (
        mock_get.call_args[1]["url"]
        == f"https://api.github.com/repos/{OWNER}/{REPO}/actions/runs/{run_id}"
    )
    assert mock_get.call_args[1]["headers"] == mock_headers
    assert mock_get.call_args[1]["timeout"] == 120
    mock_successful_response.raise_for_status.assert_called_once()
    mock_successful_response.json.assert_called_once()
    assert result == expected_path


def test_get_workflow_run_path_404_not_found(mock_404_response, mock_headers):
    """Test handling of 404 Not Found response."""
    # Arrange
    run_id = 12345

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_path.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_path.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_404_response
        result = get_workflow_run_path(OWNER, REPO, run_id, TOKEN)

    # Assert
    mock_get.assert_called_once()
    mock_404_response.raise_for_status.assert_not_called()
    mock_404_response.json.assert_not_called()
    assert result == 404


def test_get_workflow_run_path_404_without_not_found_text(mock_headers):
    """Test handling of 404 response without 'Not Found' in text."""
    # Arrange
    run_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Some other error message"
    mock_response.json.return_value = {"path": ".github/workflows/test.yml"}

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_path.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_path.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_response
        result = get_workflow_run_path(OWNER, REPO, run_id, TOKEN)

    # Assert
    mock_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    assert result == ".github/workflows/test.yml"


def test_get_workflow_run_path_http_error():
    """Test handling of HTTP error when retrieving workflow run path."""
    # Arrange
    run_id = 12345
    http_error = requests.HTTPError("500 Internal Server Error")
    mock_error_response = MagicMock()
    mock_error_response.status_code = 500
    mock_error_response.reason = "Internal Server Error"
    mock_error_response.text = "Server error"
    http_error.response = mock_error_response

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_path.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_path.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.return_value.raise_for_status.side_effect = http_error
        result = get_workflow_run_path(OWNER, REPO, run_id, TOKEN)

    # Assert
    mock_get.assert_called_once()
    assert result == ""  # Default return value from handle_exceptions decorator


def test_get_workflow_run_path_rate_limit_exceeded():
    """Test handling of rate limit exceeded error."""
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
        "X-RateLimit-Reset": "1000000010",  # 10 seconds from mock time
    }
    http_error.response = mock_error_response

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_path.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_path.create_headers"
    ) as mock_create_headers, patch(
        "time.sleep"
    ) as mock_sleep, patch(
        "time.time", return_value=1000000000
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}

        # First call raises rate limit error, second call succeeds
        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {"path": ".github/workflows/test.yml"}
        mock_get.side_effect = [mock_error_response, mock_success_response]
        mock_error_response.raise_for_status.side_effect = http_error

        result = get_workflow_run_path(OWNER, REPO, run_id, TOKEN)

    # Assert
    assert mock_get.call_count == 2
    mock_sleep.assert_called_once_with(15)  # 10 seconds + 5 buffer
    assert result == ".github/workflows/test.yml"


def test_get_workflow_run_path_json_decode_error():
    """Test handling of JSON decode error."""
    # Arrange
    run_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_path.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_path.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.return_value = mock_response
        result = get_workflow_run_path(OWNER, REPO, run_id, TOKEN)

    # Assert
    mock_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    assert result == ""  # Default return value from handle_exceptions decorator


def test_get_workflow_run_path_url_construction():
    """Test correct URL construction for the API call."""
    # Arrange
    owner = "test-owner"
    repo = "test-repo"
    run_id = 67890
    token = "test-token"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"path": ".github/workflows/custom.yml"}

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_path.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_path.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_run_path.GITHUB_API_URL",
        "https://api.github.test",
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {token}"}
        mock_get.return_value = mock_response
        get_workflow_run_path(owner, repo, run_id, token)

    # Assert
    mock_get.assert_called_once()
    assert (
        mock_get.call_args[1]["url"]
        == f"https://api.github.test/repos/{owner}/{repo}/actions/runs/{run_id}"
    )


def test_get_workflow_run_path_timeout_parameter():
    """Test that the timeout parameter is correctly passed to the request."""
    # Arrange
    run_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"path": ".github/workflows/test.yml"}

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_path.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_path.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_run_path.TIMEOUT", 60
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.return_value = mock_response
        get_workflow_run_path(OWNER, REPO, run_id, TOKEN)

    # Assert
    mock_get.assert_called_once()
    assert mock_get.call_args[1]["timeout"] == 60


def test_get_workflow_run_path_missing_path_key():
    """Test handling when the response JSON is missing the 'path' key."""
    # Arrange
    run_id = 12345
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"other_field": "value"}  # Missing 'path' key

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_run_path.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_run_path.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.return_value = mock_response
        result = get_workflow_run_path(OWNER, REPO, run_id, TOKEN)

    # Assert
    mock_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    assert result == ""  # Default return value from handle_exceptions decorator
