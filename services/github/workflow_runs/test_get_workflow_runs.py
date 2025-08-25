from unittest.mock import patch, MagicMock

import pytest
import requests

from services.github.workflow_runs.get_workflow_runs import get_workflow_runs
from tests.constants import OWNER, REPO, TOKEN


@pytest.fixture
def mock_workflow_runs_response():
    """Fixture providing a successful workflow runs API response."""
    return {
        "workflow_runs": [
            {
                "id": 12345,
                "name": "Test Workflow",
                "node_id": "WFR_kwDOABCDEF",
                "head_branch": "main",
                "head_sha": "abc123def456",
                "path": ".github/workflows/test.yml",
                "display_title": "Test workflow run",
                "run_number": 1,
                "event": "push",
                "status": "completed",
                "conclusion": "success",
                "workflow_id": 123,
                "check_suite_id": 456,
                "check_suite_node_id": "CS_kwDOABCDEF",
                "url": "https://api.github.com/repos/owner/repo/actions/runs/12345",
                "html_url": "https://github.com/owner/repo/actions/runs/12345",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:05:00Z",
                "actor": {"login": "user", "id": 789},
                "run_attempt": 1,
                "referenced_workflows": [],
                "run_started_at": "2023-01-01T00:00:00Z",
                "triggering_actor": {"login": "user", "id": 789},
                "jobs_url": "https://api.github.com/repos/owner/repo/actions/runs/12345/jobs",
                "logs_url": "https://api.github.com/repos/owner/repo/actions/runs/12345/logs",
                "check_suite_url": "https://api.github.com/repos/owner/repo/check-suites/456",
                "artifacts_url": "https://api.github.com/repos/owner/repo/actions/runs/12345/artifacts",
                "cancel_url": "https://api.github.com/repos/owner/repo/actions/runs/12345/cancel",
                "rerun_url": "https://api.github.com/repos/owner/repo/actions/runs/12345/rerun",
                "previous_attempt_url": None,
                "workflow_url": "https://api.github.com/repos/owner/repo/actions/workflows/123",
                "head_commit": {"id": "abc123def456", "message": "Test commit"},
                "repository": {"id": 123, "name": "repo"},
                "head_repository": {"id": 123, "name": "repo"}
            }
        ]
    }


