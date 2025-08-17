from unittest.mock import patch, MagicMock
import pytest
import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.refs.update_reference import update_reference
from services.github.types.github_types import BaseArgs


@pytest.fixture
def sample_base_args():
    return BaseArgs(
        input_from="github",
        owner_type="Organization",
        owner_id=123456789,
        owner="test-owner",
        repo_id=987654321,
        repo="test-repo",
        clone_url="https://github.com/test-owner/test-repo.git",
        is_fork=False,
        issue_number=1,
        issue_title="Test Issue",
        issue_body="Test issue body",
        issue_comments=[],
        latest_commit_sha="abc123",
        issuer_name="test-user",
        base_branch="main",
        new_branch="feature-branch",
        installation_id=12345678,
        token="test-token",
        sender_id=111222333,
        sender_name="test-sender",
        sender_email="test@example.com",
        is_automation=False,
        reviewers=[],
        github_urls=[],
        other_urls=[]
    )


@pytest.fixture
def mock_requests_patch():
    with patch("services.github.refs.update_reference.requests.patch") as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    with patch("services.github.refs.update_reference.create_headers") as mock:
        mock.return_value = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test-token",
            "User-Agent": "test-app",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        yield mock


def test_update_reference_success(sample_base_args, mock_requests_patch, mock_create_headers):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "def456"
    result = update_reference(sample_base_args, new_commit_sha)
    
    expected_url = f"{GITHUB_API_URL}/repos/test-owner/test-repo/git/refs/heads/feature-branch"
    expected_data = {"sha": new_commit_sha}
    expected_headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": "Bearer test-token",
        "User-Agent": "test-app",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    mock_create_headers.assert_called_once_with(token="test-token")
    mock_requests_patch.assert_called_once_with(
        url=expected_url,
        json=expected_data,
        headers=expected_headers,
        timeout=TIMEOUT
    )
    mock_response.raise_for_status.assert_called_once()
    assert result is None


def test_update_reference_with_different_branch(sample_base_args, mock_requests_patch, mock_create_headers):
    # Create a new BaseArgs with different branch
    modified_args = sample_base_args.copy()
    modified_args.update({"new_branch": "develop"})
    
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "xyz789"
    update_reference(modified_args, new_commit_sha)
    
    expected_url = f"{GITHUB_API_URL}/repos/test-owner/test-repo/git/refs/heads/develop"
    mock_requests_patch.assert_called_once()
    call_args = mock_requests_patch.call_args
    assert call_args[1]["url"] == expected_url
    assert call_args[1]["json"]["sha"] == new_commit_sha


def test_update_reference_with_different_owner_repo(sample_base_args, mock_requests_patch, mock_create_headers):
    # Create a new BaseArgs with different owner and repo
    modified_args = sample_base_args.copy()
    modified_args.update({"owner": "different-owner"})
    modified_args.update({"repo": "different-repo"})
    
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "abc999"
    update_reference(modified_args, new_commit_sha)
    
    expected_url = f"{GITHUB_API_URL}/repos/different-owner/different-repo/git/refs/heads/feature-branch"
    mock_requests_patch.assert_called_once()
    call_args = mock_requests_patch.call_args
    assert call_args[1]["url"] == expected_url


def test_update_reference_with_different_token(sample_base_args, mock_requests_patch, mock_create_headers):
    # Create a new BaseArgs with different token
    modified_args = sample_base_args.copy()
    modified_args.update({"token": "different-token"})
    
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "token123"
    update_reference(modified_args, new_commit_sha)
    
    mock_create_headers.assert_called_once_with(token="different-token")


def test_update_reference_with_long_commit_sha(sample_base_args, mock_requests_patch, mock_create_headers):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "a" * 40  # Full 40-character SHA
    update_reference(sample_base_args, new_commit_sha)
    
    mock_requests_patch.assert_called_once()
    call_args = mock_requests_patch.call_args
    assert call_args[1]["json"]["sha"] == new_commit_sha


def test_update_reference_with_short_commit_sha(sample_base_args, mock_requests_patch, mock_create_headers):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "abc123"  # Short SHA
    update_reference(sample_base_args, new_commit_sha)
    
    mock_requests_patch.assert_called_once()
    call_args = mock_requests_patch.call_args
    assert call_args[1]["json"]["sha"] == new_commit_sha


