import pytest
from unittest.mock import patch, MagicMock
import requests

from services.github.comments.get_all_comments import get_all_comments
from tests.constants import OWNER, REPO, TOKEN


@pytest.fixture
def base_args():
    """Fixture providing base arguments for testing."""
    return {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123
    }


@pytest.fixture
def mock_requests_get():
    """Fixture to mock requests.get function."""
    with patch("services.github.comments.get_all_comments.get") as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    """Fixture to mock create_headers function."""
    with patch("services.github.comments.get_all_comments.create_headers") as mock:
        mock.return_value = {"Authorization": f"Bearer {TOKEN}"}
        yield mock


def test_get_all_comments_success(base_args, mock_requests_get, mock_create_headers):
    """Test successful retrieval of comments."""
    # Arrange
    expected_comments = [
        {
            "id": 1,
            "body": "First comment",
            "user": {"login": "user1"}
        },
        {
            "id": 2,
            "body": "Second comment",
            "user": {"login": "user2"}
        }
    ]
    mock_response = MagicMock()
    mock_response.json.return_value = expected_comments
    mock_requests_get.return_value = mock_response
    
    # Act
    result = get_all_comments(base_args)
    
    # Assert
    assert result == expected_comments
    mock_create_headers.assert_called_once_with(token=TOKEN)
    mock_requests_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()


def test_get_all_comments_empty_response(base_args, mock_requests_get, mock_create_headers):
    """Test handling of empty comments list."""
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response
    
    # Act
    result = get_all_comments(base_args)
    
    # Assert
    assert result == []
    mock_requests_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()


def test_get_all_comments_correct_url_construction(base_args, mock_requests_get, mock_create_headers):
    """Test that the correct GitHub API URL is constructed."""
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response
    
    # Act
    get_all_comments(base_args)
    
    # Assert
    expected_url = f"https://api.github.com/repos/{OWNER}/{REPO}/issues/123/comments"
    mock_requests_get.assert_called_once()
    call_args = mock_requests_get.call_args
    assert call_args[1]["url"] == expected_url


def test_get_all_comments_correct_headers(base_args, mock_requests_get, mock_create_headers):
    """Test that correct headers are passed to the request."""
    # Arrange
    expected_headers = {"Authorization": f"Bearer {TOKEN}"}
    mock_create_headers.return_value = expected_headers
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response
    
    # Act
    get_all_comments(base_args)
    
    # Assert
    mock_create_headers.assert_called_once_with(token=TOKEN)
    call_args = mock_requests_get.call_args
    assert call_args[1]["headers"] == expected_headers


def test_get_all_comments_timeout_parameter(base_args, mock_requests_get, mock_create_headers):
    """Test that timeout parameter is correctly passed."""
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response
    
    # Act
    get_all_comments(base_args)
    
    # Assert
    call_args = mock_requests_get.call_args
    assert "timeout" in call_args[1]
    # Timeout should be imported from config
    from config import TIMEOUT
    assert call_args[1]["timeout"] == TIMEOUT


def test_get_all_comments_http_error(base_args, mock_requests_get, mock_create_headers):
    """Test handling of HTTP errors."""
    # Arrange
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
    mock_requests_get.return_value = mock_response
    
    # Act
    result = get_all_comments(base_args)
    
    # Assert
    assert result == []  # Should return default value due to handle_exceptions decorator
    mock_requests_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


def test_get_all_comments_json_decode_error(base_args, mock_requests_get, mock_create_headers):
    """Test handling of JSON decode errors."""
    # Arrange
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_requests_get.return_value = mock_response
    
    # Act
    result = get_all_comments(base_args)
    
    # Assert
    assert result == []  # Should return default value due to handle_exceptions decorator
    mock_requests_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()


def test_get_all_comments_network_error(base_args, mock_requests_get, mock_create_headers):
    """Test handling of network errors."""
    # Arrange
    mock_requests_get.side_effect = requests.exceptions.ConnectionError("Network error")
    
    # Act
    result = get_all_comments(base_args)
    
    # Assert
    assert result == []  # Should return default value due to handle_exceptions decorator
    mock_requests_get.assert_called_once()


def test_get_all_comments_different_issue_number(mock_requests_get, mock_create_headers):
    """Test with different issue numbers."""
    # Arrange
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 456
    }
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response
    
    # Act
    get_all_comments(base_args)
    
    # Assert
    expected_url = f"https://api.github.com/repos/{OWNER}/{REPO}/issues/456/comments"
    call_args = mock_requests_get.call_args
    assert call_args[1]["url"] == expected_url


def test_get_all_comments_different_owner_repo(mock_requests_get, mock_create_headers):
    """Test with different owner and repository."""
    # Arrange
    base_args = {
        "owner": "different_owner",
        "repo": "different_repo",
        "token": TOKEN,
        "issue_number": 123
    }
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response
    
    # Act
    get_all_comments(base_args)
    
    # Assert
    expected_url = "https://api.github.com/repos/different_owner/different_repo/issues/123/comments"
    call_args = mock_requests_get.call_args
    assert call_args[1]["url"] == expected_url


def test_get_all_comments_large_response(base_args, mock_requests_get, mock_create_headers):
    """Test handling of large comment responses."""
    # Arrange
    large_comments = [
        {"id": i, "body": f"Comment {i}", "user": {"login": f"user{i}"}}
        for i in range(100)
    ]
    mock_response = MagicMock()
    mock_response.json.return_value = large_comments
    mock_requests_get.return_value = mock_response
    
    # Act
    result = get_all_comments(base_args)
    
    # Assert
    assert result == large_comments
    assert len(result) == 100
    mock_requests_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()