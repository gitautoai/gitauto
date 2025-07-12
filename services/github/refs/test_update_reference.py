# pylint: disable=redefined-outer-name

# Standard imports
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest
import requests

# Local imports
from services.github.refs.update_reference import update_reference
from services.github.types.github_types import BaseArgs


@pytest.fixture
def mock_requests_patch():
    """Fixture to mock requests.patch for successful API calls."""
    with patch("services.github.refs.update_reference.requests.patch") as mock_patch:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_patch.return_value = mock_response
        yield mock_patch


@pytest.fixture
def mock_create_headers():
    """Fixture to mock create_headers function."""
    with patch("services.github.refs.update_reference.create_headers") as mock_headers:
        mock_headers.return_value = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        yield mock_headers


@pytest.fixture
def sample_base_args():
    """Fixture providing sample BaseArgs for testing."""
    return BaseArgs(
        owner="test_owner",
        repo="test_repo",
        new_branch="feature/test-branch",
        token="test_token_123"
    )


@pytest.fixture
def sample_commit_sha():
    """Fixture providing a sample commit SHA for testing."""
    return "abc123def456789012345678901234567890abcd"


def test_update_reference_success(mock_requests_patch, mock_create_headers, sample_base_args, sample_commit_sha):
    """Test successful update of a Git reference."""
    result = update_reference(base_args=sample_base_args, new_commit_sha=sample_commit_sha)
    
    # Verify the function returns None on success (no explicit return)
    assert result is None
    
    # Verify requests.patch was called with correct parameters
    mock_requests_patch.assert_called_once_with(
        url="https://api.github.com/repos/test_owner/test_repo/git/refs/heads/feature/test-branch",
        json={"sha": "abc123def456789012345678901234567890abcd"},
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=120,
    )
    
    # Verify create_headers was called with the token
    mock_create_headers.assert_called_once_with(token="test_token_123")
    
    # Verify raise_for_status was called
    mock_requests_patch.return_value.raise_for_status.assert_called_once()


def test_update_reference_with_different_branch_names(mock_requests_patch, mock_create_headers, sample_commit_sha):
    """Test reference update with various branch name formats."""
    test_cases = [
        "main",
        "develop",
        "feature/new-feature",
        "bugfix/fix-123",
        "hotfix/urgent-fix",
        "release/v1.0.0",
        "feature_branch_with_underscores",
        "branch-with-dashes",
        "123-numeric-start",
        "UPPERCASE-BRANCH",
    ]
    
    for branch_name in test_cases:
        mock_requests_patch.reset_mock()
        mock_create_headers.reset_mock()
        
        base_args = BaseArgs(
            owner="test_owner",
            repo="test_repo", 
            new_branch=branch_name,
            token="test_token"
        )
        
        result = update_reference(base_args=base_args, new_commit_sha=sample_commit_sha)
        assert result is None
        
        # Verify the URL contains the correct branch name
        call_args = mock_requests_patch.call_args
        expected_url = f"https://api.github.com/repos/test_owner/test_repo/git/refs/heads/{branch_name}"
        assert call_args[1]["url"] == expected_url


def test_update_reference_with_different_commit_shas(mock_requests_patch, mock_create_headers, sample_base_args):
    """Test reference update with various commit SHA formats."""
    test_shas = [
        "abc123",
        "1234567890abcdef",
        "a1b2c3d4e5f6789012345678901234567890abcd",
        "0123456789abcdef0123456789abcdef01234567",
        "f" * 40,  # 40 character SHA
        "short",  # Short SHA
        "mixed123ABC456def",  # Mixed case
    ]
    
    for sha in test_shas:
        mock_requests_patch.reset_mock()
        mock_create_headers.reset_mock()
        
        result = update_reference(base_args=sample_base_args, new_commit_sha=sha)
        assert result is None
        
        # Verify the SHA is passed correctly in the JSON payload
        call_args = mock_requests_patch.call_args
        assert call_args[1]["json"]["sha"] == sha


