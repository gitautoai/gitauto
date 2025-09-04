import base64
import pytest
import requests
from unittest.mock import MagicMock, patch

from services.github.files.create_file_with_content import create_file_with_content


class TestCreateFileWithContent:
    @pytest.fixture
    def base_args(self):
        """Base arguments for create_file_with_content function."""
        return {
            "owner": "test-owner",
            "repo": "test-repo",
            "token": "test-token",
            "new_branch": "test-branch",
            "base_branch": "main",
            "clone_url": "https://github.com/test-owner/test-repo.git",
            "github_urls": [],
            "input_from": "github",
            "skip_ci": False,
        }

    @pytest.fixture
    def base_args_with_skip_ci(self):
        """Base arguments with skip_ci enabled."""
        return {
            "owner": "test-owner",
            "repo": "test-repo",
            "token": "test-token",
            "new_branch": "test-branch",
            "base_branch": "main",
            "clone_url": "https://github.com/test-owner/test-repo.git",
            "github_urls": [],
            "input_from": "github",
            "skip_ci": True,
        }

    @pytest.fixture
    def create_test_base_args(self):
        """Factory function to create base_args with custom parameters."""
        def _create_base_args(**kwargs):
            default_args = {
                "owner": "test-owner",
                "repo": "test-repo",
                "token": "test-token",
                "new_branch": "test-branch",
                "base_branch": "main",
                "clone_url": "https://github.com/test-owner/test-repo.git",
                "github_urls": [],
                "input_from": "github",
                "skip_ci": False,
            }
            default_args.update(kwargs)
            return default_args
        return _create_base_args

    @pytest.fixture
    def mock_successful_response(self):
        """Mock successful HTTP response."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.raise_for_status.return_value = None
        return mock_response

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_successful_file_creation(
        self, mock_create_headers, mock_put, base_args, mock_successful_response
    ):
        """Test successful file creation with expected content."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_put.return_value = mock_successful_response

        file_path = "src/test.py"
        content = "print('Hello, World!')"
        result = create_file_with_content(file_path, content, base_args)

        assert result == f"File {file_path} successfully created"

        # Verify the correct API call was made
        expected_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        expected_data = {
            "message": f"Create {file_path}",
            "content": expected_content,
            "branch": "test-branch",
        }

        mock_put.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/src/test.py?ref=test-branch",
            json=expected_data,
            headers={"Authorization": "Bearer test-token"},
            timeout=120,
        )

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_file_already_exists_error(
        self, mock_create_headers, mock_put, base_args
    ):
        """Test handling when file already exists."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.reason = "Unprocessable Entity"
        mock_response.text = "Invalid request"
        http_error = requests.exceptions.HTTPError("Unprocessable Entity")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_put.return_value = mock_response

        result = create_file_with_content("existing_file.py", "content", base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_put.assert_called_once()

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_custom_commit_message(
        self, mock_create_headers, mock_put, base_args, mock_successful_response
    ):
        """Test file creation with custom commit message."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_put.return_value = mock_successful_response

        file_path = "docs/README.md"
        content = "# Documentation"
        custom_message = "Add documentation file"
        result = create_file_with_content(
            file_path, content, base_args, commit_message=custom_message
        )

        assert result == f"File {file_path} successfully created"

        # Verify the custom commit message was used
        expected_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        expected_data = {
            "message": custom_message,
            "content": expected_content,
            "branch": "test-branch",
        }

        mock_put.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/docs/README.md?ref=test-branch",
            json=expected_data,
            headers={"Authorization": "Bearer test-token"},
            timeout=120,
        )

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_skip_ci_commit_message(
        self, mock_create_headers, mock_put, base_args_with_skip_ci, mock_successful_response
    ):
        """Test file creation with skip CI commit message."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_put.return_value = mock_successful_response

        file_path = "config/settings.json"
        content = '{"debug": true}'
        result = create_file_with_content(file_path, content, base_args_with_skip_ci)

        assert result == f"File {file_path} successfully created"

        # Verify the skip CI message was used
        expected_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        expected_data = {
            "message": f"Create {file_path} [skip ci]",
            "content": expected_content,
            "branch": "test-branch",
        }

        mock_put.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/config/settings.json?ref=test-branch",
            json=expected_data,
            headers={"Authorization": "Bearer test-token"},
            timeout=120,
        )

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_empty_content(
        self, mock_create_headers, mock_put, base_args, mock_successful_response
    ):
        """Test file creation with empty content."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_put.return_value = mock_successful_response

        file_path = "empty.txt"
        content = ""
        result = create_file_with_content(file_path, content, base_args)

        assert result == f"File {file_path} successfully created"

        # Verify empty content is properly base64 encoded
        expected_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        expected_data = {
            "message": f"Create {file_path}",
            "content": expected_content,
            "branch": "test-branch",
        }

        mock_put.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/empty.txt?ref=test-branch",
            json=expected_data,
            headers={"Authorization": "Bearer test-token"},
            timeout=120,
        )

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_nested_directory_file(
        self, mock_create_headers, mock_put, base_args, mock_successful_response
    ):
        """Test file creation in nested directory structure."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_put.return_value = mock_successful_response

        file_path = "src/components/ui/Button.tsx"
        content = "export const Button = () => <button>Click me</button>;"
        result = create_file_with_content(file_path, content, base_args)

        assert result == f"File {file_path} successfully created"

        # Verify the URL is correctly constructed for nested paths
        expected_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        expected_data = {
            "message": f"Create {file_path}",
            "content": expected_content,
            "branch": "test-branch",
        }

        mock_put.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/src/components/ui/Button.tsx?ref=test-branch",
            json=expected_data,
            headers={"Authorization": "Bearer test-token"},
            timeout=120,
        )

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_unicode_content(
        self, mock_create_headers, mock_put, base_args, mock_successful_response
    ):
        """Test file creation with Unicode content."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_put.return_value = mock_successful_response

        file_path = "unicode.txt"
        content = "Hello 世界! 🌍 Café naïve résumé"
        result = create_file_with_content(file_path, content, base_args)

        assert result == f"File {file_path} successfully created"

        # Verify Unicode content is properly base64 encoded
        expected_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        expected_data = {
            "message": f"Create {file_path}",
            "content": expected_content,
            "branch": "test-branch",
        }

        mock_put.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/unicode.txt?ref=test-branch",
            json=expected_data,
            headers={"Authorization": "Bearer test-token"},
            timeout=120,
        )

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_special_characters_in_filename(
        self, mock_create_headers, mock_put, base_args, mock_successful_response
    ):
        """Test file creation with special characters in filename."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_put.return_value = mock_successful_response

        file_path = "files/test-file_v1.2.3.txt"
        content = "Test content"
        result = create_file_with_content(file_path, content, base_args)

        assert result == f"File {file_path} successfully created"

        # Verify special characters in filename are handled correctly
        expected_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        expected_data = {
            "message": f"Create {file_path}",
            "content": expected_content,
            "branch": "test-branch",
        }

        mock_put.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/files/test-file_v1.2.3.txt?ref=test-branch",
            json=expected_data,
            headers={"Authorization": "Bearer test-token"},
            timeout=120,
        )

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_base64_encoding_correctness(
        self, mock_create_headers, mock_put, base_args, mock_successful_response
    ):
        """Test that content is correctly base64 encoded."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_put.return_value = mock_successful_response

        file_path = "test.py"
        content = "def hello():\n    print('Hello, World!')\n    return 42"
        result = create_file_with_content(file_path, content, base_args)

        assert result == f"File {file_path} successfully created"

        # Verify the content was correctly base64 encoded
        call_args = mock_put.call_args
        sent_content = call_args[1]["json"]["content"]
        decoded_content = base64.b64decode(sent_content).decode("utf-8")
        assert decoded_content == content

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_large_content_handling(
        self, mock_create_headers, mock_put, base_args, mock_successful_response
    ):
        """Test file creation with large content."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_put.return_value = mock_successful_response

        # Create large content (1MB of text)
        large_content = "A" * (1024 * 1024)
        result = create_file_with_content("large_file.txt", large_content, base_args)

        assert result == "File large_file.txt successfully created"
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_put.assert_called_once()

        # Verify the content was properly base64 encoded
        call_args = mock_put.call_args
        sent_content = call_args[1]["json"]["content"]
        decoded_content = base64.b64decode(sent_content).decode("utf-8")
        assert decoded_content == large_content

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_binary_content_handling(
        self, mock_create_headers, mock_put, base_args, mock_successful_response
    ):
        """Test file creation with binary-like content."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_put.return_value = mock_successful_response

        # Create content with null bytes and special characters
        binary_content = "Binary content with \\x00 null bytes and \\xff special chars"
        result = create_file_with_content("binary_file.bin", binary_content, base_args)

        assert result == "File binary_file.bin successfully created"
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_put.assert_called_once()

        # Verify the content was properly base64 encoded
        call_args = mock_put.call_args
        sent_content = call_args[1]["json"]["content"]
        decoded_content = base64.b64decode(sent_content).decode("utf-8")
        assert decoded_content == binary_content

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_multiline_content_with_various_line_endings(
        self, mock_create_headers, mock_put, base_args, mock_successful_response
    ):
        """Test file creation with multiline content and various line endings."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_put.return_value = mock_successful_response

        # Content with different line endings
        multiline_content = "Line 1\\nLine 2\\r\\nLine 3\\rLine 4\\n"
        result = create_file_with_content("multiline.txt", multiline_content, base_args)

        assert result == "File multiline.txt successfully created"
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_put.assert_called_once()

        # Verify the content was properly base64 encoded
        call_args = mock_put.call_args
        sent_content = call_args[1]["json"]["content"]
        decoded_content = base64.b64decode(sent_content).decode("utf-8")
        assert decoded_content == multiline_content

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_file_path_with_url_special_characters(
        self, mock_create_headers, mock_put, base_args, mock_successful_response
    ):
        """Test file creation with file path containing URL special characters."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_put.return_value = mock_successful_response

        # File path with characters that need URL encoding
        file_path = "path with spaces/file@name#test.py"
        content = "# Test file with special path"
        result = create_file_with_content(file_path, content, base_args)

        assert result == f"File {file_path} successfully created"
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_put.assert_called_once()

        # Verify the URL construction
        call_args = mock_put.call_args
        expected_url = f"https://api.github.com/repos/test-owner/test-repo/contents/{file_path}?ref=test-branch"
        assert call_args[1]["url"] == expected_url

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_timeout_exception_handled_by_decorator(
        self, mock_create_headers, mock_put, base_args
    ):
        """Test that timeout exceptions are handled by the decorator."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_put.side_effect = requests.exceptions.Timeout("Request timed out")

        result = create_file_with_content("test_file.py", "content", base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_put.assert_called_once()

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_connection_error_handled_by_decorator(
        self, mock_create_headers, mock_put, base_args
    ):
        """Test that connection errors are handled by the decorator."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_put.side_effect = requests.exceptions.ConnectionError("Connection failed")

        result = create_file_with_content("test_file.py", "content", base_args)

        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_create_headers.assert_called_once_with(token="test-token")

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_rate_limit_error_handled_by_decorator(
        self, mock_create_headers, mock_put, base_args
    ):
        """Test that rate limit errors are handled by the decorator."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_put.side_effect = requests.exceptions.HTTPError("Rate limit exceeded")

        result = create_file_with_content("test_file.py", "content", base_args)
        
        # The handle_exceptions decorator should catch the error and return None
        assert result is None
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_put.assert_called_once()

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_custom_commit_message_with_skip_ci_override(
        self, mock_create_headers, mock_put, base_args_with_skip_ci, mock_successful_response
    ):
        """Test that custom commit message overrides skip_ci behavior."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_put.return_value = mock_successful_response

        file_path = "src/test.py"
        content = "print('Hello, World!')"
        custom_message = "Custom message without skip ci"

        result = create_file_with_content(
            file_path, content, base_args_with_skip_ci, commit_message=custom_message
        )

        assert result == f"File {file_path} successfully created"

        # Verify the custom commit message is used (not the skip_ci default)
        expected_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        expected_data = {
            "message": custom_message,
            "content": expected_content,
            "branch": "test-branch",
        }

        mock_put.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/src/test.py?ref=test-branch",
            json=expected_data,
            headers={"Authorization": "Bearer test-token"},
            timeout=120,
        )

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_root_level_file_creation(
        self, mock_create_headers, mock_put, base_args, mock_successful_response
    ):
        """Test file creation at root level (no subdirectories)."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_put.return_value = mock_successful_response

        file_path = "README.md"
        content = "# Project Title\\n\\nProject description."
        result = create_file_with_content(file_path, content, base_args)

        assert result == f"File {file_path} successfully created"
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_put.assert_called_once()

        # Verify the URL construction for root level file
        call_args = mock_put.call_args
        expected_url = "https://api.github.com/repos/test-owner/test-repo/contents/README.md?ref=test-branch"

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_very_long_file_path(
        self, mock_create_headers, mock_put, base_args, mock_successful_response
    ):
        """Test file creation with very long file path."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_put.return_value = mock_successful_response

        # Create a very long file path
        long_path_segments = ["very"] * 20 + ["long"] * 20 + ["path"] * 10
        file_path = "/".join(long_path_segments) + "/test_file.py"
        content = "# Test file with very long path"
        result = create_file_with_content(file_path, content, base_args)

        assert result == f"File {file_path} successfully created"
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_put.assert_called_once()

        # Verify the URL construction
        call_args = mock_put.call_args
        expected_url = f"https://api.github.com/repos/test-owner/test-repo/contents/{file_path}?ref=test-branch"
        assert call_args[1]["url"] == expected_url

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_content_with_json_special_characters(
        self, mock_create_headers, mock_put, base_args, mock_successful_response
    ):
        """Test file creation with content containing JSON special characters."""
        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_put.return_value = mock_successful_response

        # Content with JSON special characters that need escaping
        json_content = '{"message": "Hello \\"World\\"", "data": [1, 2, 3], "escaped": "\\n\\t\\r"}'
        result = create_file_with_content("config.json", json_content, base_args)

        assert result == "File config.json successfully created"
        mock_create_headers.assert_called_once_with(token="test-token")
        mock_put.assert_called_once()

        # Verify the content was properly base64 encoded
        call_args = mock_put.call_args
        sent_content = call_args[1]["json"]["content"]
        decoded_content = base64.b64decode(sent_content).decode("utf-8")
        assert decoded_content == json_content

    @patch("services.github.files.create_file_with_content.requests.put")
    @patch("services.github.files.create_file_with_content.create_headers")
    def test_base_args_missing_skip_ci_key(
        self, mock_create_headers, mock_put, mock_successful_response, create_test_base_args
    ):
        """Test function behavior when skip_ci key is missing from base_args."""
        # Create base_args without skip_ci key
        base_args_no_skip_ci = create_test_base_args(
            owner="test-owner",
            repo="test-repo",
            token="test-token",
            new_branch="test-branch",
        )
        # Ensure skip_ci is not in the dict
        if "skip_ci" in base_args_no_skip_ci:
            del base_args_no_skip_ci["skip_ci"]

        mock_create_headers.return_value = {"Authorization": "Bearer test-token"}
        mock_put.return_value = mock_successful_response

        file_path = "test.py"
        content = "print('test')"
        result = create_file_with_content(file_path, content, base_args_no_skip_ci)

        assert result == f"File {file_path} successfully created"

        # Verify the default commit message is used (no skip_ci)
        expected_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        expected_data = {
            "message": f"Create {file_path}",
            "content": expected_content,
            "branch": "test-branch",
        }

        mock_put.assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/contents/test.py?ref=test-branch",
            json=expected_data,
            headers={"Authorization": "Bearer test-token"},
            timeout=120,
        )
