# Standard imports
from unittest.mock import MagicMock, patch

# Third party imports
import pytest
import requests

# Local imports
from services.github.pulls.get_pull_request_file_changes import get_pull_request_file_changes
from config import PER_PAGE, TIMEOUT


@pytest.fixture
def mock_headers():
    return {"Authorization": "Bearer test_token", "Accept": "application/vnd.github.v3+json"}


@pytest.fixture
def mock_file_data():
    return [
        {
            "filename": "file1.py",
            "status": "modified",
            "patch": "@@ -1,5 +1,7 @@\n def test():\n-    return True\n+    # Added comment\n+    return True\n",
        },
        {
            "filename": "file2.py",
            "status": "added",
            "patch": "@@ -0,0 +1,3 @@\n+def new_function():\n+    return 'new'\n+",
        },
        {
            "filename": "file3.py",
            "status": "removed",
            "patch": "@@ -1,3 +0,0 @@\n-def old_function():\n-    return 'old'\n-",
        },
    ]


@pytest.fixture
def mock_file_data_without_patch():
    return [
        {
            "filename": "binary_file.bin",
            "status": "modified",
            # No patch for binary files
        }
    ]


def test_get_pull_request_file_changes_success(mock_headers, mock_file_data):
    """Test successful retrieval of pull request file changes."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"

    with patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers, \
         patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get:
        
        # Setup mocks
        mock_create_headers.return_value = mock_headers
        
        # Mock response for a single page of results
        mock_response = MagicMock()
        mock_response.json.return_value = mock_file_data
        mock_get.return_value = mock_response
        
        # Call function
        result = get_pull_request_file_changes(url, token)
        
        # Verify API call
        mock_create_headers.assert_called_once_with(token=token)
        mock_get.assert_called_once_with(
            url=url,
            headers=mock_headers,
            params={"per_page": PER_PAGE, "page": 1},
            timeout=TIMEOUT
        )
        mock_response.raise_for_status.assert_called_once()
        
        # Verify result
        assert len(result) == 3
        assert result[0]["filename"] == "file1.py"
        assert result[0]["status"] == "modified"
        assert result[0]["patch"] == "@@ -1,5 +1,7 @@\n def test():\n-    return True\n+    # Added comment\n+    return True\n"
        assert result[1]["filename"] == "file2.py"
        assert result[1]["status"] == "added"
        assert result[2]["filename"] == "file3.py"
        assert result[2]["status"] == "removed"


def test_get_pull_request_file_changes_multiple_pages(mock_headers, mock_file_data):
    """Test retrieval of pull request file changes with pagination."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"

    with patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers, \
         patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get:
        
        # Setup mocks
        mock_create_headers.return_value = mock_headers
        
        # Create responses for multiple pages
        first_page_response = MagicMock()
        first_page_response.json.return_value = mock_file_data
        
        second_page_data = [
            {
                "filename": "file4.py",
                "status": "modified",
                "patch": "@@ -1,3 +1,4 @@\n def another_test():\n+    # Another comment\n     return False\n",
            }
        ]
        second_page_response = MagicMock()
        second_page_response.json.return_value = second_page_data
        
        empty_page_response = MagicMock()
        empty_page_response.json.return_value = []
        
        # Configure mock to return different responses for different pages
        mock_get.side_effect = [first_page_response, second_page_response, empty_page_response]
        
        # Call function
        result = get_pull_request_file_changes(url, token)
        
        # Verify API calls
        assert mock_get.call_count == 3
        mock_get.assert_any_call(
            url=url,
            headers=mock_headers,
            params={"per_page": PER_PAGE, "page": 1},
            timeout=TIMEOUT
        )
        mock_get.assert_any_call(
            url=url,
            headers=mock_headers,
            params={"per_page": PER_PAGE, "page": 2},
            timeout=TIMEOUT
        )
        mock_get.assert_any_call(
            url=url,
            headers=mock_headers,
            params={"per_page": PER_PAGE, "page": 3},
            timeout=TIMEOUT
        )
        
        # Verify result
        assert len(result) == 4
        assert result[0]["filename"] == "file1.py"
        assert result[3]["filename"] == "file4.py"


def test_get_pull_request_file_changes_skip_files_without_patch(mock_headers, mock_file_data_without_patch):
    """Test that files without patch data are skipped."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"

    with patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers, \
         patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get:
        
        # Setup mocks
        mock_create_headers.return_value = mock_headers
        
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_file_data_without_patch
        mock_get.return_value = mock_response
        
        # Call function
        result = get_pull_request_file_changes(url, token)
        
        # Verify result - should be empty as the file doesn't have a patch
        assert len(result) == 0


def test_get_pull_request_file_changes_http_error():
    """Test handling of HTTP error."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"

    with patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers, \
         patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get:
        
        # Setup mocks
        mock_create_headers.return_value = {"Authorization": "Bearer test_token"}
        
        # Mock response with HTTP error
        mock_response = MagicMock()
        http_error = requests.exceptions.HTTPError("404 Client Error")
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response
        
        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request_file_changes(url, token)
        
        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_file_changes_connection_error():
    """Test handling of connection error."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"

    with patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers, \
         patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get:
        
        # Setup mocks
        mock_create_headers.return_value = {"Authorization": "Bearer test_token"}
        
        # Mock connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request_file_changes(url, token)
        
        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_file_changes_timeout_error():
    """Test handling of timeout error."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"

    with patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers, \
         patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get:
        
        # Setup mocks
        mock_create_headers.return_value = {"Authorization": "Bearer test_token"}
        
        # Mock timeout error
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request_file_changes(url, token)
        
        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_file_changes_json_decode_error():
    """Test handling of JSON decode error."""
    url = "https://api.github.com/repos/owner/repo/pulls/123/files"
    token = "test_token"

    with patch("services.github.pulls.get_pull_request_file_changes.create_headers") as mock_create_headers, \
         patch("services.github.pulls.get_pull_request_file_changes.requests.get") as mock_get:
        
        # Setup mocks
        mock_create_headers.return_value = {"Authorization": "Bearer test_token"}
        
        # Mock response with JSON decode error
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        
        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request_file_changes(url, token)
        
        # Verify result is None (default_return_value from decorator)
        assert result is None
