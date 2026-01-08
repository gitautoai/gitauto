# Standard imports
from unittest.mock import Mock, patch

# Third party imports
import pytest
import requests

# Local imports
from services.github.pulls.get_pull_request_file_changes import (
    get_pull_request_file_changes,
)


@pytest.fixture
def mock_requests():
    """Mock requests module for testing."""
    with patch("services.github.pulls.get_pull_request_file_changes.requests") as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    """Mock create_headers function for testing."""
    with patch(
        "services.github.pulls.get_pull_request_file_changes.create_headers"
    ) as mock:
        mock.return_value = {"Authorization": "Bearer test_token"}
        yield mock


def test_get_pull_request_file_changes_success(mock_requests, mock_create_headers):
    """Test successful retrieval of pull request file changes."""
    mock_response_data = [
        {
            "filename": "file1.py",
            "status": "modified",
            "patch": "@@ -1,3 +1,3 @@\n-old line\n+new line",
        },
        {
            "filename": "file2.js",
            "status": "added",
            "patch": "@@ -0,0 +1,5 @@\n+new file content",
        },
        {
            "filename": "file3.txt",
            "status": "removed",
            "patch": "@@ -1,2 +0,0 @@\n-deleted content",
        },
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
            "patch": "@@ -1,3 +1,3 @@\n-old line\n+new line",
        },
        {
            "filename": "file2.js",
            "status": "added",
            "patch": "@@ -0,0 +1,5 @@\n+new file content",
        },
        {
            "filename": "file3.txt",
            "status": "removed",
            "patch": "@@ -1,2 +0,0 @@\n-deleted content",
        },
    ]

    assert result == expected
    mock_create_headers.assert_called_once_with(token="test_token")
    assert mock_requests.get.call_count == 2


def test_get_pull_request_file_changes_pagination(mock_requests):
    """Test pagination handling with multiple pages."""
    page1_data = [
        {
            "filename": "file1.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,1 @@\n-old\n+new",
        }
    ]
    page2_data = [
        {"filename": "file2.js", "status": "added", "patch": "@@ -0,0 +1,1 @@\n+added"}
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
            "patch": "@@ -1,1 +1,1 @@\n-old\n+new",
        },
        {"filename": "file2.js", "status": "added", "patch": "@@ -0,0 +1,1 @@\n+added"},
    ]

    assert result == expected
    assert mock_requests.get.call_count == 3

    # Verify pagination parameters
    calls = mock_requests.get.call_args_list
    assert calls[0][1]["params"] == {"per_page": 100, "page": 1}
    assert calls[1][1]["params"] == {"per_page": 100, "page": 2}
    assert calls[2][1]["params"] == {"per_page": 100, "page": 3}


def test_get_pull_request_file_changes_filter_no_patch(mock_requests):
    """Test filtering of files without patch field."""
    mock_response_data = [
        {
            "filename": "file1.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,1 @@\n-old\n+new",
        },
        {
            "filename": "file2.js",
            "status": "renamed",
            # No patch field - should be filtered out
        },
        {
            "filename": "file3.txt",
            "status": "added",
            "patch": "@@ -0,0 +1,1 @@\n+content",
        },
        {
            "filename": "binary_file.png",
            "status": "added",
            # No patch field - should be filtered out
        },
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
            "patch": "@@ -1,1 +1,1 @@\n-old\n+new",
        },
        {
            "filename": "file3.txt",
            "status": "added",
            "patch": "@@ -0,0 +1,1 @@\n+content",
        },
    ]

    assert result == expected


def test_get_pull_request_file_changes_empty_response(
    mock_requests, mock_create_headers
):
    """Test handling of empty response."""
    mock_response = Mock()
    mock_response.json.return_value = []
    mock_response.raise_for_status.return_value = None
    mock_requests.get.return_value = mock_response

    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    assert not result
    mock_create_headers.assert_called_once_with(token="test_token")
    mock_requests.get.assert_called_once()


def test_get_pull_request_file_changes_http_error_404(mock_requests):
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


