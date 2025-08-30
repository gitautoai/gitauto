# Standard imports
from unittest.mock import MagicMock, patch

# Third party imports
import pytest
import requests

# Local imports
from services.github.pulls.get_pull_request_file_changes import get_pull_request_file_changes


@pytest.fixture
def mock_file_with_patch():
    """Mock file data with patch information."""
    return {
        "filename": "src/main.py",
        "status": "modified",
        "patch": "@@ -1,3 +1,4 @@\n import os\n+import sys\n from config import settings\n def main():",
        "additions": 1,
        "deletions": 0,
        "changes": 1,
    }


@pytest.fixture
def mock_file_without_patch():
    """Mock file data without patch information (binary file)."""
    return {
        "filename": "assets/image.png",
        "status": "added",
        "additions": 0,
        "deletions": 0,
        "changes": 0,
    }


@pytest.fixture
def mock_headers():
    """Mock headers for API requests."""
    return {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": "Bearer test_token",
        "User-Agent": "GitAuto",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def test_get_pull_request_file_changes_success_single_page(mock_file_with_patch, mock_headers):
    """Test successful retrieval of file changes with single page."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    with patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get, \
         patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers:
        
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = [mock_file_with_patch]
        mock_get.return_value = mock_response
        mock_create_headers.return_value = mock_headers
        
        # Call function
        result = get_pull_request_file_changes(url, token)
        
        # Verify API call
        mock_get.assert_called_once_with(
            url=url,
            headers=mock_headers,
            params={"per_page": 100, "page": 1},
            timeout=120
        )
        mock_response.raise_for_status.assert_called_once()
        mock_create_headers.assert_called_once_with(token=token)
        
        # Verify result
        expected = [{
            "filename": "src/main.py",
            "status": "modified",
            "patch": "@@ -1,3 +1,4 @@\n import os\n+import sys\n from config import settings\n def main():"
        }]
        assert result == expected
        assert len(result) == 1


def test_get_pull_request_file_changes_success_multiple_pages(mock_file_with_patch, mock_headers):
    """Test successful retrieval of file changes with multiple pages."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    # Create different files for each page
    file_page_1 = mock_file_with_patch.copy()
    file_page_2 = {
        "filename": "src/utils.py",
        "status": "added",
        "patch": "@@ -0,0 +1,5 @@\n+def helper():\n+    return True\n+\n+def another():\n+    pass"
    }
    
    with patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get, \
         patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers:
        
        # Setup mocks for pagination
        mock_response_1 = MagicMock()
        mock_response_1.json.return_value = [file_page_1]
        
        mock_response_2 = MagicMock()
        mock_response_2.json.return_value = [file_page_2]
        
        mock_response_3 = MagicMock()
        mock_response_3.json.return_value = []  # Empty response to end pagination
        
        mock_get.side_effect = [mock_response_1, mock_response_2, mock_response_3]
        mock_create_headers.return_value = mock_headers
        
        # Call function
        result = get_pull_request_file_changes(url, token)
        
        # Verify API calls for pagination
        assert mock_get.call_count == 3
        mock_get.assert_any_call(
            url=url,
            headers=mock_headers,
            params={"per_page": 100, "page": 1},
            timeout=120
        )
        mock_get.assert_any_call(
            url=url,
            headers=mock_headers,
            params={"per_page": 100, "page": 2},
            timeout=120
        )
        mock_get.assert_any_call(
            url=url,
            headers=mock_headers,
            params={"per_page": 100, "page": 3},
            timeout=120
        )
        
        # Verify result contains files from both pages
        expected = [
            {
                "filename": "src/main.py",
                "status": "modified",
                "patch": "@@ -1,3 +1,4 @@\n import os\n+import sys\n from config import settings\n def main():"
            },
            {
                "filename": "src/utils.py",
                "status": "added",
                "patch": "@@ -0,0 +1,5 @@\n+def helper():\n+    return True\n+\n+def another():\n+    pass"
            }
        ]
        assert result == expected
        assert len(result) == 2


def test_get_pull_request_file_changes_skip_files_without_patch(mock_file_with_patch, mock_file_without_patch, mock_headers):
    """Test that files without patch data are skipped."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    with patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get, \
         patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers:
        
        # Setup mocks with mixed files (with and without patch)
        mock_response = MagicMock()
        mock_response.json.return_value = [mock_file_with_patch, mock_file_without_patch]
        mock_get.return_value = mock_response
        mock_create_headers.return_value = mock_headers
        
        # Call function
        result = get_pull_request_file_changes(url, token)
        
        # Verify only file with patch is included
        expected = [{
            "filename": "src/main.py",
            "status": "modified",
            "patch": "@@ -1,3 +1,4 @@\n import os\n+import sys\n from config import settings\n def main():"
        }]
        assert result == expected
        assert len(result) == 1


def test_get_pull_request_file_changes_empty_response(mock_headers):
    """Test handling of empty response (no files)."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    with patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get, \
         patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers:
        
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        mock_create_headers.return_value = mock_headers
        
        # Call function
        result = get_pull_request_file_changes(url, token)
        
        # Verify API call
        mock_get.assert_called_once_with(
            url=url,
            headers=mock_headers,
            params={"per_page": 100, "page": 1},
            timeout=120
        )
        
        # Verify result is empty list
        assert result == []


def test_get_pull_request_file_changes_http_error_404(mock_headers):
    """Test handling of 404 HTTP error."""
    url = "https://api.github.com/repos/owner/repo/pulls/999/files"
    token = "test_token"
    
    with patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get, \
         patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers:
        
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Not Found"
        
        http_error = requests.exceptions.HTTPError("404 Client Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        
        mock_get.return_value = mock_response
        mock_create_headers.return_value = mock_headers
        
        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request_file_changes(url, token)
        
        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_file_changes_http_error_500(mock_headers):
    """Test handling of 500 HTTP error."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    with patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get, \
         patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers:
        
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "Internal Server Error"
        
        http_error = requests.exceptions.HTTPError("500 Server Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        
        mock_get.return_value = mock_response
        mock_create_headers.return_value = mock_headers
        
        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request_file_changes(url, token)
        
        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_file_changes_rate_limit_403(mock_headers):
    """Test handling of 403 rate limit error."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    with patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get, \
         patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers:
        
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.reason = "Forbidden"
        mock_response.text = "API rate limit exceeded"
        mock_response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Used": "5000",
            "X-RateLimit-Reset": "1640995200"
        }
        
        http_error = requests.exceptions.HTTPError("403 Client Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        
        mock_get.return_value = mock_response
        mock_create_headers.return_value = mock_headers
        
        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request_file_changes(url, token)
        
        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_file_changes_network_error(mock_headers):
    """Test handling of network connection error."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    with patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get, \
         patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers:
        
        # Setup mocks
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        mock_create_headers.return_value = mock_headers
        
        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request_file_changes(url, token)
        
        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_file_changes_timeout_error(mock_headers):
    """Test handling of timeout error."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    with patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get, \
         patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers:
        
        # Setup mocks
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        mock_create_headers.return_value = mock_headers
        
        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request_file_changes(url, token)
        
        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_file_changes_json_decode_error(mock_headers):
    """Test handling of JSON decode error."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    with patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get, \
         patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers:
        
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        mock_create_headers.return_value = mock_headers
        
        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request_file_changes(url, token)
        
        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_file_changes_headers_creation():
    """Test that headers are created correctly."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "custom_token"
    
    with patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get, \
         patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers:
        
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {"Authorization": "Bearer custom_token"}
        
        # Call function
        get_pull_request_file_changes(url, token)
        
        # Verify headers creation
        mock_create_headers.assert_called_once_with(token="custom_token")


def test_get_pull_request_file_changes_url_and_params():
    """Test that URL and parameters are passed correctly."""
    url = "https://api.github.com/repos/test-owner/test-repo/pulls/456/files"
    token = "test_token"
    
    with patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get, \
         patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers:
        
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        mock_create_headers.return_value = {"Authorization": "Bearer test_token"}
        
        # Call function
        get_pull_request_file_changes(url, token)
        
        # Verify URL and parameters
        mock_get.assert_called_once_with(
            url=url,
            headers={"Authorization": "Bearer test_token"},
            params={"per_page": 100, "page": 1},
            timeout=120
        )


def test_get_pull_request_file_changes_file_data_extraction(mock_headers):
    """Test that file data is extracted correctly."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    # Mock file with additional fields that should not be included in result
    mock_file = {
        "filename": "test.py",
        "status": "modified",
        "patch": "@@ -1,1 +1,2 @@\n print('hello')\n+print('world')",
        "additions": 1,
        "deletions": 0,
        "changes": 1,
        "blob_url": "https://github.com/owner/repo/blob/abc123/test.py",
        "raw_url": "https://github.com/owner/repo/raw/abc123/test.py",
        "contents_url": "https://api.github.com/repos/owner/repo/contents/test.py?ref=abc123",
        "sha": "abc123def456"
    }
    
    with patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get, \
         patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers:
        
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = [mock_file]
        mock_get.return_value = mock_response
        mock_create_headers.return_value = mock_headers
        
        # Call function
        result = get_pull_request_file_changes(url, token)
        
        # Verify only filename, status, and patch are extracted
        expected = [{
            "filename": "test.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,2 @@\n print('hello')\n+print('world')"
        }]
        assert result == expected
        assert len(result) == 1
        
        # Verify no extra fields are included
        result_file = result[0]
        assert "additions" not in result_file
        assert "deletions" not in result_file
        assert "changes" not in result_file
        assert "blob_url" not in result_file
        assert "raw_url" not in result_file
        assert "contents_url" not in result_file
        assert "sha" not in result_file


def test_get_pull_request_file_changes_mixed_file_statuses(mock_headers):
    """Test handling of files with different statuses."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    mock_files = [
        {
            "filename": "added_file.py",
            "status": "added",
            "patch": "@@ -0,0 +1,3 @@\n+def new_function():\n+    return True\n+"
        },
        {
            "filename": "modified_file.py",
            "status": "modified",
            "patch": "@@ -1,3 +1,4 @@\n import os\n+import sys\n from config import settings\n def main():"
        },
        {
            "filename": "deleted_file.py",
            "status": "removed",
            "patch": "@@ -1,5 +0,0 @@\n-def old_function():\n-    return False\n-\n-def another():\n-    pass"
        }
    ]
    
    with patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get, \
         patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers:
        
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = mock_files
        mock_get.return_value = mock_response
        mock_create_headers.return_value = mock_headers
        
        # Call function
        result = get_pull_request_file_changes(url, token)
        
        # Verify all files with different statuses are included
        expected = [
            {
                "filename": "added_file.py",
                "status": "added",
                "patch": "@@ -0,0 +1,3 @@\n+def new_function():\n+    return True\n+"
            },
            {
                "filename": "modified_file.py",
                "status": "modified",
                "patch": "@@ -1,3 +1,4 @@\n import os\n+import sys\n from config import settings\n def main():"
            },
            {
                "filename": "deleted_file.py",
                "status": "removed",
                "patch": "@@ -1,5 +0,0 @@\n-def old_function():\n-    return False\n-\n-def another():\n-    pass"
            }
        ]
        assert result == expected
        assert len(result) == 3
