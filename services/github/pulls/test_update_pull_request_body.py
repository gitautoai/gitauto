from unittest.mock import patch, MagicMock
import pytest
import requests
from services.github.pulls.update_pull_request_body import update_pull_request_body


@pytest.fixture
def mock_requests_patch():
    """Fixture to mock requests.patch method."""
    with patch("services.github.pulls.update_pull_request_body.requests.patch") as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    """Fixture to mock create_headers function."""
    with patch("services.github.pulls.update_pull_request_body.create_headers") as mock:
        mock.return_value = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        yield mock


@pytest.fixture
def sample_response_data():
    """Fixture providing sample GitHub API response data."""
    return {
        "id": 123456789,
        "number": 42,
        "title": "Test Pull Request",
        "body": "Updated pull request body",
        "state": "open",
        "user": {
            "login": "testuser",
            "id": 12345
        },
        "html_url": "https://github.com/owner/repo/pull/42"
    }


def test_update_pull_request_body_success(mock_requests_patch, mock_create_headers, sample_response_data):
    """Test successful pull request body update."""
    # Setup
    mock_response = MagicMock()
    mock_response.json.return_value = sample_response_data
    mock_requests_patch.return_value = mock_response
    
    url = "https://api.github.com/repos/owner/repo/pulls/42"
    token = "test_token_123"
    body = "Updated pull request body"
    
    # Execute
    result = update_pull_request_body(url=url, token=token, body=body)
    
    # Assert
    assert result == sample_response_data
    mock_create_headers.assert_called_once_with(token=token)
    mock_requests_patch.assert_called_once_with(
        url=url,
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test_token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"body": body},
        timeout=120
    )
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()


def test_update_pull_request_body_with_empty_body(mock_requests_patch, mock_create_headers, sample_response_data):
    """Test updating pull request with empty body."""
    # Setup
    mock_response = MagicMock()
    sample_response_data["body"] = ""
    mock_response.json.return_value = sample_response_data
    mock_requests_patch.return_value = mock_response
    
    url = "https://api.github.com/repos/owner/repo/pulls/42"
    token = "test_token_123"
    body = ""
    
    # Execute
    result = update_pull_request_body(url=url, token=token, body=body)
    
    # Assert
    assert result == sample_response_data
    mock_requests_patch.assert_called_once_with(
        url=url,
        headers=mock_create_headers.return_value,
        json={"body": body},
        timeout=120
    )


def test_update_pull_request_body_with_multiline_body(mock_requests_patch, mock_create_headers, sample_response_data):
    """Test updating pull request with multiline body content."""
    # Setup
    mock_response = MagicMock()
    multiline_body = "Line 1\nLine 2\n\nLine 4 with **markdown**"
    sample_response_data["body"] = multiline_body
    mock_response.json.return_value = sample_response_data
    mock_requests_patch.return_value = mock_response
    
    url = "https://api.github.com/repos/owner/repo/pulls/42"
    token = "test_token_123"
    
    # Execute
    result = update_pull_request_body(url=url, token=token, body=multiline_body)
    
    # Assert
    assert result == sample_response_data
    mock_requests_patch.assert_called_once_with(
        url=url,
        headers=mock_create_headers.return_value,
        json={"body": multiline_body},
        timeout=120
    )


def test_update_pull_request_body_with_special_characters(mock_requests_patch, mock_create_headers, sample_response_data):
    """Test updating pull request body with special characters."""
    # Setup
    mock_response = MagicMock()
    special_body = "Body with émojis 🚀 and special chars: <>&\"'"
    sample_response_data["body"] = special_body
    mock_response.json.return_value = sample_response_data
    mock_requests_patch.return_value = mock_response
    
    url = "https://api.github.com/repos/owner/repo/pulls/42"
    token = "test_token_123"
    
    # Execute
    result = update_pull_request_body(url=url, token=token, body=special_body)
    
    # Assert
    assert result == sample_response_data
    mock_requests_patch.assert_called_once_with(
        url=url,
        headers=mock_create_headers.return_value,
        json={"body": special_body},
        timeout=120
    )


def test_update_pull_request_body_http_error(mock_requests_patch, mock_create_headers):
    """Test handling of HTTP errors."""
    # Setup
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
    mock_requests_patch.return_value = mock_response
    
    url = "https://api.github.com/repos/owner/repo/pulls/999"
    token = "test_token_123"
    body = "Test body"
    
    # Execute
    result = update_pull_request_body(url=url, token=token, body=body)
    
    # Assert - should return None due to handle_exceptions decorator
    assert result is None
    mock_requests_patch.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


def test_update_pull_request_body_connection_error(mock_requests_patch, mock_create_headers):
    """Test handling of connection errors."""
    # Setup
    mock_requests_patch.side_effect = requests.exceptions.ConnectionError("Connection failed")
    
    url = "https://api.github.com/repos/owner/repo/pulls/42"
    token = "test_token_123"
    body = "Test body"
    
    # Execute
    result = update_pull_request_body(url=url, token=token, body=body)
    
    # Assert - should return None due to handle_exceptions decorator
    assert result is None
    mock_requests_patch.assert_called_once()


def test_update_pull_request_body_timeout_error(mock_requests_patch, mock_create_headers):
    """Test handling of timeout errors."""
    # Setup
    mock_requests_patch.side_effect = requests.exceptions.Timeout("Request timed out")
    
    url = "https://api.github.com/repos/owner/repo/pulls/42"
    token = "test_token_123"
    body = "Test body"
    
    # Execute
    result = update_pull_request_body(url=url, token=token, body=body)
    
    # Assert - should return None due to handle_exceptions decorator
    assert result is None
    mock_requests_patch.assert_called_once()


def test_update_pull_request_body_json_decode_error(mock_requests_patch, mock_create_headers):
    """Test handling of JSON decode errors."""
    # Setup
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_requests_patch.return_value = mock_response
    
    url = "https://api.github.com/repos/owner/repo/pulls/42"
    token = "test_token_123"
    body = "Test body"
    
    # Execute
    result = update_pull_request_body(url=url, token=token, body=body)
    
    # Assert - should return None due to handle_exceptions decorator
    assert result is None
    mock_requests_patch.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()


def test_update_pull_request_body_uses_correct_timeout(mock_requests_patch, mock_create_headers):
    """Test that the function uses the correct timeout value."""
    # Setup
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 123}
    mock_requests_patch.return_value = mock_response
    
    # Execute
    update_pull_request_body("https://api.github.com/repos/owner/repo/pulls/42", "token", "body")
    
    # Assert
    call_args = mock_requests_patch.call_args
    assert call_args.kwargs["timeout"] == 120
