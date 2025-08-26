# Standard imports
from unittest.mock import MagicMock, patch

# Third party imports
import requests

# Local imports
from services.github.pulls.get_pull_request_file_changes import get_pull_request_file_changes


def test_get_pull_request_file_changes_success_single_page():
    """Test successful retrieval of file changes with single page."""
    # Mock response data
    mock_files_data = [
        {
            "filename": "src/main.py",
            "status": "modified",
            "patch": "@@ -1,3 +1,4 @@\n import os\n+import sys\n def main():\n     pass",
            "additions": 1,
            "deletions": 0,
            "changes": 1
        },
        {
            "filename": "README.md",
            "status": "added",
            "patch": "@@ -0,0 +1,2 @@\n+# Test Project\n+This is a test.",
            "additions": 2,
            "deletions": 0,
            "changes": 2
        },
        {
            "filename": "config.json",
            "status": "removed",
            "patch": "@@ -1,3 +0,0 @@\n-{\n-  \"test\": true\n-}",
            "additions": 0,
            "deletions": 3,
            "changes": 3
        }
    ]

    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock_headers:

        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = mock_files_data
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function
        result = get_pull_request_file_changes(
            "https://api.github.com/repos/owner/repo/pulls/123/files",
            "test_token"
        )

        # Verify API call
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/owner/repo/pulls/123/files",
            headers={"Authorization": "Bearer test_token"},
            params={"per_page": 100, "page": 1},
            timeout=120,
        )
        mock_response.raise_for_status.assert_called_once()

        # Verify result
        expected_result = [
            {
                "filename": "src/main.py",
                "status": "modified",
                "patch": "@@ -1,3 +1,4 @@\n import os\n+import sys\n def main():\n     pass"
            },
            {
                "filename": "README.md",
                "status": "added",
                "patch": "@@ -0,0 +1,2 @@\n+# Test Project\n+This is a test."
            },
            {
                "filename": "config.json",
                "status": "removed",
                "patch": "@@ -1,3 +0,0 @@\n-{\n-  \"test\": true\n-}"
            }
        ]
        assert result == expected_result
        assert len(result) == 3


def test_get_pull_request_file_changes_success_multiple_pages():
    """Test successful retrieval of file changes with multiple pages."""
    # Mock response data for multiple pages
    page1_data = [
        {
            "filename": "file1.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,2 @@\n print('hello')\n+print('world')",
        }
    ]
    page2_data = [
        {
            "filename": "file2.py",
            "status": "added",
            "patch": "@@ -0,0 +1,1 @@\n+print('new file')",
        }
    ]
    empty_page = []

    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock_headers:

        # Setup mocks for multiple pages
        mock_responses = []
        for data in [page1_data, page2_data, empty_page]:
            mock_response = MagicMock()
            mock_response.json.return_value = data
            mock_responses.append(mock_response)
        
        mock_get.side_effect = mock_responses
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function
        result = get_pull_request_file_changes(
            "https://api.github.com/repos/owner/repo/pulls/456/files",
            "test_token"
        )

        # Verify API calls for pagination
        assert mock_get.call_count == 3
        expected_calls = [
            (
                "https://api.github.com/repos/owner/repo/pulls/456/files",
                {"Authorization": "Bearer test_token"},
                {"per_page": 100, "page": 1},
                120
            ),
            (
                "https://api.github.com/repos/owner/repo/pulls/456/files",
                {"Authorization": "Bearer test_token"},
                {"per_page": 100, "page": 2},
                120
            ),
            (
                "https://api.github.com/repos/owner/repo/pulls/456/files",
                {"Authorization": "Bearer test_token"},
                {"per_page": 100, "page": 3},
                120
            )
        ]
        
        for i, call in enumerate(mock_get.call_args_list):
            args, kwargs = call
            assert kwargs["url"] == expected_calls[i][0]
            assert kwargs["headers"] == expected_calls[i][1]
            assert kwargs["params"] == expected_calls[i][2]
            assert kwargs["timeout"] == expected_calls[i][3]

        # Verify result combines all pages
        expected_result = [
            {
                "filename": "file1.py",
                "status": "modified",
                "patch": "@@ -1,1 +1,2 @@\n print('hello')\n+print('world')"
            },
            {
                "filename": "file2.py",
                "status": "added",
                "patch": "@@ -0,0 +1,1 @@\n+print('new file')"
            }
        ]
        assert result == expected_result
        assert len(result) == 2


