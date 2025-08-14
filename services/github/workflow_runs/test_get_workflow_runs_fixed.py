from unittest.mock import patch, MagicMock
import time

import pytest
import requests

from services.github.workflow_runs.get_workflow_runs import get_workflow_runs
from tests.constants import OWNER, REPO, TOKEN


@pytest.fixture
def mock_workflow_runs_response():
    """Fixture providing a successful workflow runs API response."""
    return {
        "total_count": 2,
        "workflow_runs": [
            {
                "id": 12345,
                "name": "CI",
                "node_id": "WFR_kwDOABC123",
                "head_branch": "main",
                "head_sha": "abc123def456",
                "path": ".github/workflows/ci.yml",
                "display_title": "Update README",
                "run_number": 42,
                "event": "push",
                "status": "completed",
                "conclusion": "success",
                "workflow_id": 789,
                "check_suite_id": 456,
                "check_suite_node_id": "CS_kwDOABC456",
                "url": "https://api.github.com/repos/owner/repo/actions/runs/12345",
                "html_url": "https://github.com/owner/repo/actions/runs/12345",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:05:00Z",
                "actor": {"login": "user", "id": 123},
                "run_attempt": 1,
                "referenced_workflows": [],
                "run_started_at": "2023-01-01T00:00:30Z",
                "triggering_actor": {"login": "user", "id": 123},
                "jobs_url": "https://api.github.com/repos/owner/repo/actions/runs/12345/jobs",
                "logs_url": "https://api.github.com/repos/owner/repo/actions/runs/12345/logs",
                "check_suite_url": "https://api.github.com/repos/owner/repo/check-suites/456",
                "artifacts_url": "https://api.github.com/repos/owner/repo/actions/runs/12345/artifacts",
                "cancel_url": "https://api.github.com/repos/owner/repo/actions/runs/12345/cancel",
                "rerun_url": "https://api.github.com/repos/owner/repo/actions/runs/12345/rerun",
                "previous_attempt_url": None,
                "workflow_url": "https://api.github.com/repos/owner/repo/actions/workflows/789",
                "head_commit": {"id": "abc123def456", "message": "Update README"},
                "repository": {"id": 987, "name": "repo"},
                "head_repository": {"id": 987, "name": "repo"}
            },
            {
                "id": 67890,
                "name": "Deploy",
                "node_id": "WFR_kwDOABC789",
                "head_branch": "main",
                "head_sha": "def456ghi789",
                "path": ".github/workflows/deploy.yml",
                "display_title": "Deploy to production",
                "run_number": 43,
                "event": "workflow_dispatch",
                "status": "in_progress",
                "conclusion": None,
                "workflow_id": 101112,
                "check_suite_id": 789,
                "check_suite_node_id": "CS_kwDOABC789",
                "url": "https://api.github.com/repos/owner/repo/actions/runs/67890",
                "html_url": "https://github.com/owner/repo/actions/runs/67890",
                "created_at": "2023-01-01T01:00:00Z",
                "updated_at": "2023-01-01T01:02:00Z",
                "actor": {"login": "admin", "id": 456},
                "run_attempt": 1,
                "referenced_workflows": [],
                "run_started_at": "2023-01-01T01:00:15Z",
                "triggering_actor": {"login": "admin", "id": 456},
                "jobs_url": "https://api.github.com/repos/owner/repo/actions/runs/67890/jobs",
                "logs_url": "https://api.github.com/repos/owner/repo/actions/runs/67890/logs",
                "check_suite_url": "https://api.github.com/repos/owner/repo/check-suites/789",
                "artifacts_url": "https://api.github.com/repos/owner/repo/actions/runs/67890/artifacts",
                "cancel_url": "https://api.github.com/repos/owner/repo/actions/runs/67890/cancel",
                "rerun_url": "https://api.github.com/repos/owner/repo/actions/runs/67890/rerun",
                "previous_attempt_url": None,
                "workflow_url": "https://api.github.com/repos/owner/repo/actions/workflows/101112",
                "head_commit": {"id": "def456ghi789", "message": "Deploy to production"},
                "repository": {"id": 987, "name": "repo"},
                "head_repository": {"id": 987, "name": "repo"}
            }
        ]
    }


