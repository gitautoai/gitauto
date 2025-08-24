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
            timeout=120  # TIMEOUT constant from config
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
            timeout=120  # TIMEOUT constant from config
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
            timeout=120  # TIMEOUT constant from config
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
            timeout=120  # TIMEOUT constant from config
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
            timeout=120  # TIMEOUT constant from config
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
            timeout=120  # TIMEOUT constant from config
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
            timeout=120  # TIMEOUT constant from config
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

    @patch('services.github.files.get_raw_content.requests.get')
    @patch('services.github.files.get_raw_content.create_headers')
    def test_empty_file_content(self, mock_create_headers, mock_requests_get):
        """Test handling of empty file content."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        
        # Create response with empty content
        empty_content = ""
        encoded_content = base64.b64encode(empty_content.encode('utf-8')).decode('utf-8')
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "content": encoded_content,
            "encoding": "base64"
        }
        mock_requests_get.return_value = mock_response
        
        result = get_raw_content("test-owner", "test-repo", "empty.txt", "main", "test-token")
        
        assert result == ""

    @patch('services.github.files.get_raw_content.requests.get')
    @patch('services.github.files.get_raw_content.create_headers')
    def test_base64_decode_error_handled_by_decorator(self, mock_create_headers, mock_requests_get):
        """Test that base64 decode errors are handled by the exception decorator."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "content": "invalid-base64-content!@#$%",
            "encoding": "base64"
        }
        mock_requests_get.return_value = mock_response
        
        result = get_raw_content("test-owner", "test-repo", "test.py", "main", "test-token")
        
        # The handle_exceptions decorator should catch the base64 decode error and return None
        assert result is None

    @patch('services.github.files.get_raw_content.requests.get')
    @patch('services.github.files.get_raw_content.create_headers')
    def test_requests_exception_handled_by_decorator(self, mock_create_headers, mock_requests_get):
        """Test that requests exceptions are handled by the exception decorator."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_requests_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = get_raw_content("test-owner", "test-repo", "test.py", "main", "test-token")
        
        # The handle_exceptions decorator should catch the connection error and return None
        assert result is None

    @patch('services.github.files.get_raw_content.requests.get')
    @patch('services.github.files.get_raw_content.create_headers')
    def test_create_headers_exception_handled_by_decorator(self, mock_create_headers, mock_requests_get):
        """Test that create_headers exceptions are handled by the exception decorator."""

    @patch('services.github.files.get_raw_content.requests.get')
    @patch('services.github.files.get_raw_content.create_headers')
    def test_commit_sha_as_ref(self, mock_create_headers, mock_requests_get, mock_response_success):
        """Test retrieval using commit SHA as reference."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_requests_get.return_value = mock_response_success
        
        commit_sha = "abc123def456"
        result = get_raw_content("test-owner", "test-repo", "test.py", commit_sha, "test-token")
        
        assert result == "print('Hello, World!')\n"
        mock_requests_get.assert_called_once_with(
            url=f"https://api.github.com/repos/test-owner/test-repo/contents/test.py?ref={commit_sha}",
            headers={"Authorization": "Bearer test-token"},
            timeout=120  # TIMEOUT constant from config
        )

    @patch('services.github.files.get_raw_content.requests.get')
    @patch('services.github.files.get_raw_content.create_headers')
    def test_special_characters_in_file_path(self, mock_create_headers, mock_requests_get, mock_response_success):
        """Test retrieval of file with special characters in path."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_requests_get.return_value = mock_response_success
        
        file_path = "src/files with spaces/test-file.py"
        result = get_raw_content("test-owner", "test-repo", file_path, "main", "test-token")
        
        assert result == "print('Hello, World!')\n"
        mock_requests_get.assert_called_once_with(
            url=f"https://api.github.com/repos/test-owner/test-repo/contents/{file_path}?ref=main",
            headers={"Authorization": "Bearer test-token"},
            timeout=120  # TIMEOUT constant from config
        )

    @patch('services.github.files.get_raw_content.requests.get')
    @patch('services.github.files.get_raw_content.create_headers')
    def test_large_file_content(self, mock_create_headers, mock_requests_get):
        """Test handling of large file content."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        
        # Create large content (simulating a large file)
        large_content = "# Large file\n" + "print('line')\n" * 1000
        encoded_content = base64.b64encode(large_content.encode('utf-8')).decode('utf-8')
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "content": encoded_content,
            "encoding": "base64"
        }
        mock_create_headers.side_effect = Exception("Header creation failed")
        
        result = get_raw_content("test-owner", "test-repo", "test.py", "main", "test-token")
        

    @pytest.mark.parametrize(
        "owner,repo,file_path,ref",
        [
            ("test-owner", "test-repo", "README.md", "main"),
            ("org-name", "repo-name", "src/main.py", "develop"),
            ("user123", "project_name", "docs/guide.txt", "feature/new-feature"),
            ("owner-with-dashes", "repo.with.dots", "path/to/file.json", "v1.0.0"),
            ("CamelCaseOwner", "CamelCaseRepo", "CamelCase/File.py", "CamelCaseBranch"),
        ],
    )
    @patch('services.github.files.get_raw_content.requests.get')
    @patch('services.github.files.get_raw_content.create_headers')
    def test_various_parameter_combinations(self, mock_create_headers, mock_requests_get, mock_response_success, owner, repo, file_path, ref):
        """Test that the function handles various parameter combinations correctly."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_requests_get.return_value = mock_response_success
        
        result = get_raw_content(owner, repo, file_path, ref, "test-token")
        
        assert result == "print('Hello, World!')\n"
        expected_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={ref}"
        mock_requests_get.assert_called_once_with(
            url=expected_url,
            headers={"Authorization": "Bearer test-token"},
            timeout=120  # TIMEOUT constant from config
        )

    @pytest.mark.parametrize(
        "status_code",
        [400, 401, 403, 422, 500, 502, 503],
    )
    @patch('services.github.files.get_raw_content.requests.get')
    @patch('services.github.files.get_raw_content.create_headers')
    def test_various_http_error_codes(self, mock_create_headers, mock_requests_get, status_code):
        """Test handling of various HTTP error status codes."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.reason = f"HTTP {status_code} Error"
        mock_response.text = f"Error {status_code}"
        
        http_error = requests.exceptions.HTTPError(f"{status_code} Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        
        mock_requests_get.return_value = mock_response
        
        result = get_raw_content("test-owner", "test-repo", "test.py", "main", "test-token")
        
        # The handle_exceptions decorator should catch all HTTP errors and return None
        assert result is None

    @pytest.mark.parametrize(
        "file_extension,content",
        [
            (".py", "#!/usr/bin/env python3\nprint('Hello, World!')"),
            (".js", "console.log('Hello, World!');"),
            (".md", "# Hello World\n\nThis is a markdown file."),
            (".json", '{"message": "Hello, World!"}'),
            (".txt", "Hello, World!\nThis is a text file."),
            (".yml", "version: '3'\nservices:\n  app:\n    image: nginx"),
        ],
    )
    @patch('services.github.files.get_raw_content.requests.get')
    @patch('services.github.files.get_raw_content.create_headers')
    def test_various_file_types(self, mock_create_headers, mock_requests_get, file_extension, content):
