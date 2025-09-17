# Standard imports
import base64
import json
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest
import requests

# Local imports
from services.github.files.get_remote_file_content import get_remote_file_content


class TestGetRemoteFileContent:
    """Test cases for the get_remote_file_content function."""

    @pytest.fixture
    def base_args(self, create_test_base_args):
        """Create base args for testing."""
        return create_test_base_args(
            owner="test-owner",
            repo="test-repo",
            token="test-token",
            new_branch="test-branch",
        )

    @pytest.fixture
    def mock_file_response(self):
        """Mock successful file response."""
        test_content = "def hello():\n    print('Hello, World!')\n"
        encoded_content = base64.b64encode(test_content.encode("utf-8")).decode("utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": encoded_content,
            "encoding": "base64",
            "name": "test.py",
            "path": "src/test.py",
            "type": "file",
        }
        return mock_response

    @pytest.fixture
    def mock_directory_response(self):
        """Mock directory listing response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"path": "src/file1.py", "type": "file"},
            {"path": "src/file2.py", "type": "file"},
            {"path": "src/utils", "type": "dir"},
        ]
        return mock_response

    @pytest.fixture
    def mock_image_response(self):
        """Mock image file response."""
        # Create a simple base64 encoded image data
        image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": image_data,
            "encoding": "base64",
            "name": "test.png",
            "path": "images/test.png",
            "type": "file",
        }
        return mock_response

    @pytest.fixture
    def mock_404_response(self):
        """Mock 404 response."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        return mock_response

    @pytest.fixture
    def mock_500_response(self):
        """Mock 500 response that raises HTTPError."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        http_error = requests.exceptions.HTTPError("500 Server Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        return mock_response

    # Test successful file retrieval
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_successful_file_retrieval(
        self, mock_create_headers, mock_get, base_args, mock_file_response
    ):
        """Test successful file content retrieval with line numbers."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.return_value = mock_file_response

        result = get_remote_file_content("src/test.py", base_args)

        assert "Opened file: 'src/test.py' with line numbers for your information." in result
        assert "```src/test.py" in result
        assert "1:def hello():" in result
        assert "2:    print('Hello, World!')" in result

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/src/test.py?ref=test-branch",
            headers={"Authorization": "Bearer test-token"},
            timeout=120,
        )
        mock_file_response.raise_for_status.assert_called_once()

    # Test 404 error handling
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_file_not_found_404(
        self, mock_create_headers, mock_get, base_args, mock_404_response
    ):
        """Test handling of 404 file not found."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.return_value = mock_404_response

        result = get_remote_file_content("nonexistent/file.py", base_args)

        assert "get_remote_file_content encountered an HTTPError: 404 Client Error: Not Found" in result
        assert "Check the file path, correct it, and try again." in result

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()
        # Should not call raise_for_status for 404
        mock_404_response.raise_for_status.assert_not_called()

    # Test directory listing
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_directory_listing(
        self, mock_create_headers, mock_get, base_args, mock_directory_response
    ):
        """Test handling of directory path returning file listing."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.return_value = mock_directory_response

        result = get_remote_file_content("src", base_args)

        assert "Searched directory 'src' and found:" in result
        assert '"src/file1.py"' in result
        assert '"src/file2.py"' in result
        assert '"src/utils"' in result

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()
        mock_directory_response.raise_for_status.assert_called_once()

    # Test image file handling
    @patch("services.github.files.get_remote_file_content.describe_image")
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_image_file_handling(
        self, mock_create_headers, mock_get, mock_describe_image, base_args, mock_image_response
    ):
        """Test handling of image files using vision API."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.return_value = mock_image_response
        mock_describe_image.return_value = "This is a test image description."

        result = get_remote_file_content("images/test.png", base_args)

        assert "Opened image file: 'images/test.png' and described the content." in result
        assert "This is a test image description." in result

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()
        mock_describe_image.assert_called_once()

    # Test line number parameter
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_line_number_parameter(
        self, mock_create_headers, mock_get, base_args
    ):
        """Test file retrieval with specific line number."""
        # Create a large file content for testing line number functionality
        large_content = "\n".join([f"line {i}" for i in range(1, 201)])  # 200 lines
        encoded_content = base64.b64encode(large_content.encode("utf-8")).decode("utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": encoded_content,
            "encoding": "base64",
        }

        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.return_value = mock_response

        result = get_remote_file_content("large_file.py", base_args, line_number=100)

        assert "Opened file: 'large_file.py' with line numbers for your information." in result
        assert "```large_file.py#L51-L151" in result  # Should show lines around line 100
        assert "100:line 100" in result

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()

    # Test keyword search
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_keyword_search(
        self, mock_create_headers, mock_get, base_args
    ):
        """Test file retrieval with keyword search."""
        test_content = "\n".join([
            "def function1():",
            "    pass",
            "",
            "def target_function():",
            "    print('This is the target')",
            "",
            "def another_function():",
            "    pass",
            "",
            "def target_helper():",
            "    return 'target found'",
        ])
        encoded_content = base64.b64encode(test_content.encode("utf-8")).decode("utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": encoded_content,
            "encoding": "base64",
        }

        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.return_value = mock_response

        result = get_remote_file_content("test.py", base_args, keyword="target")

        assert "Opened file: 'test.py' and found multiple occurrences of 'target'." in result
        assert "target_function" in result
        assert "target_helper" in result

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()

    # Test keyword not found
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_keyword_not_found(
        self, mock_create_headers, mock_get, base_args, mock_file_response
    ):
        """Test keyword search when keyword is not found."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.return_value = mock_file_response

        result = get_remote_file_content("src/test.py", base_args, keyword="nonexistent")

        assert "Keyword 'nonexistent' not found in the file 'src/test.py'." in result

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()

    # Test both line_number and keyword provided (error case)
    def test_both_line_number_and_keyword_error(self, base_args):
        """Test error when both line_number and keyword are provided."""
        result = get_remote_file_content(
            "test.py", base_args, line_number=10, keyword="test"
        )

        assert "Error: You can only specify either line_number or keyword, not both." in result

    # Test invalid line_number string
    def test_invalid_line_number_string(self, base_args):
        """Test error when line_number is an invalid string."""
        result = get_remote_file_content("test.py", base_args, line_number="invalid")

        assert "Error: line_number 'invalid' is not a valid integer." in result

    # Test valid line_number string conversion
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_valid_line_number_string_conversion(
        self, mock_create_headers, mock_get, base_args, mock_file_response
    ):
        """Test conversion of valid line_number string to integer."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.return_value = mock_file_response

        result = get_remote_file_content("src/test.py", base_args, line_number="1")

        assert "Opened file: 'src/test.py' with line numbers for your information." in result

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()

    # Test HTTP error handling by decorator
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_http_error_handled_by_decorator(
        self, mock_create_headers, mock_get, base_args, mock_500_response
    ):
        """Test that HTTP errors are handled by the decorator."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.return_value = mock_500_response

        result = get_remote_file_content("src/test.py", base_args)

        # The handle_exceptions decorator should catch the error and return empty string
        assert result == ""

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()

    # Test JSON decode error
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_json_decode_error_handled_by_decorator(
        self, mock_create_headers, mock_get, base_args
    ):
        """Test that JSON decode errors are handled by the decorator."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        mock_get.return_value = mock_response

        result = get_remote_file_content("src/test.py", base_args)

        # The handle_exceptions decorator should catch the error and return empty string
        assert result == ""

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()

    # Test request exception
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_request_exception_handled_by_decorator(
        self, mock_create_headers, mock_get, base_args
    ):
        """Test that request exceptions are handled by the decorator."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        result = get_remote_file_content("src/test.py", base_args)

        # The handle_exceptions decorator should catch the error and return empty string
        assert result == ""

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()

    # Test base64 decode error
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_base64_decode_error_handled_by_decorator(
        self, mock_create_headers, mock_get, base_args
    ):
        """Test that base64 decode errors are handled by the decorator."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "invalid-base64-content!@#$%",
            "encoding": "base64",
        }
        mock_get.return_value = mock_response

        result = get_remote_file_content("src/test.py", base_args)

        # The handle_exceptions decorator should catch the error and return empty string
        assert result == ""

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()

    # Test kwargs parameter ignored
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_kwargs_parameter_ignored(
        self, mock_create_headers, mock_get, base_args, mock_file_response
    ):
        """Test that additional kwargs are ignored."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.return_value = mock_file_response

        result = get_remote_file_content(
            "src/test.py", base_args, extra_param="ignored", another_param=123
        )

        assert "Opened file: 'src/test.py' with line numbers for your information." in result

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()

    # Test different image file extensions
    @pytest.mark.parametrize(
        "file_extension",
        [".png", ".jpeg", ".jpg", ".webp", ".gif"]
    )
    @patch("services.github.files.get_remote_file_content.describe_image")
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_various_image_extensions(
        self, mock_create_headers, mock_get, mock_describe_image, base_args, file_extension
    ):
        """Test handling of various image file extensions."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_describe_image.return_value = f"Description of {file_extension} image"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "base64imagedata",
            "encoding": "base64",
        }
        mock_get.return_value = mock_response

        file_path = f"images/test{file_extension}"
        result = get_remote_file_content(file_path, base_args)

        assert f"Opened image file: '{file_path}' and described the content." in result
        assert f"Description of {file_extension} image" in result

        mock_describe_image.assert_called_once_with(base64_image="base64imagedata")

    # Test line break detection
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    @patch("services.github.files.get_remote_file_content.detect_line_break")
    def test_line_break_detection(
        self, mock_detect_line_break, mock_create_headers, mock_get, base_args
    ):
        """Test that line break detection is called and used."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_detect_line_break.return_value = "\r\n"  # Windows line breaks

        test_content = "line1\r\nline2\r\nline3"
        encoded_content = base64.b64encode(test_content.encode("utf-8")).decode("utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": encoded_content,
            "encoding": "base64",
        }
        mock_get.return_value = mock_response

        result = get_remote_file_content("test.py", base_args)

        assert "1:line1" in result
        assert "2:line2" in result
        assert "3:line3" in result

        mock_detect_line_break.assert_called_once_with(text=test_content)
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()

    # Test empty file content
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_empty_file_content(
        self, mock_create_headers, mock_get, base_args
    ):
        """Test handling of empty file content."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

        empty_content = ""
        encoded_content = base64.b64encode(empty_content.encode("utf-8")).decode("utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": encoded_content,
            "encoding": "base64",
        }
        mock_get.return_value = mock_response

        result = get_remote_file_content("empty.txt", base_args)

        assert "Opened file: 'empty.txt' with line numbers for your information." in result
        assert "```empty.txt" in result

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()

    # Test Unicode content handling
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_unicode_content_handling(
        self, mock_create_headers, mock_get, base_args
    ):
        """Test proper handling of Unicode content."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

        unicode_content = "# 测试文件\nprint('Hello, 世界!')\n"
        encoded_content = base64.b64encode(unicode_content.encode("utf-8")).decode("utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": encoded_content,
            "encoding": "base64",
        }
        mock_get.return_value = mock_response

        result = get_remote_file_content("unicode_test.py", base_args)

        assert "1:# 测试文件" in result
        assert "2:print('Hello, 世界!')" in result

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()

    # Test line number formatting with different widths
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_line_number_formatting_width(
        self, mock_create_headers, mock_get, base_args
    ):
        """Test that line numbers are properly formatted with correct width."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

        # Create content with more than 100 lines to test width formatting
        lines = [f"line {i}" for i in range(1, 1001)]  # 1000 lines
        test_content = "\n".join(lines)
        encoded_content = base64.b64encode(test_content.encode("utf-8")).decode("utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": encoded_content,
            "encoding": "base64",
        }
        mock_get.return_value = mock_response

        result = get_remote_file_content("large_file.py", base_args)

        # Line numbers should be right-aligned with width 4 (for 1000 lines)
        assert "   1:line 1" in result
        assert "  10:line 10" in result
        assert " 100:line 100" in result
        assert "1000:line 1000" in result

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()

    # Test line number parameter with small file (no buffer applied)
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_line_number_small_file_no_buffer(
        self, mock_create_headers, mock_get, base_args
    ):
        """Test line number parameter with small file (less than 100 lines)."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

        # Create small file content (less than 100 lines)
        small_content = "\n".join([f"line {i}" for i in range(1, 51)])  # 50 lines
        encoded_content = base64.b64encode(small_content.encode("utf-8")).decode("utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": encoded_content,
            "encoding": "base64",
        }
        mock_get.return_value = mock_response

        result = get_remote_file_content("small_file.py", base_args, line_number=25)

        # Should show entire file since it's small
        assert "Opened file: 'small_file.py' with line numbers for your information." in result
        assert "```small_file.py" in result
        assert "25:line 25" in result
        assert "1:line 1" in result  # Should include first line
        assert "50:line 50" in result  # Should include last line

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()

    # Test line number parameter at beginning of large file
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_line_number_at_beginning_large_file(
        self, mock_create_headers, mock_get, base_args
    ):
        """Test line number parameter at beginning of large file."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

        # Create large file content
        large_content = "\n".join([f"line {i}" for i in range(1, 201)])  # 200 lines
        encoded_content = base64.b64encode(large_content.encode("utf-8")).decode("utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": encoded_content,
            "encoding": "base64",
        }
        mock_get.return_value = mock_response

        result = get_remote_file_content("large_file.py", base_args, line_number=1)

        # Should show entire file since line_number <= 1
        assert "Opened file: 'large_file.py' with line numbers for your information." in result
        assert "```large_file.py" in result
        assert "1:line 1" in result
        assert "200:line 200" in result

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()

    # Test different base_args values
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_different_base_args_values(
        self, mock_create_headers, mock_get, mock_file_response, create_test_base_args
    ):
        """Test function with different base_args values."""
        custom_base_args = create_test_base_args(
            owner="different-owner",
            repo="different-repo",
            token="different-token",
            new_branch="feature-branch",
        )

        mock_create_headers.return_value = {"Authorization": "Bearer different-token"}
        mock_get.return_value = mock_file_response

        result = get_remote_file_content("src/test.py", custom_base_args)

        assert "Opened file: 'src/test.py' with line numbers for your information." in result

        mock_create_headers.assert_called_once_with(token="different-token")
        mock_get.assert_called_once_with(
            url="https://api.github.com/repos/different-owner/different-repo/contents/src/test.py?ref=feature-branch",
            headers={"Authorization": "Bearer different-token"},
            timeout=120,
        )

    # Test special characters in file path
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_special_characters_in_file_path(
        self, mock_create_headers, mock_get, base_args, mock_file_response
    ):
        """Test handling of special characters in file path."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.return_value = mock_file_response

        file_path = "src/files with spaces/test-file.py"
        result = get_remote_file_content(file_path, base_args)

        assert f"Opened file: '{file_path}' with line numbers for your information." in result

        mock_create_headers.assert_called_once_with(token="test-token")
        expected_url = f"https://api.github.com/repos/test-owner/test-repo/contents/{file_path}?ref=test-branch"
        mock_get.assert_called_once_with(
            url=expected_url,
            headers={"Authorization": "Bearer test-token"},
            timeout=120,
        )

    # Test multiple keyword occurrences with segments
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_multiple_keyword_occurrences_with_segments(
        self, mock_create_headers, mock_get, base_args
    ):
        """Test keyword search with multiple occurrences creating segments."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

        # Create content with multiple occurrences of keyword far apart
        lines = []
        for i in range(1, 201):  # 200 lines
            if i == 50 or i == 150:
                lines.append(f"line {i} with target keyword")
            else:
                lines.append(f"line {i}")

        test_content = "\n".join(lines)
        encoded_content = base64.b64encode(test_content.encode("utf-8")).decode("utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": encoded_content,
            "encoding": "base64",
        }
        mock_get.return_value = mock_response

        result = get_remote_file_content("test.py", base_args, keyword="target")

        assert "Opened file: 'test.py' and found multiple occurrences of 'target'." in result
        assert "50:line 50 with target keyword" in result
        assert "150:line 150 with target keyword" in result
        # Should contain segment separators
        assert "•\n•\n•" in result

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()

    # Test vision API error handling
    @patch("services.github.files.get_remote_file_content.describe_image")
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_vision_api_error_handling(
        self, mock_create_headers, mock_get, mock_describe_image, base_args, mock_image_response
    ):
        """Test handling of vision API errors."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_get.return_value = mock_image_response
        mock_describe_image.side_effect = Exception("Vision API error")

        result = get_remote_file_content("images/test.png", base_args)

        # The handle_exceptions decorator should catch the error and return empty string
        assert result == ""

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()
        mock_describe_image.assert_called_once()

    # Test create_headers error handling
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_create_headers_error_handling(
        self, mock_create_headers, mock_get, base_args
    ):
        """Test handling of create_headers errors."""
        mock_create_headers.side_effect = Exception("Header creation failed")

        result = get_remote_file_content("src/test.py", base_args)

        # The handle_exceptions decorator should catch the error and return empty string
        assert result == ""

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_not_called()

    # Test parametrized HTTP error codes
    @pytest.mark.parametrize(
        "status_code",
        [400, 401, 403, 422, 500, 502, 503]
    )
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_various_http_error_codes(
        self, mock_create_headers, mock_get, base_args, status_code
    ):
        """Test handling of various HTTP error status codes."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.reason = f"HTTP {status_code} Error"

        http_error = requests.exceptions.HTTPError(f"{status_code} Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error

        mock_get.return_value = mock_response

        result = get_remote_file_content("src/test.py", base_args)

        # The handle_exceptions decorator should catch all HTTP errors and return empty string
        assert result == ""

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()

    # Test parametrized file types
    @pytest.mark.parametrize(
        "file_extension,content",
        [
            (".py", "#!/usr/bin/env python3\nprint('Hello, World!')"),
            (".js", "console.log('Hello, World!');"),
            (".md", "# Hello World\n\nThis is a markdown file."),
            (".json", '{"message": "Hello, World!"}'),
            (".txt", "Hello, World!\nThis is a text file."),
            (".yml", "version: '3'\nservices:\n  app:\n    image: nginx"),
        ]
    )
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_various_file_types(
        self, mock_create_headers, mock_get, base_args, file_extension, content
    ):
        """Test handling of various file types and content."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": encoded_content,
            "encoding": "base64",
        }
        mock_get.return_value = mock_response

        file_path = f"test{file_extension}"
        result = get_remote_file_content(file_path, base_args)

        assert f"Opened file: '{file_path}' with line numbers for your information." in result
        assert f"```{file_path}" in result
        # Check that content is properly decoded and formatted
        for line_num, line in enumerate(content.split('\n'), 1):
            assert f"{line_num}:{line}" in result

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()

    # Test large file with line number at end
    @patch("services.github.files.get_remote_file_content.requests.get")
    @patch("services.github.files.get_remote_file_content.create_headers")
    def test_line_number_at_end_of_large_file(
        self, mock_create_headers, mock_get, base_args
    ):
        """Test line number parameter at end of large file."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}

        # Create large file content
        large_content = "\n".join([f"line {i}" for i in range(1, 201)])  # 200 lines
        encoded_content = base64.b64encode(large_content.encode("utf-8")).decode("utf-8")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": encoded_content,
            "encoding": "base64",
        }
        mock_get.return_value = mock_response

        result = get_remote_file_content("large_file.py", base_args, line_number=200)

        # Should show lines around line 200 (150-200)
        assert "Opened file: 'large_file.py' with line numbers for your information." in result
        assert "```large_file.py#L150-L200" in result
        assert "200:line 200" in result
        assert "150:line 150" in result

        mock_create_headers.assert_called_once_with(token="test-token")
        mock_get.assert_called_once()