@pytest.fixture
def mock_successful_response(mock_workflow_runs_response):
    """Fixture providing a successful HTTP response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_workflow_runs_response
    return mock_response


@pytest.fixture
def mock_empty_response():
    """Fixture providing an empty workflow runs response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"total_count": 0, "workflow_runs": []}
    return mock_response


@pytest.fixture
def mock_headers():
    """Fixture providing mock headers."""
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "GitAuto",
        "X-GitHub-Api-Version": "2022-11-28"
    }


def test_get_workflow_runs_with_commit_sha_success(mock_successful_response, mock_headers, mock_workflow_runs_response):
    """Test successful retrieval of workflow runs with commit SHA."""
    # Arrange
    commit_sha = "abc123def456"
    expected_workflow_runs = mock_workflow_runs_response["workflow_runs"]

    # Act
    with patch("services.github.workflow_runs.get_workflow_runs.get") as mock_get, \
         patch("services.github.workflow_runs.get_workflow_runs.create_headers") as mock_create_headers:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_successful_response
        result = get_workflow_runs(OWNER, REPO, TOKEN, commit_sha=commit_sha)

    # Assert
    mock_create_headers.assert_called_once_with(token=TOKEN, media_type="")
    mock_get.assert_called_once()
    assert mock_get.call_args[1]["url"] == f"https://api.github.com/repos/{OWNER}/{REPO}/actions/runs?head_sha={commit_sha}"
    assert mock_get.call_args[1]["headers"] == mock_headers
    assert mock_get.call_args[1]["timeout"] == 120
    mock_successful_response.raise_for_status.assert_called_once()
    mock_successful_response.json.assert_called_once()
    assert result == expected_workflow_runs
    assert len(result) == 2
    assert result[0]["id"] == 12345
    assert result[1]["id"] == 67890


def test_get_workflow_runs_with_branch_success(mock_successful_response, mock_headers, mock_workflow_runs_response):
    """Test successful retrieval of workflow runs with branch."""
    # Arrange
    branch = "feature/test-branch"
    expected_workflow_runs = mock_workflow_runs_response["workflow_runs"]

    # Act
    with patch("services.github.workflow_runs.get_workflow_runs.get") as mock_get, \
         patch("services.github.workflow_runs.get_workflow_runs.create_headers") as mock_create_headers:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_successful_response
        result = get_workflow_runs(OWNER, REPO, TOKEN, branch=branch)

    # Assert
    mock_create_headers.assert_called_once_with(token=TOKEN, media_type="")
    mock_get.assert_called_once()
    assert mock_get.call_args[1]["url"] == f"https://api.github.com/repos/{OWNER}/{REPO}/actions/runs?branch={branch}"
    assert mock_get.call_args[1]["headers"] == mock_headers
    assert mock_get.call_args[1]["timeout"] == 120
    mock_successful_response.raise_for_status.assert_called_once()
    mock_successful_response.json.assert_called_once()
    assert result == expected_workflow_runs


def test_get_workflow_runs_with_both_commit_sha_and_branch(mock_successful_response, mock_headers):
    """Test that commit_sha takes precedence when both commit_sha and branch are provided."""
    # Arrange
    commit_sha = "abc123def456"
    branch = "feature/test-branch"

    # Act
    with patch("services.github.workflow_runs.get_workflow_runs.get") as mock_get, \
         patch("services.github.workflow_runs.get_workflow_runs.create_headers") as mock_create_headers:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_successful_response
        get_workflow_runs(OWNER, REPO, TOKEN, commit_sha=commit_sha, branch=branch)

    # Assert
    mock_get.assert_called_once()
    # Should use commit_sha, not branch
    assert mock_get.call_args[1]["url"] == f"https://api.github.com/repos/{OWNER}/{REPO}/actions/runs?head_sha={commit_sha}"


def test_get_workflow_runs_empty_response(mock_empty_response, mock_headers):
    """Test handling of empty workflow runs response."""
    # Arrange
    commit_sha = "abc123def456"

    # Act
    with patch("services.github.workflow_runs.get_workflow_runs.get") as mock_get, \
         patch("services.github.workflow_runs.get_workflow_runs.create_headers") as mock_create_headers:
        mock_create_headers.return_value = mock_headers
        mock_get.return_value = mock_empty_response
        result = get_workflow_runs(OWNER, REPO, TOKEN, commit_sha=commit_sha)

    # Assert
    mock_get.assert_called_once()
    mock_empty_response.raise_for_status.assert_called_once()
    mock_empty_response.json.assert_called_once()
    assert result == []


