# Standard imports
from unittest import mock

# Third party imports
import pytest
import requests

# Local imports
from config import GITHUB_APP_IDS
from services.github.comments.get_comments import get_comments
from services.github.github_types import BaseArgs
from tests.constants import OWNER, REPO, TOKEN


def test_get_comments_happy_path():
    # Arrange
    issue_number = 123
    base_args: BaseArgs = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "input_from": "github",
        "owner_type": "organization",
        "owner_id": 123456,
        "repo_id": 789012,
        "clone_url": "https://github.com/gitautoai/gitauto.git",
        "is_fork": False,
        "issue_number": issue_number,
        "issue_title": "Test Issue",
        "issue_body": "Test Body",
        "issue_comments": [],
        "latest_commit_sha": "abc123",
        "comment_url": None,
        "issuer_name": "testuser",
        "base_branch": "main",
        "new_branch": "test-branch",
        "installation_id": 12345,
        "sender_id": 67890,
        "sender_name": "sender",
        "sender_email": "sender@example.com",
        "is_automation": False,
        "reviewers": [],
        "github_urls": [],
        "other_urls": [],
        "pr_body": ""
    }
    
    mock_response = mock.Mock()
    mock_response.json.return_value = [
        {"body": "Comment 1", "performed_via_github_app": None},
        {"body": "Comment 2", "performed_via_github_app": None}
    ]
    mock_response.raise_for_status.return_value = None
    
    # Act
    with mock.patch('requests.get', return_value=mock_response):
        result = get_comments(issue_number, base_args)
    
    # Assert
    assert result == ["Comment 1", "Comment 2"]
    assert len(result) == 2


def test_get_comments_with_includes_me_true():
    # Arrange
    issue_number = 123
    base_args: BaseArgs = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "input_from": "github",
        "owner_type": "organization",
        "owner_id": 123456,
        "repo_id": 789012,
        "clone_url": "https://github.com/gitautoai/gitauto.git",
        "is_fork": False,
        "issue_number": issue_number,
        "issue_title": "Test Issue",
        "issue_body": "Test Body",
        "issue_comments": [],
        "latest_commit_sha": "abc123",
        "comment_url": None,
        "issuer_name": "testuser",
        "base_branch": "main",
        "new_branch": "test-branch",
        "installation_id": 12345,
        "sender_id": 67890,
        "sender_name": "sender",
        "sender_email": "sender@example.com",
        "is_automation": False,
        "reviewers": [],
        "github_urls": [],
        "other_urls": [],
        "pr_body": ""
    }
    
    # Create a response with both app comments and regular comments
    mock_response = mock.Mock()
    mock_response.json.return_value = [
        {"body": "Comment 1", "performed_via_github_app": None},
        {"body": "Comment 2", "performed_via_github_app": {"id": GITHUB_APP_IDS[0]}},
        {"body": "Comment 3", "performed_via_github_app": {"id": 999999}}  # Not in GITHUB_APP_IDS
    ]
    mock_response.raise_for_status.return_value = None
    
    # Act
    with mock.patch('requests.get', return_value=mock_response):
        result = get_comments(issue_number, base_args, includes_me=True)
    
    # Assert
    assert result == ["Comment 1", "Comment 2", "Comment 3"]
    assert len(result) == 3


