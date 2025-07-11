from unittest.mock import patch, MagicMock
import pytest
import requests
from requests.exceptions import HTTPError

from config import GITHUB_API_URL, TIMEOUT
from services.github.branches.check_branch_exists import check_branch_exists


@pytest.fixture
def mock_requests_get():
    """Fixture to mock requests.get"""
    with patch("services.github.branches.check_branch_exists.requests.get") as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    """Fixture to mock create_headers function"""
    with patch("services.github.branches.check_branch_exists.create_headers") as mock:
        mock.return_value = {"Authorization": "Bearer test_token"}
        yield mock


@pytest.fixture
def sample_params():
    """Fixture providing sample parameters for testing"""
    return {
        "owner": "test_owner",
        "repo": "test_repo", 
        "branch_name": "main",
        "token": "test_token"
    }


def test_check_branch_exists_returns_true_when_branch_exists(mock_requests_get, mock_create_headers, sample_params):
    """Test that function returns True when branch exists (200 response)"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response
    
    # Call function
    result = check_branch_exists(**sample_params)
    
    # Assertions
    assert result is True
    expected_url = f"{GITHUB_API_URL}/repos/{sample_params['owner']}/{sample_params['repo']}/branches/{sample_params['branch_name']}"
    mock_requests_get.assert_called_once_with(
        url=expected_url,
        headers={"Authorization": "Bearer test_token"},
        timeout=TIMEOUT
    )
    mock_create_headers.assert_called_once_with(token=sample_params["token"], media_type="")
    mock_response.raise_for_status.assert_called_once()


def test_check_branch_exists_returns_false_when_branch_not_found(mock_requests_get, mock_create_headers, sample_params):
    """Test that function returns False when branch doesn't exist (404 response)"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_requests_get.return_value = mock_response
    
    # Call function
    result = check_branch_exists(**sample_params)
    
    # Assertions
    assert result is False
    expected_url = f"{GITHUB_API_URL}/repos/{sample_params['owner']}/{sample_params['repo']}/branches/{sample_params['branch_name']}"
    mock_requests_get.assert_called_once_with(
        url=expected_url,
        headers={"Authorization": "Bearer test_token"},
        timeout=TIMEOUT
    )
    mock_create_headers.assert_called_once_with(token=sample_params["token"], media_type="")
    # raise_for_status should not be called for 404
    mock_response.raise_for_status.assert_not_called()


def test_check_branch_exists_returns_false_for_empty_branch_name(mock_requests_get, mock_create_headers, sample_params):
    """Test that function returns False when branch_name is empty"""
    sample_params["branch_name"] = ""
    
    result = check_branch_exists(**sample_params)
    
    assert result is False
    # Should not make any HTTP requests
    mock_requests_get.assert_not_called()
    mock_create_headers.assert_not_called()


def test_check_branch_exists_returns_false_for_none_branch_name(mock_requests_get, mock_create_headers, sample_params):
    """Test that function returns False when branch_name is None"""
    sample_params["branch_name"] = None
    
    result = check_branch_exists(**sample_params)
    
    assert result is False
    # Should not make any HTTP requests
    mock_requests_get.assert_not_called()
    mock_create_headers.assert_not_called()


def test_check_branch_exists_handles_http_error_gracefully(mock_requests_get, mock_create_headers, sample_params):
    """Test that function handles HTTP errors gracefully and returns False"""
    # Setup mock response to raise HTTPError
    mock_response = MagicMock()
    mock_response.status_code = 500
    # Create a proper HTTPError with response attribute
    http_error = HTTPError("Server Error")
    http_error.response = mock_response
    mock_response.reason = "Internal Server Error"
    mock_response.text = "Server Error"
    mock_requests_get.return_value = mock_response
    
    # Call function
    result = check_branch_exists(**sample_params)
    
    # Should return False due to @handle_exceptions decorator
    assert result is False
    expected_url = f"{GITHUB_API_URL}/repos/{sample_params['owner']}/{sample_params['repo']}/branches/{sample_params['branch_name']}"
    mock_requests_get.assert_called_once_with(
        url=expected_url,
        headers={"Authorization": "Bearer test_token"},
        timeout=TIMEOUT
    )
    mock_response.raise_for_status.assert_called_once()


