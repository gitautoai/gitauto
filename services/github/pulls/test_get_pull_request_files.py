# Standard imports
import json
from unittest.mock import Mock, patch

import pytest
import requests
from services.github.pulls.get_pull_request_files import get_pull_request_files


@pytest.fixture
def mock_requests():
    """Mock requests module for testing HTTP calls"""
    with patch("services.github.pulls.get_pull_request_files.requests") as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    """Mock create_headers function"""
    with patch("services.github.pulls.get_pull_request_files.create_headers") as mock:
        mock.return_value = {"Authorization": "token test_token"}
        yield mock


def test_get_pull_request_files_success(mock_requests, mock_create_headers):
    """Test successful retrieval of pull request files"""
    mock_response_data = [
        {"filename": "file1.py", "status": "modified"},
        {"filename": "file2.js", "status": "added"},
        {"filename": "file3.txt", "status": "removed"},
    ]
    # Setup mock response
    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None

    # Mock for empty second page (pagination)
    empty_response = Mock()
    empty_response.json.return_value = []

    mock_requests.get.side_effect = [mock_response, empty_response]

    # Call function
    result = get_pull_request_files(
        "https://api.github.com/repos/test/test/pulls/1/files", "token123"
    )

    # Verify result
    expected = [
        {"filename": "file1.py", "status": "modified"},
        {"filename": "file2.js", "status": "added"},
        {"filename": "file3.txt", "status": "removed"},
    ]

    assert result == expected
    mock_create_headers.assert_called_once_with(token="token123")
    assert mock_requests.get.call_count == 2


def test_get_pull_request_files_pagination():
    """Test pagination handling"""
    page1_data = [{"filename": "file1.py", "status": "modified"}]
    page2_data = [{"filename": "file2.js", "status": "added"}]

    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response1 = Mock()
        mock_response1.json.return_value = page1_data
        mock_response1.raise_for_status.return_value = None

        mock_response2 = Mock()
        mock_response2.json.return_value = page2_data
        mock_response2.raise_for_status.return_value = None

        mock_response3 = Mock()
        mock_response3.json.return_value = []  # Empty page ends pagination
        mock_response3.raise_for_status.return_value = None

        mock_get.side_effect = [mock_response1, mock_response2, mock_response3]

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        expected = [
            {"filename": "file1.py", "status": "modified"},
            {"filename": "file2.js", "status": "added"},
        ]

        assert result == expected
        assert mock_get.call_count == 3


def test_get_pull_request_files_missing_fields():
    """Test handling of files with missing filename or status fields"""
    mock_response_data = [
        {"filename": "file1.py", "status": "modified"},
        {"filename": "file2.js"},  # Missing status
        {"status": "added"},  # Missing filename
        {"filename": "file3.txt", "status": "removed"},
    ]

    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        
        empty_response = Mock()
        empty_response.json.return_value = []
        empty_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_response, empty_response]

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        expected = [
            {"filename": "file1.py", "status": "modified"},
            {"filename": "file3.txt", "status": "removed"},
        ]

        assert result == expected


def test_get_pull_request_files_http_error():
    """Test handling of HTTP errors"""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 404
        http_error = requests.exceptions.HTTPError("404 Not Found")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        assert result == []


def test_get_pull_request_files_empty_response():
    """Test handling of empty response"""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        assert result == []
        assert mock_get.call_count == 1


def test_get_pull_request_files_request_timeout():
    """Test handling of request timeout"""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        assert result == []
        assert mock_get.call_count == 1


def test_get_pull_request_files_connection_error():
    """Test handling of connection errors"""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        assert result == []
        assert mock_get.call_count == 1


def test_get_pull_request_files_json_decode_error():
    """Test handling of JSON decode errors"""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        assert result == []
        assert mock_get.call_count == 1


def test_get_pull_request_files_unauthorized():
    """Test handling of 401 Unauthorized error"""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 401
        http_error = requests.exceptions.HTTPError("401 Unauthorized")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        assert result == []


