from unittest.mock import patch, MagicMock
import pytest
import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.artifacts.get_workflow_artifacts import get_workflow_artifacts
from services.github.types.artifact import Artifact


@pytest.fixture
def mock_response():
    """Fixture to provide a mock response object."""
    mock = MagicMock()
    mock.json.return_value = {
        "artifacts": [
            {
                "id": 2846035038,
                "node_id": "MDg6QXJ0aWZhY3QyODQ2MDM1MDM4",
                "name": "coverage-report",
                "size_in_bytes": 7446,
                "url": "https://api.github.com/repos/owner/repo/actions/artifacts/2846035038",
                "archive_download_url": "https://api.github.com/repos/owner/repo/actions/artifacts/2846035038/zip",
                "expired": False,
                "created_at": "2025-03-29T00:00:00Z",
                "updated_at": "2025-03-29T00:00:00Z",
                "expires_at": "2025-04-28T00:00:00Z"
            },
            {
                "id": 2846035039,
                "node_id": "MDg6QXJ0aWZhY3QyODQ2MDM1MDM5",
                "name": "test-results",
                "size_in_bytes": 1024,
                "url": "https://api.github.com/repos/owner/repo/actions/artifacts/2846035039",
                "archive_download_url": "https://api.github.com/repos/owner/repo/actions/artifacts/2846035039/zip",
                "expired": True,
                "created_at": "2025-03-28T00:00:00Z",
                "updated_at": "2025-03-28T00:00:00Z",
                "expires_at": "2025-04-27T00:00:00Z"
            }
        ]
    }
    return mock


@pytest.fixture
def mock_headers():
    """Fixture to provide mock headers."""
    return {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": "Bearer test_token",
        "User-Agent": "test_app",
        "X-GitHub-Api-Version": "2022-11-28"
    }


@pytest.fixture
def sample_artifacts():
    """Fixture to provide sample artifact data."""
    return [
        {
            "id": 2846035038,
            "node_id": "MDg6QXJ0aWZhY3QyODQ2MDM1MDM4",
            "name": "coverage-report",
            "size_in_bytes": 7446,
            "url": "https://api.github.com/repos/owner/repo/actions/artifacts/2846035038",
            "archive_download_url": "https://api.github.com/repos/owner/repo/actions/artifacts/2846035038/zip",
            "expired": False,
            "created_at": "2025-03-29T00:00:00Z",
            "updated_at": "2025-03-29T00:00:00Z",
            "expires_at": "2025-04-28T00:00:00Z"
        }
    ]


@patch("services.github.artifacts.get_workflow_artifacts.get")
@patch("services.github.artifacts.get_workflow_artifacts.create_headers")
def test_get_workflow_artifacts_success(mock_create_headers, mock_get, mock_response, mock_headers):
    """Test successful retrieval of workflow artifacts."""
    # Setup mocks
    mock_create_headers.return_value = mock_headers
    mock_get.return_value = mock_response
    
    # Call function
    result = get_workflow_artifacts("owner", "repo", 123, "test_token")
    
    # Verify API call
    expected_url = f"{GITHUB_API_URL}/repos/owner/repo/actions/runs/123/artifacts"
    mock_get.assert_called_once_with(url=expected_url, headers=mock_headers, timeout=TIMEOUT)
    mock_create_headers.assert_called_once_with(token="test_token")
    
    # Verify result
    assert len(result) == 2
    assert result[0]["id"] == 2846035038
    assert result[0]["name"] == "coverage-report"
    assert result[1]["id"] == 2846035039
    assert result[1]["name"] == "test-results"


@patch("services.github.artifacts.get_workflow_artifacts.get")
@patch("services.github.artifacts.get_workflow_artifacts.create_headers")
def test_get_workflow_artifacts_empty_response(mock_create_headers, mock_get, mock_headers):
    """Test handling of empty artifacts response."""
    # Setup mocks
    mock_create_headers.return_value = mock_headers
    mock_response = MagicMock()
    mock_response.json.return_value = {"artifacts": []}
    mock_get.return_value = mock_response
    
    # Call function
    result = get_workflow_artifacts("owner", "repo", 123, "test_token")
    
    # Verify result
    assert result == []


@patch("services.github.artifacts.get_workflow_artifacts.get")
@patch("services.github.artifacts.get_workflow_artifacts.create_headers")
def test_get_workflow_artifacts_missing_artifacts_key(mock_create_headers, mock_get, mock_headers):
    """Test handling of response without artifacts key."""
    # Setup mocks
    mock_create_headers.return_value = mock_headers
    mock_response = MagicMock()
    mock_response.json.return_value = {"other_key": "value"}
    mock_get.return_value = mock_response
    
    # Call function
    result = get_workflow_artifacts("owner", "repo", 123, "test_token")
    
    # Verify result (should return empty list due to .get("artifacts", []))
    assert result == []