def test_update_reference_http_error_returns_false(sample_base_args, mock_requests_patch, mock_create_headers):
    mock_response = MagicMock()
    http_error = requests.exceptions.HTTPError("404 Not Found")
    mock_error_response = MagicMock()
    mock_error_response.reason = "Not Found"
    mock_error_response.text = "The requested resource was not found"
    mock_error_response.headers = {"X-RateLimit-Limit": "5000", "X-RateLimit-Remaining": "4999", "X-RateLimit-Used": "1"}
    mock_error_response.status_code = 404
    http_error.response = mock_error_response
    mock_response.raise_for_status.side_effect = http_error
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "error123"
    result = update_reference(sample_base_args, new_commit_sha)
    
    assert result is False


def test_update_reference_connection_error_returns_false(sample_base_args, mock_requests_patch, mock_create_headers):
    # Create a proper ConnectionError
    connection_error = requests.exceptions.ConnectionError("Connection failed")
    # Set side_effect to the exception
    mock_requests_patch.side_effect = connection_error
    
    new_commit_sha = "connection123"
    result = update_reference(sample_base_args, new_commit_sha)
    
    assert result is False


def test_update_reference_timeout_error_returns_false(sample_base_args, mock_requests_patch, mock_create_headers):
    # Create a proper Timeout error
    timeout_error = requests.exceptions.Timeout("Request timed out")
    # Set side_effect to the exception
    mock_requests_patch.side_effect = timeout_error
    
    new_commit_sha = "timeout123"
    result = update_reference(sample_base_args, new_commit_sha)
    
    assert result is False


def test_update_reference_request_exception_returns_false(sample_base_args, mock_requests_patch, mock_create_headers):
    # Create a proper RequestException
    request_exception = requests.exceptions.RequestException("Generic request error")
    # Set side_effect to the exception
    mock_requests_patch.side_effect = request_exception
    
    new_commit_sha = "request123"
    result = update_reference(sample_base_args, new_commit_sha)
    
    assert result is False


def test_update_reference_uses_correct_timeout(sample_base_args, mock_requests_patch, mock_create_headers):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "timeout456"
    update_reference(sample_base_args, new_commit_sha)
    
    mock_requests_patch.assert_called_once()
    call_args = mock_requests_patch.call_args
    assert call_args[1]["timeout"] == TIMEOUT


def test_update_reference_uses_patch_method(sample_base_args, mock_requests_patch, mock_create_headers):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "patch123"
    update_reference(sample_base_args, new_commit_sha)
    
    mock_requests_patch.assert_called_once()


def test_update_reference_sends_json_data(sample_base_args, mock_requests_patch, mock_create_headers):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "json123"
    update_reference(sample_base_args, new_commit_sha)
    
    mock_requests_patch.assert_called_once()
    call_args = mock_requests_patch.call_args
    assert "json" in call_args[1]
    assert call_args[1]["json"] == {"sha": new_commit_sha}


def test_update_reference_calls_raise_for_status(sample_base_args, mock_requests_patch, mock_create_headers):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "status123"
    update_reference(sample_base_args, new_commit_sha)
    
    mock_response.raise_for_status.assert_called_once()


def test_update_reference_with_special_characters_in_branch(sample_base_args, mock_requests_patch, mock_create_headers):
    # Create a new BaseArgs with branch containing special characters
    modified_args = sample_base_args.copy()
    modified_args.update({"new_branch": "feature/fix-bug-123"})
    
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "special123"
    update_reference(modified_args, new_commit_sha)
    
    expected_url = f"{GITHUB_API_URL}/repos/test-owner/test-repo/git/refs/heads/feature/fix-bug-123"
    mock_requests_patch.assert_called_once()
    call_args = mock_requests_patch.call_args
    assert call_args[1]["url"] == expected_url


def test_update_reference_with_unicode_characters_in_branch(sample_base_args, mock_requests_patch, mock_create_headers):
    # Create a new BaseArgs with branch containing unicode characters
    modified_args = sample_base_args.copy()
    modified_args.update({"new_branch": "feature-测试"})
    
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "unicode123"
    update_reference(modified_args, new_commit_sha)
    
    expected_url = f"{GITHUB_API_URL}/repos/test-owner/test-repo/git/refs/heads/feature-测试"
    mock_requests_patch.assert_called_once()
    call_args = mock_requests_patch.call_args
    assert call_args[1]["url"] == expected_url


def test_update_reference_with_empty_commit_sha(sample_base_args, mock_requests_patch, mock_create_headers):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = ""  # Empty SHA
    update_reference(sample_base_args, new_commit_sha)
    
    mock_requests_patch.assert_called_once()
    call_args = mock_requests_patch.call_args
    assert call_args[1]["json"]["sha"] == ""