def test_get_comments_with_includes_me_false():
    # Arrange
    issue_number = 123
    base_args: BaseArgs = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "input_from": "github",
        "owner_type": "organization",
        "owner_id": 123456,
        "repo_id": 789012,
        "clone_url": "https://github.com/gitautoai/gitauto.git",
        "is_fork": False,
        "issue_number": issue_number,
        "issue_title": "Test Issue",
        "issue_body": "Test Body",
        "issue_comments": [],
        "latest_commit_sha": "abc123",
        "comment_url": None,
        "issuer_name": "testuser",
        "base_branch": "main",
        "new_branch": "test-branch",
        "installation_id": 12345,
        "sender_id": 67890,
        "sender_name": "sender",
        "sender_email": "sender@example.com",
        "is_automation": False,
        "reviewers": [],
        "github_urls": [],
        "other_urls": [],
        "pr_body": ""
    }
    
    # Create a response with both app comments and regular comments
    mock_response = mock.Mock()
    mock_response.json.return_value = [
        {"body": "Comment 1", "performed_via_github_app": None},
        {"body": "Comment 2", "performed_via_github_app": {"id": GITHUB_APP_IDS[0]}},
        {"body": "Comment 3", "performed_via_github_app": {"id": 999999}}  # Not in GITHUB_APP_IDS
    ]
    mock_response.raise_for_status.return_value = None
    
    # Act
    with mock.patch('requests.get', return_value=mock_response):
        result = get_comments(issue_number, base_args, includes_me=False)
    
    # Assert
    assert result == ["Comment 1", "Comment 3"]
    assert len(result) == 2
    assert "Comment 2" not in result


def test_get_comments_http_error():
    # Arrange
    issue_number = 123
    base_args: BaseArgs = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "input_from": "github",
        "owner_type": "organization",
        "owner_id": 123456,
        "repo_id": 789012,
        "clone_url": "https://github.com/gitautoai/gitauto.git",
        "is_fork": False,
        "issue_number": issue_number,
        "issue_title": "Test Issue",
        "issue_body": "Test Body",
        "issue_comments": [],
        "latest_commit_sha": "abc123",
        "comment_url": None,
        "issuer_name": "testuser",
        "base_branch": "main",
        "new_branch": "test-branch",
        "installation_id": 12345,
        "sender_id": 67890,
        "sender_name": "sender",
        "sender_email": "sender@example.com",
        "is_automation": False,
        "reviewers": [],
        "github_urls": [],
        "other_urls": [],
        "pr_body": ""
    }
    
    # Create a mock HTTP error
    mock_response = mock.Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error")
    mock_response.status_code = 404
    mock_response.reason = "Not Found"
    mock_response.text = "Not Found"
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Used": "1"
    }
    
    # Act
    with mock.patch('requests.get', return_value=mock_response):
        result = get_comments(issue_number, base_args)
    
    # Assert
    assert result == []


def test_get_comments_rate_limit_error():
    # Arrange
    issue_number = 123
    base_args: BaseArgs = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "input_from": "github",
        "owner_type": "organization",
        "owner_id": 123456,
        "repo_id": 789012,
        "clone_url": "https://github.com/gitautoai/gitauto.git",
        "is_fork": False,
        "issue_number": issue_number,
        "issue_title": "Test Issue",
        "issue_body": "Test Body",
        "issue_comments": [],
        "latest_commit_sha": "abc123",
        "comment_url": None,
        "issuer_name": "testuser",
        "base_branch": "main",
        "new_branch": "test-branch",
        "installation_id": 12345,
        "sender_id": 67890,
        "sender_name": "sender",
        "sender_email": "sender@example.com",
        "is_automation": False,
        "reviewers": [],
        "github_urls": [],
        "other_urls": [],
        "pr_body": ""
    }
    
    # Create a mock rate limit error
    mock_response = mock.Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("403 Forbidden")
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_response.text = "API rate limit exceeded"
    
    # Set rate limit headers
    future_time = 9999999999  # A time far in the future
    mock_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Used": "5000",
        "X-RateLimit-Reset": str(future_time)
    }
    
    # Mock time.sleep to avoid waiting in tests
    mock_sleep = mock.patch('time.sleep', return_value=None)
    
    # Create a successful response for the retry
    success_response = mock.Mock()
    success_response.json.return_value = [{"body": "Comment after rate limit"}]
    success_response.raise_for_status.return_value = None
    
    # Act
    with mock_sleep, \
         mock.patch('requests.get', side_effect=[mock_response, success_response]):
        result = get_comments(issue_number, base_args)
    
    # Assert
    assert result == ["Comment after rate limit"]


