from unittest.mock import patch, MagicMock
import pytest
from requests.exceptions import HTTPError

from config import GITHUB_API_URL, TIMEOUT
from services.github.workflow_runs.get_workflow_runs import get_workflow_runs


@pytest.fixture
def mock_requests_get():
    """Fixture to provide a mocked requests.get method."""
    with patch("services.github.workflow_runs.get_workflow_runs.get") as mock:
        mock_response = MagicMock()
        mock_response.json.return_value = {"workflow_runs": []}
        mock.return_value = mock_response
        yield mock


@pytest.fixture
def mock_create_headers():
    """Fixture to provide a mocked create_headers function."""
    with patch("services.github.workflow_runs.get_workflow_runs.create_headers") as mock:
        mock.return_value = {"Authorization": "Bearer test_token"}
        yield mock


@pytest.fixture
def sample_workflow_runs_response():
    """Fixture providing a sample workflow runs response."""
    return {
        "workflow_runs": [
            {
                "id": 123456,
                "name": "Test Workflow",
                "status": "completed",
                "conclusion": "success"
            }
        ]
    }


def test_get_workflow_runs_with_commit_sha(mock_requests_get, mock_create_headers, sample_workflow_runs_response):
    """Test get_workflow_runs with commit SHA parameter."""
    mock_requests_get.return_value.json.return_value = sample_workflow_runs_response
    
    result = get_workflow_runs(
        owner="owner",
        repo="repo",
        token="test_token",
        commit_sha="abc123def456"
    )
    
    expected_url = f"{GITHUB_API_URL}/repos/owner/repo/actions/runs?head_sha=abc123def456"
    mock_requests_get.assert_called_once_with(
        url=expected_url,
        headers=mock_create_headers.return_value,
        timeout=TIMEOUT
    )
    mock_create_headers.assert_called_once_with(token="test_token", media_type="")
    assert result == sample_workflow_runs_response["workflow_runs"]


def test_get_workflow_runs_with_branch(mock_requests_get, mock_create_headers, sample_workflow_runs_response):
    """Test get_workflow_runs with branch parameter."""
    mock_requests_get.return_value.json.return_value = sample_workflow_runs_response
    
    result = get_workflow_runs(
        owner="owner",
        repo="repo",
        token="test_token",
        branch="main"
    )
    
    expected_url = f"{GITHUB_API_URL}/repos/owner/repo/actions/runs?branch=main"
    mock_requests_get.assert_called_once_with(
        url=expected_url,
        headers=mock_create_headers.return_value,
        timeout=TIMEOUT
    )
    mock_create_headers.assert_called_once_with(token="test_token", media_type="")
    assert result == sample_workflow_runs_response["workflow_runs"]


def test_get_workflow_runs_missing_parameters():
    """Test get_workflow_runs returns empty list when both commit_sha and branch are missing."""
    result = get_workflow_runs(
        owner="owner",
        repo="repo",
        token="test_token"
    )
    
    assert result == []


def test_get_workflow_runs_handles_http_error(mock_requests_get, mock_create_headers):
    """Test get_workflow_runs handles HTTP errors gracefully."""
    # Create a proper HTTPError by making the mock response raise it
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = HTTPError("404 Client Error")
    mock_response.status_code = 404
    mock_response.reason = "Not Found"
    mock_response.text = "Repository not found"
    mock_response.headers = {}
    mock_requests_get.return_value = mock_response
    
    result = get_workflow_runs(
        owner="owner",
        repo="repo",
        token="test_token",
        commit_sha="abc123def456"
    )
    
    assert result == []


def test_get_workflow_runs_with_empty_response(mock_requests_get, mock_create_headers):
    """Test get_workflow_runs with empty workflow runs response."""
    mock_requests_get.return_value.json.return_value = {"workflow_runs": []}
    
    result = get_workflow_runs(
        owner="owner",
        repo="repo",
        token="test_token",
        commit_sha="abc123def456"
    )
    
    assert result == []


def test_get_workflow_runs_commit_sha_takes_precedence(mock_requests_get, mock_create_headers, sample_workflow_runs_response):
    """Test get_workflow_runs when both commit_sha and branch are provided (commit_sha takes precedence)."""
    mock_requests_get.return_value.json.return_value = sample_workflow_runs_response
    
    result = get_workflow_runs(
        owner="owner",
        repo="repo",
        token="test_token",
        commit_sha="abc123def456",
        branch="main"
    )
    
    expected_url = f"{GITHUB_API_URL}/repos/owner/repo/actions/runs?head_sha=abc123def456"
    mock_requests_get.assert_called_once_with(
        url=expected_url,
        headers=mock_create_headers.return_value,
        timeout=TIMEOUT
    )
    assert result == sample_workflow_runs_response["workflow_runs"]