def test_get_pull_request_file_changes_http_error_500(mock_requests):
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


def test_get_pull_request_file_changes_network_error(mock_requests):
    """Test handling of network connection error."""
    mock_requests.get.side_effect = requests.exceptions.ConnectionError("Network error")

    # Should return None due to handle_exceptions decorator
    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    assert result is None


def test_get_pull_request_file_changes_timeout_error(mock_requests):
    """Test handling of timeout error."""
    mock_requests.get.side_effect = requests.exceptions.Timeout("Request timeout")

    # Should return None due to handle_exceptions decorator
    result = get_pull_request_file_changes(
        "https://api.github.com/repos/test/test/pulls/1/files", "test_token"
    )

    assert result is None


def test_get_pull_request_file_changes_json_decode_error(mock_requests):
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


def test_get_pull_request_file_changes_request_parameters(
    mock_requests, mock_create_headers
):
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
        timeout=120,
    )


def test_get_pull_request_file_changes_large_patch(mock_requests):
    """Test handling of files with large patch content."""
    large_patch = "@@ -1,100 +1,100 @@\n" + "\n".join(
        [f"-old line {i}\n+new line {i}" for i in range(50)]
    )

    mock_response_data = [
        {"filename": "large_file.py", "status": "modified", "patch": large_patch}
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
        {"filename": "large_file.py", "status": "modified", "patch": large_patch}
    ]

    assert result == expected


def test_get_pull_request_file_changes_mixed_file_types(mock_requests):
    """Test handling of mixed file types and statuses."""
    mock_response_data = [
        {
            "filename": "src/main.py",
            "status": "modified",
            "patch": "@@ -10,1 +10,1 @@\n-    old_code()\n+    new_code()",
        },
        {
            "filename": "tests/test_main.py",
            "status": "added",
            "patch": "@@ -0,0 +1,10 @@\n+def test_new_feature():\n+    assert True",
        },
        {
            "filename": "old_file.py",
            "status": "removed",
            "patch": "@@ -1,5 +0,0 @@\n-def old_function():\n-    pass",
        },
        {
            "filename": "README.md",
            "status": "modified",
            "patch": "@@ -1,1 +1,2 @@\n # Project\n+\n+Updated documentation",
        },
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

    assert result is not None
    assert len(result) == 4
    assert all(
        "filename" in change and "status" in change and "patch" in change
        for change in result
    )

    # Verify specific files are included
    filenames = [change["filename"] for change in result]
    assert "src/main.py" in filenames
    assert "tests/test_main.py" in filenames
    assert "old_file.py" in filenames
    assert "README.md" in filenames


def test_get_pull_request_file_changes_special_characters_in_filename(mock_requests):
    """Test handling of filenames with special characters."""
    mock_response_data = [
        {
            "filename": "file with spaces.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,1 @@\n-old\n+new",
        },
        {
            "filename": "file-with-dashes.js",
            "status": "added",
            "patch": "@@ -0,0 +1,1 @@\n+content",
        },
        {
            "filename": "file_with_underscores.txt",
            "status": "modified",
            "patch": "@@ -1,1 +1,1 @@\n-before\n+after",
        },
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

    assert result is not None
    assert len(result) == 3
    filenames = [change["filename"] for change in result]
    assert "file with spaces.py" in filenames
    assert "file-with-dashes.js" in filenames
    assert "file_with_underscores.txt" in filenames


def test_get_pull_request_file_changes_empty_patch(mock_requests):
    """Test handling of files with empty patch content."""
    mock_response_data = [
        {"filename": "file1.py", "status": "modified", "patch": ""},  # Empty patch
        {
            "filename": "file2.py",
            "status": "modified",
            "patch": "@@ -1,1 +1,1 @@\n-old\n+new",  # Non-empty patch
        },
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
    assert result is not None
    assert len(result) == 2
    assert result[0]["filename"] == "file1.py"
    assert result[0]["patch"] == ""
    assert result[1]["filename"] == "file2.py"
    assert result[1]["patch"] == "@@ -1,1 +1,1 @@\n-old\n+new"