def test_get_pull_request_files_forbidden():
    """Test handling of 403 Forbidden error"""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.reason = "Forbidden"
        mock_response.text = "API rate limit exceeded"
        mock_response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Used": "5000",
            "X-RateLimit-Reset": "1640995200"
        }
        http_error = requests.exceptions.HTTPError("403 Forbidden")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        assert result == []


def test_get_pull_request_files_internal_server_error():
    """Test handling of 500 Internal Server Error"""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 500
        http_error = requests.exceptions.HTTPError("500 Internal Server Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        assert result == []


def test_get_pull_request_files_various_file_statuses():
    """Test handling of various file statuses"""
    mock_response_data = [
        {"filename": "added_file.py", "status": "added"},
        {"filename": "modified_file.js", "status": "modified"},
        {"filename": "removed_file.txt", "status": "removed"},
        {"filename": "renamed_file.md", "status": "renamed"},  # Not in Status literal but should be handled
    ]

    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        
        empty_response = Mock()
        empty_response.json.return_value = []
        empty_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_response, empty_response]

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        expected = [
            {"filename": "added_file.py", "status": "added"},
            {"filename": "modified_file.js", "status": "modified"},
            {"filename": "removed_file.txt", "status": "removed"},
            {"filename": "renamed_file.md", "status": "renamed"},
        ]

        assert result == expected


def test_get_pull_request_files_malformed_data():
    """Test handling of malformed file data"""
    mock_response_data = [
        {"filename": "valid_file.py", "status": "modified"},
        {"filename": None, "status": "added"},  # None filename
        {"filename": "", "status": "modified"},  # Empty filename
        {"filename": "file_with_empty_status.js", "status": ""},  # Empty status
        {"filename": "valid_file2.txt", "status": None},  # None status
        None,  # Null file object
        {},  # Empty file object
        {"other_field": "value"},  # Missing both filename and status
    ]

    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        
        empty_response = Mock()
        empty_response.json.return_value = []
        empty_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_response, empty_response]

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        # Only the first file should be included as it has both filename and status
        expected = [
            {"filename": "valid_file.py", "status": "modified"},
        ]

        assert result == expected


def test_get_pull_request_files_large_pagination():
    """Test handling of multiple pages with large datasets"""
    # Create mock data for 3 pages
    page1_data = [{"filename": f"file_{i}.py", "status": "modified"} for i in range(1, 6)]
    page2_data = [{"filename": f"file_{i}.js", "status": "added"} for i in range(6, 11)]
    page3_data = [{"filename": f"file_{i}.txt", "status": "removed"} for i in range(11, 16)]

    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response1 = Mock()
        mock_response1.json.return_value = page1_data
        mock_response1.raise_for_status.return_value = None

        mock_response2 = Mock()
        mock_response2.json.return_value = page2_data
        mock_response2.raise_for_status.return_value = None

        mock_response3 = Mock()
        mock_response3.json.return_value = page3_data
        mock_response3.raise_for_status.return_value = None

        mock_response4 = Mock()
        mock_response4.json.return_value = []  # Empty page ends pagination
        mock_response4.raise_for_status.return_value = None

        mock_get.side_effect = [mock_response1, mock_response2, mock_response3, mock_response4]

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        # Should have all files from all pages
        expected = page1_data + page2_data + page3_data
        assert result == expected
        assert len(result) == 15
        assert mock_get.call_count == 4


def test_get_pull_request_files_request_parameters():
    """Test that correct parameters are passed to requests.get"""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get, \
         patch("services.github.pulls.get_pull_request_files.create_headers") as mock_headers, \
         patch("services.github.pulls.get_pull_request_files.PER_PAGE", 50), \
         patch("services.github.pulls.get_pull_request_files.TIMEOUT", 30):
        
        mock_headers.return_value = {"Authorization": "Bearer test_token"}
        
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        url = "https://api.github.com/repos/test/test/pulls/1/files"
        token = "test_token_123"
        
        get_pull_request_files(url, token)

        # Verify create_headers was called with correct token
        mock_headers.assert_called_once_with(token=token)
        
        # Verify requests.get was called with correct parameters
        mock_get.assert_called_once_with(
            url=url,
            headers={"Authorization": "Bearer test_token"},
            params={"per_page": 50, "page": 1},
            timeout=30
        )


