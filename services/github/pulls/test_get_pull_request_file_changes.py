# Standard imports
from unittest.mock import Mock, patch
import time

# Third party imports
import pytest
import requests

# Local imports
from services.github.pulls.get_pull_request_file_changes import get_pull_request_file_changes


@pytest.fixture
def mock_requests():
    """Mock requests module for testing."""
    with patch("services.github.pulls.get_pull_request_file_changes.requests") as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    """Mock create_headers function for testing."""
    with patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock:
        mock.return_value = {"Authorization": "Bearer test_token"}
        yield mock


@pytest.fixture
def mock_time():
    """Mock time module for testing rate limit scenarios."""
    with patch("utils.error.handle_exceptions.time") as mock:
        yield mock


def test_get_pull_request_file_changes_success(mock_requests, mock_create_headers):
    """Test successful retrieval of pull request file changes."""
    mock_response_data = [
        {
            "filename": "file1.py",
            "status": "modified",
            "patch": "@@ -1,3 +1,3 @@\n-old line\n+new line"
        },
        {
            "filename": "file2.js",
            "status": "added",
            "patch": "@@ -0,0 +1,5 @@\n+new file content"
        },
        {
            "filename": "file3.txt",
            "status": "removed",
            "patch": "@@ -1,2 +0,0 @@\n-deleted content"
        }
    ]

    # Setup mock response
    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None

    # Mock for empty second page (pagination)
    empty_response = Mock()
    empty_response.json.return_value = []
    empty_response.raise_for_status.return_value = None

    mock_requests.get.side_effect = [mock_response, empty_response]

    # Call function
    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    # Verify result
    expected = [
        {
            "filename": "file1.py",
            "status": "modified",
            "patch": "@@ -1,3 +1,3 @@\n-old line\n+new line"
        },
        {
            "filename": "file2.js",
            "status": "added",
            "patch": "@@ -0,0 +1,5 @@\n+new file content"
        },
        {
            "filename": "file3.txt",
            "status": "removed",
            "patch": "@@ -1,2 +0,0 @@\n-deleted content"
        }
    ]

    assert result == expected
    mock_create_headers.assert_called_once_with(token="test_token")
    assert mock_requests.get.call_count == 2


def test_get_pull_request_file_changes_pagination(mock_requests, mock_create_headers):
    """Test pagination handling with multiple pages."""
    page1_data = [
        {
            "filename": "file1.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,1 @@\n-old\n+new"
        }
    ]
    page2_data = [
        {
            "filename": "file2.js",
            "status": "added",
            "patch": "@@ -0,0 +1,1 @@\n+added"
        }
    ]

    mock_response1 = Mock()
    mock_response1.json.return_value = page1_data
    mock_response1.raise_for_status.return_value = None

    mock_response2 = Mock()
    mock_response2.json.return_value = page2_data
    mock_response2.raise_for_status.return_value = None

    mock_response3 = Mock()
    mock_response3.json.return_value = []  # Empty page ends pagination
    mock_response3.raise_for_status.return_value = None

    mock_requests.get.side_effect = [mock_response1, mock_response2, mock_response3]

    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    expected = [
        {
            "filename": "file1.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,1 @@\n-old\n+new"
        },
        {
            "filename": "file2.js",
            "status": "added",
            "patch": "@@ -0,0 +1,1 @@\n+added"
        }
    ]

    assert result == expected
    assert mock_requests.get.call_count == 3

    # Verify pagination parameters
    calls = mock_requests.get.call_args_list
    assert calls[0][1]["params"] == {"per_page": 100, "page": 1}
    assert calls[1][1]["params"] == {"per_page": 100, "page": 2}
    assert calls[2][1]["params"] == {"per_page": 100, "page": 3}


def test_get_pull_request_file_changes_filter_no_patch(mock_requests, mock_create_headers):
    """Test filtering of files without patch field."""
    mock_response_data = [
        {
            "filename": "file1.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,1 @@\n-old\n+new"
        },
        {
            "filename": "file2.js",
            "status": "renamed"
            # No patch field - should be filtered out
        },
        {
            "filename": "file3.txt",
            "status": "added",
            "patch": "@@ -0,0 +1,1 @@\n+content"
        },
        {
            "filename": "binary_file.png",
            "status": "added"
            # No patch field - should be filtered out
        }
    ]

    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None

    empty_response = Mock()
    empty_response.json.return_value = []
    empty_response.raise_for_status.return_value = None

    mock_requests.get.side_effect = [mock_response, empty_response]

    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    expected = [
        {
            "filename": "file1.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,1 @@\n-old\n+new"
        },
        {
            "filename": "file3.txt",
            "status": "added",
            "patch": "@@ -0,0 +1,1 @@\n+content"
        }
    ]

    assert result == expected


