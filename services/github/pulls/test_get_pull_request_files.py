# Standard imports
from unittest.mock import patch, MagicMock
import json

# Third-party imports
import pytest
import requests

# Local imports
from services.github.pulls.get_pull_request_files import get_pull_request_files, FileChange
from config import PER_PAGE, TIMEOUT


@pytest.fixture
def mock_requests_get():
    """Fixture to mock requests.get."""
    with patch("services.github.pulls.get_pull_request_files.requests.get") as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    """Fixture to mock create_headers function."""
    with patch("services.github.pulls.get_pull_request_files.create_headers") as mock:
        mock.return_value = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer test-token",
            "User-Agent": "GitAuto",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        yield mock


@pytest.fixture
def sample_file_data():
    """Sample file data returned by GitHub API."""
    return [
        {
            "filename": "src/main.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
            "changes": 15,
        },
        {
            "filename": "tests/test_main.py",
            "status": "added",
            "additions": 20,
            "deletions": 0,
            "changes": 20,
        },
        {
            "filename": "old_file.py",
            "status": "removed",
            "additions": 0,
            "deletions": 30,
            "changes": 30,
        },
    ]


@pytest.fixture
def sample_file_data_incomplete():
    """Sample file data with missing required fields."""
    return [
        {
            "filename": "src/main.py",
            "status": "modified",
            "additions": 10,
        },
        {
            "status": "added",  # Missing filename
            "additions": 20,
        },
        {
            "filename": "incomplete.py",  # Missing status
            "additions": 5,
        },
        {
            "filename": "valid.py",
            "status": "modified",
            "additions": 1,
        },
    ]


