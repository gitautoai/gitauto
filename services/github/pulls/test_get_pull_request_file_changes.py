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
        "filename": "src/example.py",
        "status": "modified",
        "patch": "@@ -1,3 +1,4 @@\n def hello():\n+    print('world')\n     pass",
        "additions": 1,
        "deletions": 0,
        "changes": 1
    }


@pytest.fixture
def mock_file_without_patch():
    """Mock file data without patch information (e.g., binary file)."""
    return {
        "filename": "assets/image.png",
        "status": "added",
        "additions": 0,
        "deletions": 0,
        "changes": 0
    }


@pytest.fixture
def mock_multiple_files():
    """Mock multiple files with mixed patch availability."""
    return [
        {
            "filename": "src/file1.py",
            "status": "modified",
            "patch": "@@ -1,2 +1,3 @@\n def func1():\n+    print('modified')\n     pass",
        },
        {
            "filename": "assets/binary.jpg",
            "status": "added",
            # No patch field for binary files
        },
        {
            "filename": "src/file2.py",
            "status": "added",
            "patch": "@@ -0,0 +1,3 @@\n+def new_function():\n+    return True\n+",
        },
        {
            "filename": "README.md",
            "status": "deleted",
            "patch": "@@ -1,5 +0,0 @@\n-# Old README\n-\n-This is old content\n-\n-To be removed",
        }
    ]


def test_get_pull_request_file_changes_success_single_page():
    """Test successful retrieval of file changes from a single page."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    mock_files = [
        {
            "filename": "src/example.py",
            "status": "modified",
            "patch": "@@ -1,3 +1,4 @@\n def hello():\n+    print('world')\n     pass",
        }
    ]
    
    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock_headers:
        
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = mock_files
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}
        
        # Call function
        result = get_pull_request_file_changes(url, token)
        
        # Verify API call
        mock_get.assert_called_once_with(
            url=url,
            headers={"Authorization": "Bearer test_token"},
            params={"per_page": 100, "page": 1},
            timeout=120,
        )
        mock_response.raise_for_status.assert_called_once()
        mock_headers.assert_called_once_with(token=token)
        
        # Verify result
        expected = [
            {
                "filename": "src/example.py",
                "status": "modified",
                "patch": "@@ -1,3 +1,4 @@\n def hello():\n+    print('world')\n     pass",
            }
        ]
        assert result == expected


def test_get_pull_request_file_changes_success_multiple_pages():
    """Test successful retrieval of file changes across multiple pages."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    # First page
    page1_files = [
        {
            "filename": "src/file1.py",
            "status": "modified",
            "patch": "@@ -1,2 +1,3 @@\n def func1():\n+    print('page1')\n     pass",
        }
    ]
    
    # Second page
    page2_files = [
        {
            "filename": "src/file2.py",
            "status": "added",
            "patch": "@@ -0,0 +1,2 @@\n+def func2():\n+    return 'page2'",
        }
    ]
    
    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock_headers:
        
        # Setup mocks for pagination
        mock_response1 = MagicMock()
        mock_response1.json.return_value = page1_files
        
        mock_response2 = MagicMock()
        mock_response2.json.return_value = page2_files
        
        mock_response3 = MagicMock()
        mock_response3.json.return_value = []  # Empty page to end pagination
        
        mock_get.side_effect = [mock_response1, mock_response2, mock_response3]
        mock_headers.return_value = {"Authorization": "Bearer test_token"}
        
        # Call function
        result = get_pull_request_file_changes(url, token)
        
        # Verify API calls for all pages
        assert mock_get.call_count == 3
        mock_get.assert_any_call(
            url=url,
            headers={"Authorization": "Bearer test_token"},
            params={"per_page": 100, "page": 1},
            timeout=120,
        )
        mock_get.assert_any_call(
            url=url,
            headers={"Authorization": "Bearer test_token"},
            params={"per_page": 100, "page": 2},
            timeout=120,
        )
        mock_get.assert_any_call(
            url=url,
            headers={"Authorization": "Bearer test_token"},
            params={"per_page": 100, "page": 3},
            timeout=120,
        )
        
        # Verify result contains files from both pages
        expected = [
            {
                "filename": "src/file1.py",
                "status": "modified",
                "patch": "@@ -1,2 +1,3 @@\n def func1():\n+    print('page1')\n     pass",
            },
            {
                "filename": "src/file2.py",
                "status": "added",
                "patch": "@@ -0,0 +1,2 @@\n+def func2():\n+    return 'page2'",
            }
        ]
        assert result == expected