def test_get_pull_request_file_changes_empty_response(mock_requests, mock_create_headers):
    """Test handling of empty response."""
    mock_response = Mock()
    mock_response.json.return_value = []
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response

    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    assert result == []
    mock_create_headers.assert_called_once_with(token="test_token")
    mock_requests.get.assert_called_once()


def test_get_pull_request_file_changes_http_error_404(mock_requests, mock_create_headers):
    """Test handling of 404 HTTP error."""
    mock_response = Mock()
    mock_response.status_code = 404
    http_error = requests.exceptions.HTTPError("404 Not Found")
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error
    mock_requests.get.return_value = mock_response

    # Should return None due to handle_exceptions decorator
    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/999/files", "test_token"
    )

    assert result is None


def test_get_pull_request_file_changes_http_error_500(mock_requests, mock_create_headers):
    """Test handling of 500 HTTP error."""
    mock_response = Mock()
    mock_response.status_code = 500
    http_error = requests.exceptions.HTTPError("500 Internal Server Error")
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error
    mock_requests.get.return_value = mock_response

    # Should return None due to handle_exceptions decorator
    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    assert result is None


def test_get_pull_request_file_changes_network_error(mock_requests, mock_create_headers):
    """Test handling of network connection error."""
    mock_requests.get.side_effect = requests.exceptions.ConnectionError("Network error")

    # Should return None due to handle_exceptions decorator
    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    assert result is None


def test_get_pull_request_file_changes_timeout_error(mock_requests, mock_create_headers):
    """Test handling of timeout error."""
    mock_requests.get.side_effect = requests.exceptions.Timeout("Request timeout")

    # Should return None due to handle_exceptions decorator
    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    assert result is None


def test_get_pull_request_file_changes_json_decode_error(mock_requests, mock_create_headers):
    """Test handling of JSON decode error."""
    mock_response = Mock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response

    # Should return None due to handle_exceptions decorator
    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    assert result is None


def test_get_pull_request_file_changes_request_parameters(mock_requests, mock_create_headers):
    """Test that request parameters are correctly set."""
    mock_response = Mock()
    mock_response.json.return_value = []
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response

    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "custom_token"

    get_pull_request_file_changes(url, token)

    # Verify headers creation
    mock_create_headers.assert_called_once_with(token=token)

    # Verify request parameters
    mock_requests.get.assert_called_once_with(
        url=url,
        headers={"Authorization": "Bearer test_token"},
        params={"per_page": 100, "page": 1},
        timeout=120
    )


def test_get_pull_request_file_changes_large_patch(mock_requests, mock_create_headers):
    """Test handling of files with large patch content."""
    large_patch = "@@ -1,100 +1,100 @@\n" + "\n".join([f"-old line {i}\n+new line {i}" for i in range(50)])
    
    mock_response_data = [
        {
            "filename": "large_file.py",
            "status": "modified",
            "patch": large_patch
        }
    ]

    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None

    empty_response = Mock()
    empty_response.json.return_value = []
    empty_response.raise_for_status.return_value = None

    mock_requests.get.side_effect = [mock_response, empty_response]

    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    expected = [
        {
            "filename": "large_file.py",
            "status": "modified",
            "patch": large_patch
        }
    ]

    assert result == expected


def test_get_pull_request_file_changes_mixed_file_types(mock_requests, mock_create_headers):
    """Test handling of mixed file types and statuses."""
    mock_response_data = [
        {
            "filename": "src/main.py",
            "status": "modified",
            "patch": "@@ -10,1 +10,1 @@\n-    old_code()\n+    new_code()"
        },
        {
            "filename": "tests/test_main.py",
            "status": "added",
            "patch": "@@ -0,0 +1,10 @@\n+def test_new_feature():\n+    assert True"
        },
        {
            "filename": "old_file.py",
            "status": "removed",
            "patch": "@@ -1,5 +0,0 @@\n-def old_function():\n-    pass"
        },
        {
            "filename": "README.md",
            "status": "modified",
            "patch": "@@ -1,1 +1,2 @@\n # Project\n+\n+Updated documentation"
        }
    ]

    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None

    empty_response = Mock()
    empty_response.json.return_value = []
    empty_response.raise_for_status.return_value = None

    mock_requests.get.side_effect = [mock_response, empty_response]

    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    assert len(result) == 4
    assert all("filename" in change and "status" in change and "patch" in change for change in result)
    
    # Verify specific files are included
    filenames = [change["filename"] for change in result]
    assert "src/main.py" in filenames
    assert "tests/test_main.py" in filenames
    assert "old_file.py" in filenames
    assert "README.md" in filenames