def test_update_reference_with_numeric_commit_sha(sample_base_args, mock_requests_patch, mock_create_headers):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "1234567890abcdef"  # Numeric and hex characters
    update_reference(sample_base_args, new_commit_sha)
    
    mock_requests_patch.assert_called_once()
    call_args = mock_requests_patch.call_args
    assert call_args[1]["json"]["sha"] == new_commit_sha


def test_update_reference_rate_limit_error_returns_false(sample_base_args, mock_requests_patch, mock_create_headers):
    mock_response = MagicMock()
    http_error = requests.exceptions.HTTPError("403 Forbidden")
    mock_error_response = MagicMock()
    mock_error_response.reason = "Forbidden"
    mock_error_response.text = "API rate limit exceeded"
    mock_error_response.headers = {
        "X-RateLimit-Limit": "5000", 
        "X-RateLimit-Remaining": "0", 
        "X-RateLimit-Used": "5000",
        "X-RateLimit-Reset": str(int(time.time()) + 3600)  # 1 hour from now
    }
    mock_error_response.status_code = 403
    http_error.response = mock_error_response
    mock_response.raise_for_status.side_effect = http_error
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "ratelimit123"
    result = update_reference(sample_base_args, new_commit_sha)
    
    assert result is False


def test_update_reference_unauthorized_error_returns_false(sample_base_args, mock_requests_patch, mock_create_headers):
    mock_response = MagicMock()
    http_error = requests.exceptions.HTTPError("401 Unauthorized")
    mock_error_response = MagicMock()
    mock_error_response.reason = "Unauthorized"
    mock_error_response.text = "Bad credentials"
    mock_error_response.headers = {"X-RateLimit-Limit": "5000", "X-RateLimit-Remaining": "4999", "X-RateLimit-Used": "1"}
    mock_error_response.status_code = 401
    http_error.response = mock_error_response
    mock_response.raise_for_status.side_effect = http_error
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "unauthorized123"
    result = update_reference(sample_base_args, new_commit_sha)
    
    assert result is False


def test_update_reference_server_error_returns_false(sample_base_args, mock_requests_patch, mock_create_headers):
    mock_response = MagicMock()
    http_error = requests.exceptions.HTTPError("500 Internal Server Error")
    mock_error_response = MagicMock()
    mock_error_response.reason = "Internal Server Error"
    mock_error_response.text = "Server error occurred"
    mock_error_response.headers = {"X-RateLimit-Limit": "5000", "X-RateLimit-Remaining": "4999", "X-RateLimit-Used": "1"}
    mock_error_response.status_code = 500
    http_error.response = mock_error_response
    mock_response.raise_for_status.side_effect = http_error
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "server123"
    result = update_reference(sample_base_args, new_commit_sha)
    
    assert result is False


def test_update_reference_json_decode_error_returns_false(sample_base_args, mock_requests_patch, mock_create_headers):
    import json
    json_error = json.JSONDecodeError("Invalid JSON", "invalid json", 0)
    mock_requests_patch.side_effect = json_error
    
    new_commit_sha = "json_error123"
    result = update_reference(sample_base_args, new_commit_sha)
    
    assert result is False


def test_update_reference_attribute_error_returns_false(sample_base_args, mock_requests_patch, mock_create_headers):
    attribute_error = AttributeError("'NoneType' object has no attribute 'patch'")
    mock_requests_patch.side_effect = attribute_error
    
    new_commit_sha = "attr_error123"
    result = update_reference(sample_base_args, new_commit_sha)
    
    assert result is False


def test_update_reference_key_error_returns_false(sample_base_args, mock_requests_patch, mock_create_headers):
    key_error = KeyError("missing_key")
    mock_requests_patch.side_effect = key_error
    
    new_commit_sha = "key_error123"
    result = update_reference(sample_base_args, new_commit_sha)
    
    assert result is False


def test_update_reference_type_error_returns_false(sample_base_args, mock_requests_patch, mock_create_headers):
    type_error = TypeError("unsupported operand type(s)")
    mock_requests_patch.side_effect = type_error
    
    new_commit_sha = "type_error123"
    result = update_reference(sample_base_args, new_commit_sha)
    
    assert result is False


def test_update_reference_generic_exception_returns_false(sample_base_args, mock_requests_patch, mock_create_headers):
    generic_error = Exception("Generic error occurred")
    mock_requests_patch.side_effect = generic_error
    
    new_commit_sha = "generic_error123"
    result = update_reference(sample_base_args, new_commit_sha)
    
    assert result is False