def test_get_pull_request_file_changes_filters_files_without_patch():
    """Test that files without patch field are filtered out."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    mock_files = [
        {
            "filename": "src/text_file.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,2 @@\n print('hello')\n+print('world')",
        },
        {
            "filename": "assets/binary_file.jpg",
            "status": "added",
            # No patch field - should be filtered out
        },
        {
            "filename": "docs/readme.md",
            "status": "deleted",
            "patch": "@@ -1,3 +0,0 @@\n-# Documentation\n-\n-Content removed",
        }
    ]
    
    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock_headers:
        
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = mock_files
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}
        
        # Call function
        result = get_pull_request_file_changes(url, token)
        
        # Verify only files with patch are included
        expected = [
            {
                "filename": "src/text_file.py",
                "status": "modified",
                "patch": "@@ -1,1 +1,2 @@\n print('hello')\n+print('world')",
            },
            {
                "filename": "docs/readme.md",
                "status": "deleted",
                "patch": "@@ -1,3 +0,0 @@\n-# Documentation\n-\n-Content removed",
            }
        ]
        assert result == expected
        assert len(result) == 2  # Binary file should be filtered out


def test_get_pull_request_file_changes_empty_response():
    """Test handling of empty response (no files changed)."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock_headers:
        
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}
        
        # Call function
        result = get_pull_request_file_changes(url, token)
        
        # Verify API call
        mock_get.assert_called_once_with(
            url=url,
            headers={"Authorization": "Bearer test_token"},
            params={"per_page": 100, "page": 1},
            timeout=120,
        )
        
        # Verify empty result
        assert result == []


def test_get_pull_request_file_changes_http_error_404():
    """Test handling of 404 HTTP error."""
    url = "https://api.github.com/repos/owner/repo/pulls/999/files"
    token = "test_token"
    
    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
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
        
        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request_file_changes(url, token)
        
        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_file_changes_http_error_500():
    """Test handling of 500 HTTP error."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock_headers:
        
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "Internal Server Error"
        
        http_error = requests.exceptions.HTTPError("500 Server Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}
        
        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request_file_changes(url, token)
        
        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_file_changes_network_error():
    """Test handling of network connection error."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock_headers:
        
        # Setup mocks
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        mock_headers.return_value = {"Authorization": "Bearer test_token"}
        
        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request_file_changes(url, token)
        
        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_file_changes_timeout_error():
    """Test handling of timeout error."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock_headers:
        
        # Setup mocks
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        mock_headers.return_value = {"Authorization": "Bearer test_token"}
        
        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request_file_changes(url, token)
        
        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_file_changes_json_decode_error():
    """Test handling of JSON decode error."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock_headers:
        
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}
        
        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request_file_changes(url, token)
        
        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_file_changes_headers_creation():
    """Test that headers are created correctly with the provided token."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "custom_test_token"
    
    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock_headers:
        
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer custom_test_token"}
        
        # Call function
        get_pull_request_file_changes(url, token)
        
        # Verify headers creation with correct token
        mock_headers.assert_called_once_with(token="custom_test_token")


def test_get_pull_request_file_changes_different_file_statuses():
    """Test handling of different file statuses (added, modified, deleted, renamed)."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    mock_files = [
        {
            "filename": "new_file.py",
            "status": "added",
            "patch": "@@ -0,0 +1,3 @@\n+def new_function():\n+    return 'added'\n+",
        },
        {
            "filename": "existing_file.py",
            "status": "modified",
            "patch": "@@ -1,2 +1,3 @@\n def existing():\n+    print('modified')\n     pass",
        },
        {
            "filename": "old_file.py",
            "status": "deleted",
            "patch": "@@ -1,5 +0,0 @@\n-def old_function():\n-    return 'deleted'\n-\n-# This file is removed\n-",
        },
        {
            "filename": "renamed_file.py",
            "status": "renamed",
            "patch": "@@ -1,1 +1,2 @@\n def renamed():\n+    print('renamed')\n     pass",
        }
    ]
    
    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock_headers:
        
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = mock_files
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}
        
        # Call function
        result = get_pull_request_file_changes(url, token)
        
        # Verify all file statuses are handled correctly
        assert len(result) == 4
        statuses = [file["status"] for file in result]
        assert "added" in statuses
        assert "modified" in statuses
        assert "deleted" in statuses
        assert "renamed" in statuses
        
        # Verify structure of returned data
        for file_change in result:
            assert "filename" in file_change
            assert "status" in file_change
            assert "patch" in file_change
            assert len(file_change) == 3  # Only these three fields should be present


def test_get_pull_request_file_changes_create_headers_error():
    """Test handling of create_headers function error."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"
    
    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock_headers:
        
        # Setup mocks
        mock_headers.side_effect = Exception("Header creation failed")
        
        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request_file_changes(url, token)
        
        # Verify result is None (default_return_value from decorator)
        assert result is None
        
        # Verify requests.get was not called due to header creation failure
        mock_get.assert_not_called()
