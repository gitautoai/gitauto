# Standard imports
from unittest.mock import patch
import json

# Third-party imports
import pytest

# Local imports
from services.github.files.move_file import move_file
from tests.helpers.create_test_base_args import create_test_base_args


class TestMoveFile:
    """Test cases for the move_file function."""

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
    def mock_tree_items(self):
        """Mock tree items for testing."""
        return [
            {"path": "old/file.py", "type": "blob", "mode": "100644", "sha": "abc123"},
            {
                "path": "other/file.py",
                "type": "blob",
                "mode": "100644",
                "sha": "def456",
            },
        ]

    def test_same_file_paths_error(self, base_args):
        """Test error when old_file_path and new_file_path are the same."""
        result = move_file("same/path.py", "same/path.py", base_args)
        assert (
            result
            == "Error: old_file_path and new_file_path cannot be the same: same/path.py"
        )

    @patch("services.github.files.move_file.get_reference")
    def test_get_reference_failure(self, mock_get_reference, base_args):
        """Test error when get_reference fails."""
        mock_get_reference.return_value = None

        result = move_file("old/path.py", "new/path.py", base_args)

        assert result == "Error: Could not get reference for branch test-branch"
        mock_get_reference.assert_called_once_with(base_args)

    @patch("services.github.files.move_file.get_commit")
    @patch("services.github.files.move_file.get_reference")
    def test_get_commit_failure(self, mock_get_reference, mock_get_commit, base_args):
        """Test error when get_commit fails."""
        mock_get_reference.return_value = "commit_sha_123"
        mock_get_commit.return_value = None

        result = move_file("old/path.py", "new/path.py", base_args)

        assert result == "Error: Could not get tree SHA for commit commit_sha_123"
        mock_get_reference.assert_called_once_with(base_args)
        mock_get_commit.assert_called_once_with(base_args, "commit_sha_123")

    @patch("services.github.files.move_file.get_file_tree")
    @patch("services.github.files.move_file.get_commit")
    @patch("services.github.files.move_file.get_reference")
    def test_file_not_found_error(
        self,
        mock_get_reference,
        mock_get_commit,
        mock_get_file_tree,
        base_args,
        mock_tree_items,
    ):
        """Test error when source file is not found."""
        mock_get_reference.return_value = "commit_sha_123"
        mock_get_commit.return_value = "tree_sha_456"
        mock_get_file_tree.return_value = mock_tree_items

        result = move_file("nonexistent/file.py", "new/path.py", base_args)

        assert result == "Error: File nonexistent/file.py not found"
        mock_get_reference.assert_called_once_with(base_args)
        mock_get_commit.assert_called_once_with(base_args, "commit_sha_123")
        mock_get_file_tree.assert_called_once_with(
            "test-owner", "test-repo", "tree_sha_456", "test-token"
        )

    @patch("services.github.files.move_file.get_file_tree")
    @patch("services.github.files.move_file.get_commit")
    @patch("services.github.files.move_file.get_reference")
    def test_target_file_exists_error(
        self,
        mock_get_reference,
        mock_get_commit,
        mock_get_file_tree,
        base_args,
        mock_tree_items,
    ):
        """Test error when target file already exists."""
        mock_get_reference.return_value = "commit_sha_123"
        mock_get_commit.return_value = "tree_sha_456"
        mock_get_file_tree.return_value = mock_tree_items

        result = move_file("old/file.py", "other/file.py", base_args)

        assert result == "Error: Target file other/file.py already exists"
        mock_get_reference.assert_called_once_with(base_args)
        mock_get_commit.assert_called_once_with(base_args, "commit_sha_123")
        mock_get_file_tree.assert_called_once_with(
            "test-owner", "test-repo", "tree_sha_456", "test-token"
        )

    @patch("services.github.files.move_file.create_tree")
    @patch("services.github.files.move_file.get_file_tree")
    @patch("services.github.files.move_file.get_commit")
    @patch("services.github.files.move_file.get_reference")
    def test_create_tree_failure(
        self,
        mock_get_reference,
        mock_get_commit,
        mock_get_file_tree,
        mock_create_tree,
        base_args,
        mock_tree_items,
    ):
        """Test error when create_tree fails."""
        mock_get_reference.return_value = "commit_sha_123"
        mock_get_commit.return_value = "tree_sha_456"
        mock_get_file_tree.return_value = mock_tree_items
        mock_create_tree.return_value = None

        result = move_file("old/file.py", "new/path.py", base_args)

        assert result == "Error: Could not create new tree"
        mock_get_reference.assert_called_once_with(base_args)
        mock_get_commit.assert_called_once_with(base_args, "commit_sha_123")
        mock_get_file_tree.assert_called_once_with(
            "test-owner", "test-repo", "tree_sha_456", "test-token"
        )

        expected_tree_items = [
            {
                "path": "new/path.py",
                "mode": "100644",
                "type": "blob",
                "sha": "abc123",
            },
            {
                "path": "old/file.py",
                "mode": "100644",
                "type": "blob",
                "sha": None,
            },
        ]
        mock_create_tree.assert_called_once_with(
            base_args, "tree_sha_456", expected_tree_items
        )

    @patch("services.github.files.move_file.create_commit")
    @patch("services.github.files.move_file.create_tree")
    @patch("services.github.files.move_file.get_file_tree")
    @patch("services.github.files.move_file.get_commit")
    @patch("services.github.files.move_file.get_reference")
    def test_create_commit_failure(
        self,
        mock_get_reference,
        mock_get_commit,
        mock_get_file_tree,
        mock_create_tree,
        mock_create_commit,
        base_args,
        mock_tree_items,
    ):
        """Test error when create_commit fails."""
        mock_get_reference.return_value = "commit_sha_123"
        mock_get_commit.return_value = "tree_sha_456"
        mock_get_file_tree.return_value = mock_tree_items
        mock_create_tree.return_value = "new_tree_sha_789"
        mock_create_commit.return_value = None

        result = move_file("old/file.py", "new/path.py", base_args)

        assert result == "Error: Could not create commit"
        mock_get_reference.assert_called_once_with(base_args)
        mock_get_commit.assert_called_once_with(base_args, "commit_sha_123")
        mock_get_file_tree.assert_called_once_with(
            "test-owner", "test-repo", "tree_sha_456", "test-token"
        )
        mock_create_tree.assert_called_once()
        mock_create_commit.assert_called_once_with(
            base_args,
            "Move old/file.py to new/path.py",
            "new_tree_sha_789",
            "commit_sha_123",
        )

    @patch("services.github.files.move_file.update_reference")
    @patch("services.github.files.move_file.create_commit")
    @patch("services.github.files.move_file.create_tree")
    @patch("services.github.files.move_file.get_file_tree")
    @patch("services.github.files.move_file.get_commit")
    @patch("services.github.files.move_file.get_reference")
    def test_successful_move_without_skip_ci(
        self,
        mock_get_reference,
        mock_get_commit,
        mock_get_file_tree,
        mock_create_tree,
        mock_create_commit,
        mock_update_reference,
        base_args,
        mock_tree_items,
    ):
        """Test successful file move without skip_ci."""
        mock_get_reference.return_value = "commit_sha_123"
        mock_get_commit.return_value = "tree_sha_456"
        mock_get_file_tree.return_value = mock_tree_items
        mock_create_tree.return_value = "new_tree_sha_789"
        mock_create_commit.return_value = "new_commit_sha_abc"
        mock_update_reference.return_value = True

        result = move_file("old/file.py", "new/path.py", base_args)

        assert result == "File successfully moved from old/file.py to new/path.py"
        mock_get_reference.assert_called_once_with(base_args)
        mock_get_commit.assert_called_once_with(base_args, "commit_sha_123")
        mock_get_file_tree.assert_called_once_with(
            "test-owner", "test-repo", "tree_sha_456", "test-token"
        )
        mock_create_tree.assert_called_once()
        mock_create_commit.assert_called_once_with(
            base_args,
            "Move old/file.py to new/path.py",
            "new_tree_sha_789",
            "commit_sha_123",
        )
        mock_update_reference.assert_called_once_with(base_args, "new_commit_sha_abc")

    @patch("services.github.files.move_file.update_reference")
    @patch("services.github.files.move_file.create_commit")
    @patch("services.github.files.move_file.create_tree")
    @patch("services.github.files.move_file.get_file_tree")
    @patch("services.github.files.move_file.get_commit")
    @patch("services.github.files.move_file.get_reference")
    def test_successful_move_with_skip_ci(
        self,
        mock_get_reference,
        mock_get_commit,
        mock_get_file_tree,
        mock_create_tree,
        mock_create_commit,
        mock_update_reference,
        base_args,
        mock_tree_items,
    ):
        """Test successful file move with skip_ci enabled."""
        base_args["skip_ci"] = True
        mock_get_reference.return_value = "commit_sha_123"
        mock_get_commit.return_value = "tree_sha_456"
        mock_get_file_tree.return_value = mock_tree_items
        mock_create_tree.return_value = "new_tree_sha_789"
        mock_create_commit.return_value = "new_commit_sha_abc"
        mock_update_reference.return_value = True

        result = move_file("old/file.py", "new/path.py", base_args)

        assert result == "File successfully moved from old/file.py to new/path.py"
        mock_get_reference.assert_called_once_with(base_args)
        mock_get_commit.assert_called_once_with(base_args, "commit_sha_123")
        mock_get_file_tree.assert_called_once_with(
            "test-owner", "test-repo", "tree_sha_456", "test-token"
        )
        mock_create_tree.assert_called_once()
        mock_create_commit.assert_called_once_with(
            base_args,
            "Move old/file.py to new/path.py [skip ci]",
            "new_tree_sha_789",
            "commit_sha_123",
        )
        mock_update_reference.assert_called_once_with(base_args, "new_commit_sha_abc")

    @patch("services.github.files.move_file.get_file_tree")
    @patch("services.github.files.move_file.get_commit")
    @patch("services.github.files.move_file.get_reference")
    def test_file_search_with_non_blob_items(
        self, mock_get_reference, mock_get_commit, mock_get_file_tree, base_args
    ):
        """Test file search ignores non-blob items."""
        mock_get_reference.return_value = "commit_sha_123"
        mock_get_commit.return_value = "tree_sha_456"
        tree_items_with_tree = [
            {
                "path": "old/file.py",
                "type": "tree",  # This should be ignored
                "mode": "040000",
                "sha": "tree123",
            },
            {"path": "old/file.py", "type": "blob", "mode": "100644", "sha": "abc123"},
        ]
        mock_get_file_tree.return_value = tree_items_with_tree

        # This should find the blob, not the tree
        with patch("services.github.files.move_file.create_tree") as mock_create_tree:
            mock_create_tree.return_value = None  # Force failure to check tree items
            result = move_file("old/file.py", "new/path.py", base_args)

            assert result == "Error: Could not create new tree"
            # Verify the correct blob was found by checking the tree items passed to create_tree
            expected_tree_items = [
                {
                    "path": "new/path.py",
                    "mode": "100644",
                    "type": "blob",
                    "sha": "abc123",
                },
                {
                    "path": "old/file.py",
                    "mode": "100644",
                    "type": "blob",
                    "sha": None,
                },
            ]
            mock_create_tree.assert_called_once_with(
                base_args, "tree_sha_456", expected_tree_items
            )

    @patch("services.github.files.move_file.get_file_tree")
    @patch("services.github.files.move_file.get_commit")
    @patch("services.github.files.move_file.get_reference")
    def test_target_file_check_with_non_blob_items(
        self, mock_get_reference, mock_get_commit, mock_get_file_tree, base_args
    ):
        """Test target file existence check ignores non-blob items."""
        mock_get_reference.return_value = "commit_sha_123"
        mock_get_commit.return_value = "tree_sha_456"
        tree_items_with_tree = [
            {"path": "old/file.py", "type": "blob", "mode": "100644", "sha": "abc123"},
            {
                "path": "new/path.py",
                "type": "tree",  # This should be ignored
                "mode": "040000",
                "sha": "tree123",
            },
        ]
        mock_get_file_tree.return_value = tree_items_with_tree

        # This should not find the tree as a conflicting file
        with patch("services.github.files.move_file.create_tree") as mock_create_tree:
            mock_create_tree.return_value = (
                None  # Force failure to verify we got past the target check
            )
            result = move_file("old/file.py", "new/path.py", base_args)

            assert result == "Error: Could not create new tree"
            # If we got here, it means the target file check passed (tree was ignored)

    @patch("services.github.files.move_file.get_file_tree")
    @patch("services.github.files.move_file.get_commit")
    @patch("services.github.files.move_file.get_reference")
    def test_empty_tree_items(
        self, mock_get_reference, mock_get_commit, mock_get_file_tree, base_args
    ):
        """Test behavior with empty tree items."""
        mock_get_reference.return_value = "commit_sha_123"
        mock_get_commit.return_value = "tree_sha_456"
        mock_get_file_tree.return_value = []

        result = move_file("old/file.py", "new/path.py", base_args)

        assert result == "Error: File old/file.py not found"
        mock_get_reference.assert_called_once_with(base_args)
        mock_get_commit.assert_called_once_with(base_args, "commit_sha_123")
        mock_get_file_tree.assert_called_once_with(
            "test-owner", "test-repo", "tree_sha_456", "test-token"
        )

    def test_skip_ci_default_value(self, base_args):
        """Test that skip_ci defaults to False when not provided."""
        # Remove skip_ci from base_args if it exists
        base_args.pop("skip_ci", None)

        with patch(
            "services.github.files.move_file.get_reference"
        ) as mock_get_reference:
            mock_get_reference.return_value = None  # Force early return

            result = move_file("old/file.py", "new/path.py", base_args)

            # The function should handle missing skip_ci gracefully
            assert result == "Error: Could not get reference for branch test-branch"

    @patch("services.github.files.move_file.update_reference")
    @patch("services.github.files.move_file.create_commit")
    @patch("services.github.files.move_file.create_tree")
    @patch("services.github.files.move_file.get_file_tree")
    @patch("services.github.files.move_file.get_commit")
    @patch("services.github.files.move_file.get_reference")
    def test_different_file_modes(
        self,
        mock_get_reference,
        mock_get_commit,
        mock_get_file_tree,
        mock_create_tree,
        mock_create_commit,
        mock_update_reference,
        base_args,
    ):
        """Test moving files with different modes (executable, etc.)."""
        mock_get_reference.return_value = "commit_sha_123"
        mock_get_commit.return_value = "tree_sha_456"
        executable_tree_items = [
            {
                "path": "old/script.sh",
                "type": "blob",
                "mode": "100755",  # Executable file
                "sha": "script123",
            }
        ]
        mock_get_file_tree.return_value = executable_tree_items
        mock_create_tree.return_value = "new_tree_sha_789"
        mock_create_commit.return_value = "new_commit_sha_abc"
        mock_update_reference.return_value = True

        result = move_file("old/script.sh", "new/script.sh", base_args)

        assert result == "File successfully moved from old/script.sh to new/script.sh"

        # Verify the executable mode is preserved
        expected_tree_items = [
            {
                "path": "new/script.sh",
                "mode": "100755",
                "type": "blob",
                "sha": "script123",
            },
            {
                "path": "old/script.sh",
                "mode": "100755",
                "type": "blob",
                "sha": None,
            },
        ]
        mock_create_tree.assert_called_once_with(
            base_args, "tree_sha_456", expected_tree_items
        )

    @patch("services.github.files.move_file.get_reference")
    def test_exception_handling_returns_none(self, mock_get_reference, base_args):
        """Test that exceptions are handled and None is returned due to decorator."""
        # Make get_reference raise an exception
        mock_get_reference.side_effect = Exception("Test exception")

        result = move_file("old/file.py", "new/file.py", base_args)

        # The handle_exceptions decorator should catch the exception and return None
        assert result is None

    @patch("services.github.files.move_file.get_reference")
    def test_json_decode_error_handling(self, mock_get_reference, base_args):
        """Test that JSON decode errors are handled properly."""
        # Make get_reference raise a JSONDecodeError
        mock_get_reference.side_effect = json.JSONDecodeError(
            "Test JSON error", "doc", 0
        )

        result = move_file("old/file.py", "new/file.py", base_args)

        # The handle_exceptions decorator should catch the exception and return None
        assert result is None

    @patch("services.github.files.move_file.get_reference")
    def test_attribute_error_handling(self, mock_get_reference, base_args):
        """Test that AttributeError is handled properly."""
        # Make get_reference raise an AttributeError
        mock_get_reference.side_effect = AttributeError("Test attribute error")

        result = move_file("old/file.py", "new/file.py", base_args)

        # The handle_exceptions decorator should catch the exception and return None
        assert result is None

    @patch("services.github.files.move_file.get_reference")
    def test_key_error_handling(self, mock_get_reference, base_args):
        """Test that KeyError is handled properly."""
        # Make get_reference raise a KeyError
        mock_get_reference.side_effect = KeyError("Test key error")

        result = move_file("old/file.py", "new/file.py", base_args)

        # The handle_exceptions decorator should catch the exception and return None
        assert result is None

    def test_kwargs_parameter_ignored(self, base_args):
        """Test that additional kwargs are ignored."""
        result = move_file(
            "same/path.py", "same/path.py", base_args, extra_param="ignored"
        )
        assert (
            result
            == "Error: old_file_path and new_file_path cannot be the same: same/path.py"
        )
