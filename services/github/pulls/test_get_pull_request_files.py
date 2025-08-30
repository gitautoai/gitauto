# Standard imports
from unittest.mock import MagicMock, patch

# Third party imports
import pytest
import requests

# Local imports
from services.github.pulls.get_pull_request_files import get_pull_request_files


@pytest.fixture
def mock_requests_get():
    """Fixture to mock requests.get."""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    """Fixture to mock create_headers."""
    with patch(
        "services.github.pulls.get_pull_request_files.create_headers"
    ) as mock:
        mock.return_value = {"Authorization": "Bearer test_token"}
        yield mock


@pytest.fixture
def sample_file_data():
    """Fixture providing sample file data from GitHub API."""
    return [
        {
            "filename": "src/main.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
            "changes": 15,
            "blob_url": "https://github.com/owner/repo/blob/abc123/src/main.py",
            "raw_url": "https://github.com/owner/repo/raw/abc123/src/main.py",
            "contents_url": "https://api.github.com/repos/owner/repo/contents/src/main.py?ref=abc123",
            "patch": "@@ -1,3 +1,3 @@\n-print('hello')\n+print('hello world')",
        },
        {
            "filename": "tests/test_new.py",
            "status": "added",
            "additions": 20,
            "deletions": 0,
            "changes": 20,
            "blob_url": "https://github.com/owner/repo/blob/abc123/tests/test_new.py",
            "raw_url": "https://github.com/owner/repo/raw/abc123/tests/test_new.py",
            "contents_url": "https://api.github.com/repos/owner/repo/contents/tests/test_new.py?ref=abc123",
            "patch": "@@ -0,0 +1,20 @@\n+def test_something():\n+    pass",
        },
        {
            "filename": "old_file.py",
            "status": "removed",
            "additions": 0,
            "deletions": 15,
            "changes": 15,
            "blob_url": None,
            "raw_url": None,
            "contents_url": None,
            "patch": "@@ -1,15 +0,0 @@\n-# This file is removed",
        },
    ]


@pytest.fixture
def expected_file_changes():
    """Fixture providing expected file changes output."""
    return [
        {"filename": "src/main.py", "status": "modified"},
        {"filename": "tests/test_new.py", "status": "added"},
        {"filename": "old_file.py", "status": "removed"},
    ]


def test_get_pull_request_files_success_single_page(
    mock_requests_get, mock_create_headers, sample_file_data, expected_file_changes
):
    """Test successful retrieval of pull request files with single page."""
    # Setup mocks
    mock_response = MagicMock()
    mock_response.json.return_value = sample_file_data
    mock_requests_get.return_value = mock_response

    # Call function
    result = get_pull_request_files(
        "https://api.github.com/repos/owner/repo/pulls/123/files", "test_token"
    )

    # Verify API call
    mock_requests_get.assert_called_once_with(
        url="https://api.github.com/repos/owner/repo/pulls/123/files",
        headers={"Authorization": "Bearer test_token"},
        params={"per_page": 100, "page": 1},
        timeout=120,
    )
    mock_response.raise_for_status.assert_called_once()
    mock_create_headers.assert_called_once_with(token="test_token")

    # Verify result
    assert result == expected_file_changes
    assert len(result) == 3
    assert all("filename" in item and "status" in item for item in result)


def test_get_pull_request_files_success_multiple_pages(
    mock_requests_get, mock_create_headers
):
    """Test successful retrieval of pull request files with multiple pages."""
    # Setup mock responses for multiple pages
    page1_data = [
        {"filename": "file1.py", "status": "modified"},
        {"filename": "file2.py", "status": "added"},
    ]
    page2_data = [
        {"filename": "file3.py", "status": "removed"},
    ]
    empty_page = []

    mock_response1 = MagicMock()
    mock_response1.json.return_value = page1_data
    mock_response2 = MagicMock()
    mock_response2.json.return_value = page2_data
    mock_response3 = MagicMock()
    mock_response3.json.return_value = empty_page

    mock_requests_get.side_effect = [mock_response1, mock_response2, mock_response3]

    # Call function
    result = get_pull_request_files(
        "https://api.github.com/repos/owner/repo/pulls/123/files", "test_token"
    )

    # Verify API calls
    assert mock_requests_get.call_count == 3
    expected_calls = [
        {
            "url": "https://api.github.com/repos/owner/repo/pulls/123/files",
            "headers": {"Authorization": "Bearer test_token"},
            "params": {"per_page": 100, "page": 1},
            "timeout": 120,
        },
        {
            "url": "https://api.github.com/repos/owner/repo/pulls/123/files",
            "headers": {"Authorization": "Bearer test_token"},
            "params": {"per_page": 100, "page": 2},
            "timeout": 120,
        },
        {
            "url": "https://api.github.com/repos/owner/repo/pulls/123/files",
            "headers": {"Authorization": "Bearer test_token"},
            "params": {"per_page": 100, "page": 3},
            "timeout": 120,
        },
    ]

    for i, call in enumerate(mock_requests_get.call_args_list):
        assert call.kwargs == expected_calls[i]

    # Verify result
    expected_result = [
        {"filename": "file1.py", "status": "modified"},
        {"filename": "file2.py", "status": "added"},
        {"filename": "file3.py", "status": "removed"},
    ]
    assert result == expected_result
    assert len(result) == 3


