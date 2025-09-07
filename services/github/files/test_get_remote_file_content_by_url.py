# Standard imports
import base64
import json
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest
import requests

# Local imports
from services.github.files.get_remote_file_content_by_url import get_remote_file_content_by_url


class TestGetRemoteFileContentByUrl:
    """Test cases for the get_remote_file_content_by_url function."""

    @pytest.fixture
    def sample_file_content(self):
        """Sample file content for testing."""
        return "def hello_world():\n    print('Hello, World!')\n    return 'success'\n\nif __name__ == '__main__':\n    hello_world()"

    @pytest.fixture
    def encoded_sample_content(self, sample_file_content):
        """Base64 encoded sample content."""
        return base64.b64encode(sample_file_content.encode("utf-8")).decode("utf-8")

    @pytest.fixture
    def mock_github_response(self, encoded_sample_content):
        """Mock successful GitHub API response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "content": encoded_sample_content,
            "encoding": "base64",
            "name": "test.py",
            "path": "src/test.py",
            "type": "file",
            "sha": "abc123def456",
        }
        return mock_response

    @pytest.fixture
    def mock_parse_github_url(self):
        """Mock parse_github_url function."""
        return {
            "owner": "test-owner",
            "repo": "test-repo",
            "ref": "main",
            "file_path": "src/test.py",
            "start_line": None,
            "end_line": None,
        }

    @pytest.fixture
    def mock_parse_github_url_with_lines(self):
        """Mock parse_github_url function with line numbers."""
        return {
            "owner": "test-owner",
            "repo": "test-repo",
            "ref": "main",
            "file_path": "src/test.py",
            "start_line": 2,
            "end_line": 4,
        }

    @pytest.fixture
    def mock_parse_github_url_single_line(self):
        """Mock parse_github_url function with single line."""
        return {
            "owner": "test-owner",
            "repo": "test-repo",
            "ref": "main",
            "file_path": "src/test.py",
            "start_line": 3,
            "end_line": None,
        }

    @patch("services.github.files.get_remote_file_content_by_url.requests.get")
    @patch("services.github.files.get_remote_file_content_by_url.create_headers")
    @patch("services.github.files.get_remote_file_content_by_url.parse_github_url")
    def test_successful_file_retrieval_full_content(
        self, mock_parse_url, mock_create_headers, mock_requests_get,
        mock_parse_github_url, mock_github_response
    ):
        """Test successful retrieval of full file content without line filtering."""
        mock_parse_url.return_value = mock_parse_github_url
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_requests_get.return_value = mock_github_response

        url = "https://github.com/test-owner/test-repo/blob/main/src/test.py"
        result = get_remote_file_content_by_url(url, "test-token")

        expected_content = (
            "## src/test.py\n\n"
            "1: def hello_world():\n"
            "2:     print('Hello, World!')\n"
            "3:     return 'success'\n"
            "4: \n"
            "5: if __name__ == '__main__':\n"
            "6:     hello_world()"
        )
        assert result == expected_content

        mock_parse_url.assert_called_once_with(url)
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_requests_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/src/test.py?ref=main",
            headers={"Authorization": "Bearer test-token"},
            timeout=120,
        )
        mock_github_response.raise_for_status.assert_called_once()

    @patch("services.github.files.get_remote_file_content_by_url.requests.get")
    @patch("services.github.files.get_remote_file_content_by_url.create_headers")
    @patch("services.github.files.get_remote_file_content_by_url.parse_github_url")
    def test_successful_file_retrieval_with_line_range(
        self, mock_parse_url, mock_create_headers, mock_requests_get,
        mock_parse_github_url_with_lines, mock_github_response
    ):
        """Test successful retrieval with line range filtering."""
        mock_parse_url.return_value = mock_parse_github_url_with_lines
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_requests_get.return_value = mock_github_response

        url = "https://github.com/test-owner/test-repo/blob/main/src/test.py#L2-L4"
        result = get_remote_file_content_by_url(url, "test-token")

        expected_content = (
            "## src/test.py#L2-L4\n\n"
            "2:     print('Hello, World!')\n"
            "3:     return 'success'\n"
            "4: "
        )
        assert result == expected_content

        mock_parse_url.assert_called_once_with(url)
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_requests_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/src/test.py?ref=main",
            headers={"Authorization": "Bearer test-token"},
            timeout=120,
        )

    @patch("services.github.files.get_remote_file_content_by_url.requests.get")
    @patch("services.github.files.get_remote_file_content_by_url.create_headers")
    @patch("services.github.files.get_remote_file_content_by_url.parse_github_url")
    def test_successful_file_retrieval_single_line(
        self, mock_parse_url, mock_create_headers, mock_requests_get,
        mock_parse_github_url_single_line, mock_github_response
    ):
        """Test successful retrieval with single line filtering."""
        mock_parse_url.return_value = mock_parse_github_url_single_line
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_requests_get.return_value = mock_github_response

        url = "https://github.com/test-owner/test-repo/blob/main/src/test.py#L3"
        result = get_remote_file_content_by_url(url, "test-token")

        expected_content = "## src/test.py#L3\n\n3:     return 'success'"
        assert result == expected_content

        mock_parse_url.assert_called_once_with(url)
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_requests_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/src/test.py?ref=main",
            headers={"Authorization": "Bearer test-token"},
            timeout=120,
        )

    @patch("services.github.files.get_remote_file_content_by_url.requests.get")
    @patch("services.github.files.get_remote_file_content_by_url.create_headers")
    @patch("services.github.files.get_remote_file_content_by_url.parse_github_url")
    def test_http_error_handled_by_decorator(
        self, mock_parse_url, mock_create_headers, mock_requests_get,
        mock_parse_github_url
    ):
        """Test that HTTP errors are handled by the decorator."""
        mock_parse_url.return_value = mock_parse_github_url
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "File not found"
        http_error = requests.exceptions.HTTPError("404 Not Found")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_requests_get.return_value = mock_response

        url = "https://github.com/test-owner/test-repo/blob/main/nonexistent.py"
        result = get_remote_file_content_by_url(url, "test-token")

        # The handle_exceptions decorator should catch the error and return empty string
        assert result == ""
        mock_parse_url.assert_called_once_with(url)
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_requests_get.assert_called_once()

    @patch("services.github.files.get_remote_file_content_by_url.requests.get")
    @patch("services.github.files.get_remote_file_content_by_url.create_headers")
    @patch("services.github.files.get_remote_file_content_by_url.parse_github_url")
    def test_json_decode_error_handled_by_decorator(
        self, mock_parse_url, mock_create_headers, mock_requests_get,
        mock_parse_github_url
    ):
        """Test that JSON decode errors are handled by the decorator."""
        mock_parse_url.return_value = mock_parse_github_url
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        mock_requests_get.return_value = mock_response

        url = "https://github.com/test-owner/test-repo/blob/main/src/test.py"
        result = get_remote_file_content_by_url(url, "test-token")

        # The handle_exceptions decorator should catch the error and return empty string
        assert result == ""
        mock_parse_url.assert_called_once_with(url)
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_requests_get.assert_called_once()

    @patch("services.github.files.get_remote_file_content_by_url.requests.get")
    @patch("services.github.files.get_remote_file_content_by_url.create_headers")
    @patch("services.github.files.get_remote_file_content_by_url.parse_github_url")
    def test_base64_decode_error_handled_by_decorator(
        self, mock_parse_url, mock_create_headers, mock_requests_get,
        mock_parse_github_url
    ):
        """Test that base64 decode errors are handled by the decorator."""
        mock_parse_url.return_value = mock_parse_github_url
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "content": "invalid-base64-content!@#$%",
            "encoding": "base64",
        }
        mock_requests_get.return_value = mock_response

        url = "https://github.com/test-owner/test-repo/blob/main/src/test.py"
        result = get_remote_file_content_by_url(url, "test-token")

        # The handle_exceptions decorator should catch the error and return empty string
        assert result == ""
        mock_parse_url.assert_called_once_with(url)
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_requests_get.assert_called_once()

    @patch("services.github.files.get_remote_file_content_by_url.requests.get")
    @patch("services.github.files.get_remote_file_content_by_url.create_headers")
    @patch("services.github.files.get_remote_file_content_by_url.parse_github_url")
    def test_requests_exception_handled_by_decorator(
        self, mock_parse_url, mock_create_headers, mock_requests_get,
        mock_parse_github_url
    ):
        """Test that requests exceptions are handled by the decorator."""
        mock_parse_url.return_value = mock_parse_github_url
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_requests_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        url = "https://github.com/test-owner/test-repo/blob/main/src/test.py"
        result = get_remote_file_content_by_url(url, "test-token")

        # The handle_exceptions decorator should catch the error and return empty string
        assert result == ""
        mock_parse_url.assert_called_once_with(url)
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_requests_get.assert_called_once()

    @patch("services.github.files.get_remote_file_content_by_url.requests.get")
    @patch("services.github.files.get_remote_file_content_by_url.create_headers")
    @patch("services.github.files.get_remote_file_content_by_url.parse_github_url")
    def test_parse_github_url_exception_handled_by_decorator(
        self, mock_parse_url, mock_create_headers, mock_requests_get
    ):
        """Test that parse_github_url exceptions are handled by the decorator."""
        mock_parse_url.side_effect = Exception("URL parsing failed")

        url = "https://github.com/test-owner/test-repo/blob/main/src/test.py"
        result = get_remote_file_content_by_url(url, "test-token")

        # The handle_exceptions decorator should catch the error and return empty string
        assert result == ""
        mock_parse_url.assert_called_once_with(url)
        # Should not call other functions if parse_github_url fails
        mock_create_headers.assert_not_called()
        mock_requests_get.assert_not_called()

    @patch("services.github.files.get_remote_file_content_by_url.requests.get")
    @patch("services.github.files.get_remote_file_content_by_url.create_headers")
    @patch("services.github.files.get_remote_file_content_by_url.parse_github_url")
    def test_create_headers_exception_handled_by_decorator(
        self, mock_parse_url, mock_create_headers, mock_requests_get,
        mock_parse_github_url
    ):
        """Test that create_headers exceptions are handled by the decorator."""
        mock_parse_url.return_value = mock_parse_github_url
        mock_create_headers.side_effect = Exception("Header creation failed")

        url = "https://github.com/test-owner/test-repo/blob/main/src/test.py"
        result = get_remote_file_content_by_url(url, "test-token")

        # The handle_exceptions decorator should catch the error and return empty string
        assert result == ""
        mock_parse_url.assert_called_once_with(url)
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_requests_get.assert_not_called()

    @patch("services.github.files.get_remote_file_content_by_url.requests.get")
    @patch("services.github.files.get_remote_file_content_by_url.create_headers")
    @patch("services.github.files.get_remote_file_content_by_url.parse_github_url")
    def test_empty_file_content(
        self, mock_parse_url, mock_create_headers, mock_requests_get,
        mock_parse_github_url
    ):
        """Test handling of empty file content."""
        mock_parse_url.return_value = mock_parse_github_url
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        
        empty_content = ""
        encoded_content = base64.b64encode(empty_content.encode("utf-8")).decode("utf-8")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "content": encoded_content,
            "encoding": "base64",
        }
        mock_requests_get.return_value = mock_response

        url = "https://github.com/test-owner/test-repo/blob/main/empty.txt"
        result = get_remote_file_content_by_url(url, "test-token")

        expected_content = "## src/test.py\n\n1: "
        assert result == expected_content

    @patch("services.github.files.get_remote_file_content_by_url.requests.get")
    @patch("services.github.files.get_remote_file_content_by_url.create_headers")
    @patch("services.github.files.get_remote_file_content_by_url.parse_github_url")
    def test_unicode_content_handling(
        self, mock_parse_url, mock_create_headers, mock_requests_get,
        mock_parse_github_url
    ):
        """Test proper handling of Unicode content."""
        mock_parse_url.return_value = mock_parse_github_url
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        
        unicode_content = "# 测试文件\nprint('Hello, 世界!')\n# 这是一个测试"
        encoded_content = base64.b64encode(unicode_content.encode("utf-8")).decode("utf-8")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "content": encoded_content,
            "encoding": "base64",
        }
        mock_requests_get.return_value = mock_response

        url = "https://github.com/test-owner/test-repo/blob/main/unicode_test.py"
        result = get_remote_file_content_by_url(url, "test-token")

        expected_content = (
            "## src/test.py\n\n"
            "1: # 测试文件\n"
            "2: print('Hello, 世界!')\n"
            "3: # 这是一个测试"
        )
        assert result == expected_content

    @patch("services.github.files.get_remote_file_content_by_url.requests.get")
    @patch("services.github.files.get_remote_file_content_by_url.create_headers")
    @patch("services.github.files.get_remote_file_content_by_url.parse_github_url")
    def test_different_branch_and_commit_sha(
        self, mock_parse_url, mock_create_headers, mock_requests_get,
        mock_github_response
    ):
        """Test retrieval with different branch and commit SHA."""
        mock_parse_url.return_value = {
            "owner": "test-owner",
            "repo": "test-repo",
            "ref": "feature-branch",
            "file_path": "src/test.py",
            "start_line": None,
            "end_line": None,
        }
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_requests_get.return_value = mock_github_response

        url = "https://github.com/test-owner/test-repo/blob/feature-branch/src/test.py"
        result = get_remote_file_content_by_url(url, "test-token")

        assert "## src/test.py" in result
        mock_requests_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/src/test.py?ref=feature-branch",
            headers={"Authorization": "Bearer test-token"},
            timeout=120,
        )

    @patch("services.github.files.get_remote_file_content_by_url.requests.get")
    @patch("services.github.files.get_remote_file_content_by_url.create_headers")
    @patch("services.github.files.get_remote_file_content_by_url.parse_github_url")
    def test_nested_file_path(
        self, mock_parse_url, mock_create_headers, mock_requests_get,
        mock_github_response
    ):
        """Test retrieval of nested file path."""
        mock_parse_url.return_value = {
            "owner": "test-owner",
            "repo": "test-repo",
            "ref": "main",
            "file_path": "src/utils/helpers/file.py",
            "start_line": None,
            "end_line": None,
        }
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_requests_get.return_value = mock_github_response

        url = "https://github.com/test-owner/test-repo/blob/main/src/utils/helpers/file.py"
        result = get_remote_file_content_by_url(url, "test-token")

        assert "## src/utils/helpers/file.py" in result
        mock_requests_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/src/utils/helpers/file.py?ref=main",
            headers={"Authorization": "Bearer test-token"},
            timeout=120,
        )

    @patch("services.github.files.get_remote_file_content_by_url.requests.get")
    @patch("services.github.files.get_remote_file_content_by_url.create_headers")
    @patch("services.github.files.get_remote_file_content_by_url.parse_github_url")
    def test_line_range_edge_cases(
        self, mock_parse_url, mock_create_headers, mock_requests_get,
        mock_github_response
    ):
        """Test line range edge cases."""
        # Test line range that exceeds file length
        mock_parse_url.return_value = {
            "owner": "test-owner",
            "repo": "test-repo",
            "ref": "main",
            "file_path": "src/test.py",
            "start_line": 5,
            "end_line": 10,  # File only has 6 lines
        }
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_requests_get.return_value = mock_github_response

        url = "https://github.com/test-owner/test-repo/blob/main/src/test.py#L5-L10"
        result = get_remote_file_content_by_url(url, "test-token")

        expected_content = (
            "## src/test.py#L5-L10\n\n"
            "5: if __name__ == '__main__':\n"
            "6:     hello_world()"
        )
        assert result == expected_content

    @patch("services.github.files.get_remote_file_content_by_url.requests.get")
    @patch("services.github.files.get_remote_file_content_by_url.create_headers")
    @patch("services.github.files.get_remote_file_content_by_url.parse_github_url")
    def test_single_line_edge_case(
        self, mock_parse_url, mock_create_headers, mock_requests_get,
        mock_github_response
    ):
        """Test single line edge case that exceeds file length."""
        mock_parse_url.return_value = {
            "owner": "test-owner",
            "repo": "test-repo",
            "ref": "main",
            "file_path": "src/test.py",
            "start_line": 10,  # File only has 6 lines
            "end_line": None,
        }
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_requests_get.return_value = mock_github_response

        url = "https://github.com/test-owner/test-repo/blob/main/src/test.py#L10"
        result = get_remote_file_content_by_url(url, "test-token")

        # Should handle gracefully when line number exceeds file length
        expected_content = "## src/test.py#L10\n\n"
        assert result == expected_content
        # Verify that the result contains the header even when no content lines are available
        assert "## src/test.py#L10" in result

    @pytest.mark.parametrize(
        "status_code",
        [400, 401, 403, 422, 500, 502, 503],
    )
    @patch("services.github.files.get_remote_file_content_by_url.requests.get")
    @patch("services.github.files.get_remote_file_content_by_url.create_headers")
    @patch("services.github.files.get_remote_file_content_by_url.parse_github_url")
    def test_various_http_error_codes(
        self, mock_parse_url, mock_create_headers, mock_requests_get,
        mock_parse_github_url, status_code
    ):
        """Test handling of various HTTP error status codes."""
        mock_parse_url.return_value = mock_parse_github_url
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.reason = f"HTTP {status_code} Error"
        mock_response.text = f"Error {status_code}"
        
        http_error = requests.exceptions.HTTPError(f"{status_code} Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_requests_get.return_value = mock_response

        url = "https://github.com/test-owner/test-repo/blob/main/src/test.py"
        result = get_remote_file_content_by_url(url, "test-token")

        # The handle_exceptions decorator should catch all HTTP errors and return empty string
        assert result == ""

    @pytest.mark.parametrize(
        "owner,repo,ref,file_path",
        [
            ("test-owner", "test-repo", "main", "README.md"),
            ("org-name", "repo-name", "develop", "src/main.py"),
            ("user123", "project_name", "feature/new-feature", "docs/guide.txt"),
            ("owner-with-dashes", "repo.with.dots", "v1.0.0", "path/to/file.json"),
            ("CamelCaseOwner", "CamelCaseRepo", "CamelCaseBranch", "CamelCase/File.py"),
        ],
    )
    @patch("services.github.files.get_remote_file_content_by_url.requests.get")
    @patch("services.github.files.get_remote_file_content_by_url.create_headers")
    @patch("services.github.files.get_remote_file_content_by_url.parse_github_url")
    def test_various_parameter_combinations(
        self, mock_parse_url, mock_create_headers, mock_requests_get,
        mock_github_response, owner, repo, ref, file_path
    ):
        """Test that the function handles various parameter combinations correctly."""
        mock_parse_url.return_value = {
            "owner": owner,
            "repo": repo,
            "ref": ref,
            "file_path": file_path,
            "start_line": None,
            "end_line": None,
        }
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_requests_get.return_value = mock_github_response

        url = f"https://github.com/{owner}/{repo}/blob/{ref}/{file_path}"
        result = get_remote_file_content_by_url(url, "test-token")

        assert f"## {file_path}" in result
        expected_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={ref}"
        mock_requests_get.assert_called_once_with(
            url=expected_url,
            headers={"Authorization": "Bearer test-token"},
            timeout=120,
        )

    @patch("services.github.files.get_remote_file_content_by_url.requests.get")
    @patch("services.github.files.get_remote_file_content_by_url.create_headers")
    @patch("services.github.files.get_remote_file_content_by_url.parse_github_url")
    def test_large_file_content(
        self, mock_parse_url, mock_create_headers, mock_requests_get,
        mock_parse_github_url
    ):
        """Test handling of large file content."""
        mock_parse_url.return_value = mock_parse_github_url
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        
        # Create large content (simulating a large file)
        large_content = "# Large file\n" + "print('line')\n" * 100
        encoded_content = base64.b64encode(large_content.encode("utf-8")).decode("utf-8")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "content": encoded_content,
            "encoding": "base64",
        }
        mock_requests_get.return_value = mock_response

        url = "https://github.com/test-owner/test-repo/blob/main/large_file.py"
        result = get_remote_file_content_by_url(url, "test-token")

        assert "## src/test.py" in result
        assert "1: # Large file" in result
        assert "101: print('line')" in result
        # Should have 102 lines total (1 header + 100 print lines + 1 empty line at end)
        assert len(result.split("\n")) >= 104  # Including the header lines