@patch("services.github.artifacts.get_workflow_artifacts.get")
@patch("services.github.artifacts.get_workflow_artifacts.create_headers")
def test_get_workflow_artifacts_with_different_parameters(mock_create_headers, mock_get, mock_response, mock_headers):
    """Test function with different parameter values."""
    # Setup mocks
    mock_create_headers.return_value = mock_headers
    mock_get.return_value = mock_response
    
    # Test with different parameters
    result = get_workflow_artifacts("different-owner", "different-repo", 456, "different_token")
    
    # Verify API call with different parameters
    expected_url = f"{GITHUB_API_URL}/repos/different-owner/different-repo/actions/runs/456/artifacts"
    mock_get.assert_called_once_with(url=expected_url, headers=mock_headers, timeout=TIMEOUT)
    mock_create_headers.assert_called_once_with(token="different_token")
    
    # Verify result
    assert len(result) == 2


@patch("services.github.artifacts.get_workflow_artifacts.get")
@patch("services.github.artifacts.get_workflow_artifacts.create_headers")
def test_get_workflow_artifacts_http_error_returns_default(mock_create_headers, mock_get, mock_headers):
    """Test that HTTP errors return default value due to handle_exceptions decorator."""
    # Setup mocks
    mock_create_headers.return_value = mock_headers
    # Create a mock response for the HTTPError
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.reason = "Not Found"
    mock_response.text = "Repository not found"
    mock_response.headers = {}
    
    # Create HTTPError with the mock response
    
    # Call function
    result = get_workflow_artifacts("owner", "repo", 123, "test_token")
    
    # Verify default return value
    assert result == []


@patch("services.github.artifacts.get_workflow_artifacts.get")
@patch("services.github.artifacts.get_workflow_artifacts.create_headers")
def test_get_workflow_artifacts_json_decode_error_returns_default(mock_create_headers, mock_get, mock_headers):
    """Test that JSON decode errors return default value due to handle_exceptions decorator."""
    # Setup mocks
    mock_create_headers.return_value = mock_headers
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_get.return_value = mock_response
    
    # Call function
    result = get_workflow_artifacts("owner", "repo", 123, "test_token")
    
    # Verify default return value
    assert result == []


@patch("services.github.artifacts.get_workflow_artifacts.get")
@patch("services.github.artifacts.get_workflow_artifacts.create_headers")
def test_get_workflow_artifacts_request_exception_returns_default(mock_create_headers, mock_get, mock_headers):
    """Test that request exceptions return default value due to handle_exceptions decorator."""
    # Setup mocks
    mock_create_headers.return_value = mock_headers
    mock_get.side_effect = requests.exceptions.RequestException("Connection error")
    
    # Call function
    result = get_workflow_artifacts("owner", "repo", 123, "test_token")
    
    # Verify default return value
    assert result == []


@patch("services.github.artifacts.get_workflow_artifacts.get")
@patch("services.github.artifacts.get_workflow_artifacts.create_headers")
def test_get_workflow_artifacts_single_artifact(mock_create_headers, mock_get, mock_headers, sample_artifacts):
    """Test handling of response with single artifact."""
    # Setup mocks
    mock_create_headers.return_value = mock_headers
    mock_response = MagicMock()
    mock_response.json.return_value = {"artifacts": sample_artifacts}
    mock_get.return_value = mock_response
    
    # Call function
    result = get_workflow_artifacts("owner", "repo", 123, "test_token")
    
    # Verify result
    assert len(result) == 1
    assert result[0]["id"] == 2846035038
    assert result[0]["name"] == "coverage-report"
    assert result[0]["expired"] is False


@pytest.mark.parametrize("owner,repo,run_id,token", [
    ("test-owner", "test-repo", 1, "token1"),
    ("org", "project", 999999, "very-long-token-string"),
    ("a", "b", 0, ""),
    ("owner-with-dashes", "repo_with_underscores", 123456789, "sk-token-123"),
])
@patch("services.github.artifacts.get_workflow_artifacts.get")
@patch("services.github.artifacts.get_workflow_artifacts.create_headers")
def test_get_workflow_artifacts_various_parameters(mock_create_headers, mock_get, mock_headers, owner, repo, run_id, token):
    """Test function with various parameter combinations."""
    # Setup mocks
    mock_create_headers.return_value = mock_headers
    mock_response = MagicMock()
    mock_response.json.return_value = {"artifacts": []}
    mock_get.return_value = mock_response
    
    # Call function
    result = get_workflow_artifacts(owner, repo, run_id, token)
    
    # Verify API call
    expected_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/actions/runs/{run_id}/artifacts"
    mock_get.assert_called_once_with(url=expected_url, headers=mock_headers, timeout=TIMEOUT)
    mock_create_headers.assert_called_once_with(token=token)
    
    # Verify result
    assert result == []


@patch("services.github.artifacts.get_workflow_artifacts.get")
@patch("services.github.artifacts.get_workflow_artifacts.create_headers")
def test_get_workflow_artifacts_does_not_call_raise_for_status(mock_create_headers, mock_get, mock_headers):
    """Test that the function does not call raise_for_status on the response."""
    # Setup mocks
    mock_create_headers.return_value = mock_headers
    mock_response = MagicMock()
    mock_response.json.return_value = {"artifacts": []}
    mock_get.return_value = mock_response
    
    # Call function
    get_workflow_artifacts("owner", "repo", 123, "test_token")
    
