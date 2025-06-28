"""Unit tests for get_pull_request_files function.

Related Documentation:
https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#list-pull-requests-files
"""

import json
from unittest.mock import patch, Mock
import pytest
import requests

from services.github.pull_requests.get_pull_request_files import get_pull_request_files


class TestGetPullRequestFiles:
    """Test cases for get_pull_request_files function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_url = "https://api.github.com/repos/owner/repo/pulls/123/files"
        self.test_token = "test_token_123"
        self.test_headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {self.test_token}",
            "User-Agent": "test-app",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    @patch("services.github.pull_requests.get_pull_request_files.requests.get")
    @patch("services.github.pull_requests.get_pull_request_files.create_headers")
    def test_get_pull_request_files_single_page_success(self, mock_create_headers, mock_get):
        """Test successful retrieval of files from a single page."""
        # Arrange
        mock_create_headers.return_value = self.test_headers
        mock_response = Mock()
        mock_response.json.return_value = [
            {"filename": "file1.py", "status": "modified"},
            {"filename": "file2.js", "status": "added"},
            {"filename": "file3.md", "status": "deleted"},
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        result = get_pull_request_files(self.test_url, self.test_token)

        # Assert
        assert result == ["file1.py", "file2.js", "file3.md"]
        mock_create_headers.assert_called_once_with(token=self.test_token)
        mock_get.assert_called_once_with(
            url=self.test_url,
            headers=self.test_headers,
            params={"per_page": 100, "page": 1},
            timeout=120,
        )

    @patch("services.github.pull_requests.get_pull_request_files.requests.get")
    @patch("services.github.pull_requests.get_pull_request_files.create_headers")
    def test_get_pull_request_files_multiple_pages_success(self, mock_create_headers, mock_get):
        """Test successful retrieval of files from multiple pages."""
        # Arrange
        mock_create_headers.return_value = self.test_headers
        
        # First page response
        first_response = Mock()
        first_response.json.return_value = [
            {"filename": "page1_file1.py", "status": "modified"},
            {"filename": "page1_file2.js", "status": "added"},
        ]
        first_response.raise_for_status.return_value = None
        
        # Second page response
        second_response = Mock()
        second_response.json.return_value = [
            {"filename": "page2_file1.py", "status": "modified"},
        ]
        second_response.raise_for_status.return_value = None
        
        # Third page response (empty)
        third_response = Mock()
        third_response.json.return_value = []
        third_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [first_response, second_response, third_response]

        # Act
        result = get_pull_request_files(self.test_url, self.test_token)

        # Assert
        assert result == ["page1_file1.py", "page1_file2.js", "page2_file1.py"]
        mock_create_headers.assert_called_once_with(token=self.test_token)
        assert mock_get.call_count == 3
        
        # Verify pagination parameters
        expected_calls = [
            ({"per_page": 100, "page": 1}),
            ({"per_page": 100, "page": 2}),
            ({"per_page": 100, "page": 3}),
        ]
        for i, call in enumerate(mock_get.call_args_list):
            assert call[1]["params"] == expected_calls[i]

    @patch("services.github.pull_requests.get_pull_request_files.requests.get")
    @patch("services.github.pull_requests.get_pull_request_files.create_headers")
    def test_get_pull_request_files_empty_response(self, mock_create_headers, mock_get):
        """Test handling of empty response (no files in PR)."""
        # Arrange
        mock_create_headers.return_value = self.test_headers
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        result = get_pull_request_files(self.test_url, self.test_token)

        # Assert
        assert result == []
        mock_create_headers.assert_called_once_with(token=self.test_token)
        mock_get.assert_called_once()

    @patch("services.github.pull_requests.get_pull_request_files.requests.get")
    @patch("services.github.pull_requests.get_pull_request_files.create_headers")
    def test_get_pull_request_files_missing_filename_field(self, mock_create_headers, mock_get):
        """Test handling of files without filename field."""
        # Arrange
        mock_create_headers.return_value = self.test_headers
        mock_response = Mock()
        mock_response.json.return_value = [
            {"filename": "valid_file.py", "status": "modified"},
            {"status": "added"},  # Missing filename field
            {"filename": "another_valid_file.js", "status": "deleted"},
            {"other_field": "value"},  # Missing filename field
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        result = get_pull_request_files(self.test_url, self.test_token)

        # Assert
        assert result == ["valid_file.py", "another_valid_file.js"]
        mock_create_headers.assert_called_once_with(token=self.test_token)

    @patch("services.github.pull_requests.get_pull_request_files.requests.get")
    @patch("services.github.pull_requests.get_pull_request_files.create_headers")
    def test_get_pull_request_files_http_error_404(self, mock_create_headers, mock_get):
        """Test handling of HTTP 404 error."""
        # Arrange
        mock_create_headers.return_value = self.test_headers
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        # Act
        result = get_pull_request_files(self.test_url, self.test_token)

        # Assert
        assert result == []  # Default return value from decorator

    @patch("services.github.pull_requests.get_pull_request_files.requests.get")
    @patch("services.github.pull_requests.get_pull_request_files.create_headers")
    def test_get_pull_request_files_http_error_403(self, mock_create_headers, mock_get):
        """Test handling of HTTP 403 error (rate limit or permissions)."""
        # Arrange
        mock_create_headers.return_value = self.test_headers
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("403 Forbidden")
        mock_get.return_value = mock_response

        # Act
        result = get_pull_request_files(self.test_url, self.test_token)

        # Assert
        assert result == []  # Default return value from decorator

    @patch("services.github.pull_requests.get_pull_request_files.requests.get")
    @patch("services.github.pull_requests.get_pull_request_files.create_headers")
    def test_get_pull_request_files_connection_error(self, mock_create_headers, mock_get):
        """Test handling of connection errors."""
        # Arrange
        mock_create_headers.return_value = self.test_headers
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        # Act
        result = get_pull_request_files(self.test_url, self.test_token)

        # Assert
        assert result == []  # Default return value from decorator

    @patch("services.github.pull_requests.get_pull_request_files.requests.get")
    @patch("services.github.pull_requests.get_pull_request_files.create_headers")
    def test_get_pull_request_files_timeout_error(self, mock_create_headers, mock_get):
        """Test handling of timeout errors."""
        # Arrange
        mock_create_headers.return_value = self.test_headers
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        # Act
        result = get_pull_request_files(self.test_url, self.test_token)

        # Assert
        assert result == []  # Default return value from decorator

    @patch("services.github.pull_requests.get_pull_request_files.requests.get")
    @patch("services.github.pull_requests.get_pull_request_files.create_headers")
    def test_get_pull_request_files_json_decode_error(self, mock_create_headers, mock_get):
        """Test handling of JSON decode errors."""
        # Arrange
        mock_create_headers.return_value = self.test_headers
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response

        # Act
        result = get_pull_request_files(self.test_url, self.test_token)

        # Assert
        assert result == []  # Default return value from decorator

    @patch("services.github.pull_requests.get_pull_request_files.requests.get")
    @patch("services.github.pull_requests.get_pull_request_files.create_headers")
    def test_get_pull_request_files_with_special_characters_in_filenames(self, mock_create_headers, mock_get):
        """Test handling of filenames with special characters."""
        # Arrange
        mock_create_headers.return_value = self.test_headers
        mock_response = Mock()
        mock_response.json.return_value = [
            {"filename": "file with spaces.py", "status": "modified"},
            {"filename": "file-with-dashes.js", "status": "added"},
            {"filename": "file_with_underscores.md", "status": "deleted"},
            {"filename": "file.with.dots.txt", "status": "modified"},
            {"filename": "файл-с-unicode.py", "status": "added"},
            {"filename": "path/to/nested/file.py", "status": "modified"},
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        result = get_pull_request_files(self.test_url, self.test_token)

        # Assert
        expected_files = [
            "file with spaces.py",
            "file-with-dashes.js",
            "file_with_underscores.md",
            "file.with.dots.txt",
            "файл-с-unicode.py",
            "path/to/nested/file.py",
        ]
        assert result == expected_files

    @patch("services.github.pull_requests.get_pull_request_files.requests.get")
    @patch("services.github.pull_requests.get_pull_request_files.create_headers")
    def test_get_pull_request_files_with_empty_filename(self, mock_create_headers, mock_get):
        """Test handling of empty filename values."""
        # Arrange
        mock_create_headers.return_value = self.test_headers
        mock_response = Mock()
        mock_response.json.return_value = [
            {"filename": "valid_file.py", "status": "modified"},
            {"filename": "", "status": "added"},  # Empty filename
            {"filename": "another_valid_file.js", "status": "deleted"},
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        result = get_pull_request_files(self.test_url, self.test_token)

        # Assert
        assert result == ["valid_file.py", "", "another_valid_file.js"]

    @patch("services.github.pull_requests.get_pull_request_files.requests.get")
    @patch("services.github.pull_requests.get_pull_request_files.create_headers")
    def test_get_pull_request_files_with_none_filename(self, mock_create_headers, mock_get):
        """Test handling of None filename values."""
        # Arrange
        mock_create_headers.return_value = self.test_headers
        mock_response = Mock()
        mock_response.json.return_value = [
            {"filename": "valid_file.py", "status": "modified"},
            {"filename": None, "status": "added"},  # None filename
            {"filename": "another_valid_file.js", "status": "deleted"},
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        result = get_pull_request_files(self.test_url, self.test_token)

        # Assert
        assert result == ["valid_file.py", None, "another_valid_file.js"]

    def test_get_pull_request_files_with_invalid_url(self):
        """Test function with invalid URL."""
        # Act
        result = get_pull_request_files("invalid-url", self.test_token)

        # Assert
        assert result == []  # Default return value from decorator

    def test_get_pull_request_files_with_empty_token(self):
        """Test function with empty token."""
        # Act
        result = get_pull_request_files(self.test_url, "")

        # Assert
        assert result == []  # Default return value from decorator

    def test_get_pull_request_files_with_none_token(self):
        """Test function with None token."""
        # Act
        result = get_pull_request_files(self.test_url, None)

        # Assert
        assert result == []  # Default return value from decorator

    @patch("services.github.pull_requests.get_pull_request_files.requests.get")
    @patch("services.github.pull_requests.get_pull_request_files.create_headers")
    def test_get_pull_request_files_uses_correct_config_values(self, mock_create_headers, mock_get):
        """Test that function uses correct configuration values."""
        # Arrange
        mock_create_headers.return_value = self.test_headers
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        get_pull_request_files(self.test_url, self.test_token)

        # Assert
        # Verify that PER_PAGE (100) and TIMEOUT (120) from config are used
        mock_get.assert_called_once_with(
            url=self.test_url,
            headers=self.test_headers,
            params={"per_page": 100, "page": 1},
            timeout=120,
        )

    @patch("services.github.pull_requests.get_pull_request_files.requests.get")
    @patch("services.github.pull_requests.get_pull_request_files.create_headers")
    def test_get_pull_request_files_preserves_filename_order(self, mock_create_headers, mock_get):
        """Test that function preserves the order of filenames from API response."""
        # Arrange
        mock_create_headers.return_value = self.test_headers
        mock_response = Mock()
        mock_response.json.return_value = [
            {"filename": "z_last_file.py", "status": "modified"},
            {"filename": "a_first_file.js", "status": "added"},
            {"filename": "m_middle_file.md", "status": "deleted"},
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        result = get_pull_request_files(self.test_url, self.test_token)

        # Assert
        # Order should be preserved as returned by API
        assert result == ["z_last_file.py", "a_first_file.js", "m_middle_file.md"]

    @patch("services.github.pull_requests.get_pull_request_files.requests.get")
    @patch("services.github.pull_requests.get_pull_request_files.create_headers")
    def test_get_pull_request_files_handles_large_response(self, mock_create_headers, mock_get):
        """Test handling of large number of files across multiple pages."""
        # Arrange
        mock_create_headers.return_value = self.test_headers
        
        # Create responses for multiple pages
        responses = []
        expected_files = []
        
        # Create 5 pages with 20 files each (100 total files)
        for page in range(1, 6):
            page_files = []
            for file_num in range(1, 21):
                filename = f"page{page}_file{file_num}.py"
                page_files.append({"filename": filename, "status": "modified"})
                expected_files.append(filename)
            
            response = Mock()
            response.json.return_value = page_files
            response.raise_for_status.return_value = None
            responses.append(response)
        
        # Add empty response to end pagination
        empty_response = Mock()
        empty_response.json.return_value = []
        empty_response.raise_for_status.return_value = None
        responses.append(empty_response)
        
        mock_get.side_effect = responses

        # Act
        result = get_pull_request_files(self.test_url, self.test_token)

        # Assert
        assert len(result) == 100
        assert result == expected_files
        assert mock_get.call_count == 6  # 5 pages + 1 empty page