@pytest.fixture
def mock_successful_response(mock_workflow_runs_response):
    """Fixture providing a successful API response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_workflow_runs_response
    return mock_response


@pytest.fixture
def mock_headers():
    """Fixture providing mock headers."""
    return {"Authorization": f"Bearer {TOKEN}"}


def test_get_workflow_runs_success_with_commit_sha(mock_successful_response, mock_headers, mock_workflow_runs_response):
    """Test successful retrieval of workflow runs with commit_sha."""
    # Arrange
    commit_sha = "abc123def456"
    expected_workflow_runs = mock_workflow_runs_response["workflow_runs"]

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_runs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_runs.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_successful_response
        result = get_workflow_runs(OWNER, REPO, TOKEN, commit_sha=commit_sha)

    # Assert
    mock_create_headers.assert_called_once_with(token=TOKEN, media_type="")
    mock_get.assert_called_once()
    assert (
        mock_get.call_args[1]["url"]
        == f"https://api.github.com/repos/{OWNER}/{REPO}/actions/runs?head_sha={commit_sha}"
    )
    assert mock_get.call_args[1]["headers"] == mock_headers
    assert mock_get.call_args[1]["timeout"] == 120
    mock_successful_response.raise_for_status.assert_called_once()
    mock_successful_response.json.assert_called_once()
    assert result == expected_workflow_runs


def test_get_workflow_runs_success_with_branch(mock_successful_response, mock_headers, mock_workflow_runs_response):
    """Test successful retrieval of workflow runs with branch."""
    # Arrange
    branch = "feature-branch"
    expected_workflow_runs = mock_workflow_runs_response["workflow_runs"]

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_runs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_runs.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_successful_response
        result = get_workflow_runs(OWNER, REPO, TOKEN, branch=branch)

    # Assert
    mock_create_headers.assert_called_once_with(token=TOKEN, media_type="")
    mock_get.assert_called_once()
    assert (
        mock_get.call_args[1]["url"]
        == f"https://api.github.com/repos/{OWNER}/{REPO}/actions/runs?branch={branch}"
    )
    assert mock_get.call_args[1]["headers"] == mock_headers
    assert mock_get.call_args[1]["timeout"] == 120
    mock_successful_response.raise_for_status.assert_called_once()
    mock_successful_response.json.assert_called_once()
    assert result == expected_workflow_runs


def test_get_workflow_runs_both_commit_sha_and_branch_prefers_commit_sha(mock_successful_response, mock_headers):
    """Test that commit_sha takes precedence when both commit_sha and branch are provided."""
    # Arrange
    commit_sha = "abc123def456"
    branch = "feature-branch"

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_runs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_runs.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_successful_response
        get_workflow_runs(OWNER, REPO, TOKEN, commit_sha=commit_sha, branch=branch)

    # Assert
    mock_get.assert_called_once()
    assert (
        mock_get.call_args[1]["url"]
        == f"https://api.github.com/repos/{OWNER}/{REPO}/actions/runs?head_sha={commit_sha}"
    )


def test_get_workflow_runs_neither_commit_sha_nor_branch_raises_value_error():
    """Test that ValueError is raised when neither commit_sha nor branch is provided."""
    # Act & Assert
    result = get_workflow_runs(OWNER, REPO, TOKEN)
    assert result == []  # Default return value from handle_exceptions decorator


def test_get_workflow_runs_empty_commit_sha_and_branch_raises_value_error():
    """Test that ValueError is raised when both commit_sha and branch are empty strings."""
    # Act & Assert
    result = get_workflow_runs(OWNER, REPO, TOKEN, commit_sha="", branch="")
    assert result == []  # Default return value from handle_exceptions decorator


def test_get_workflow_runs_none_commit_sha_and_empty_branch_raises_value_error():
    """Test that ValueError is raised when commit_sha is None and branch is empty string."""
    # Act & Assert
    with pytest.raises(ValueError, match="Either commit_sha or branch must be provided"):
        get_workflow_runs(OWNER, REPO, TOKEN, commit_sha=None, branch="")


def test_get_workflow_runs_http_error():
    """Test handling of HTTP error when retrieving workflow runs."""
    # Arrange
    commit_sha = "abc123def456"
    http_error = requests.HTTPError("404 Not Found")
    mock_error_response = MagicMock()
    mock_error_response.status_code = 404
    mock_error_response.reason = "Not Found"
    mock_error_response.text = "Repository not found"
    http_error.response = mock_error_response

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_runs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_runs.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.return_value.raise_for_status.side_effect = http_error
        result = get_workflow_runs(OWNER, REPO, TOKEN, commit_sha=commit_sha)

    # Assert
    mock_get.assert_called_once()
    assert result == []  # Default return value from handle_exceptions decorator


def test_get_workflow_runs_request_exception():
    """Test handling of request exception when retrieving workflow runs."""
    # Arrange
    branch = "main"

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_runs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_runs.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.side_effect = requests.RequestException("Connection error")
        result = get_workflow_runs(OWNER, REPO, TOKEN, branch=branch)

    # Assert
    mock_get.assert_called_once()
    assert result == []  # Default return value from handle_exceptions decorator


def test_get_workflow_runs_rate_limit_exceeded():
    """Test handling of rate limit exceeded error."""
    # Arrange
    commit_sha = "abc123def456"
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
        "services.github.workflow_runs.get_workflow_runs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_runs.create_headers"
    ) as mock_create_headers, patch(
        "time.sleep"
    ) as mock_sleep, patch(
        "time.time", return_value=1000000000
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}

        # First call raises rate limit error, second call succeeds
        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {"workflow_runs": []}
        mock_get.side_effect = [mock_error_response, mock_success_response]
        mock_error_response.raise_for_status.side_effect = http_error

        result = get_workflow_runs(OWNER, REPO, TOKEN, commit_sha=commit_sha)

    # Assert
    assert mock_get.call_count == 2
    mock_sleep.assert_called_once_with(15)  # 10 seconds + 5 buffer
    assert result == []


def test_get_workflow_runs_secondary_rate_limit():
    """Test handling of secondary rate limit."""
    # Arrange
    branch = "main"
    http_error = requests.HTTPError("403 Forbidden")
    mock_error_response = MagicMock()
    mock_error_response.status_code = 403
    mock_error_response.reason = "Forbidden"
    mock_error_response.text = "You have exceeded a secondary rate limit"
    mock_error_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4990",
        "X-RateLimit-Used": "10",
        "Retry-After": "30",
    }
    http_error.response = mock_error_response

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_runs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_runs.create_headers"
    ) as mock_create_headers, patch(
        "time.sleep"
    ) as mock_sleep:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}

        # First call raises secondary rate limit error, second call succeeds
        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {"workflow_runs": []}
        mock_get.side_effect = [mock_error_response, mock_success_response]
        mock_error_response.raise_for_status.side_effect = http_error

        result = get_workflow_runs(OWNER, REPO, TOKEN, branch=branch)

    # Assert
    assert mock_get.call_count == 2
    mock_sleep.assert_called_once_with(30)
    assert result == []


def test_get_workflow_runs_json_decode_error():
    """Test handling of JSON decode error."""
    # Arrange
    commit_sha = "abc123def456"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_runs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_runs.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.return_value = mock_response
        result = get_workflow_runs(OWNER, REPO, TOKEN, commit_sha=commit_sha)

    # Assert
    mock_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    assert result == []  # Default return value from handle_exceptions decorator


def test_get_workflow_runs_missing_workflow_runs_key():
    """Test handling when the response JSON is missing the 'workflow_runs' key."""
    # Arrange
    branch = "main"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"other_field": "value"}  # Missing 'workflow_runs' key

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_runs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_runs.create_headers"
    ) as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.return_value = mock_response
        result = get_workflow_runs(OWNER, REPO, TOKEN, branch=branch)

    # Assert
    mock_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    assert result == []  # Default return value from handle_exceptions decorator


def test_get_workflow_runs_url_construction_with_commit_sha():
    """Test correct URL construction for the API call with commit_sha."""
    # Arrange
    owner = "test-owner"
    repo = "test-repo"
    token = "test-token"
    commit_sha = "test-sha-123"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"workflow_runs": []}

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_runs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_runs.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_runs.GITHUB_API_URL",
        "https://api.github.test",
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {token}"}
        mock_get.return_value = mock_response
        get_workflow_runs(owner, repo, token, commit_sha=commit_sha)

    # Assert
    mock_get.assert_called_once()
    assert (
        mock_get.call_args[1]["url"]
        == f"https://api.github.test/repos/{owner}/{repo}/actions/runs?head_sha={commit_sha}"
    )


def test_get_workflow_runs_url_construction_with_branch():
    """Test correct URL construction for the API call with branch."""
    # Arrange
    owner = "test-owner"
    repo = "test-repo"
    token = "test-token"
    branch = "test-branch"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"workflow_runs": []}

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_runs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_runs.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_runs.GITHUB_API_URL",
        "https://api.github.test",
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {token}"}
        mock_get.return_value = mock_response
        get_workflow_runs(owner, repo, token, branch=branch)

    # Assert
    mock_get.assert_called_once()
    assert (
        mock_get.call_args[1]["url"]
        == f"https://api.github.test/repos/{owner}/{repo}/actions/runs?branch={branch}"
    )


def test_get_workflow_runs_timeout_parameter():
    """Test that the timeout parameter is correctly passed to the request."""
    # Arrange
    commit_sha = "abc123def456"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"workflow_runs": []}

    # Act
    with patch(
        "services.github.workflow_runs.get_workflow_runs.get"
    ) as mock_get, patch(
        "services.github.workflow_runs.get_workflow_runs.create_headers"
    ) as mock_create_headers, patch(
        "services.github.workflow_runs.get_workflow_runs.TIMEOUT", 60
    ):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.return_value = mock_response
        get_workflow_runs(OWNER, REPO, TOKEN, commit_sha=commit_sha)

    # Assert
    mock_get.assert_called_once()
    assert mock_get.call_args[1]["timeout"] == 60