@pytest.mark.parametrize("commit_sha", [
    "a1b2c3d4e5f6",  # Short SHA
    "a1b2c3d4e5f67890abcdef1234567890abcdef12",  # Full 40-character SHA
    "0123456789abcdef0123456789abcdef01234567",  # All hex characters
    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",  # All same character
    "1234567890123456789012345678901234567890",  # All numbers (valid hex)
])
def test_update_reference_with_various_commit_sha_formats(sample_base_args, mock_requests_patch, mock_create_headers, commit_sha):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    update_reference(sample_base_args, commit_sha)
    
    mock_requests_patch.assert_called_once()
    call_args = mock_requests_patch.call_args
    assert call_args[1]["json"]["sha"] == commit_sha


@pytest.mark.parametrize("branch_name", [
    "main",
    "develop", 
    "feature/new-feature",
    "hotfix/urgent-fix",
    "release/v1.0.0",
    "bugfix/issue-123",
    "feature_branch_with_underscores",
    "branch-with-dashes",
    "UPPERCASE_BRANCH",
    "mixed_Case_Branch",
])
def test_update_reference_with_various_branch_names(sample_base_args, mock_requests_patch, mock_create_headers, branch_name):
    modified_args = sample_base_args.copy()
    modified_args.update({"new_branch": branch_name})
    
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "branch_test123"
    update_reference(modified_args, new_commit_sha)
    
    expected_url = f"{GITHUB_API_URL}/repos/test-owner/test-repo/git/refs/heads/{branch_name}"
    mock_requests_patch.assert_called_once()
    call_args = mock_requests_patch.call_args
    assert call_args[1]["url"] == expected_url


@pytest.mark.parametrize("status_code,reason,text", [
    (400, "Bad Request", "Invalid request"),
    (401, "Unauthorized", "Bad credentials"),
    (403, "Forbidden", "Access denied"),
    (404, "Not Found", "Repository not found"),
    (409, "Conflict", "Reference already exists"),
    (422, "Unprocessable Entity", "Validation failed"),
    (500, "Internal Server Error", "Server error"),
    (502, "Bad Gateway", "Bad gateway"),
    (503, "Service Unavailable", "Service unavailable"),
])
def test_update_reference_various_http_errors_return_false(sample_base_args, mock_requests_patch, mock_create_headers, status_code, reason, text):
    mock_response = MagicMock()
    http_error = requests.exceptions.HTTPError(f"{status_code} {reason}")
    mock_error_response = MagicMock()
    mock_error_response.reason = reason
    mock_error_response.text = text
    mock_error_response.headers = {"X-RateLimit-Limit": "5000", "X-RateLimit-Remaining": "4999", "X-RateLimit-Used": "1"}
    mock_error_response.status_code = status_code
    http_error.response = mock_error_response
    mock_response.raise_for_status.side_effect = http_error
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = f"error_{status_code}"
    result = update_reference(sample_base_args, new_commit_sha)
    
    assert result is False


def test_update_reference_extracts_correct_values_from_base_args(sample_base_args, mock_requests_patch, mock_create_headers):
    # Test that the function correctly extracts values from BaseArgs
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "extract_test123"
    update_reference(sample_base_args, new_commit_sha)
    
    # Verify that create_headers was called with the token from base_args
    mock_create_headers.assert_called_once_with(token=sample_base_args["token"])
    
    # Verify the URL construction uses correct values from base_args
    expected_url = f"{GITHUB_API_URL}/repos/{sample_base_args['owner']}/{sample_base_args['repo']}/git/refs/heads/{sample_base_args['new_branch']}"
    mock_requests_patch.assert_called_once()
    call_args = mock_requests_patch.call_args
    assert call_args[1]["url"] == expected_url


def test_update_reference_preserves_request_structure(sample_base_args, mock_requests_patch, mock_create_headers):
    # Test that the request structure matches GitHub API expectations
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "structure_test123"
    update_reference(sample_base_args, new_commit_sha)
    
    mock_requests_patch.assert_called_once()
    call_args = mock_requests_patch.call_args
    
    # Verify all required parameters are present
    assert "url" in call_args[1]
    assert "json" in call_args[1]
    assert "headers" in call_args[1]
    assert "timeout" in call_args[1]
    
    # Verify the JSON payload structure
    json_payload = call_args[1]["json"]
    assert isinstance(json_payload, dict)
    assert "sha" in json_payload
    assert json_payload["sha"] == new_commit_sha
    assert len(json_payload) == 1  # Only 'sha' should be in the payload
