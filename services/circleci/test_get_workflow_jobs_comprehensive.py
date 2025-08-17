from unittest.mock import patch, Mock
import pytest
from requests.exceptions import HTTPError, RequestException, Timeout

from services.circleci.get_workflow_jobs import get_circleci_workflow_jobs


@pytest.fixture
def mock_requests_get():
    """Mock requests.get for testing."""
    with patch("services.circleci.get_workflow_jobs.get") as mock:
        yield mock


@pytest.fixture
def sample_workflow_jobs():
    """Sample workflow jobs data for testing."""
    return [
        {
            "job_number": 123,
            "stopped_at": "2023-01-01T12:30:00Z",
            "started_at": "2023-01-01T12:00:00Z",
            "name": "Quick Validation Tests (Should Pass)",
            "project_slug": "github/owner/repo",
            "type": "build",
            "requires": {},
            "status": "success",
            "id": "job-123",
            "dependencies": []
        },
        {
            "job_number": 124,
            "stopped_at": "2023-01-01T12:45:00Z",
            "started_at": "2023-01-01T12:30:00Z",
            "name": "Stress Tests (Intentional Failure)",
            "project_slug": "github/owner/repo",
            "type": "build",
            "requires": {},
            "status": "failed",
            "id": "job-124",
            "dependencies": []
        }
    ]


def test_get_workflow_jobs_with_valid_token(mock_requests_get, sample_workflow_jobs):
    """Test getting workflow jobs with valid token and workflow ID."""
    workflow_id = "772ddda7-d6b7-49ad-9123-108d9f8164b5"
    token = "test-token"
    
    mock_response_data = {"items": sample_workflow_jobs, "next_page_token": None}
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response
    
    result = get_circleci_workflow_jobs(workflow_id, token)
    
    # Should return a list of jobs
    assert isinstance(result, list)
    assert len(result) == 2
    
    # Check that jobs have expected structure
    job_names = [job["name"] for job in result]
    assert "Quick Validation Tests (Should Pass)" in job_names
    assert "Stress Tests (Intentional Failure)" in job_names
    
    # Check for failed job
    failed_jobs = [job for job in result if job["status"] == "failed"]
    assert len(failed_jobs) == 1
    
    # Check for successful job
    success_jobs = [job for job in result if job["status"] == "success"]
    assert len(success_jobs) == 1


def test_get_workflow_jobs_404_response(mock_requests_get):
    """Test handling of 404 response for invalid workflow ID."""
    workflow_id = "invalid-workflow-id-123"
    token = "test-token"
    
    mock_response = Mock()
    mock_response.status_code = 404
    mock_requests_get.return_value = mock_response
    
    result = get_circleci_workflow_jobs(workflow_id, token)
    
    # Should return empty list for 404
    assert result == []


def test_get_workflow_jobs_401_response(mock_requests_get):
    """Test handling of 401 authentication error."""
    workflow_id = "test-workflow-id"
    token = "invalid-token"
    
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = HTTPError("401 Unauthorized")
    mock_requests_get.return_value = mock_response
    
    result = get_circleci_workflow_jobs(workflow_id, token)
    
    # Should return empty list due to exception handling
    assert result == []


def test_get_workflow_jobs_empty_response(mock_requests_get):
    """Test handling of empty workflow jobs response."""
    workflow_id = "empty-workflow-id"
    token = "test-token"
    
    mock_response_data = {"items": [], "next_page_token": None}
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response
    
    result = get_circleci_workflow_jobs(workflow_id, token)
    
    assert isinstance(result, list)
    assert len(result) == 0


def test_get_workflow_jobs_missing_items_key(mock_requests_get):
    """Test handling of response without items key."""
    workflow_id = "test-workflow-id"
    token = "test-token"
    
    mock_response_data = {"next_page_token": None}  # Missing items key
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response
    
    result = get_circleci_workflow_jobs(workflow_id, token)
    
    assert isinstance(result, list)
    assert len(result) == 0


def test_get_workflow_jobs_url_construction(mock_requests_get):
    """Test that the URL is constructed correctly."""
    workflow_id = "test-workflow-id-123"
    token = "test-token"
    
    mock_response = Mock()
    mock_response.status_code = 404
    mock_requests_get.return_value = mock_response
    
    get_circleci_workflow_jobs(workflow_id, token)
    
    # Verify the URL construction
    expected_url = f"https://circleci.com/api/v2/workflow/{workflow_id}/job"
    mock_requests_get.assert_called_with(
        url=expected_url,
        headers={"Circle-Token": token},
        timeout=30  # TIMEOUT from config
    )


def test_get_workflow_jobs_request_exception(mock_requests_get):
    """Test handling of request exceptions."""
    workflow_id = "test-workflow-id"
    token = "test-token"
    
    mock_requests_get.side_effect = RequestException("Network error")
    
    result = get_circleci_workflow_jobs(workflow_id, token)
    
    # Should return empty list due to exception handling
    assert result == []


def test_get_workflow_jobs_timeout_exception(mock_requests_get):
    """Test handling of timeout exceptions."""
    workflow_id = "test-workflow-id"
    token = "test-token"
    
    mock_requests_get.side_effect = Timeout("Request timeout")
    
    result = get_circleci_workflow_jobs(workflow_id, token)
    
    # Should return empty list due to exception handling
    assert result == []


def test_get_workflow_jobs_with_pagination_token(mock_requests_get, sample_workflow_jobs):
    """Test handling of response with pagination token."""
    workflow_id = "test-workflow-id"
    token = "test-token"
    
    mock_response_data = {"items": sample_workflow_jobs, "next_page_token": "next-token-123"}
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response
    
    result = get_circleci_workflow_jobs(workflow_id, token)
    
    # Should still return the jobs from the first page
    assert isinstance(result, list)
    assert len(result) == 2


def test_get_workflow_jobs_json_decode_error(mock_requests_get):
    """Test handling of JSON decode errors."""
    workflow_id = "test-workflow-id"
    token = "test-token"
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response
    
    result = get_circleci_workflow_jobs(workflow_id, token)
    
    # Should return empty list due to exception handling
    assert result == []


def test_get_workflow_jobs_malformed_response_data(mock_requests_get):
    """Test handling of malformed response data."""
    workflow_id = "test-workflow-id"
    token = "test-token"
    
    # Response with items as non-list
    mock_response_data = {"items": "not-a-list", "next_page_token": None}
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response
    
    result = get_circleci_workflow_jobs(workflow_id, token)
    
    # Should return the malformed data as-is (function doesn't validate structure)
    assert result == "not-a-list"


@pytest.mark.parametrize("status_code", [500, 502, 503])
def test_get_workflow_jobs_server_errors(mock_requests_get, status_code):
    """Test handling of various server error status codes."""
    workflow_id = "test-workflow-id"
    token = "test-token"
    
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.raise_for_status.side_effect = HTTPError(f"{status_code} Server Error")
    mock_requests_get.return_value = mock_response
    
    result = get_circleci_workflow_jobs(workflow_id, token)
    
    # Should return empty list due to exception handling
    assert result == []