def test_get_pull_request_files_empty_response(mock_requests_get, mock_create_headers):
    """Test handling of empty response (no files changed)."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response

    # Call function
    result = get_pull_request_files(
        "https://api.github.com/repos/owner/repo/pulls/123/files", "test_token"
    )

    # Verify result
    assert result == []
    assert len(result) == 0


def test_get_pull_request_files_filters_incomplete_files(
    mock_requests_get, mock_create_headers
):
    """Test that files without filename or status are filtered out."""
    # Setup mock with incomplete file data
    incomplete_files = [
        {"filename": "complete_file.py", "status": "modified"},  # Complete
        {"filename": "missing_status.py"},  # Missing status
        {"status": "added"},  # Missing filename
        {"filename": "another_complete.py", "status": "removed"},  # Complete
        {},  # Missing both
    ]

    mock_response = MagicMock()
    mock_response.json.return_value = incomplete_files
    mock_requests_get.return_value = mock_response

    # Call function
    result = get_pull_request_files(
        "https://api.github.com/repos/owner/repo/pulls/123/files", "test_token"
    )

    # Verify result - only complete files should be included
    expected_result = [
        {"filename": "complete_file.py", "status": "modified"},
        {"filename": "another_complete.py", "status": "removed"},
    ]
    assert result == expected_result
    assert len(result) == 2


def test_get_pull_request_files_http_error_404(mock_requests_get, mock_create_headers):
    """Test handling of 404 HTTP error."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.reason = "Not Found"
    mock_response.text = "Not Found"

    http_error = requests.exceptions.HTTPError("404 Client Error")
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error

    mock_requests_get.return_value = mock_response

    # Call function - should return [] due to handle_exceptions decorator
    result = get_pull_request_files(
        "https://api.github.com/repos/owner/repo/pulls/999/files", "test_token"
    )

    # Verify result is empty list (default_return_value from decorator)
    assert result == []


def test_get_pull_request_files_http_error_500(mock_requests_get, mock_create_headers):
    """Test handling of 500 HTTP error."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.reason = "Internal Server Error"
    mock_response.text = "Internal Server Error"

    http_error = requests.exceptions.HTTPError("500 Server Error")
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error

    mock_requests_get.return_value = mock_response

    # Call function - should return [] due to handle_exceptions decorator
    result = get_pull_request_files(
        "https://api.github.com/repos/owner/repo/pulls/123/files", "test_token"
    )

    # Verify result is empty list (default_return_value from decorator)
    assert result == []


def test_get_pull_request_files_network_error(mock_requests_get, mock_create_headers):
    """Test handling of network connection error."""
    # Setup mock
    mock_requests_get.side_effect = requests.exceptions.ConnectionError("Network error")

    # Call function - should return [] due to handle_exceptions decorator
    result = get_pull_request_files(
        "https://api.github.com/repos/owner/repo/pulls/123/files", "test_token"
    )

    # Verify result is empty list (default_return_value from decorator)
    assert result == []


def test_get_pull_request_files_timeout_error(mock_requests_get, mock_create_headers):
    """Test handling of timeout error."""
    # Setup mock
    mock_requests_get.side_effect = requests.exceptions.Timeout("Request timeout")

    # Call function - should return [] due to handle_exceptions decorator
    result = get_pull_request_files(
        "https://api.github.com/repos/owner/repo/pulls/123/files", "test_token"
    )

    # Verify result is empty list (default_return_value from decorator)
    assert result == []


def test_get_pull_request_files_json_decode_error(
    mock_requests_get, mock_create_headers
):
    """Test handling of JSON decode error."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_requests_get.return_value = mock_response

    # Call function - should return [] due to handle_exceptions decorator
    result = get_pull_request_files(
        "https://api.github.com/repos/owner/repo/pulls/123/files", "test_token"
    )

    # Verify result is empty list (default_return_value from decorator)
    assert result == []


def test_get_pull_request_files_headers_creation(mock_requests_get, mock_create_headers):
    """Test that headers are created correctly."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response
    mock_create_headers.return_value = {"Authorization": "Bearer custom_token"}

    # Call function
    get_pull_request_files(
        "https://api.github.com/repos/owner/repo/pulls/123/files", "custom_token"
    )

    # Verify headers creation
    mock_create_headers.assert_called_once_with(token="custom_token")


def test_get_pull_request_files_with_different_urls(
    mock_requests_get, mock_create_headers
):
    """Test that the function works with different URL formats."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"filename": "test.py", "status": "modified"}
    ]
    mock_requests_get.return_value = mock_response

    test_urls = [
        "https://api.github.com/repos/owner/repo/pulls/123/files",
        "https://api.github.com/repos/test-org/test-repo/pulls/456/files",
        "https://api.github.com/repos/user/my-repo/pulls/789/files",
    ]

    for url in test_urls:
        # Call function
        result = get_pull_request_files(url, "test_token")

        # Verify result
        assert result == [{"filename": "test.py", "status": "modified"}]

        # Verify URL was used correctly
        mock_requests_get.assert_called_with(
            url=url,
            headers={"Authorization": "Bearer test_token"},
            params={"per_page": 100, "page": 1},
            timeout=120,
        )

        # Reset mock for next iteration
        mock_requests_get.reset_mock()


