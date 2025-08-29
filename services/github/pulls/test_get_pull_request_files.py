# Standard imports
from unittest.mock import MagicMock, patch

# Third party imports
import pytest
import requests

# Local imports
from services.github.pulls.get_pull_request_files import get_pull_request_files, FileChange


def test_get_pull_request_files_success():
    """Test successful retrieval of pull request files."""
    # Mock response data
    mock_files_page1 = [
        {
            "filename": "file1.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
            "changes": 15,
        },
        {
            "filename": "file2.py",
            "status": "added",
            "additions": 20,
            "deletions": 0,
            "changes": 20,
        },
    ]
    
    mock_files_page2 = [
        {
            "filename": "file3.py",
            "status": "removed",
            "additions": 0,
            "deletions": 15,
            "changes": 15,
        },
    ]
    
    # Empty response to indicate end of pagination
    mock_files_page3 = []

    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get, patch(
        "services.github.pulls.get_pull_request_files.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_response1 = MagicMock()
        mock_response1.json.return_value = mock_files_page1
        
        mock_response2 = MagicMock()
        mock_response2.json.return_value = mock_files_page2
        
        mock_response3 = MagicMock()
        mock_response3.json.return_value = mock_files_page3
        
        mock_get.side_effect = [mock_response1, mock_response2, mock_response3]
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function
        result = get_pull_request_files(
            "https://api.github.com/repos/owner/repo/pulls/123/files", "test_token"
        )

        # Verify API calls
        assert mock_get.call_count == 3
        
        # First page call
        mock_get.assert_any_call(
            url="https://api.github.com/repos/owner/repo/pulls/123/files",
            headers={"Authorization": "Bearer test_token"},
            params={"per_page": 100, "page": 1},
            timeout=120,
        )
        
        # Second page call
        mock_get.assert_any_call(
            url="https://api.github.com/repos/owner/repo/pulls/123/files",
            headers={"Authorization": "Bearer test_token"},
            params={"per_page": 100, "page": 2},
            timeout=120,
        )
        
        # Third page call
        mock_get.assert_any_call(
            url="https://api.github.com/repos/owner/repo/pulls/123/files",
            headers={"Authorization": "Bearer test_token"},
            params={"per_page": 100, "page": 3},
            timeout=120,
        )

        # Verify result
        expected_result = [
            {"filename": "file1.py", "status": "modified"},
            {"filename": "file2.py", "status": "added"},
            {"filename": "file3.py", "status": "removed"},
        ]
        assert result == expected_result


def test_get_pull_request_files_empty_response():
    """Test handling of empty response."""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get, patch(
        "services.github.pulls.get_pull_request_files.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function
        result = get_pull_request_files(
            "https://api.github.com/repos/owner/repo/pulls/123/files", "test_token"
        )

        # Verify API call
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/owner/repo/pulls/123/files",
            headers={"Authorization": "Bearer test_token"},
            params={"per_page": 100, "page": 1},
            timeout=120,
        )

        # Verify result
        assert result == []


def test_get_pull_request_files_missing_fields():
    """Test handling of response with missing fields."""
    # Mock response with missing fields
    mock_files = [
        {
            "filename": "file1.py",
            # Missing status field
            "additions": 10,
            "deletions": 5,
        },
        {
            # Missing filename field
            "status": "added",
            "additions": 20,
            "deletions": 0,
        },
        {
            "filename": "file3.py",
            "status": "removed",
            "additions": 0,
            "deletions": 15,
        },
    ]

    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get, patch(
        "services.github.pulls.get_pull_request_files.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = mock_files
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function
        result = get_pull_request_files(
            "https://api.github.com/repos/owner/repo/pulls/123/files", "test_token"
        )

        # Verify API call
        mock_get.assert_called_once()

        # Verify result - only the file with both filename and status should be included
        expected_result = [
            {"filename": "file3.py", "status": "removed"},
        ]
        assert result == expected_result


def test_get_pull_request_files_http_error():
    """Test handling of HTTP error."""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get, patch(
        "services.github.pulls.get_pull_request_files.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Not Found"
        
        http_error = requests.exceptions.HTTPError("404 Client Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should return empty list due to handle_exceptions decorator
        result = get_pull_request_files(
            "https://api.github.com/repos/owner/repo/pulls/999/files", "test_token"
        )

        # Verify result is empty list (default_return_value from decorator)
        assert result == []


def test_get_pull_request_files_network_error():
    """Test handling of network connection error."""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get, patch(
        "services.github.pulls.get_pull_request_files.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should return empty list due to handle_exceptions decorator
        result = get_pull_request_files(
            "https://api.github.com/repos/owner/repo/pulls/123/files", "test_token"
        )

        # Verify result is empty list (default_return_value from decorator)
        assert result == []


def test_get_pull_request_files_timeout_error():
    """Test handling of timeout error."""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get, patch(
        "services.github.pulls.get_pull_request_files.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should return empty list due to handle_exceptions decorator
        result = get_pull_request_files(
            "https://api.github.com/repos/owner/repo/pulls/123/files", "test_token"
        )

        # Verify result is empty list (default_return_value from decorator)
        assert result == []


def test_get_pull_request_files_json_decode_error():
    """Test handling of JSON decode error."""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get, patch(
        "services.github.pulls.get_pull_request_files.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should return empty list due to handle_exceptions decorator
        result = get_pull_request_files(
            "https://api.github.com/repos/owner/repo/pulls/123/files", "test_token"
        )

        # Verify result is empty list (default_return_value from decorator)
        assert result == []


def test_get_pull_request_files_headers_creation():
    """Test that headers are created correctly."""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get, patch(
        "services.github.pulls.get_pull_request_files.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer custom_token"}

        # Call function
        get_pull_request_files(
            "https://api.github.com/repos/owner/repo/pulls/123/files", "custom_token"
        )

        # Verify headers creation
        mock_headers.assert_called_once_with(token="custom_token")


def test_get_pull_request_files_pagination_logic():
    """Test the pagination logic of the function."""
    # Create mock responses for multiple pages
    mock_files_page1 = [{"filename": "file1.py", "status": "modified"}]
    mock_files_page2 = [{"filename": "file2.py", "status": "added"}]
    mock_files_page3 = []  # Empty response to end pagination

    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get, patch(
        "services.github.pulls.get_pull_request_files.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_response1 = MagicMock()
        mock_response1.json.return_value = mock_files_page1
        
        mock_response2 = MagicMock()
        mock_response2.json.return_value = mock_files_page2
        
        mock_response3 = MagicMock()
        mock_response3.json.return_value = mock_files_page3
        
        mock_get.side_effect = [mock_response1, mock_response2, mock_response3]
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function
        result = get_pull_request_files(
            "https://api.github.com/repos/owner/repo/pulls/123/files", "test_token"
        )

        # Verify API calls with correct page numbers
        assert mock_get.call_count == 3
        
        # Check page parameter for each call
        call_args_list = mock_get.call_args_list
        assert call_args_list[0][1]["params"]["page"] == 1
        assert call_args_list[1][1]["params"]["page"] == 2
        assert call_args_list[2][1]["params"]["page"] == 3

        # Verify result contains files from all pages
        expected_result = [
            {"filename": "file1.py", "status": "modified"},
            {"filename": "file2.py", "status": "added"},
        ]
        assert result == expected_result


def test_get_pull_request_files_return_type():
    """Test that the return value is a list of FileChange objects."""
    # Mock response data
    mock_files = [
        {"filename": "file1.py", "status": "modified"},
    ]

    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get, patch(
        "services.github.pulls.get_pull_request_files.create_headers"
    ) as mock_headers:
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = mock_files
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function
        result = get_pull_request_files(
            "https://api.github.com/repos/owner/repo/pulls/123/files", "test_token"
        )

        # Verify result is a list
        assert isinstance(result, list)
        
        # Verify each item in the result matches the FileChange type
        for item in result:
            assert isinstance(item, dict)
            assert "filename" in item
            assert "status" in item
            assert item["status"] in ["added", "modified", "removed"]


def test_get_pull_request_files_with_different_urls():
    """Test the function with different URL formats."""
    test_urls = [
        "https://api.github.com/repos/owner/repo/pulls/123/files",
        "https://api.github.com/repos/owner-with-dash/repo_with_underscore/pulls/456/files",
        "https://api.github.com/repos/org/very-long-repository-name-with-hyphens/pulls/789/files",
    ]

    for url in test_urls:
        with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get, patch(
            "services.github.pulls.get_pull_request_files.create_headers"
        ) as mock_headers:
            # Setup mocks
            mock_response = MagicMock()
            mock_response.json.return_value = []
            mock_get.return_value = mock_response
            mock_headers.return_value = {"Authorization": "Bearer test_token"}

            # Call function
            result = get_pull_request_files(url, "test_token")

            # Verify API call with correct URL
            mock_get.assert_called_once()
            assert mock_get.call_args[1]["url"] == url
            
            # Verify result
            assert result == []


def test_get_pull_request_files_with_rate_limit_retry():
    """Test handling of rate limit errors with retry logic."""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get, patch(
        "services.github.pulls.get_pull_request_files.create_headers"
    ) as mock_headers:
        # Setup mocks for rate limit error then success
        mock_error_response = MagicMock()
        mock_error_response.status_code = 403
        mock_error_response.reason = "Forbidden"
        mock_error_response.text = "API rate limit exceeded"
        mock_error_response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Used": "5000",
            "X-RateLimit-Reset": "0",  # Set to 0 to avoid actual waiting in test
        }
        
        http_error = requests.exceptions.HTTPError("403 Forbidden")
        http_error.response = mock_error_response
        mock_error_response.raise_for_status.side_effect = http_error
        
        # Success response after rate limit
        mock_success_response = MagicMock()
        mock_success_response.json.return_value = [{"filename": "file1.py", "status": "modified"}]
        
        # First call raises rate limit error, second call succeeds
        mock_get.side_effect = [mock_error_response, mock_success_response]
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should handle rate limit and retry
        with patch("time.sleep") as mock_sleep:  # Mock sleep to avoid waiting
            result = get_pull_request_files(
                "https://api.github.com/repos/owner/repo/pulls/123/files", "test_token"
            )

        # Verify sleep was called (rate limit handling)
        mock_sleep.assert_called_once()
        
        # Verify result contains the file from the successful retry
        expected_result = [{"filename": "file1.py", "status": "modified"}]
        assert result == expected_result