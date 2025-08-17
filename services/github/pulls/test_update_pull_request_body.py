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
        "user": {"login": "testuser", "id": 12345},
        "html_url": "https://github.com/owner/repo/pull/42",
    }


def test_update_pull_request_body_success(
    mock_requests_patch, mock_create_headers, sample_response_data
):
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
        timeout=120,
    )
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()


def test_update_pull_request_body_with_empty_body(
    mock_requests_patch, mock_create_headers, sample_response_data
):
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
        timeout=120,
    )


def test_update_pull_request_body_with_multiline_body(
    mock_requests_patch, mock_create_headers, sample_response_data
):
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
        timeout=120,
    )


def test_update_pull_request_body_with_special_characters(
    mock_requests_patch, mock_create_headers, sample_response_data
):
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
        timeout=120,
    )


def test_update_pull_request_body_http_error(mock_requests_patch, mock_create_headers):
    """Test handling of HTTP errors."""
    # Setup
    mock_response = MagicMock()
    http_error = requests.exceptions.HTTPError("404 Not Found")
    mock_error_response = MagicMock()
    mock_error_response.status_code = 404
    http_error.response = mock_error_response
    mock_error_response.reason = "Not Found"
    mock_error_response.text = "Pull request not found"
    mock_response.raise_for_status.side_effect = http_error
    mock_error_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Used": "1",
    }
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


def test_update_pull_request_body_connection_error(
    mock_requests_patch, mock_create_headers
):
    """Test handling of connection errors."""
    # Setup
    mock_requests_patch.side_effect = requests.exceptions.ConnectionError(
        "Connection failed"
    )

    url = "https://api.github.com/repos/owner/repo/pulls/42"
    token = "test_token_123"
    body = "Test body"

    # Execute
    result = update_pull_request_body(url=url, token=token, body=body)

    # Assert - should return None due to handle_exceptions decorator
    assert result is None
    mock_requests_patch.assert_called_once()


def test_update_pull_request_body_timeout_error(
    mock_requests_patch, mock_create_headers
):
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


def test_update_pull_request_body_json_decode_error(
    mock_requests_patch, mock_create_headers
):
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


def test_update_pull_request_body_uses_correct_timeout(
    mock_requests_patch, mock_create_headers
):
    """Test that the function uses the correct timeout value."""
    # Setup
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 123}
    mock_requests_patch.return_value = mock_response

    # Execute
    update_pull_request_body(
        "https://api.github.com/repos/owner/repo/pulls/42", "token", "body"
    )

    # Assert
    call_args = mock_requests_patch.call_args
    assert call_args.kwargs["timeout"] == 120


def test_update_pull_request_body_with_none_body(
    mock_requests_patch, mock_create_headers, sample_response_data
):
    """Test updating pull request with None body."""
    # Setup
    mock_response = MagicMock()
    sample_response_data["body"] = None
    mock_response.json.return_value = sample_response_data
    mock_requests_patch.return_value = mock_response

    url = "https://api.github.com/repos/owner/repo/pulls/42"
    token = "test_token_123"
    body = None

    # Execute
    result = update_pull_request_body(url=url, token=token, body=body)

    # Assert
    assert result == sample_response_data
    mock_requests_patch.assert_called_once_with(
        url=url,
        headers=mock_create_headers.return_value,
        json={"body": None},
        timeout=120,
    )


def test_update_pull_request_body_with_very_long_body(
    mock_requests_patch, mock_create_headers, sample_response_data
):
    """Test updating pull request with very long body content."""
    # Setup
    mock_response = MagicMock()
    long_body = "A" * 10000  # Very long body
    sample_response_data["body"] = long_body
    mock_response.json.return_value = sample_response_data
    mock_requests_patch.return_value = mock_response

    url = "https://api.github.com/repos/owner/repo/pulls/42"
    token = "test_token_123"

    # Execute
    result = update_pull_request_body(url=url, token=token, body=long_body)

    # Assert
    assert result == sample_response_data
    mock_requests_patch.assert_called_once_with(
        url=url,
        headers=mock_create_headers.return_value,
        json={"body": long_body},
        timeout=120,
    )