def test_check_branch_exists_handles_request_exception_gracefully(mock_requests_get, mock_create_headers, sample_params):
    """Test that function handles request exceptions gracefully and returns False"""
    # Setup mock to raise RequestException
    mock_requests_get.side_effect = requests.exceptions.RequestException("Network error")
    
    # Call function
    result = check_branch_exists(**sample_params)
    
    # Should return False due to @handle_exceptions decorator
    assert result is False


def test_check_branch_exists_constructs_correct_url(mock_requests_get, mock_create_headers):
    """Test that function constructs the correct GitHub API URL"""
    owner = "facebook"
    repo = "react"
    branch_name = "feature/new-hooks"
    token = "ghp_test_token"
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response
    
    check_branch_exists(owner, repo, branch_name, token)
    
    expected_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/branches/{branch_name}"
    mock_requests_get.assert_called_once_with(
        url=expected_url,
        headers={"Authorization": "Bearer test_token"},
        timeout=TIMEOUT
    )


def test_check_branch_exists_passes_correct_headers(mock_requests_get, mock_create_headers, sample_params):
    """Test that function passes correct headers to the request"""
    expected_headers = {
        "Authorization": "Bearer test_token",
        "Accept": "application/vnd.github+json",
        "User-Agent": "GitAuto"
    }
    mock_create_headers.return_value = expected_headers
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response
    
    check_branch_exists(**sample_params)
    
    mock_create_headers.assert_called_once_with(token=sample_params["token"], media_type="")
    mock_requests_get.assert_called_once_with(
        url=f"{GITHUB_API_URL}/repos/{sample_params['owner']}/{sample_params['repo']}/branches/{sample_params['branch_name']}",
        headers=expected_headers,
        timeout=TIMEOUT
    )


@pytest.mark.parametrize("branch_name", [
    "main",
    "develop", 
    "feature/new-feature",
    "hotfix/urgent-fix",
    "release/v1.0.0",
    "user/john/experimental",
    "123-numeric-branch",
    "branch-with-dashes",
    "branch_with_underscores"
])
def test_check_branch_exists_with_various_branch_names(mock_requests_get, mock_create_headers, branch_name):
    """Test that function works with various valid branch name formats"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response
    
    result = check_branch_exists("owner", "repo", branch_name, "token")
    
    assert result is True
    expected_url = f"{GITHUB_API_URL}/repos/owner/repo/branches/{branch_name}"
    mock_requests_get.assert_called_once_with(
        url=expected_url,
        headers={"Authorization": "Bearer test_token"},
        timeout=TIMEOUT
    )


@pytest.mark.parametrize("empty_value", [
    "",
    None,
    "   ",  # whitespace only
    "\t",   # tab only
    "\n",   # newline only
])
def test_check_branch_exists_with_empty_branch_names(mock_requests_get, mock_create_headers, empty_value):
    """Test that function returns False for various empty branch name values"""
    result = check_branch_exists("owner", "repo", empty_value, "token")
    
    assert result is False
    # Should not make any HTTP requests for empty values
    mock_requests_get.assert_not_called()
    mock_create_headers.assert_not_called()


@pytest.mark.parametrize("status_code", [
    200,  # OK
    201,  # Created
    202,  # Accepted
    204,  # No Content
])
def test_check_branch_exists_with_success_status_codes(mock_requests_get, mock_create_headers, status_code):
    """Test that function returns True for various success status codes"""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response
    
    result = check_branch_exists("owner", "repo", "branch", "token")
    
    assert result is True
    mock_response.raise_for_status.assert_called_once()


@pytest.mark.parametrize("status_code", [
    400,  # Bad Request
    401,  # Unauthorized
    403,  # Forbidden
    500,  # Internal Server Error
    502,  # Bad Gateway
    503,  # Service Unavailable
])
def test_check_branch_exists_with_error_status_codes_that_raise_for_status(mock_requests_get, mock_create_headers, status_code):
    """Test that function handles various error status codes that would raise_for_status"""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    # Create a proper HTTPError with response attribute
    http_error = HTTPError(f"{status_code} Error")
    http_error.response = mock_response
    mock_response.reason = f"{status_code} Error"
    mock_response.text = f"{status_code} Error"
    mock_requests_get.return_value = mock_response
    
    result = check_branch_exists("owner", "repo", "branch", "token")
    
    # Should return False due to @handle_exceptions decorator
    assert result is False
    mock_response.raise_for_status.assert_called_once()


def test_check_branch_exists_function_signature():
    """Test that function has correct signature and type annotations"""
    import inspect
    
