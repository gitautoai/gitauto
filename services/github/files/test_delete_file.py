# Standard imports
from unittest.mock import patch
import json

# Third-party imports
import pytest

# Local imports
from services.github.files.delete_file import delete_file
from tests.helpers.create_test_base_args import create_test_base_args


class TestDeleteFile:
    """Test cases for the delete_file function."""

    @pytest.fixture
    def base_args(self):
        """Create base args for testing."""
        return create_test_base_args(
            owner="test-owner",
            repo="test-repo",
            token="test-token",
            new_branch="test-branch",
        )

    @pytest.fixture
    def mock_file_info(self):
        """Mock file info for testing."""
        return {
            "name": "test_file.py",
            "path": "test_file.py",
            "sha": "abc123def456",
            "size": 1024,
            "url": "https://api.github.com/repos/test-owner/test-repo/contents/test_file.py",
            "html_url": "https://github.com/test-owner/test-repo/blob/main/test_file.py",
            "git_url": "https://api.github.com/repos/test-owner/test-repo/git/blobs/abc123def456",
            "download_url": "https://raw.githubusercontent.com/test-owner/test-repo/main/test_file.py",
            "type": "file",
            "content": "dGVzdCBjb250ZW50",
            "encoding": "base64",
        }

    @patch("services.github.files.delete_file.get_file_info")
    def test_file_not_found(self, mock_get_file_info, base_args):
        """Test error when file is not found."""
        mock_get_file_info.return_value = None

        result = delete_file("nonexistent_file.py", base_args)

        assert result == "Error: File nonexistent_file.py not found or is a directory"
        mock_get_file_info.assert_called_once_with("nonexistent_file.py", base_args)

    @patch("services.github.files.delete_file.get_file_info")
    def test_file_info_missing_sha(self, mock_get_file_info, base_args, mock_file_info):
        """Test error when file info doesn't contain SHA."""
        # Remove SHA from file info
        mock_file_info_no_sha = mock_file_info.copy()
        del mock_file_info_no_sha["sha"]
        mock_get_file_info.return_value = mock_file_info_no_sha

        result = delete_file("test_file.py", base_args)

        assert result == "Error: Unable to get SHA for file test_file.py"
        mock_get_file_info.assert_called_once_with("test_file.py", base_args)

    @patch("services.github.files.delete_file.get_file_info")
    def test_file_info_empty_sha(self, mock_get_file_info, base_args, mock_file_info):
        """Test error when file info contains empty SHA."""
        # Set SHA to empty string
        mock_file_info_empty_sha = mock_file_info.copy()
        mock_file_info_empty_sha["sha"] = ""
        mock_get_file_info.return_value = mock_file_info_empty_sha

        result = delete_file("test_file.py", base_args)

        assert result == "Error: Unable to get SHA for file test_file.py"
        mock_get_file_info.assert_called_once_with("test_file.py", base_args)

    @patch("services.github.files.delete_file.get_file_info")
    def test_file_info_none_sha(self, mock_get_file_info, base_args, mock_file_info):
        """Test error when file info contains None SHA."""
        # Set SHA to None
        mock_file_info_none_sha = mock_file_info.copy()
        mock_file_info_none_sha["sha"] = None
        mock_get_file_info.return_value = mock_file_info_none_sha

        result = delete_file("test_file.py", base_args)

        assert result == "Error: Unable to get SHA for file test_file.py"
        mock_get_file_info.assert_called_once_with("test_file.py", base_args)

    @patch("services.github.files.delete_file.get_file_info")
    def test_file_info_whitespace_sha(
        self, mock_get_file_info, base_args, mock_file_info
    ):
        """Test error when file info contains whitespace-only SHA."""
        # Set SHA to whitespace string
        mock_file_info_whitespace_sha = mock_file_info.copy()
        mock_file_info_whitespace_sha["sha"] = "   "
        mock_get_file_info.return_value = mock_file_info_whitespace_sha

        result = delete_file("test_file.py", base_args)

        assert result == "Error: Unable to get SHA for file test_file.py"
        mock_get_file_info.assert_called_once_with("test_file.py", base_args)

    @patch("services.github.files.delete_file.delete_file_by_sha")
    @patch("services.github.files.delete_file.get_file_info")
    def test_successful_deletion(
        self, mock_get_file_info, mock_delete_file_by_sha, base_args, mock_file_info
    ):
        """Test successful file deletion."""
        mock_get_file_info.return_value = mock_file_info
        mock_delete_file_by_sha.return_value = "File test_file.py successfully deleted"

        result = delete_file("test_file.py", base_args)

        assert result == "File test_file.py successfully deleted"
        mock_get_file_info.assert_called_once_with("test_file.py", base_args)
        mock_delete_file_by_sha.assert_called_once_with(
            "test_file.py", "abc123def456", base_args
        )

    @patch("services.github.files.delete_file.delete_file_by_sha")
    @patch("services.github.files.delete_file.get_file_info")
    def test_delete_file_by_sha_failure(
        self, mock_get_file_info, mock_delete_file_by_sha, base_args, mock_file_info
    ):
        """Test when delete_file_by_sha fails."""
        mock_get_file_info.return_value = mock_file_info
        mock_delete_file_by_sha.return_value = None  # Simulating failure

        result = delete_file("test_file.py", base_args)

        assert result is None
        mock_get_file_info.assert_called_once_with("test_file.py", base_args)
        mock_delete_file_by_sha.assert_called_once_with(
            "test_file.py", "abc123def456", base_args
        )

    @patch("services.github.files.delete_file.delete_file_by_sha")
    @patch("services.github.files.delete_file.get_file_info")
    def test_delete_file_by_sha_returns_error_message(
        self, mock_get_file_info, mock_delete_file_by_sha, base_args, mock_file_info
    ):
        """Test when delete_file_by_sha returns an error message."""
        mock_get_file_info.return_value = mock_file_info
        mock_delete_file_by_sha.return_value = "Error: Failed to delete file"

        result = delete_file("test_file.py", base_args)

        assert result == "Error: Failed to delete file"
        mock_get_file_info.assert_called_once_with("test_file.py", base_args)
        mock_delete_file_by_sha.assert_called_once_with(
            "test_file.py", "abc123def456", base_args
        )

    @patch("services.github.files.delete_file.get_file_info")
    def test_exception_handling_returns_none(self, mock_get_file_info, base_args):
        """Test that exceptions are handled and None is returned due to decorator."""
        # Make get_file_info raise an exception
        mock_get_file_info.side_effect = Exception("Test exception")

        result = delete_file("test_file.py", base_args)

        # The handle_exceptions decorator should catch the exception and return None
        assert result is None

    @patch("services.github.files.delete_file.get_file_info")
    def test_json_decode_error_handling(self, mock_get_file_info, base_args):
        """Test that JSON decode errors are handled properly."""
        # Make get_file_info raise a JSONDecodeError
        mock_get_file_info.side_effect = json.JSONDecodeError(
            "Test JSON error", "doc", 0
        )

        result = delete_file("test_file.py", base_args)

        # The handle_exceptions decorator should catch the exception and return None
        assert result is None

    @patch("services.github.files.delete_file.get_file_info")
    def test_attribute_error_handling(self, mock_get_file_info, base_args):
        """Test that AttributeError is handled properly."""
        # Make get_file_info raise an AttributeError
        mock_get_file_info.side_effect = AttributeError("Test attribute error")

        result = delete_file("test_file.py", base_args)

        # The handle_exceptions decorator should catch the exception and return None
        assert result is None

    @patch("services.github.files.delete_file.get_file_info")
    def test_key_error_handling(self, mock_get_file_info, base_args):
        """Test that KeyError is handled properly."""
        # Make get_file_info raise a KeyError
        mock_get_file_info.side_effect = KeyError("Test key error")

        result = delete_file("test_file.py", base_args)

        # The handle_exceptions decorator should catch the exception and return None
        assert result is None

    def test_kwargs_parameter_ignored(self, base_args):
        """Test that additional kwargs are ignored."""
        with patch(
            "services.github.files.delete_file.get_file_info"
        ) as mock_get_file_info:
            mock_get_file_info.return_value = None

            result = delete_file("test_file.py", base_args, extra_param="ignored")

            assert result == "Error: File test_file.py not found or is a directory"
            mock_get_file_info.assert_called_once_with("test_file.py", base_args)

    @patch("services.github.files.delete_file.delete_file_by_sha")
    @patch("services.github.files.delete_file.get_file_info")
    def test_different_file_paths(
        self, mock_get_file_info, mock_delete_file_by_sha, base_args, mock_file_info
    ):
        """Test deletion with different file paths."""
        mock_get_file_info.return_value = mock_file_info
        mock_delete_file_by_sha.return_value = (
            "File path/to/nested/file.py successfully deleted"
        )

        result = delete_file("path/to/nested/file.py", base_args)

        assert result == "File path/to/nested/file.py successfully deleted"
        mock_get_file_info.assert_called_once_with("path/to/nested/file.py", base_args)
        mock_delete_file_by_sha.assert_called_once_with(
            "path/to/nested/file.py", "abc123def456", base_args
        )

    def test_empty_file_path(self, base_args):
        """Test behavior with empty file path."""
        with patch(
            "services.github.files.delete_file.get_file_info"
        ) as mock_get_file_info:
            mock_get_file_info.return_value = None

            result = delete_file("", base_args)

            assert result == "Error: File  not found or is a directory"
            mock_get_file_info.assert_called_once_with("", base_args)