def test_get_pull_request_files_status_types(mock_requests_get, mock_create_headers):
    """Test that all valid status types are handled correctly."""
    # Setup mock with all status types
    files_with_all_statuses = [
        {"filename": "added_file.py", "status": "added"},
        {"filename": "modified_file.py", "status": "modified"},
        {"filename": "removed_file.py", "status": "removed"},
    ]

    mock_response = MagicMock()
    mock_response.json.return_value = files_with_all_statuses
    mock_requests_get.return_value = mock_response

    # Call function
    result = get_pull_request_files(
        "https://api.github.com/repos/owner/repo/pulls/123/files", "test_token"
    )

    # Verify result
    expected_result = [
        {"filename": "added_file.py", "status": "added"},
        {"filename": "modified_file.py", "status": "modified"},
        {"filename": "removed_file.py", "status": "removed"},
    ]
    assert result == expected_result
    assert len(result) == 3


def test_get_pull_request_files_large_number_of_files(
    mock_requests_get, mock_create_headers
):
    """Test handling of a large number of files across multiple pages."""
    # Create mock data for multiple pages
    files_per_page = 100
    total_pages = 3
    
    mock_responses = []
    expected_files = []
    
    for page in range(1, total_pages + 1):
        page_files = []
        for i in range(files_per_page):
            file_num = (page - 1) * files_per_page + i + 1
            file_data = {
                "filename": f"file_{file_num}.py",
                "status": "modified" if file_num % 2 == 0 else "added",
            }
            page_files.append(file_data)
            expected_files.append({
                "filename": f"file_{file_num}.py",
                "status": "modified" if file_num % 2 == 0 else "added",
            })
        
        mock_response = MagicMock()
        mock_response.json.return_value = page_files
        mock_responses.append(mock_response)
    
    # Add empty response to end pagination
    empty_response = MagicMock()
    empty_response.json.return_value = []
    mock_responses.append(empty_response)
    
    mock_requests_get.side_effect = mock_responses

    # Call function
    result = get_pull_request_files(
        "https://api.github.com/repos/owner/repo/pulls/123/files", "test_token"
    )

    # Verify result
    assert len(result) == total_pages * files_per_page
    assert result == expected_files
    assert mock_requests_get.call_count == total_pages + 1  # +1 for empty page


@pytest.mark.parametrize(
    "url,token",
    [
        ("https://api.github.com/repos/owner1/repo1/pulls/1/files", "token1"),
        ("https://api.github.com/repos/test-org/test-project/pulls/999/files", "ghp_token123"),
        ("https://api.github.com/repos/user/my-repo/pulls/42/files", "personal_access_token"),
    ],
)
def test_get_pull_request_files_with_various_parameters(
    mock_requests_get, mock_create_headers, url, token
):
    """Test that the function works with various parameter combinations."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests_get.return_value = mock_response

    # Call function
    result = get_pull_request_files(url, token)

    # Verify result
    assert result == []
    mock_requests_get.assert_called_once()
    mock_create_headers.assert_called_once_with(token=token)

    # Verify correct parameters were passed
    call_args = mock_requests_get.call_args
    assert call_args.kwargs["url"] == url
    assert call_args.kwargs["timeout"] == 120
    assert call_args.kwargs["params"] == {"per_page": 100, "page": 1}


def test_get_pull_request_files_return_type_structure():
    """Test that the return type has the correct structure."""
    import inspect
    from services.github.pulls.get_pull_request_files import FileChange

    # Check FileChange TypedDict structure
    assert hasattr(FileChange, "__annotations__")
    annotations = FileChange.__annotations__
    assert "filename" in annotations
    assert "status" in annotations
    assert annotations["filename"] is str

    # Check function signature
    sig = inspect.signature(get_pull_request_files)
    params = sig.parameters
    assert params["url"].annotation is str
    assert params["token"].annotation is str


def test_get_pull_request_files_has_docstring():
    """Test that the function has a docstring with GitHub API reference."""
    assert get_pull_request_files.__doc__ is not None
    assert "https://docs.github.com/en/rest/pulls/pulls" in get_pull_request_files.__doc__
    assert "list-pull-requests-files" in get_pull_request_files.__doc__


def test_get_pull_request_files_decorator_configuration():
    """Test that the handle_exceptions decorator is configured correctly."""
    # The decorator should be configured with default_return_value=[] and raise_on_error=False
    # We can test this by checking the behavior when an exception occurs
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock_get:
        mock_get.side_effect = Exception("Test exception")
        
        result = get_pull_request_files("test_url", "test_token")
        
        # Should return empty list (default_return_value) instead of raising
        assert result == []