def test_update_pull_request_body_with_different_url_formats(
    mock_requests_patch, mock_create_headers, sample_response_data
):
    """Test updating pull request with different URL formats."""
    # Setup
    mock_response = MagicMock()
    mock_response.json.return_value = sample_response_data
    mock_requests_patch.return_value = mock_response

    # Test with different URL format
    url = "https://api.github.com/repos/org-name/repo-name/pulls/999"
    token = "test_token_123"
    body = "Test body"

    # Execute
    result = update_pull_request_body(url=url, token=token, body=body)

    # Assert
    assert result == sample_response_data
    mock_requests_patch.assert_called_once_with(
        url=url,
        headers=mock_create_headers.return_value,
        json={"body": body},
        timeout=120,
    )


def test_update_pull_request_body_headers_called_correctly(
    mock_requests_patch, mock_create_headers
):
    """Test that create_headers is called with the correct token."""
    # Setup
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 123}
    mock_requests_patch.return_value = mock_response

    url = "https://api.github.com/repos/owner/repo/pulls/42"
    token = "custom_test_token_456"
    body = "Test body"

    # Execute
    update_pull_request_body(url=url, token=token, body=body)

    # Assert
    mock_create_headers.assert_called_once_with(token=token)


@pytest.mark.parametrize(
    "body_content",
    [
        "",
        "Simple body",
        "Body with\nmultiple\nlines",
        "Body with **markdown** and _formatting_",
        "Body with émojis 🚀 and unicode ñáéíóú",
        "Body with special chars: <>&\"'",
        None,
        "A" * 1000,  # Long body
    ],
)
def test_update_pull_request_body_with_various_body_contents(
    mock_requests_patch, mock_create_headers, body_content
):
    """Test updating pull request with various body content types."""
    # Setup
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 123, "body": body_content}
    mock_requests_patch.return_value = mock_response

    url = "https://api.github.com/repos/owner/repo/pulls/42"
    token = "test_token"

    # Execute
    result = update_pull_request_body(url=url, token=token, body=body_content)

    # Assert
    assert result == {"id": 123, "body": body_content}
    mock_requests_patch.assert_called_once_with(
        url=url,
        headers=mock_create_headers.return_value,
        json={"body": body_content},
        timeout=120,
    )

    # Reset mocks for next iteration
    mock_requests_patch.reset_mock()
    mock_create_headers.reset_mock()


def test_update_pull_request_body_request_structure(
    mock_requests_patch, mock_create_headers
):
    """Test that the request is structured correctly."""
    # Setup
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 123}
    mock_requests_patch.return_value = mock_response

    expected_headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": "Bearer test_token",
        "User-Agent": "GitAuto",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    mock_create_headers.return_value = expected_headers

    url = "https://api.github.com/repos/owner/repo/pulls/42"
    token = "test_token"
    body = "Test body content"

    # Execute
    update_pull_request_body(url=url, token=token, body=body)

    # Assert request structure
    mock_requests_patch.assert_called_once()
    call_args = mock_requests_patch.call_args

    # Verify all required parameters are present
    assert call_args.kwargs["url"] == url
    assert call_args.kwargs["headers"] == expected_headers
    assert call_args.kwargs["json"] == {"body": body}
    assert call_args.kwargs["timeout"] == 120

    # Verify no unexpected parameters
    expected_kwargs = {"url", "headers", "json", "timeout"}
    assert set(call_args.kwargs.keys()) == expected_kwargs


def test_update_pull_request_body_response_processing(
    mock_requests_patch, mock_create_headers
):
    """Test that the response is processed correctly."""
    # Setup
    expected_response_data = {
        "id": 987654321,
        "number": 42,
        "title": "Updated PR",
        "body": "New body content",
        "state": "open",
        "html_url": "https://github.com/owner/repo/pull/42",
    }

    mock_response = MagicMock()
    mock_response.json.return_value = expected_response_data
    mock_requests_patch.return_value = mock_response

    # Execute
    result = update_pull_request_body(
        "https://api.github.com/repos/owner/repo/pulls/42", "token", "body"
    )

    # Assert
    assert result == expected_response_data
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()

    # Verify the exact response data is returned
    assert result["id"] == 987654321
    assert result["number"] == 42
    assert result["body"] == "New body content"