def test_get_pull_request_file_changes_special_characters_in_filename(mock_requests, mock_create_headers):
    """Test handling of filenames with special characters."""
    mock_response_data = [
        {
            "filename": "file with spaces.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,1 @@\n-old\n+new"
        },
        {
            "filename": "file-with-dashes.js",
            "status": "added",
            "patch": "@@ -0,0 +1,1 @@\n+content"
        },
        {
            "filename": "file_with_underscores.txt",
            "status": "modified",
            "patch": "@@ -1,1 +1,1 @@\n-before\n+after"
        }
    ]

    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None

    empty_response = Mock()
    empty_response.json.return_value = []
    empty_response.raise_for_status.return_value = None

    mock_requests.get.side_effect = [mock_response, empty_response]

    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    assert len(result) == 3
    filenames = [change["filename"] for change in result]
    assert "file with spaces.py" in filenames
    assert "file-with-dashes.js" in filenames
    assert "file_with_underscores.txt" in filenames


def test_get_pull_request_file_changes_empty_patch(mock_requests, mock_create_headers):
    """Test handling of files with empty patch content."""
    mock_response_data = [
        {
            "filename": "file1.py",
            "status": "modified",
            "patch": ""  # Empty patch
        },
        {
            "filename": "file2.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,1 @@\n-old\n+new"  # Non-empty patch
        }
    ]

    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None

    empty_response = Mock()
    empty_response.json.return_value = []
    empty_response.raise_for_status.return_value = None

    mock_requests.get.side_effect = [mock_response, empty_response]

    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    # Both files should be included, even with empty patch
    assert len(result) == 2
    assert result[0]["filename"] == "file1.py"
    assert result[0]["patch"] == ""
    assert result[1]["filename"] == "file2.py"
    assert result[1]["patch"] == "@@ -1,1 +1,1 @@\n-old\n+new"


def test_get_pull_request_file_changes_rate_limit_403_with_retry(mock_requests, mock_create_headers, mock_time):
    """Test handling of 403 rate limit error with retry logic."""
    # Mock current time
    mock_time.time.return_value = 1000
    
    # First call hits rate limit
    mock_response_rate_limit = Mock()
    mock_response_rate_limit.status_code = 403
    mock_response_rate_limit.reason = "rate limit exceeded"
    mock_response_rate_limit.text = "API rate limit exceeded"
    mock_response_rate_limit.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Used": "5000",
        "X-RateLimit-Reset": "1065"  # Reset in 65 seconds + 5 buffer = 70 seconds wait
    }
    
    rate_limit_error = requests.exceptions.HTTPError("403 Forbidden")
    rate_limit_error.response = mock_response_rate_limit
    mock_response_rate_limit.raise_for_status.side_effect = rate_limit_error
    
    # Second call succeeds after retry
    mock_response_success = Mock()
    mock_response_success.json.return_value = [
        {
            "filename": "test.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,1 @@\n-old\n+new"
        }
    ]
    mock_response_success.raise_for_status.return_value = None
    
    # Empty response for pagination
    empty_response = Mock()
    empty_response.json.return_value = []
    empty_response.raise_for_status.return_value = None
    
    mock_requests.get.side_effect = [mock_response_rate_limit, mock_response_success, empty_response]

    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    expected = [
        {
            "filename": "test.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,1 @@\n-old\n+new"
        }
    ]

    assert result == expected
    # Verify sleep was called with correct duration (65 + 5 = 70 seconds)
    mock_time.sleep.assert_called_once_with(70)
    # Should make 3 calls total: rate limit, retry success, pagination check
    assert mock_requests.get.call_count == 3


