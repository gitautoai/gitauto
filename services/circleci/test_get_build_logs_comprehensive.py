from unittest.mock import patch, Mock
import pytest
from requests.exceptions import HTTPError

from services.circleci.get_build_logs import get_circleci_build_logs


@pytest.fixture
def mock_requests_get():
    """Mock requests.get for testing."""
    with patch("services.circleci.get_build_logs.get") as mock:
        yield mock


@pytest.fixture
def sample_failed_build_data():
    """Sample failed build data for testing."""
    return {
        "build_num": 16,
        "status": "failed",
        "failed": True,
        "steps": [
            {
                "name": "Test Step",
                "actions": [
                    {
                        "status": "failed",
                        "output_url": "https://circleci.com/api/v1.1/output/123"
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_log_entries():
    """Sample log entries for testing."""
    return [
        {
            "message": "Error: Test failed\r\n",
            "time": "2023-01-01T12:00:00Z",
            "type": "out"
        },
        {
            "message": "Stack trace here\r",
            "time": "2023-01-01T12:00:01Z", 
            "type": "err"
        }
    ]


def test_get_build_logs_successful_failed_build(mock_requests_get, sample_failed_build_data, sample_log_entries):
    """Test getting build logs from a failed build."""
    project_slug = "github/owner/repo"
    build_number = 16
    token = "test-token"
    
    def mock_get_side_effect(url, **kwargs):
        mock_response = Mock()
        if "/project/" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = sample_failed_build_data
            mock_response.raise_for_status.return_value = None
        else:  # output_url request
            mock_response.status_code = 200
            mock_response.json.return_value = sample_log_entries
        return mock_response
    
    mock_requests_get.side_effect = mock_get_side_effect
    
    result = get_circleci_build_logs(project_slug, build_number, token)
    
    assert isinstance(result, str)
    assert "CircleCI Build Log: Test Step" in result
    assert "Error: Test failed" in result
    assert "Stack trace here" in result
    # Verify carriage returns are cleaned up
    assert "\r\n" not in result
    assert "\r" not in result


def test_get_build_logs_404_response(mock_requests_get):
    """Test handling of 404 response."""
    project_slug = "github/owner/repo"
    build_number = 16
    token = "test-token"
    
    mock_response = Mock()
    mock_response.status_code = 404
    mock_requests_get.return_value = mock_response
    
    result = get_circleci_build_logs(project_slug, build_number, token)
    
    assert result == 404


def test_get_build_logs_401_response(mock_requests_get):
    """Test handling of 401 authentication error."""
    project_slug = "github/owner/repo"
    build_number = 16
    token = "invalid-token"
    
    mock_response = Mock()
    mock_response.status_code = 401
    mock_requests_get.return_value = mock_response
    
    result = get_circleci_build_logs(project_slug, build_number, token)
    
    assert result == "CircleCI authentication failed. Please check your token."


def test_get_build_logs_successful_build_returns_none(mock_requests_get):
    """Test that successful builds return None."""
    project_slug = "github/owner/repo"
    build_number = 15
    token = "test-token"
    
    successful_build_data = {
        "build_num": 15,
        "status": "success",
        "failed": False,
        "steps": []
    }
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = successful_build_data
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response
    
    result = get_circleci_build_logs(project_slug, build_number, token)
    
    assert result is None


def test_get_build_logs_infrastructure_fail_status(mock_requests_get, sample_log_entries):
    """Test handling of infrastructure_fail status."""
    project_slug = "github/owner/repo"
    build_number = 17
    token = "test-token"
    
    infra_fail_build_data = {
        "build_num": 17,
        "status": "infrastructure_fail",
        "failed": True,
        "steps": [
            {
                "name": "Infrastructure Step",
                "actions": [
                    {
                        "status": "infrastructure_fail",
                        "output_url": "https://circleci.com/api/v1.1/output/456"
                    }
                ]
            }
        ]
    }
    
    def mock_get_side_effect(url, **kwargs):
        mock_response = Mock()
        if "/project/" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = infra_fail_build_data
            mock_response.raise_for_status.return_value = None
        else:  # output_url request
            mock_response.status_code = 200
            mock_response.json.return_value = sample_log_entries
        return mock_response
    
    mock_requests_get.side_effect = mock_get_side_effect
    
    result = get_circleci_build_logs(project_slug, build_number, token)
    
    assert isinstance(result, str)
    assert "CircleCI Build Log: Infrastructure Step" in result


def test_get_build_logs_timedout_status(mock_requests_get, sample_log_entries):
    """Test handling of timedout status."""
    project_slug = "github/owner/repo"
    build_number = 18
    token = "test-token"
    
    timeout_build_data = {
        "build_num": 18,
        "status": "timedout",
        "failed": True,
        "steps": [
            {
                "name": "Timeout Step",
                "actions": [
                    {
                        "status": "timedout",
                        "output_url": "https://circleci.com/api/v1.1/output/789"
                    }
                ]
            }
        ]
    }
    
    def mock_get_side_effect(url, **kwargs):
        mock_response = Mock()
        if "/project/" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = timeout_build_data
            mock_response.raise_for_status.return_value = None
        else:  # output_url request
            mock_response.status_code = 200
            mock_response.json.return_value = sample_log_entries
        return mock_response
    
    mock_requests_get.side_effect = mock_get_side_effect
    
    result = get_circleci_build_logs(project_slug, build_number, token)
    
    assert isinstance(result, str)
    assert "CircleCI Build Log: Timeout Step" in result


def test_get_build_logs_no_output_url(mock_requests_get):
    """Test handling of actions without output_url."""
    project_slug = "github/owner/repo"
    build_number = 19
    token = "test-token"
    
    build_data_no_output = {
        "build_num": 19,
        "status": "failed",
        "failed": True,
        "steps": [
            {
                "name": "No Output Step",
                "actions": [
                    {
                        "status": "failed",
                        # No output_url field
                    }
                ]
            }
        ]
    }
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = build_data_no_output
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response
    
    result = get_circleci_build_logs(project_slug, build_number, token)
    
    assert result == "No error logs found in CircleCI build."


def test_get_build_logs_log_fetch_failure(mock_requests_get, sample_failed_build_data):
    """Test handling of log fetch failure."""
    project_slug = "github/owner/repo"
    build_number = 20
    token = "test-token"
    
    def mock_get_side_effect(url, **kwargs):
        mock_response = Mock()
        if "/project/" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = sample_failed_build_data
            mock_response.raise_for_status.return_value = None
        else:  # output_url request fails
            mock_response.status_code = 500
        return mock_response
    
    mock_requests_get.side_effect = mock_get_side_effect
    
    result = get_circleci_build_logs(project_slug, build_number, token)
    
    assert result == "No error logs found in CircleCI build."


def test_get_build_logs_url_construction(mock_requests_get):
    """Test that the URL is constructed correctly."""
    project_slug = "github/owner/repo"
    build_number = 25
    token = "test-token"
    
    mock_response = Mock()
    mock_response.status_code = 404
    mock_requests_get.return_value = mock_response
    
    get_circleci_build_logs(project_slug, build_number, token)
    
    # Verify the URL construction
    expected_url = f"https://circleci.com/api/v1.1/project/{project_slug}/{build_number}"
    mock_requests_get.assert_called_with(
        url=expected_url,
        headers={"Circle-Token": token},
        timeout=30  # TIMEOUT from config
    )


def test_get_build_logs_non_list_log_data(mock_requests_get, sample_failed_build_data):
    """Test handling of non-list log data."""
    project_slug = "github/owner/repo"
    build_number = 21
    token = "test-token"
    
    def mock_get_side_effect(url, **kwargs):
        mock_response = Mock()
        if "/project/" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = sample_failed_build_data
            mock_response.raise_for_status.return_value = None
        else:  # output_url returns non-list data
            mock_response.status_code = 200
            mock_response.json.return_value = "String log data instead of list"
        return mock_response
    
    mock_requests_get.side_effect = mock_get_side_effect
    
    result = get_circleci_build_logs(project_slug, build_number, token)
    
    assert isinstance(result, str)
    assert "String log data instead of list" in result


def test_get_build_logs_non_dict_log_entries(mock_requests_get, sample_failed_build_data):
    """Test handling of non-dict log entries."""
    project_slug = "github/owner/repo"
    build_number = 22
    token = "test-token"
    
    mixed_log_data = [
        {"message": "Valid entry", "time": "2023-01-01T12:00:00Z", "type": "out"},
        "Invalid string entry",
        123,  # Invalid number entry
        {"message": "Another valid entry", "time": "2023-01-01T12:00:01Z", "type": "err"}
    ]
    
    def mock_get_side_effect(url, **kwargs):
        mock_response = Mock()
        if "/project/" in url:
            mock_response.status_code = 200
            mock_response.json.return_value = sample_failed_build_data
            mock_response.raise_for_status.return_value = None
        else:  # output_url returns mixed data types
            mock_response.status_code = 200
            mock_response.json.return_value = mixed_log_data
        return mock_response
    
    mock_requests_get.side_effect = mock_get_side_effect
    
    result = get_circleci_build_logs(project_slug, build_number, token)
    
    assert isinstance(result, str)
    assert "Valid entry" in result
    assert "Another valid entry" in result
    assert "Invalid string entry" in result
    assert "123" in result
