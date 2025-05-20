import pytest
from unittest.mock import patch, MagicMock
import requests

from services.github.comments.create_comment import create_comment
from services.github.create_headers import create_headers
from tests.constants import OWNER, REPO, TOKEN
from config import GITHUB_API_URL, TIMEOUT


def test_create_comment_github_success():
    """Test successful comment creation with GitHub input."""
    # Arrange
    body = "Test comment body"
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123,
        "input_from": "github"
    }
    expected_url = f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/issues/123/comments/1"
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"url": expected_url}
    
    # Act
    with patch("requests.post", return_value=mock_response) as mock_post:
        result = create_comment(body, base_args)
    
    # Assert
    mock_post.assert_called_once_with(
        url=f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/issues/123/comments",
        headers=create_headers(token=TOKEN),
        json={"body": body},
        timeout=TIMEOUT
    )
    assert result == expected_url


def test_create_comment_jira_input():
    """Test comment creation with Jira input."""
    # Arrange
    body = "Test comment body"
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123,
        "input_from": "jira"
    }
    
    # Act
    with patch("requests.post") as mock_post:
        result = create_comment(body, base_args)
    
    # Assert
    mock_post.assert_not_called()
    assert result is None


def test_create_comment_default_input_from():
    """Test comment creation with default input_from value."""
    # Arrange
    body = "Test comment body"
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123,
        # input_from not provided, should default to "github"
    }
    expected_url = f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/issues/123/comments/1"
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"url": expected_url}
    
    # Act
    with patch("requests.post", return_value=mock_response) as mock_post:
        result = create_comment(body, base_args)
    
    # Assert
    mock_post.assert_called_once()
    assert result == expected_url


def test_create_comment_http_error():
    """Test error handling when HTTP request fails."""
    # Arrange
    body = "Test comment body"
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123,
        "input_from": "github"
    }
    
    mock_response = MagicMock()
    # Create a proper mock response for the HTTPError
    error_response = MagicMock()
    error_response.status_code = 404
    error_response.reason = "Not Found"
    error_response.text = "Resource not found"
    error_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Used": "1"
    }
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error", response=error_response)
    
    # Act
    with patch("requests.post", return_value=mock_response) as mock_post:
        result = create_comment(body, base_args)
    
    # Assert
    mock_post.assert_called_once()
    assert result is None  # Default return value from handle_exceptions


def test_create_comment_json_decode_error():
    """Test error handling when JSON decoding fails."""
    # Arrange
    body = "Test comment body"
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123,
        "input_from": "github"
    }
    
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    
    # Act
    with patch("requests.post", return_value=mock_response) as mock_post:
        result = create_comment(body, base_args)
    
    # Assert
    mock_post.assert_called_once()
    assert result is None  # Default return value from handle_exceptions


def test_create_comment_missing_url_in_response():
    """Test error handling when 'url' key is missing in response."""
    # Arrange
    body = "Test comment body"
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123,
        "input_from": "github"
    }
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 12345}  # Missing 'url' key
    
    # Act
    with patch("requests.post", return_value=mock_response) as mock_post:
        result = create_comment(body, base_args)
    
    # Assert
    mock_post.assert_called_once()
    assert result is None  # Default return value from handle_exceptions


def test_create_comment_empty_body():
    """Test comment creation with empty body."""
    # Arrange
    body = ""
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123,
        "input_from": "github"
    }
    expected_url = f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/issues/123/comments/1"
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"url": expected_url}
    
    # Act
    with patch("requests.post", return_value=mock_response) as mock_post:
        result = create_comment(body, base_args)
    
    # Assert
    mock_post.assert_called_once_with(
        url=f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/issues/123/comments",
        headers=create_headers(token=TOKEN),
        json={"body": body},
        timeout=TIMEOUT
    )
    assert result == expected_url


def test_create_comment_unknown_input_from():
    """Test comment creation with unknown input_from value."""
    # Arrange
    body = "Test comment body"
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123,
        "input_from": "unknown"  # Not "github" or "jira"
    }
    
    # Act
    with patch("requests.post") as mock_post:
        result = create_comment(body, base_args)
    
    # Assert
    mock_post.assert_not_called()
    assert result is None  # Default return value from handle_exceptions


def test_create_comment_connection_error():
    """Test error handling when connection to GitHub API fails."""
    # Arrange
    body = "Test comment body"
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123,
        "input_from": "github"
    }
    
    # Act
    with patch("requests.post", side_effect=requests.exceptions.ConnectionError("Connection refused")) as mock_post:
        result = create_comment(body, base_args)
    
    # Assert
    mock_post.assert_called_once()
    assert result is None  # Default return value from handle_exceptions


def test_create_comment_timeout_error():
    """Test error handling when GitHub API request times out."""
    # Arrange
    body = "Test comment body"
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123,
        "input_from": "github"
    }
    
    # Act
    with patch("requests.post", side_effect=requests.exceptions.Timeout("Request timed out")) as mock_post:
        result = create_comment(body, base_args)
    
    # Assert
    mock_post.assert_called_once()
    assert result is None  # Default return value from handle_exceptions