def test_get_workflow_runs_no_commit_sha_or_branch():
    """Test that default return value is returned when neither commit_sha nor branch is provided."""
    # Act
    result = get_workflow_runs(OWNER, REPO, TOKEN)
    
    # Assert
    assert result == []  # Default return value from handle_exceptions decorator


def test_get_workflow_runs_empty_commit_sha_and_branch():
    """Test that default return value is returned when both commit_sha and branch are empty strings."""
    # Act
    result = get_workflow_runs(OWNER, REPO, TOKEN, commit_sha="", branch="")
    
    # Assert
    assert result == []  # Default return value from handle_exceptions decorator


def test_get_workflow_runs_none_commit_sha_and_branch():
    """Test that default return value is returned when both commit_sha and branch are None."""
    # Act
    result = get_workflow_runs(OWNER, REPO, TOKEN, commit_sha=None, branch=None)
    
    # Assert
    assert result == []  # Default return value from handle_exceptions decorator


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
    with patch("services.github.workflow_runs.get_workflow_runs.get") as mock_get, \
         patch("services.github.workflow_runs.get_workflow_runs.create_headers") as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.return_value.raise_for_status.side_effect = http_error
        result = get_workflow_runs(OWNER, REPO, TOKEN, commit_sha=commit_sha)

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
        "X-RateLimit-Reset": "1000000010",
    }
    http_error.response = mock_error_response

    # Act
    with patch("services.github.workflow_runs.get_workflow_runs.get") as mock_get, \
         patch("services.github.workflow_runs.get_workflow_runs.create_headers") as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.return_value.raise_for_status.side_effect = http_error
        result = get_workflow_runs(OWNER, REPO, TOKEN, commit_sha=commit_sha)

    # Assert
    mock_get.assert_called_once()
    assert result == []  # Default return value from handle_exceptions decorator


def test_get_workflow_runs_json_decode_error():
    """Test handling of JSON decode error."""
    # Arrange
    commit_sha = "abc123def456"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")

    # Act
    with patch("services.github.workflow_runs.get_workflow_runs.get") as mock_get, \
         patch("services.github.workflow_runs.get_workflow_runs.create_headers") as mock_create_headers:
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
    commit_sha = "abc123def456"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"total_count": 0}  # Missing 'workflow_runs' key

    # Act
    with patch("services.github.workflow_runs.get_workflow_runs.get") as mock_get, \
         patch("services.github.workflow_runs.get_workflow_runs.create_headers") as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.return_value = mock_response
        result = get_workflow_runs(OWNER, REPO, TOKEN, commit_sha=commit_sha)

    # Assert
    mock_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()
    assert result == []  # Default return value from handle_exceptions decorator


def test_get_workflow_runs_request_exception():
    """Test handling of request exception when retrieving workflow runs."""
    # Arrange
    commit_sha = "abc123def456"

    # Act
    with patch("services.github.workflow_runs.get_workflow_runs.get") as mock_get, \
         patch("services.github.workflow_runs.get_workflow_runs.create_headers") as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.side_effect = requests.RequestException("Connection error")
        result = get_workflow_runs(OWNER, REPO, TOKEN, commit_sha=commit_sha)

    # Assert
    mock_get.assert_called_once()
    assert result == []  # Default return value from handle_exceptions decorator


def test_get_workflow_runs_url_construction_with_commit_sha():
    """Test correct URL construction for the API call with commit SHA."""
    # Arrange
    owner = "test-owner"
    repo = "test-repo"
    token = "test-token"
    commit_sha = "abc123def456"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"workflow_runs": []}

    # Act
    with patch("services.github.workflow_runs.get_workflow_runs.get") as mock_get, \
         patch("services.github.workflow_runs.get_workflow_runs.create_headers") as mock_create_headers, \
         patch("services.github.workflow_runs.get_workflow_runs.GITHUB_API_URL", "https://api.github.test"):
        mock_create_headers.return_value = {"Authorization": f"Bearer {token}"}
        mock_get.return_value = mock_response
        get_workflow_runs(owner, repo, token, commit_sha=commit_sha)

    # Assert
    mock_get.assert_called_once()
    assert mock_get.call_args[1]["url"] == f"https://api.github.test/repos/{owner}/{repo}/actions/runs?head_sha={commit_sha}"


