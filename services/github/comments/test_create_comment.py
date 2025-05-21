import pytest
from unittest.mock import patch, MagicMock, call

from services.github.comments.create_comment import create_comment
from tests.constants import OWNER, REPO, TOKEN


def test_create_comment_github_success():
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = {"url": "https://api.github.com/repos/owner/repo/issues/comments/123"}
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123,
        "input_from": "github"
    }
    
    # Act
    with patch("services.github.comments.create_comment.requests.post") as mock_post:
        mock_post.return_value = mock_response
        result = create_comment("Test comment", base_args)
    
    # Assert
    mock_post.assert_called_once()
    expected_url = f"https://api.github.com/repos/{OWNER}/{REPO}/issues/123/comments"
    assert mock_post.call_args[0][0] == expected_url
    assert "headers" in mock_post.call_args[1]
    assert "timeout" in mock_post.call_args[1]
    assert mock_post.call_args[1]["json"] == {"body": "Test comment"}


def test_create_comment_jira_input():
    # Arrange
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123,
        "input_from": "jira"
    }
    
    # Act
    with patch("services.github.comments.create_comment.requests.post") as mock_post:
        result = create_comment("Test comment", base_args)
    
    # Assert
    mock_post.assert_not_called()
    assert result is None


def test_create_comment_default_input_from():
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = {"url": "https://api.github.com/repos/owner/repo/issues/comments/123"}
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123
        # input_from not provided, should default to "github"
    }
    
    # Act
    with patch("services.github.comments.create_comment.requests.post") as mock_post:
        mock_post.return_value = mock_response
        result = create_comment("Test comment", base_args)
    
    # Assert
    mock_post.assert_called_once()
    assert result == "https://api.github.com/repos/owner/repo/issues/comments/123"


def test_create_comment_request_error():
    # Arrange
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("API error")
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123,
        "input_from": "github"
    }
    
    # Act
    with patch("services.github.comments.create_comment.requests.post") as mock_post:
        mock_post.return_value = mock_response
        result = create_comment("Test comment", base_args)
    
    # Assert
    mock_post.assert_called_once()
    assert result is None  # The handle_exceptions decorator should return None on error
    assert "headers" in mock_post.call_args[1]
    assert mock_post.call_args[1]["json"] == {"body": "Test comment"}