def test_get_pull_request_files_pagination_parameters():
    """Test that pagination parameters are correctly incremented"""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get, \
         patch("services.github.pulls.get_pull_request_files.PER_PAGE", 25):
        
        # First page has data, second page is empty
        mock_response1 = Mock()
        mock_response1.json.return_value = [{"filename": "test.py", "status": "modified"}]
        mock_response1.raise_for_status.return_value = None

        mock_response2 = Mock()
        mock_response2.json.return_value = []
        mock_response2.raise_for_status.return_value = None

        mock_get.side_effect = [mock_response1, mock_response2]

        get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        # Verify pagination parameters
        assert mock_get.call_count == 2
        
        # First call should have page=1
        first_call = mock_get.call_args_list[0]
        assert first_call[1]["params"]["page"] == 1
        assert first_call[1]["params"]["per_page"] == 25
        
        # Second call should have page=2
        second_call = mock_get.call_args_list[1]
        assert second_call[1]["params"]["page"] == 2
        assert second_call[1]["params"]["per_page"] == 25


def test_get_pull_request_files_exception_handling():
    """Test that various exceptions are handled gracefully"""
    exceptions_to_test = [
        AttributeError("Attribute error"),
        KeyError("Key error"),
        TypeError("Type error"),
        ValueError("Value error"),
        Exception("Generic exception"),
    ]

    for exception in exceptions_to_test:
        with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
            mock_get.side_effect = exception

            result = get_pull_request_files(
                "https://api.github.com/repos/test/test/pulls/1/files", "token123"
            )

            assert result == []


def test_get_pull_request_files_mixed_valid_invalid_files():
    """Test handling of mixed valid and invalid file entries"""
    mock_response_data = [
        {"filename": "valid1.py", "status": "added"},
        {"filename": "valid2.js", "status": "modified"},
        {"invalid": "entry"},  # Missing filename and status
        {"filename": "valid3.txt", "status": "removed"},
        {"filename": "partial.md"},  # Missing status
        {"status": "added"},  # Missing filename
        {"filename": "valid4.css", "status": "modified"},
    ]

    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        
        empty_response = Mock()
        empty_response.json.return_value = []
        empty_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_response, empty_response]

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        # Only valid entries should be included
        expected = [
            {"filename": "valid1.py", "status": "added"},
            {"filename": "valid2.js", "status": "modified"},
            {"filename": "valid3.txt", "status": "removed"},
            {"filename": "valid4.css", "status": "modified"},
        ]

        assert result == expected
        assert len(result) == 4


def test_get_pull_request_files_empty_url():
    """Test handling of empty URL"""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.InvalidURL("Invalid URL")

        result = get_pull_request_files("", "token123")

        assert result == []


def test_get_pull_request_files_empty_token():
    """Test handling of empty token"""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", ""
        )

        assert result == []


def test_get_pull_request_files_single_page_with_files():
    """Test successful single page response with files"""
    mock_response_data = [
        {"filename": "src/main.py", "status": "modified"},
        {"filename": "tests/test_main.py", "status": "added"},
    ]

    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        
        empty_response = Mock()
        empty_response.json.return_value = []
        empty_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_response, empty_response]

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        expected = [
            {"filename": "src/main.py", "status": "modified"},
            {"filename": "tests/test_main.py", "status": "added"},
        ]

        assert result == expected
        assert mock_get.call_count == 2


def test_get_pull_request_files_response_json_none():
    """Test handling when response.json() returns None"""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = None
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        assert result == []
        assert mock_get.call_count == 1


