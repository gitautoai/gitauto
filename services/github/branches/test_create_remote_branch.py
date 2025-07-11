from unittest.mock import patch, MagicMock
import pytest
import requests
from services.github.branches.create_remote_branch import create_remote_branch
from services.github.types.github_types import BaseArgs


@pytest.fixture
def mock_requests_post():
    """Fixture to mock requests.post for successful API calls."""
    with patch("services.github.branches.create_remote_branch.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def mock_create_headers():
    """Fixture to mock create_headers function."""
    with patch("services.github.branches.create_remote_branch.create_headers") as mock_headers:
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
def sample_sha():
    """Fixture providing a sample SHA for testing."""
    return "abc123def456789"


def test_create_remote_branch_success(mock_requests_post, mock_create_headers, sample_base_args, sample_sha):
    """Test successful creation of a remote branch."""
    result = create_remote_branch(sha=sample_sha, base_args=sample_base_args)
    
    # Verify the function returns None on success
    assert result is None
    
    # Verify requests.post was called with correct parameters
    mock_requests_post.assert_called_once_with(
        url="https://api.github.com/repos/test_owner/test_repo/git/refs",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"ref": "refs/heads/feature/test-branch", "sha": "abc123def456789"},
        timeout=120,
    )
    
    # Verify create_headers was called with the token
    mock_create_headers.assert_called_once_with(token="test_token_123")
    
    # Verify raise_for_status was called
    mock_requests_post.return_value.raise_for_status.assert_called_once()


def test_create_remote_branch_with_different_branch_names(mock_requests_post, mock_create_headers, sample_sha):
    """Test branch creation with various branch name formats."""
    test_cases = [
        "main",
        "develop",
        "feature/new-feature",
        "bugfix/fix-123",
        "hotfix/urgent-fix",
        "release/v1.0.0",
        "feature_branch_with_underscores",
        "branch-with-dashes",
    ]
    
    for branch_name in test_cases:
        base_args = BaseArgs(
            owner="test_owner",
            repo="test_repo", 
            new_branch=branch_name,
            token="test_token"
        )
        
        result = create_remote_branch(sha=sample_sha, base_args=base_args)
        assert result is None
        
        # Verify the ref format is correct
        call_args = mock_requests_post.call_args
        expected_ref = f"refs/heads/{branch_name}"
        assert call_args[1]["json"]["ref"] == expected_ref


def test_create_remote_branch_with_different_shas(mock_requests_post, mock_create_headers, sample_base_args):
    """Test branch creation with various SHA formats."""
    test_shas = [
        "abc123",
        "1234567890abcdef",
        "a1b2c3d4e5f6789012345678901234567890abcd",
        "0123456789abcdef0123456789abcdef01234567",
    ]
    
    for sha in test_shas:
        result = create_remote_branch(sha=sha, base_args=sample_base_args)
        assert result is None
        
        # Verify the SHA is passed correctly
        call_args = mock_requests_post.call_args
        assert call_args[1]["json"]["sha"] == sha


def test_create_remote_branch_http_error_handled(mock_create_headers, sample_base_args, sample_sha):
    """Test that HTTP errors are handled by the decorator."""
    with patch("services.github.branches.create_remote_branch.requests.post") as mock_post:
        # Mock an HTTP error response
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_post.return_value = mock_response
        
        # The function should return None due to handle_exceptions decorator
        result = create_remote_branch(sha=sample_sha, base_args=sample_base_args)
        assert result is None
        
        # Verify the request was still made
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()


def test_create_remote_branch_request_timeout_handled(mock_create_headers, sample_base_args, sample_sha):
    """Test that request timeout is handled by the decorator."""
    with patch("services.github.branches.create_remote_branch.requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
        
        # The function should return None due to handle_exceptions decorator
        result = create_remote_branch(sha=sample_sha, base_args=sample_base_args)
        assert result is None
        
        # Verify the request was attempted
        mock_post.assert_called_once()


def test_create_remote_branch_connection_error_handled(mock_create_headers, sample_base_args, sample_sha):
    """Test that connection errors are handled by the decorator."""
    with patch("services.github.branches.create_remote_branch.requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        # The function should return None due to handle_exceptions decorator
        result = create_remote_branch(sha=sample_sha, base_args=sample_base_args)
        assert result is None
        
        # Verify the request was attempted
        mock_post.assert_called_once()


def test_create_remote_branch_uses_correct_api_url(mock_requests_post, mock_create_headers, sample_base_args, sample_sha):
    """Test that the correct GitHub API URL is used."""
    create_remote_branch(sha=sample_sha, base_args=sample_base_args)
    
    call_args = mock_requests_post.call_args
    expected_url = "https://api.github.com/repos/test_owner/test_repo/git/refs"
    assert call_args[1]["url"] == expected_url


def test_create_remote_branch_uses_correct_timeout(mock_requests_post, mock_create_headers, sample_base_args, sample_sha):
    """Test that the correct timeout value is used."""
    create_remote_branch(sha=sample_sha, base_args=sample_base_args)
    
    call_args = mock_requests_post.call_args
    assert call_args[1]["timeout"] == 120


def test_create_remote_branch_json_payload_structure(mock_requests_post, mock_create_headers, sample_base_args, sample_sha):
    """Test that the JSON payload has the correct structure."""
    create_remote_branch(sha=sample_sha, base_args=sample_base_args)
    
    call_args = mock_requests_post.call_args
    json_payload = call_args[1]["json"]
    
    # Verify payload structure
    assert "ref" in json_payload
    assert "sha" in json_payload
    assert len(json_payload) == 2
    
    # Verify payload values
    assert json_payload["ref"] == "refs/heads/feature/test-branch"
    assert json_payload["sha"] == sample_sha


def test_create_remote_branch_with_special_characters_in_owner_repo(mock_requests_post, mock_create_headers, sample_sha):
    """Test branch creation with special characters in owner and repo names."""
    base_args = BaseArgs(
        owner="test-owner_123",
        repo="test.repo-name_456",
        new_branch="feature/test",
        token="test_token"
    )
    
    result = create_remote_branch(sha=sample_sha, base_args=base_args)
    assert result is None
    
    call_args = mock_requests_post.call_args
    expected_url = "https://api.github.com/repos/test-owner_123/test.repo-name_456/git/refs"
    assert call_args[1]["url"] == expected_url


def test_create_remote_branch_extracts_base_args_correctly(mock_requests_post, mock_create_headers, sample_sha):
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
    
    create_remote_branch(sha=sample_sha, base_args=base_args)
    
    # Verify only the required fields were used
    call_args = mock_requests_post.call_args
    assert "extracted_owner" in call_args[1]["url"]
    assert "extracted_repo" in call_args[1]["url"]
    assert call_args[1]["json"]["ref"] == "refs/heads/extracted/branch"
    
    # Verify create_headers was called with the extracted token
    mock_create_headers.assert_called_once_with(token="extracted_token")