def test_get_pull_request_file_changes_rate_limit_429_secondary(mock_requests, mock_create_headers, mock_time):
    """Test handling of 429 secondary rate limit error."""
    # First call hits secondary rate limit
    mock_response_rate_limit = Mock()
    mock_response_rate_limit.status_code = 429
    mock_response_rate_limit.reason = "Too Many Requests"
    mock_response_rate_limit.text = "You have exceeded a secondary rate limit"
    mock_response_rate_limit.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4000",
        "X-RateLimit-Used": "1000",
        "Retry-After": "30"
    }
    
    rate_limit_error = requests.exceptions.HTTPError("429 Too Many Requests")
    rate_limit_error.response = mock_response_rate_limit
    mock_response_rate_limit.raise_for_status.side_effect = rate_limit_error
    
    # Second call succeeds after retry
    mock_response_success = Mock()
    mock_response_success.json.return_value = [
        {
            "filename": "test.py",
            "status": "added",
            "patch": "@@ -0,0 +1,1 @@\n+new content"
        }
    ]
    mock_response_success.raise_for_status.return_value = None
    
    # Empty response for pagination
    empty_response = Mock()
    empty_response.json.return_value = []
    empty_response.raise_for_status.return_value = None
    
    mock_requests.get.side_effect = [mock_response_rate_limit, mock_response_success, empty_response]

    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    expected = [
        {
            "filename": "test.py",
            "status": "added",
            "patch": "@@ -0,0 +1,1 @@\n+new content"
        }
    ]

    assert result == expected
    # Verify sleep was called with Retry-After value
    mock_time.sleep.assert_called_once_with(30)
    assert mock_requests.get.call_count == 3


def test_get_pull_request_file_changes_rate_limit_already_reset(mock_requests, mock_create_headers, mock_time):
    """Test handling of rate limit when reset time has already passed."""
    # Mock current time to be after reset time
    mock_time.time.return_value = 2000
    
    # First call hits rate limit but reset time has passed
    mock_response_rate_limit = Mock()
    mock_response_rate_limit.status_code = 403
    mock_response_rate_limit.reason = "rate limit exceeded"
    mock_response_rate_limit.text = "API rate limit exceeded"
    mock_response_rate_limit.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Used": "5000",
        "X-RateLimit-Reset": "1500"  # Reset time in the past
    }
    
    rate_limit_error = requests.exceptions.HTTPError("403 Forbidden")
    rate_limit_error.response = mock_response_rate_limit
    mock_response_rate_limit.raise_for_status.side_effect = rate_limit_error
    
    # Second call succeeds after minimal wait
    mock_response_success = Mock()
    mock_response_success.json.return_value = []
    mock_response_success.raise_for_status.return_value = None
    
    mock_requests.get.side_effect = [mock_response_rate_limit, mock_response_success]

    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    assert result == []
    # Should sleep for minimal time (1 second) since reset time has passed
    mock_time.sleep.assert_called_once_with(1)
    assert mock_requests.get.call_count == 2


def test_get_pull_request_file_changes_http_error_401(mock_requests, mock_create_headers):
    """Test handling of 401 Unauthorized error."""
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.reason = "Unauthorized"
    mock_response.text = "Bad credentials"
    http_error = requests.exceptions.HTTPError("401 Unauthorized")
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error
    mock_requests.get.return_value = mock_response

    # Should return None due to handle_exceptions decorator
    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "invalid_token"
    )

    assert result is None


def test_get_pull_request_file_changes_http_error_422(mock_requests, mock_create_headers):
    """Test handling of 422 Unprocessable Entity error."""
    mock_response = Mock()
    mock_response.status_code = 422
    mock_response.reason = "Unprocessable Entity"
    mock_response.text = "Validation Failed"
    http_error = requests.exceptions.HTTPError("422 Unprocessable Entity")
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error
    mock_requests.get.return_value = mock_response

    # Should return None due to handle_exceptions decorator
    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/invalid/files", "test_token"
    )

    assert result is None


def test_get_pull_request_file_changes_key_error_in_response(mock_requests, mock_create_headers):
    """Test handling of missing required keys in API response."""
    # Response with missing 'status' field
    mock_response_data = [
        {
            "filename": "file1.py",
            # Missing 'status' field
            "patch": "@@ -1,1 +1,1 @@\n-old\n+new"
        }
    ]

    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response

    # Should return None due to handle_exceptions decorator catching KeyError
    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    assert result is None


def test_get_pull_request_file_changes_attribute_error(mock_requests, mock_create_headers):
    """Test handling of AttributeError in response processing."""
    mock_response = Mock()
    # Simulate AttributeError when accessing json method
    mock_response.json = None
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response

    # Should return None due to handle_exceptions decorator catching AttributeError
    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    assert result is None