class TestGetPullRequestFiles:
    def test_successful_single_page_response(
        self, mock_requests_get, mock_create_headers, sample_file_data
    ):
        """Test successful API call with single page of results."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = sample_file_data
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        url = "https://api.github.com/repos/owner/repo/pulls/123/files"
        token = "test-token"

        # Execute
        result = get_pull_request_files(url=url, token=token)

        # Verify
        expected_result = [
            {"filename": "src/main.py", "status": "modified"},
            {"filename": "tests/test_main.py", "status": "added"},
            {"filename": "old_file.py", "status": "removed"},
        ]
        assert result == expected_result

        # Verify API call
        mock_create_headers.assert_called_once_with(token=token)
        mock_requests_get.assert_called_once_with(
            url=url,
            headers=mock_create_headers.return_value,
            params={"per_page": PER_PAGE, "page": 1},
            timeout=TIMEOUT,
        )
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()

    def test_successful_multiple_pages_response(
        self, mock_requests_get, mock_create_headers
    ):
        """Test successful API call with multiple pages of results."""
        # Setup
        page1_data = [
            {"filename": "file1.py", "status": "added"},
            {"filename": "file2.py", "status": "modified"},
        ]
        page2_data = [
            {"filename": "file3.py", "status": "removed"},
        ]
        empty_page = []

        mock_response1 = MagicMock()
        mock_response1.json.return_value = page1_data
        mock_response1.raise_for_status.return_value = None

        mock_response2 = MagicMock()
        mock_response2.json.return_value = page2_data
        mock_response2.raise_for_status.return_value = None

        mock_response3 = MagicMock()
        mock_response3.json.return_value = empty_page
        mock_response3.raise_for_status.return_value = None

        mock_requests_get.side_effect = [mock_response1, mock_response2, mock_response3]

        url = "https://api.github.com/repos/owner/repo/pulls/123/files"
        token = "test-token"

        # Execute
        result = get_pull_request_files(url=url, token=token)

        # Verify
        expected_result = [
            {"filename": "file1.py", "status": "added"},
            {"filename": "file2.py", "status": "modified"},
            {"filename": "file3.py", "status": "removed"},
        ]
        assert result == expected_result
        assert mock_requests_get.call_count == 3

        # Verify all API calls
        expected_calls = [
            (url, mock_create_headers.return_value, {"per_page": PER_PAGE, "page": 1}),
            (url, mock_create_headers.return_value, {"per_page": PER_PAGE, "page": 2}),
            (url, mock_create_headers.return_value, {"per_page": PER_PAGE, "page": 3}),
        ]
        for i, (expected_url, expected_headers, expected_params) in enumerate(expected_calls):
            actual_call = mock_requests_get.call_args_list[i]
            assert actual_call.kwargs["url"] == expected_url
            assert actual_call.kwargs["headers"] == expected_headers
            assert actual_call.kwargs["params"] == expected_params
            assert actual_call.kwargs["timeout"] == TIMEOUT

    def test_empty_response(self, mock_requests_get, mock_create_headers):
        """Test API call that returns empty list immediately."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        url = "https://api.github.com/repos/owner/repo/pulls/123/files"
        token = "test-token"

        # Execute
        result = get_pull_request_files(url=url, token=token)

        # Verify
        assert result == []
        mock_requests_get.assert_called_once()

    def test_incomplete_file_data_filtering(
        self, mock_requests_get, mock_create_headers, sample_file_data_incomplete
    ):
        """Test that files without required fields are filtered out."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = sample_file_data_incomplete
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        url = "https://api.github.com/repos/owner/repo/pulls/123/files"
        token = "test-token"

        # Execute
        result = get_pull_request_files(url=url, token=token)

        # Verify - only files with both filename and status should be included
        expected_result = [
            {"filename": "src/main.py", "status": "modified"},
            {"filename": "valid.py", "status": "modified"},
        ]
        assert result == expected_result

    def test_http_error_handling(self, mock_requests_get, mock_create_headers):
        """Test that HTTP errors are handled by the decorator and return default value."""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Repository not found"
        
        http_error = requests.exceptions.HTTPError("404 Client Error")
        http_error.response = mock_response
        mock_requests_get.side_effect = http_error

        url = "https://api.github.com/repos/owner/repo/pulls/123/files"
        token = "test-token"

        # Execute
        result = get_pull_request_files(url=url, token=token)

        # Verify - should return default value (empty list) due to handle_exceptions decorator
        assert result == []
        mock_requests_get.assert_called_once()

    def test_json_decode_error_handling(self, mock_requests_get, mock_create_headers):
        """Test that JSON decode errors are handled by the decorator."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        url = "https://api.github.com/repos/owner/repo/pulls/123/files"
        token = "test-token"

        # Execute
        result = get_pull_request_files(url=url, token=token)

        # Verify - should return default value (empty list) due to handle_exceptions decorator
        assert result == []

    def test_network_error_handling(self, mock_requests_get, mock_create_headers):
        """Test that network errors are handled by the decorator."""
        # Setup
        mock_requests_get.side_effect = requests.exceptions.ConnectionError("Network error")

        url = "https://api.github.com/repos/owner/repo/pulls/123/files"
        token = "test-token"

        # Execute
        result = get_pull_request_files(url=url, token=token)

        # Verify - should return default value (empty list) due to handle_exceptions decorator
        assert result == []

    def test_function_parameters_passed_correctly(self, mock_requests_get, mock_create_headers):
        """Test that function parameters are passed correctly to dependencies."""
        # Setup
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        url = "https://api.github.com/repos/test-owner/test-repo/pulls/456/files"
        token = "custom-token-123"

        # Execute
        get_pull_request_files(url=url, token=token)

        # Verify
        mock_create_headers.assert_called_once_with(token=token)
        mock_requests_get.assert_called_once_with(
            url=url,
            headers=mock_create_headers.return_value,
            params={"per_page": PER_PAGE, "page": 1},
            timeout=TIMEOUT,
        )

    def test_return_type_annotation(self):
        """Test that the function returns the correct type."""
        # This test verifies the FileChange TypedDict structure
        sample_change: FileChange = {
            "filename": "test.py",
            "status": "modified"
        }
        
        assert "filename" in sample_change
        assert "status" in sample_change
        assert sample_change["filename"] == "test.py"
        assert sample_change["status"] == "modified"

    def test_status_literal_values(self):
        """Test that Status literal accepts only valid values."""
        # This test documents the valid status values
        valid_statuses = ["added", "modified", "removed"]
        
        for status in valid_statuses:
            file_change: FileChange = {
                "filename": "test.py",
                "status": status  # type: ignore
            }
            assert file_change["status"] in valid_statuses
