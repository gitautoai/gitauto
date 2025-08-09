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
    sample_base_args["new_branch"] = "develop"
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "xyz789"
    update_reference(sample_base_args, new_commit_sha)
    
    expected_url = f"{GITHUB_API_URL}/repos/test-owner/test-repo/git/refs/heads/develop"
    mock_requests_patch.assert_called_once()
    call_args = mock_requests_patch.call_args
    assert call_args[1]["url"] == expected_url
    assert call_args[1]["json"]["sha"] == new_commit_sha


def test_update_reference_with_different_owner_repo(sample_base_args, mock_requests_patch, mock_create_headers):
    sample_base_args["owner"] = "different-owner"
    sample_base_args["repo"] = "different-repo"
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "abc999"
    update_reference(sample_base_args, new_commit_sha)
    
    expected_url = f"{GITHUB_API_URL}/repos/different-owner/different-repo/git/refs/heads/feature-branch"
    mock_requests_patch.assert_called_once()
    call_args = mock_requests_patch.call_args
    assert call_args[1]["url"] == expected_url


def test_update_reference_with_different_token(sample_base_args, mock_requests_patch, mock_create_headers):
    sample_base_args["token"] = "different-token"
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "token123"
    update_reference(sample_base_args, new_commit_sha)
    
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
    mock_error_response.status_code = 404
    http_error.response = mock_error_response
    mock_response.raise_for_status.side_effect = http_error
    mock_requests_patch.return_value = mock_response
    
    new_commit_sha = "error123"
    result = update_reference(sample_base_args, new_commit_sha)
    
    assert result is False


def test_update_reference_connection_error_returns_false(sample_base_args, mock_requests_patch, mock_create_headers):
    mock_requests_patch.side_effect = requests.exceptions.ConnectionError("Connection failed")
    
    new_commit_sha = "connection123"
    result = update_reference(sample_base_args, new_commit_sha)
    
    assert result is False


def test_update_reference_timeout_error_returns_false(sample_base_args, mock_requests_patch, mock_create_headers):
    mock_requests_patch.side_effect = requests.exceptions.Timeout("Request timed out")
    
    new_commit_sha = "timeout123"
    result = update_reference(sample_base_args, new_commit_sha)
    
    assert result is False


def test_update_reference_request_exception_returns_false(sample_base_args, mock_requests_patch, mock_create_headers):
    mock_requests_patch.side_effect = requests.exceptions.RequestException("Generic request error")
    
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
