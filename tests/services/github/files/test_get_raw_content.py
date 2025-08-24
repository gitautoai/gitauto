# Standard imports
import base64
import json
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest
import requests

# Local imports
from services.github.files.get_raw_content import get_raw_content


class TestGetRawContent:
    """Test cases for the get_raw_content function."""

    @pytest.fixture
    def mock_response_success(self):
        """Create a successful mock response with file content."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        
        # Create base64 encoded content
        test_content = "print('Hello, World!')\n"
        encoded_content = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
        
        mock_response.json.return_value = {
            "content": encoded_content,
            "encoding": "base64",
            "name": "test.py",
            "path": "test.py",
            "type": "file"
        }
        return mock_response

    @pytest.fixture
    def mock_response_directory(self):
        """Create a mock response for a directory."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"name": "file1.py", "type": "file"},
            {"name": "file2.py", "type": "file"}
        ]
        return mock_response

    @pytest.fixture
    def mock_response_no_content(self):
        """Create a mock response without content field."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "name": "test.py",
            "path": "test.py",
            "type": "file"
            # Missing "content" field
        }
        return mock_response

    @pytest.fixture
    def mock_response_404(self):
        """Create a 404 mock response."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        return mock_response

    @pytest.fixture
    def mock_response_500(self):
        """Create a 500 mock response that raises HTTPError."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        return mock_response

    @patch('services.github.files.get_raw_content.requests.get')
    @patch('services.github.files.get_raw_content.create_headers')
    def test_successful_file_retrieval(self, mock_create_headers, mock_requests_get, mock_response_success):
        """Test successful retrieval of file content."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_requests_get.return_value = mock_response_success
        
        result = get_raw_content("test-owner", "test-repo", "test.py", "main", "test-token")
        
        assert result == "print('Hello, World!')\n"
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_requests_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/test.py?ref=main",
            headers={"Authorization": "Bearer test-token"},
            timeout=120
        )
        mock_response_success.raise_for_status.assert_called_once()

    @patch('services.github.files.get_raw_content.requests.get')
    @patch('services.github.files.get_raw_content.create_headers')
    def test_file_not_found_404(self, mock_create_headers, mock_requests_get, mock_response_404):
        """Test handling of 404 file not found."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_requests_get.return_value = mock_response_404
        
        result = get_raw_content("test-owner", "test-repo", "nonexistent.py", "main", "test-token")
        
        assert result is None
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_requests_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/nonexistent.py?ref=main",
            headers={"Authorization": "Bearer test-token"},
            timeout=120
        )
        # Should not call raise_for_status for 404
        mock_response_404.raise_for_status.assert_not_called()

    @patch('services.github.files.get_raw_content.requests.get')
    @patch('services.github.files.get_raw_content.create_headers')
    def test_directory_returns_none(self, mock_create_headers, mock_requests_get, mock_response_directory):
        """Test that directory requests return None."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_requests_get.return_value = mock_response_directory
        
        result = get_raw_content("test-owner", "test-repo", "src", "main", "test-token")
        
        assert result is None
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_requests_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/src?ref=main",
            headers={"Authorization": "Bearer test-token"},
            timeout=120
        )
        mock_response_directory.raise_for_status.assert_called_once()

    @patch('services.github.files.get_raw_content.requests.get')
    @patch('services.github.files.get_raw_content.create_headers')
    def test_response_without_content_field(self, mock_create_headers, mock_requests_get, mock_response_no_content):
        """Test handling of response without content field."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_requests_get.return_value = mock_response_no_content
        
        result = get_raw_content("test-owner", "test-repo", "test.py", "main", "test-token")
        
        assert result is None
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_requests_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/test.py?ref=main",
            headers={"Authorization": "Bearer test-token"},
            timeout=120
        )
        mock_response_no_content.raise_for_status.assert_called_once()

    @patch('services.github.files.get_raw_content.requests.get')
    @patch('services.github.files.get_raw_content.create_headers')
    def test_server_error_handled_by_decorator(self, mock_create_headers, mock_requests_get, mock_response_500):
        """Test that server errors are handled by the exception decorator."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_requests_get.return_value = mock_response_500
        
        result = get_raw_content("test-owner", "test-repo", "test.py", "main", "test-token")
        
        # The handle_exceptions decorator should catch the HTTPError and return None
        assert result is None
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_requests_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/test.py?ref=main",
            headers={"Authorization": "Bearer test-token"},
            timeout=120
        )

    @patch('services.github.files.get_raw_content.requests.get')
    @patch('services.github.files.get_raw_content.create_headers')
    def test_different_branch_ref(self, mock_create_headers, mock_requests_get, mock_response_success):
        """Test retrieval with different branch reference."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_requests_get.return_value = mock_response_success
        
        result = get_raw_content("test-owner", "test-repo", "test.py", "feature-branch", "test-token")
        
        assert result == "print('Hello, World!')\n"
        mock_requests_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/test.py?ref=feature-branch",
            headers={"Authorization": "Bearer test-token"},
            timeout=120
        )

    @patch('services.github.files.get_raw_content.requests.get')
    @patch('services.github.files.get_raw_content.create_headers')
    def test_nested_file_path(self, mock_create_headers, mock_requests_get, mock_response_success):
        """Test retrieval of nested file path."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_requests_get.return_value = mock_response_success
        
        result = get_raw_content("test-owner", "test-repo", "src/utils/helper.py", "main", "test-token")
        
        assert result == "print('Hello, World!')\n"
        mock_requests_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/src/utils/helper.py?ref=main",
            headers={"Authorization": "Bearer test-token"},
            timeout=120
        )

    @patch('services.github.files.get_raw_content.requests.get')
    @patch('services.github.files.get_raw_content.create_headers')
    def test_unicode_content_decoding(self, mock_create_headers, mock_requests_get):
        """Test proper decoding of Unicode content."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        
        # Create response with Unicode content
        unicode_content = "# 测试文件\nprint('Hello, 世界!')\n"
        encoded_content = base64.b64encode(unicode_content.encode('utf-8')).decode('utf-8')
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "content": encoded_content,
            "encoding": "base64"
        }
        mock_requests_get.return_value = mock_response
        
        result = get_raw_content("test-owner", "test-repo", "unicode_test.py", "main", "test-token")
        
        assert result == unicode_content

    @patch('services.github.files.get_raw_content.requests.get')
    @patch('services.github.files.get_raw_content.create_headers')
    def test_json_decode_error_handled_by_decorator(self, mock_create_headers, mock_requests_get):
        """Test that JSON decode errors are handled by the exception decorator."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        mock_requests_get.return_value = mock_response
        
        result = get_raw_content("test-owner", "test-repo", "test.py", "main", "test-token")
        
        # The handle_exceptions decorator should catch the JSONDecodeError and return None
        assert result is None
