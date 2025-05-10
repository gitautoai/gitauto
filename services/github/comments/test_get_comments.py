# Standard imports
from unittest.mock import patch, MagicMock

# Third party imports
import pytest
from requests.exceptions import HTTPError

# Local imports
from config import GITHUB_APP_IDS
from services.github.comments.get_comments import get_comments
from tests.constants import OWNER, REPO, TOKEN


@pytest.fixture
def base_args():
    return {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "input_from": "github",
        "owner_type": "Organization",
        "owner_id": 123456,
        "repo_id": 789012,
        "clone_url": "https://github.com/gitautoai/gitauto.git",
        "is_fork": False,
        "issue_number": 1,
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
        "sender_name": "testuser",
        "sender_email": "test@example.com",
        "is_automation": False,
        "reviewers": [],
        "github_urls": [],
        "other_urls": [],
        "pr_body": ""
    }


def test_get_comments_success(base_args):
    # Mock response data
    mock_comments = [
        {
            "body": "Comment 1",
            "performed_via_github_app": None
        },
        {
            "body": "Comment 2",
            "performed_via_github_app": None
        }
    ]
    
    # Mock the requests.get method
    with patch('requests.get') as mock_get:
        # Configure the mock to return a successful response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_comments
        mock_get.return_value = mock_response
        
        # Call the function
        result = get_comments(issue_number=1, base_args=base_args)
        
        # Verify the result
        assert result == ["Comment 1", "Comment 2"]
        
        # Verify the request was made correctly
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert f"/repos/{OWNER}/{REPO}/issues/1/comments" in kwargs['url']
        assert "Bearer" in kwargs['headers']['Authorization']


def test_get_comments_filter_app_comments(base_args):
    # Use the first app ID from the config
    app_id = GITHUB_APP_IDS[0]
    
    # Mock response data with a mix of app and non-app comments
    mock_comments = [
        {
            "body": "Comment from user",
            "performed_via_github_app": None
        },
        {
            "body": "Comment from app",
            "performed_via_github_app": {"id": app_id}
        },
        {
            "body": "Another comment from user",
            "performed_via_github_app": None
        },
        {
            "body": "Comment from different app",
            "performed_via_github_app": {"id": 999999}  # Not in GITHUB_APP_IDS
        }
    ]
    
    # Mock the requests.get method
    with patch('requests.get') as mock_get:
        # Configure the mock to return a successful response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_comments
        mock_get.return_value = mock_response
        
        # Call the function with includes_me=False (default)
        result = get_comments(issue_number=1, base_args=base_args)
        
        # Verify the result - should only include non-app comments and comments from other apps
        assert result == ["Comment from user", "Another comment from user", "Comment from different app"]


def test_get_comments_include_app_comments(base_args):
    # Use the first app ID from the config
    app_id = GITHUB_APP_IDS[0]
    
    # Mock response data with a mix of app and non-app comments
    mock_comments = [
        {
            "body": "Comment from user",
            "performed_via_github_app": None
        },
        {
            "body": "Comment from app",
            "performed_via_github_app": {"id": app_id}
        }
    ]
    
    # Mock the requests.get method
    with patch('requests.get') as mock_get:
        # Configure the mock to return a successful response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_comments
        mock_get.return_value = mock_response
        
        # Call the function with includes_me=True
        result = get_comments(issue_number=1, base_args=base_args, includes_me=True)
        
        # Verify the result - should include all comments
        assert result == ["Comment from user", "Comment from app"]


def test_get_comments_http_error(base_args):
    # Mock the requests.get method to raise an HTTPError
    with patch('requests.get') as mock_get:
        # Configure the mock to raise an HTTPError
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = HTTPError("404 Client Error")
        mock_get.return_value = mock_response
        
        # Call the function
        result = get_comments(issue_number=1, base_args=base_args)
        
        # Verify the result - should return empty list due to handle_exceptions decorator
        assert result == []


def test_get_comments_empty_response(base_args):
    # Mock response data with empty list
    mock_comments = []
    
    # Mock the requests.get method
    with patch('requests.get') as mock_get:
        # Configure the mock to return a successful response with empty list
        mock_response = MagicMock()
        mock_response.json.return_value = mock_comments
        mock_get.return_value = mock_response
        
        # Call the function
        result = get_comments(issue_number=1, base_args=base_args)
        
        # Verify the result - should return empty list
        assert result == []


def test_get_comments_malformed_response(base_args):
    # Mock response data with missing 'body' field
    mock_comments = [
        {
            "id": 1,
            # Missing 'body' field
            "performed_via_github_app": None
        }
    ]
    
    # Mock the requests.get method
    with patch('requests.get') as mock_get:
        # Configure the mock to return a successful response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_comments
        mock_get.return_value = mock_response
        
        # Call the function - should handle the KeyError due to missing 'body'
        result = get_comments(issue_number=1, base_args=base_args)
        
        # Verify the result - should return empty list due to handle_exceptions decorator
        assert result == []