def test_get_pull_request_file_changes_extensive_pagination(mock_requests, mock_create_headers):
    """Test handling of extensive pagination with many pages."""
    # Create 5 pages of data
    pages_data = []
    for page_num in range(5):
        page_data = [
            {
                "filename": f"file_{page_num}_{i}.py",
                "status": "modified",
                "patch": f"@@ -1,1 +1,1 @@\n-old_{page_num}_{i}\n+new_{page_num}_{i}"
            }
            for i in range(2)  # 2 files per page
        ]
        pages_data.append(page_data)
    
    # Add empty page to end pagination
    pages_data.append([])
    
    # Create mock responses
    mock_responses = []
    for page_data in pages_data:
        mock_response = Mock()
        mock_response.json.return_value = page_data
        mock_response.raise_for_status.return_value = None
        mock_responses.append(mock_response)
    
    mock_requests.get.side_effect = mock_responses

    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    # Should have 10 files total (5 pages * 2 files per page)
    assert len(result) == 10
    
    # Verify all files are included
    for page_num in range(5):
        for i in range(2):
            expected_filename = f"file_{page_num}_{i}.py"
            assert any(change["filename"] == expected_filename for change in result)
    
    # Verify 6 requests were made (5 pages + 1 empty page)
    assert mock_requests.get.call_count == 6
    
    # Verify pagination parameters
    calls = mock_requests.get.call_args_list
    for i, call in enumerate(calls):
        assert call[1]["params"] == {"per_page": 100, "page": i + 1}


def test_get_pull_request_file_changes_unicode_content(mock_requests, mock_create_headers):
    """Test handling of files with unicode characters in content."""
    mock_response_data = [
        {
            "filename": "unicode_file.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,1 @@\n-# 旧いコード\n+# 新しいコード"
        },
        {
            "filename": "émoji_file.js",
            "status": "added",
            "patch": "@@ -0,0 +1,1 @@\n+console.log('Hello 🌍');"
        }
    ]

    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None

    empty_response = Mock()
    empty_response.json.return_value = []
    empty_response.raise_for_status.return_value = None

    mock_requests.get.side_effect = [mock_response, empty_response]

    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    expected = [
        {
            "filename": "unicode_file.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,1 @@\n-# 旧いコード\n+# 新しいコード"
        },
        {
            "filename": "émoji_file.js",
            "status": "added",
            "patch": "@@ -0,0 +1,1 @@\n+console.log('Hello 🌍');"
        }
    ]

    assert result == expected


def test_get_pull_request_file_changes_malformed_json_response(mock_requests, mock_create_headers):
    """Test handling of malformed JSON response."""
    mock_response = Mock()
    # Simulate JSON decode error with malformed response
    json_error = ValueError("Expecting ',' delimiter: line 1 column 15 (char 14)")
    json_error.doc = '{"filename": "test"'  # Malformed JSON
    mock_response.json.side_effect = json_error
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response

    # Should return None due to handle_exceptions decorator
    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    assert result is None


def test_get_pull_request_file_changes_type_error_in_processing(mock_requests, mock_create_headers):
    """Test handling of TypeError during response processing."""
    # Response with wrong data type (string instead of list)
    mock_response = Mock()
    mock_response.json.return_value = "invalid_response_type"
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response

    # Should return None due to handle_exceptions decorator catching TypeError
    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    assert result is None


def test_get_pull_request_file_changes_none_response_data(mock_requests, mock_create_headers):
    """Test handling of None response from API."""
    mock_response = Mock()
    mock_response.json.return_value = None
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response

    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    # Should return empty list since None is falsy and breaks the loop
    assert result == []


def test_get_pull_request_file_changes_mixed_valid_invalid_files(mock_requests, mock_create_headers):
    """Test handling of mixed valid and invalid file entries."""
    mock_response_data = [
        {
            "filename": "valid_file.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,1 @@\n-old\n+new"
        },
        {
            "filename": "no_patch_file.js",
            "status": "renamed"
            # No patch field - should be filtered out
        },
        {
            "filename": "another_valid_file.txt",
            "status": "added",
            "patch": "@@ -0,0 +1,1 @@\n+content"
        },
        None,  # Invalid entry - should be handled gracefully
        {
            "filename": "final_valid_file.md",
            "status": "modified",
            "patch": "@@ -1,1 +1,2 @@\n # Title\n+\n+Content"
        }
    ]

    mock_response = Mock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None

    empty_response = Mock()
    empty_response.json.return_value = []
    empty_response.raise_for_status.return_value = None

    mock_requests.get.side_effect = [mock_response, empty_response]

    # Should return None due to handle_exceptions decorator catching the error
    # when trying to access 'patch' key on None entry
    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    assert result is None