def test_get_pull_request_file_changes_files_without_patch():
    """Test handling of files without patch data (e.g., binary files)."""
    mock_files_data = [
        {
            "filename": "text_file.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,2 @@\n print('hello')\n+print('world')",
        },
        {
            "filename": "binary_file.png",
            "status": "added",
            # No patch field for binary files
        },
        {
            "filename": "another_text.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,1 @@\n-old_code\n+new_code",
        }
    ]

    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock_headers:

        mock_response = MagicMock()
        mock_response.json.return_value = mock_files_data
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function
        result = get_pull_request_file_changes(
            "https://api.github.com/repos/owner/repo/pulls/789/files",
            "test_token"
        )

        # Verify result excludes files without patch
        expected_result = [
            {
                "filename": "text_file.py",
                "status": "modified",
                "patch": "@@ -1,1 +1,2 @@\n print('hello')\n+print('world')"
            },
            {
                "filename": "another_text.py",
                "status": "modified",
                "patch": "@@ -1,1 +1,1 @@\n-old_code\n+new_code"
            }
        ]
        assert result == expected_result
        assert len(result) == 2


def test_get_pull_request_file_changes_empty_response():
    """Test handling of empty response (no files changed)."""
    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock_headers:

        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function
        result = get_pull_request_file_changes(
            "https://api.github.com/repos/owner/repo/pulls/999/files",
            "test_token"
        )

        # Verify result is empty list
        assert result == []
        assert len(result) == 0


def test_get_pull_request_file_changes_http_error_404():
    """Test handling of 404 HTTP error."""
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
        result = get_pull_request_file_changes(
            "https://api.github.com/repos/owner/repo/pulls/999/files",
            "test_token"
        )

        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_file_changes_http_error_500():
    """Test handling of 500 HTTP error."""
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
        result = get_pull_request_file_changes(
            "https://api.github.com/repos/owner/repo/pulls/123/files",
            "test_token"
        )

        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_file_changes_network_error():
    """Test handling of network connection error."""
    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock_headers:

        # Setup mocks
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request_file_changes(
            "https://api.github.com/repos/owner/repo/pulls/123/files",
            "test_token"
        )

        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_file_changes_timeout_error():
    """Test handling of timeout error."""
    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock_headers:

        # Setup mocks
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function - should return None due to handle_exceptions decorator
        result = get_pull_request_file_changes(
            "https://api.github.com/repos/owner/repo/pulls/123/files",
            "test_token"
        )

        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_file_changes_json_decode_error():
    """Test handling of JSON decode error."""
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
        result = get_pull_request_file_changes(
            "https://api.github.com/repos/owner/repo/pulls/123/files",
            "test_token"
        )

        # Verify result is None (default_return_value from decorator)
        assert result is None


def test_get_pull_request_file_changes_headers_creation():
    """Test that headers are created correctly."""
    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock_headers:

        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer custom_token"}

        # Call function
        get_pull_request_file_changes(
            "https://api.github.com/repos/owner/repo/pulls/123/files",
            "custom_token"
        )

        # Verify headers creation
        mock_headers.assert_called_once_with(token="custom_token")


def test_get_pull_request_file_changes_pagination_parameters():
    """Test that pagination parameters are set correctly."""
    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock_headers:

        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function
        get_pull_request_file_changes(
            "https://api.github.com/repos/owner/repo/pulls/123/files",
            "test_token"
        )

        # Verify pagination parameters
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/owner/repo/pulls/123/files",
            headers={"Authorization": "Bearer test_token"},
            params={"per_page": 100, "page": 1},
            timeout=120,
        )


def test_get_pull_request_file_changes_different_file_statuses():
    """Test handling of different file status types."""
    mock_files_data = [
        {
            "filename": "modified_file.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,1 @@\n-old\n+new",
        },
        {
            "filename": "added_file.py",
            "status": "added",
            "patch": "@@ -0,0 +1,1 @@\n+new file content",
        },
        {
            "filename": "removed_file.py",
            "status": "removed",
            "patch": "@@ -1,1 +0,0 @@\n-deleted content",
        },
        {
            "filename": "renamed_file.py",
            "status": "renamed",
            "patch": "@@ -1,1 +1,1 @@\n-old name content\n+new name content",
        }
    ]

    with patch(
        "services.github.pulls.get_pull_request_file_changes.requests.get"
    ) as mock_get, patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock_headers:

        mock_response = MagicMock()
        mock_response.json.return_value = mock_files_data
        mock_get.return_value = mock_response
        mock_headers.return_value = {"Authorization": "Bearer test_token"}

        # Call function
        result = get_pull_request_file_changes(
            "https://api.github.com/repos/owner/repo/pulls/123/files",
            "test_token"
        )

        # Verify all file statuses are handled correctly
        assert len(result) == 4
        statuses = [change["status"] for change in result]
        assert "modified" in statuses
        assert "added" in statuses
        assert "removed" in statuses
        assert "renamed" in statuses

        # Verify structure of each result
        for change in result:
            assert "filename" in change
            assert "status" in change
            assert "patch" in change
            assert len(change) == 3  # Only these three fields should be present
