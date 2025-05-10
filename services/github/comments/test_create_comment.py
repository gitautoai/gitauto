import pytest
from unittest.mock import patch, MagicMock

from tests.constants import OWNER, REPO, TOKEN
from services.github.comments.create_comment import create_comment


def test_create_comment_github_success():
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = {"url": "https://api.github.com/repos/owner/repo/issues/comments/1"}
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123
    }
    
    # Act
    with patch("services.github.comments.create_comment.requests.post") as mock_post:
        mock_post.return_value = mock_response
        result = create_comment("Test comment body", base_args)
    
    # Assert
    mock_post.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    assert result == "https://api.github.com/repos/owner/repo/issues/comments/1"


def test_create_comment_github_with_explicit_input_from():
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = {"url": "https://api.github.com/repos/owner/repo/issues/comments/1"}
    
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
        result = create_comment("Test comment body", base_args)
    
    # Assert
    mock_post.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    assert result == "https://api.github.com/repos/owner/repo/issues/comments/1"


def test_create_comment_github_http_error():
    # Arrange
    from requests.exceptions import HTTPError
    
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = HTTPError("404 Client Error")
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123
    }
    
    # Act
    with patch("services.github.comments.create_comment.requests.post") as mock_post:
        mock_post.return_value = mock_response
        result = create_comment("Test comment body", base_args)
    
    # Assert
    mock_post.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    assert result is None  # Should return None due to @handle_exceptions


def test_create_comment_github_connection_error():
    # Arrange
    from requests.exceptions import ConnectionError
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123
    }
    
    # Act
    with patch("services.github.comments.create_comment.requests.post") as mock_post:
        mock_post.side_effect = ConnectionError("Connection refused")
        result = create_comment("Test comment body", base_args)
    
    # Assert
    mock_post.assert_called_once()
    assert result is None  # Should return None due to @handle_exceptions


def test_create_comment_github_timeout_error():
    # Arrange
    from requests.exceptions import Timeout
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123
    }
    
    # Act
    with patch("services.github.comments.create_comment.requests.post") as mock_post:
        mock_post.side_effect = Timeout("Request timed out")
        result = create_comment("Test comment body", base_args)
    
    # Assert
    mock_post.assert_called_once()
    assert result is None  # Should return None due to @handle_exceptions


def test_create_comment_github_json_error():
    # Arrange
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123
    }
    
    # Act
    with patch("services.github.comments.create_comment.requests.post") as mock_post:
        mock_post.return_value = mock_response
        result = create_comment("Test comment body", base_args)
    
    # Assert
    mock_post.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    assert result is None  # Should return None due to @handle_exceptions


def test_create_comment_jira():
    # Arrange
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123,
        "input_from": "jira"
    }
    
    # Act
    result = create_comment("Test comment body", base_args)
    
    # Assert
    assert result is None


def test_create_comment_unknown_input_from():
    # Arrange
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123,
        "input_from": "unknown"
    }
    
    # Act
    result = create_comment("Test comment body", base_args)
    
    # Assert
    assert result is None  # Should return None as no condition matches


def test_create_comment_with_headers():
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = {"url": "https://api.github.com/repos/owner/repo/issues/comments/1"}
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123
    }
    
    # Act
    with patch("services.github.comments.create_comment.requests.post") as mock_post, \
         patch("services.github.comments.create_comment.create_headers") as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_post.return_value = mock_response
        result = create_comment("Test comment body", base_args)
    
    # Assert
    mock_create_headers.assert_called_once_with(token=TOKEN)
    mock_post.assert_called_once()
    assert mock_post.call_args[1]["headers"] == {"Authorization": f"Bearer {TOKEN}"}
    assert result == "https://api.github.com/repos/owner/repo/issues/comments/1"