def test_get_pull_request_files_file_with_special_characters():
    """Test handling of files with special characters in names"""
    mock_response_data = [
        {"filename": "file with spaces.py", "status": "added"},
        {"filename": "file-with-dashes.js", "status": "modified"},
        {"filename": "file_with_underscores.txt", "status": "removed"},
        {"filename": "file.with.dots.md", "status": "modified"},
        {"filename": "файл-с-unicode.py", "status": "added"},
        {"filename": "file@with#special$chars%.txt", "status": "modified"},
    ]

    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        
        empty_response = Mock()
        empty_response.json.return_value = []
        empty_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_response, empty_response]

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        assert result == mock_response_data
        assert len(result) == 6


def test_get_pull_request_files_rate_limit_with_retry():
    """Test handling of rate limit with retry after headers"""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get, \
         patch("time.sleep") as mock_sleep:
        
        # First call hits rate limit
        mock_response_rate_limit = Mock()
        mock_response_rate_limit.status_code = 403
        mock_response_rate_limit.reason = "Forbidden"
        mock_response_rate_limit.text = "API rate limit exceeded"
        mock_response_rate_limit.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Used": "5000",
            "X-RateLimit-Reset": "1640995200"
        }
        rate_limit_error = requests.exceptions.HTTPError("403 Forbidden")
        rate_limit_error.response = mock_response_rate_limit
        mock_response_rate_limit.raise_for_status.side_effect = rate_limit_error

        # Second call succeeds
        mock_response_success = Mock()
        mock_response_success.json.return_value = []
        mock_response_success.raise_for_status.return_value = None

        mock_get.side_effect = [mock_response_rate_limit, mock_response_success]

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        assert result == []
        # Should have called sleep due to rate limiting
        mock_sleep.assert_called()


def test_get_pull_request_files_secondary_rate_limit():
    """Test handling of secondary rate limit"""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get, \
         patch("time.sleep") as mock_sleep:
        
        # First call hits secondary rate limit
        mock_response_rate_limit = Mock()
        mock_response_rate_limit.status_code = 403
        mock_response_rate_limit.reason = "Forbidden"
        mock_response_rate_limit.text = "You have exceeded a secondary rate limit"
        mock_response_rate_limit.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Used": "1",
            "Retry-After": "60"
        }
        rate_limit_error = requests.exceptions.HTTPError("403 Forbidden")
        rate_limit_error.response = mock_response_rate_limit
        mock_response_rate_limit.raise_for_status.side_effect = rate_limit_error

        # Second call succeeds
        mock_response_success = Mock()
        mock_response_success.json.return_value = []
        mock_response_success.raise_for_status.return_value = None

        mock_get.side_effect = [mock_response_rate_limit, mock_response_success]

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        assert result == []
        # Should have called sleep with retry-after value
        mock_sleep.assert_called_with(60)


def test_get_pull_request_files_file_iteration_edge_cases():
    """Test edge cases in file iteration logic"""
    mock_response_data = [
        {"filename": "valid.py", "status": "modified"},
        {"filename": "valid.js", "status": "added", "extra_field": "ignored"},  # Extra fields should be ignored
        {"filename": "valid.txt", "status": "removed", "patches": "@@ -1,3 +1,3 @@"},  # GitHub API includes patches
    ]

    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        
        empty_response = Mock()
        empty_response.json.return_value = []
        empty_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_response, empty_response]

        result = get_pull_request_files(
            "https://api.github.com/repos/test/test/pulls/1/files", "token123"
        )

        # Should only include filename and status, ignoring extra fields
        expected = [
            {"filename": "valid.py", "status": "modified"},
            {"filename": "valid.js", "status": "added"},
            {"filename": "valid.txt", "status": "removed"},
        ]

        assert result == expected


def test_get_pull_request_files_request_exception_types():
    """Test handling of different request exception types"""
    exception_types = [
        requests.exceptions.RequestException("Generic request error"),
        requests.exceptions.URLRequired("URL required"),
        requests.exceptions.TooManyRedirects("Too many redirects"),
        requests.exceptions.ConnectTimeout("Connect timeout"),
        requests.exceptions.ReadTimeout("Read timeout"),
    ]

    for exception in exception_types:
        with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
            mock_get.side_effect = exception

            result = get_pull_request_files(
                "https://api.github.com/repos/test/test/pulls/1/files", "token123"
            )

            assert result == []