def test_update_reference_http_error_handled(mock_create_headers, sample_base_args, sample_commit_sha):
    """Test that HTTP errors are handled by the decorator."""
    with patch("services.github.refs.update_reference.requests.patch") as mock_patch:
        # Mock an HTTP error response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Reference not found"
        
        http_error = requests.exceptions.HTTPError("404 Not Found")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_patch.return_value = mock_response
        
        # The function should return False due to handle_exceptions decorator
        result = update_reference(base_args=sample_base_args, new_commit_sha=sample_commit_sha)
        assert result is False
        
        # Verify the request was still made
        mock_patch.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_update_reference_422_unprocessable_entity_handled(mock_create_headers, sample_base_args, sample_commit_sha):
    """Test that 422 Unprocessable Entity errors are handled by the decorator."""
    with patch("services.github.refs.update_reference.requests.patch") as mock_patch:
        # Mock a 422 error response (common when SHA doesn't exist)
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.reason = "Unprocessable Entity"
        mock_response.text = "Object does not exist"
        
        http_error = requests.exceptions.HTTPError("422 Unprocessable Entity")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_patch.return_value = mock_response
        
        # The function should return False due to handle_exceptions decorator
        result = update_reference(base_args=sample_base_args, new_commit_sha=sample_commit_sha)
        assert result is False
        
        # Verify the request was still made
        mock_patch.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_update_reference_request_timeout_handled(mock_create_headers, sample_base_args, sample_commit_sha):
    """Test that request timeout is handled by the decorator."""
    with patch("services.github.refs.update_reference.requests.patch") as mock_patch:
        mock_patch.side_effect = requests.exceptions.Timeout("Request timed out")
        
        # The function should return False due to handle_exceptions decorator
        result = update_reference(base_args=sample_base_args, new_commit_sha=sample_commit_sha)
        assert result is False
        
        # Verify the request was attempted
        mock_patch.assert_called_once()


def test_update_reference_connection_error_handled(mock_create_headers, sample_base_args, sample_commit_sha):
    """Test that connection errors are handled by the decorator."""
    with patch("services.github.refs.update_reference.requests.patch") as mock_patch:
        mock_patch.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        # The function should return False due to handle_exceptions decorator
        result = update_reference(base_args=sample_base_args, new_commit_sha=sample_commit_sha)
        assert result is False
        
        # Verify the request was attempted
        mock_patch.assert_called_once()


def test_update_reference_uses_correct_api_url(mock_requests_patch, mock_create_headers, sample_base_args, sample_commit_sha):
    """Test that the correct GitHub API URL is used."""
    update_reference(base_args=sample_base_args, new_commit_sha=sample_commit_sha)
    
    call_args = mock_requests_patch.call_args
    expected_url = "https://api.github.com/repos/test_owner/test_repo/git/refs/heads/feature/test-branch"
    assert call_args[1]["url"] == expected_url


def test_update_reference_uses_correct_timeout(mock_requests_patch, mock_create_headers, sample_base_args, sample_commit_sha):
    """Test that the correct timeout value is used."""
    update_reference(base_args=sample_base_args, new_commit_sha=sample_commit_sha)
    
    call_args = mock_requests_patch.call_args
    assert call_args[1]["timeout"] == 120


def test_update_reference_json_payload_structure(mock_requests_patch, mock_create_headers, sample_base_args, sample_commit_sha):
    """Test that the JSON payload has the correct structure."""
    update_reference(base_args=sample_base_args, new_commit_sha=sample_commit_sha)
    
    call_args = mock_requests_patch.call_args
    json_payload = call_args[1]["json"]
    
    # Verify payload structure
    assert "sha" in json_payload
    assert len(json_payload) == 1
    
    # Verify payload values
    assert json_payload["sha"] == sample_commit_sha


def test_update_reference_with_special_characters_in_owner_repo(mock_requests_patch, mock_create_headers, sample_commit_sha):
    """Test reference update with special characters in owner and repo names."""
    base_args = BaseArgs(
        owner="test-owner_123",
        repo="test.repo-name_456",
        new_branch="feature/test",
        token="test_token"
    )
    
    result = update_reference(base_args=base_args, new_commit_sha=sample_commit_sha)
    assert result is None
    
    call_args = mock_requests_patch.call_args
    expected_url = "https://api.github.com/repos/test-owner_123/test.repo-name_456/git/refs/heads/feature/test"
    assert call_args[1]["url"] == expected_url


def test_update_reference_extracts_base_args_correctly(mock_requests_patch, mock_create_headers, sample_commit_sha):
    """Test that BaseArgs values are extracted correctly."""
    base_args = BaseArgs(
        owner="extracted_owner",
        repo="extracted_repo", 
        new_branch="extracted/branch",
        token="extracted_token",
        # Include other fields that should be ignored
        issue_number=123,
        sender_name="test_sender"
    )
    
    update_reference(base_args=base_args, new_commit_sha=sample_commit_sha)
    
    # Verify only the required fields were used
    call_args = mock_requests_patch.call_args
    assert "extracted_owner" in call_args[1]["url"]
    assert "extracted_repo" in call_args[1]["url"]
    assert "extracted/branch" in call_args[1]["url"]
    
    # Verify create_headers was called with the extracted token
    mock_create_headers.assert_called_once_with(token="extracted_token")


