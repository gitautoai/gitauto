# Standard imports
from unittest.mock import patch, MagicMock
import json

# Third-party imports
import pytest
import requests

# Local imports
from services.github.files.get_file_info import get_file_info
from tests.helpers.create_test_base_args import create_test_base_args


class TestGetFileInfo:
    """Test cases for the get_file_info function."""

    @pytest.fixture
    def base_args(self):
        """Create base args for testing."""
        return create_test_base_args(
            owner="test-owner",
            repo="test-repo",
            token="test-token",
            new_branch="test-branch"
        )

    @pytest.fixture
    def mock_file_info(self):
        """Mock file info response for testing."""
        return {
            "type": "file",
            "encoding": "base64",
            "size": 1024,
            "name": "test.py",
            "path": "src/test.py",
            "content": "aGVsbG8gd29ybGQ=",  # base64 encoded "hello world"
            "sha": "abc123def456",
            "url": "https://api.github.com/repos/test-owner/test-repo/contents/src/test.py",
            "git_url": "https://api.github.com/repos/test-owner/test-repo/git/blobs/abc123def456",
            "html_url": "https://github.com/test-owner/test-repo/blob/test-branch/src/test.py",
            "download_url": "https://raw.githubusercontent.com/test-owner/test-repo/test-branch/src/test.py",
            "_links": {
                "self": "https://api.github.com/repos/test-owner/test-repo/contents/src/test.py",
                "git": "https://api.github.com/repos/test-owner/test-repo/git/blobs/abc123def456",
                "html": "https://github.com/test-owner/test-repo/blob/test-branch/src/test.py"
            }
        }

    @pytest.fixture
    def mock_directory_info(self):
        """Mock directory info response for testing."""
        return {
            "type": "dir",
            "size": 0,
            "name": "src",
            "path": "src",
            "sha": "dir123abc456",
            "url": "https://api.github.com/repos/test-owner/test-repo/contents/src",
            "git_url": "https://api.github.com/repos/test-owner/test-repo/git/trees/dir123abc456",
            "html_url": "https://github.com/test-owner/test-repo/tree/test-branch/src",
            "download_url": None,
            "_links": {
                "self": "https://api.github.com/repos/test-owner/test-repo/contents/src",
                "git": "https://api.github.com/repos/test-owner/test-repo/git/trees/dir123abc456",
                "html": "https://github.com/test-owner/test-repo/tree/test-branch/src"
            }
        }

    @pytest.fixture
    def mock_directory_listing(self):
        """Mock directory listing response for testing."""
        return [
            {
                "type": "file",
                "name": "file1.py",
                "path": "src/file1.py",
                "sha": "file1sha"
            },
            {
                "type": "file",
                "name": "file2.py",
                "path": "src/file2.py",
                "sha": "file2sha"
            }
        ]

    @patch("services.github.files.get_file_info.requests.get")
    @patch("services.github.files.get_file_info.create_headers")
    def test_successful_file_retrieval(self, mock_create_headers, mock_get, base_args, mock_file_info):
        """Test successful file information retrieval."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_file_info
        mock_get.return_value = mock_response

        result = get_file_info("src/test.py", base_args)

        assert result == mock_file_info
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/src/test.py?ref=test-branch",
            headers={"Authorization": "Bearer test-token"},
            timeout=120
        )
        mock_response.raise_for_status.assert_called_once()

    @patch("services.github.files.get_file_info.requests.get")
    @patch("services.github.files.get_file_info.create_headers")
    def test_file_not_found_404(self, mock_create_headers, mock_get, base_args):
        """Test handling of 404 file not found."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = get_file_info("nonexistent/file.py", base_args)

        assert result is None
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/nonexistent/file.py?ref=test-branch",
            headers={"Authorization": "Bearer test-token"},
            timeout=120
        )
        # Should not call raise_for_status for 404
        mock_response.raise_for_status.assert_not_called()

    @patch("services.github.files.get_file_info.requests.get")
    @patch("services.github.files.get_file_info.create_headers")
    def test_directory_response_returns_none(self, mock_create_headers, mock_get, base_args, mock_directory_info):
        """Test that directory response returns None."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_directory_info
        mock_get.return_value = mock_response

        result = get_file_info("src", base_args)

        assert result is None
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/src?ref=test-branch",
            headers={"Authorization": "Bearer test-token"},
            timeout=120
        )
        mock_response.raise_for_status.assert_called_once()

    @patch("services.github.files.get_file_info.requests.get")
    @patch("services.github.files.get_file_info.create_headers")
    def test_directory_listing_returns_none(self, mock_create_headers, mock_get, base_args, mock_directory_listing):
        """Test that directory listing (list response) returns None."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_directory_listing
        mock_get.return_value = mock_response

        result = get_file_info("src", base_args)

        assert result is None
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/src?ref=test-branch",
            headers={"Authorization": "Bearer test-token"},
            timeout=120
        )
        mock_response.raise_for_status.assert_called_once()

    @patch("services.github.files.get_file_info.requests.get")
    @patch("services.github.files.get_file_info.create_headers")
    def test_http_error_handled_by_decorator(self, mock_create_headers, mock_get, base_args):
        """Test that HTTP errors are handled by the decorator."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_response = MagicMock()
        mock_response.status_code = 403
        http_error = requests.exceptions.HTTPError("Forbidden")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        result = get_file_info("src/test.py", base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    @patch("services.github.files.get_file_info.requests.get")
    @patch("services.github.files.get_file_info.create_headers")
    def test_json_decode_error_handled_by_decorator(self, mock_create_headers, mock_get, base_args):
        """Test that JSON decode errors are handled by the decorator."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        mock_get.return_value = mock_response

        result = get_file_info("src/test.py", base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    @patch("services.github.files.get_file_info.requests.get")
    @patch("services.github.files.get_file_info.create_headers")
    def test_request_exception_handled_by_decorator(self, mock_create_headers, mock_get, base_args):
        """Test that request exceptions are handled by the decorator."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        result = get_file_info("src/test.py", base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()

    @patch("services.github.files.get_file_info.requests.get")
    @patch("services.github.files.get_file_info.create_headers")
    def test_kwargs_parameter_ignored(self, mock_create_headers, mock_get, base_args, mock_file_info):
        """Test that additional kwargs are ignored."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_file_info
        mock_get.return_value = mock_response

        result = get_file_info("src/test.py", base_args, extra_param="ignored", another_param=123)

        assert result == mock_file_info
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()

    @patch("services.github.files.get_file_info.requests.get")
    @patch("services.github.files.get_file_info.create_headers")
    def test_url_construction_with_special_characters(self, mock_create_headers, mock_get, base_args, mock_file_info):
        """Test URL construction with special characters in file path."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_file_info
        mock_get.return_value = mock_response

        file_path = "src/special file with spaces.py"
        result = get_file_info(file_path, base_args)

        assert result == mock_file_info
        mock_create_headers.assert_called_once_with(token="test-token")
        expected_url = f"https://api.github.com/repos/test-owner/test-repo/contents/{file_path}?ref=test-branch"
        mock_get.assert_called_once_with(
            url=expected_url,
            headers={"Authorization": "Bearer test-token"},
            timeout=120
        )

    @patch("services.github.files.get_file_info.requests.get")
    @patch("services.github.files.get_file_info.create_headers")
    def test_different_base_args_values(self, mock_create_headers, mock_get, mock_file_info):
        """Test function with different base_args values."""
        custom_base_args = create_test_base_args(
            owner="different-owner",
            repo="different-repo",
            token="different-token",
            new_branch="feature-branch"
        )
        
        mock_create_headers.return_value = {"Authorization": "Bearer different-token"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_file_info
        mock_get.return_value = mock_response

        result = get_file_info("src/test.py", custom_base_args)

        assert result == mock_file_info
        mock_create_headers.assert_called_once_with(token="different-token")
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/different-owner/different-repo/contents/src/test.py?ref=feature-branch",
            headers={"Authorization": "Bearer different-token"},
            timeout=120
        )