def test_get_comments_json_decode_error():
    # Arrange
    issue_number = 123
    base_args: BaseArgs = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "input_from": "github",
        "owner_type": "organization",
        "owner_id": 123456,
        "repo_id": 789012,
        "clone_url": "https://github.com/gitautoai/gitauto.git",
        "is_fork": False,
        "issue_number": issue_number,
        "issue_title": "Test Issue",
        "issue_body": "Test Body",
        "issue_comments": [],
        "latest_commit_sha": "abc123",
        "comment_url": None,
        "issuer_name": "testuser",
        "base_branch": "main",
        "new_branch": "test-branch",
        "installation_id": 12345,
        "sender_id": 67890,
        "sender_name": "sender",
        "sender_email": "sender@example.com",
        "is_automation": False,
        "reviewers": [],
        "github_urls": [],
        "other_urls": [],
        "pr_body": ""
    }
    
    # Create a mock response that will cause a JSON decode error
    mock_response = mock.Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Invalid JSON")
    
    # Act
    with mock.patch('requests.get', return_value=mock_response):
        result = get_comments(issue_number, base_args)
    
    # Assert
    assert result == []


def test_get_comments_empty_response():
    # Arrange
    issue_number = 123
    base_args: BaseArgs = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "input_from": "github",
        "owner_type": "organization",
        "owner_id": 123456,
        "repo_id": 789012,
        "clone_url": "https://github.com/gitautoai/gitauto.git",
        "is_fork": False,
        "issue_number": issue_number,
        "issue_title": "Test Issue",
        "issue_body": "Test Body",
        "issue_comments": [],
        "latest_commit_sha": "abc123",
        "comment_url": None,
        "issuer_name": "testuser",
        "base_branch": "main",
        "new_branch": "test-branch",
        "installation_id": 12345,
        "sender_id": 67890,
        "sender_name": "sender",
        "sender_email": "sender@example.com",
        "is_automation": False,
        "reviewers": [],
        "github_urls": [],
        "other_urls": [],
        "pr_body": ""
    }
    
    # Create a mock response with empty list
    mock_response = mock.Mock()
    mock_response.json.return_value = []
    mock_response.raise_for_status.return_value = None
    
    # Act
    with mock.patch('requests.get', return_value=mock_response):
        result = get_comments(issue_number, base_args)
    
    # Assert
    assert result == []
    assert len(result) == 0


def test_get_comments_missing_body():
    # Arrange
    issue_number = 123
    base_args: BaseArgs = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "input_from": "github",
        "owner_type": "organization",
        "owner_id": 123456,
        "repo_id": 789012,
        "clone_url": "https://github.com/gitautoai/gitauto.git",
        "is_fork": False,
        "issue_number": issue_number,
        "issue_title": "Test Issue",
        "issue_body": "Test Body",
        "issue_comments": [],
        "latest_commit_sha": "abc123",
        "comment_url": None,
        "issuer_name": "testuser",
        "base_branch": "main",
        "new_branch": "test-branch",
        "installation_id": 12345,
        "sender_id": 67890,
        "sender_name": "sender",
        "sender_email": "sender@example.com",
        "is_automation": False,
        "reviewers": [],
        "github_urls": [],
        "other_urls": [],
        "pr_body": ""
    }
    
    # Create a response with comments missing the body field
    mock_response = mock.Mock()
    mock_response.json.return_value = [
        {"id": 1, "performed_via_github_app": None},  # Missing body
        {"body": "Comment 2", "performed_via_github_app": None}
    ]
    mock_response.raise_for_status.return_value = None
    
    # Act
    with mock.patch('requests.get', return_value=mock_response), \
         pytest.raises(KeyError):  # Should raise KeyError when accessing missing 'body'
        get_comments(issue_number, base_args)