def test_update_reference_with_monkeypatch(monkeypatch, sample_base_args, sample_commit_sha):
    """Test using monkeypatch for configuration values."""
    # Mock configuration values
    monkeypatch.setattr("services.github.refs.update_reference.GITHUB_API_URL", "https://test.api.github.com")
    monkeypatch.setattr("services.github.refs.update_reference.TIMEOUT", 60)
    
    with patch("services.github.refs.update_reference.requests.patch") as mock_patch, \
         patch("services.github.refs.update_reference.create_headers") as mock_headers:
        
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_patch.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test"}
        
        result = update_reference(base_args=sample_base_args, new_commit_sha=sample_commit_sha)
        assert result is None
        
        # Verify the mocked URL and timeout were used
        call_args = mock_patch.call_args
        assert "https://test.api.github.com" in call_args[1]["url"]
        assert call_args[1]["timeout"] == 60


def test_update_reference_with_empty_values(mock_requests_patch, mock_create_headers):
    """Test behavior with empty or minimal values."""
    base_args = BaseArgs(
        owner="",
        repo="",
        new_branch="",
        token=""
    )
    
    result = update_reference(base_args=base_args, new_commit_sha="")
    assert result is None
    
    # Verify the function still makes the request even with empty values
    mock_requests_patch.assert_called_once()
    call_args = mock_requests_patch.call_args
    assert call_args[1]["json"]["sha"] == ""
    assert call_args[1]["url"] == "https://api.github.com/repos///git/refs/heads/"


@pytest.mark.parametrize("error_type,error_message", [
    (requests.exceptions.Timeout, "Timeout Error"),
    (requests.exceptions.ConnectionError, "Connection Error"),
    (requests.exceptions.RequestException, "Request Error"),
    (ValueError, "Value Error"),
    (KeyError, "Key Error"),
])
def test_update_reference_handles_various_exceptions(mock_create_headers, sample_base_args, sample_commit_sha, error_type, error_message):
    """Test that various exception types are handled by the decorator."""
    with patch("services.github.refs.update_reference.requests.patch") as mock_patch:
        mock_patch.side_effect = error_type(error_message)
        
        # The function should return False due to handle_exceptions decorator
        result = update_reference(base_args=sample_base_args, new_commit_sha=sample_commit_sha)
        assert result is False
        
        # Verify the request was attempted
        mock_patch.assert_called_once()


def test_update_reference_handles_http_error_exception(mock_create_headers, sample_base_args, sample_commit_sha):
    """Test that HTTPError is handled by the decorator with proper response object."""
    with patch("services.github.refs.update_reference.requests.patch") as mock_patch:
        # Create a proper HTTPError with response object
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "HTTP Error"
        http_error = requests.exceptions.HTTPError("HTTP Error")
        http_error.response = mock_response
        mock_patch.side_effect = http_error
        
        # The function should return False due to handle_exceptions decorator
        result = update_reference(base_args=sample_base_args, new_commit_sha=sample_commit_sha)
        assert result is False
        
        # Verify the request was attempted
        mock_patch.assert_called_once()


def test_update_reference_api_endpoint_structure(mock_requests_patch, mock_create_headers, sample_base_args, sample_commit_sha):
    """Test that the API endpoint follows GitHub's expected structure."""
    update_reference(base_args=sample_base_args, new_commit_sha=sample_commit_sha)
    
    call_args = mock_requests_patch.call_args
    url = call_args[1]["url"]
    
    # Verify URL structure matches GitHub API pattern
    assert url.startswith("https://api.github.com/repos/")
    assert "/git/refs/heads/" in url
    assert "/test_owner/test_repo/" in url


def test_update_reference_request_method_and_headers(mock_requests_patch, mock_create_headers, sample_base_args, sample_commit_sha):
    """Test that the correct HTTP method and headers are used."""
    update_reference(base_args=sample_base_args, new_commit_sha=sample_commit_sha)
    
    # Verify PATCH method was used (implicit in requests.patch call)
    mock_requests_patch.assert_called_once()
    
    # Verify headers were set correctly
    call_args = mock_requests_patch.call_args
    assert "headers" in call_args[1]
    
    # Verify create_headers was called
    mock_create_headers.assert_called_once_with(token="test_token_123")


def test_update_reference_url_format_consistency(mock_requests_patch, mock_create_headers, sample_commit_sha):
    """Test that the URL format is consistently correct for different inputs."""
    test_cases = [
        ("owner1", "repo1", "branch1", "https://api.github.com/repos/owner1/repo1/git/refs/heads/branch1"),
        ("my-org", "my-repo", "feature/test", "https://api.github.com/repos/my-org/my-repo/git/refs/heads/feature/test"),
        ("user_123", "repo.name", "hotfix/v1.2.3", "https://api.github.com/repos/user_123/repo.name/git/refs/heads/hotfix/v1.2.3"),
    ]
    
    for owner, repo, branch, expected_url in test_cases:
        mock_requests_patch.reset_mock()
        
        base_args = BaseArgs(
            owner=owner,
            repo=repo,
            new_branch=branch,
            token="test_token"
        )
        
        update_reference(base_args=base_args, new_commit_sha=sample_commit_sha)
        
        call_args = mock_requests_patch.call_args
        assert call_args[1]["url"] == expected_url