def test_get_workflow_runs_url_construction_with_branch():
    """Test correct URL construction for the API call with branch."""
    # Arrange
    owner = "test-owner"
    repo = "test-repo"
    token = "test-token"
    branch = "feature/test-branch"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"workflow_runs": []}

    # Act
    with patch("services.github.workflow_runs.get_workflow_runs.get") as mock_get, \
         patch("services.github.workflow_runs.get_workflow_runs.create_headers") as mock_create_headers, \
         patch("services.github.workflow_runs.get_workflow_runs.GITHUB_API_URL", "https://api.github.test"):
        mock_create_headers.return_value = {"Authorization": f"Bearer {token}"}
        mock_get.return_value = mock_response
        get_workflow_runs(owner, repo, token, branch=branch)

    # Assert
    mock_get.assert_called_once()
    assert mock_get.call_args[1]["url"] == f"https://api.github.test/repos/{owner}/{repo}/actions/runs?branch={branch}"


def test_get_workflow_runs_timeout_parameter():
    """Test that the timeout parameter is correctly passed to the request."""
    # Arrange
    commit_sha = "abc123def456"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"workflow_runs": []}

    # Act
    with patch("services.github.workflow_runs.get_workflow_runs.get") as mock_get, \
         patch("services.github.workflow_runs.get_workflow_runs.create_headers") as mock_create_headers, \
         patch("services.github.workflow_runs.get_workflow_runs.TIMEOUT", 60):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.return_value = mock_response
        get_workflow_runs(OWNER, REPO, TOKEN, commit_sha=commit_sha)

    # Assert
    mock_get.assert_called_once()
    assert mock_get.call_args[1]["timeout"] == 60


def test_get_workflow_runs_special_characters_in_branch():
    """Test handling of special characters in branch name."""
    # Arrange
    branch = "feature/fix-bug-#123"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"workflow_runs": []}

    # Act
    with patch("services.github.workflow_runs.get_workflow_runs.get") as mock_get, \
         patch("services.github.workflow_runs.get_workflow_runs.create_headers") as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.return_value = mock_response
        result = get_workflow_runs(OWNER, REPO, TOKEN, branch=branch)

    # Assert
    mock_get.assert_called_once()
    assert mock_get.call_args[1]["url"] == f"https://api.github.com/repos/{OWNER}/{REPO}/actions/runs?branch={branch}"
    assert result == []


def test_get_workflow_runs_long_commit_sha():
    """Test handling of long commit SHA."""
    # Arrange
    commit_sha = "a" * 40  # 40 character SHA
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"workflow_runs": []}

    # Act
    with patch("services.github.workflow_runs.get_workflow_runs.get") as mock_get, \
         patch("services.github.workflow_runs.get_workflow_runs.create_headers") as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.return_value = mock_response
        result = get_workflow_runs(OWNER, REPO, TOKEN, commit_sha=commit_sha)

    # Assert
    mock_get.assert_called_once()
    assert mock_get.call_args[1]["url"] == f"https://api.github.com/repos/{OWNER}/{REPO}/actions/runs?head_sha={commit_sha}"
    assert result == []


@pytest.mark.parametrize("commit_sha,branch,expected_url_suffix", [
    ("abc123", None, "?head_sha=abc123"),
    (None, "main", "?branch=main"),
    ("def456", "feature", "?head_sha=def456"),  # commit_sha takes precedence
    ("", "develop", "?branch=develop"),  # empty commit_sha falls back to branch
])
def test_get_workflow_runs_parameter_combinations(commit_sha, branch, expected_url_suffix):
    """Test various combinations of commit_sha and branch parameters."""
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"workflow_runs": []}

    # Act
    with patch("services.github.workflow_runs.get_workflow_runs.get") as mock_get, \
         patch("services.github.workflow_runs.get_workflow_runs.create_headers") as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.return_value = mock_response
        get_workflow_runs(OWNER, REPO, TOKEN, commit_sha=commit_sha, branch=branch)

    # Assert
    mock_get.assert_called_once()
    expected_url = f"https://api.github.com/repos/{OWNER}/{REPO}/actions/runs{expected_url_suffix}"
    assert mock_get.call_args[1]["url"] == expected_url
