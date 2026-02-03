import os
import tempfile
from unittest.mock import patch

from services.aws.cleanup_tmp import cleanup_tmp


def test_cleanup_tmp_deletes_owner_folders():
    """Test that cleanup_tmp deletes owner/repo folders."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create mock PR folders
        pr_folder = os.path.join(tmp_dir, "Foxquilt", "repo", "pr-123")
        os.makedirs(pr_folder)

        # Create a file inside
        test_file = os.path.join(pr_folder, "test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("test content")

        with patch("services.aws.cleanup_tmp.TMP_DIR", tmp_dir):
            with patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "test"}):
                cleanup_tmp()

        # Owner folder should be deleted
        assert not os.path.exists(os.path.join(tmp_dir, "Foxquilt"))


def test_cleanup_tmp_skips_system_directories():
    """Test that cleanup_tmp skips system directories like .cache, pip, npm."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create system directories that should be preserved
        for sys_dir in [".cache", "pip", "npm", "yarn", "cache"]:
            os.makedirs(os.path.join(tmp_dir, sys_dir))
            with open(os.path.join(tmp_dir, sys_dir, "file.txt"), "w", encoding="utf-8") as f:
                f.write("keep me")

        # Create an owner folder that should be deleted
        os.makedirs(os.path.join(tmp_dir, "Foxquilt", "repo"))

        with patch("services.aws.cleanup_tmp.TMP_DIR", tmp_dir):
            with patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "test"}):
                cleanup_tmp()

        # System directories should still exist
        for sys_dir in [".cache", "pip", "npm", "yarn", "cache"]:
            assert os.path.exists(os.path.join(tmp_dir, sys_dir))

        # Owner folder should be deleted
        assert not os.path.exists(os.path.join(tmp_dir, "Foxquilt"))


def test_cleanup_tmp_handles_empty_tmp():
    """Test that cleanup_tmp handles empty /tmp gracefully."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        with patch("services.aws.cleanup_tmp.TMP_DIR", tmp_dir):
            with patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "test"}):
                # Should not raise
                cleanup_tmp()


def test_cleanup_tmp_handles_nonexistent_tmp():
    """Test that cleanup_tmp handles non-existent /tmp gracefully."""
    with patch("services.aws.cleanup_tmp.TMP_DIR", "/nonexistent/path"):
        with patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "test"}):
            # Should not raise
            cleanup_tmp()


def test_cleanup_tmp_skips_when_not_on_lambda():
    """Test that cleanup_tmp does nothing when not running on Lambda."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a folder that would be deleted on Lambda
        os.makedirs(os.path.join(tmp_dir, "Foxquilt", "repo"))

        with patch("services.aws.cleanup_tmp.TMP_DIR", tmp_dir):
            # No AWS_LAMBDA_FUNCTION_NAME set - simulates local dev
            with patch.dict(os.environ, {}, clear=True):
                cleanup_tmp()

        # Folder should NOT be deleted (we're not on Lambda)
        assert os.path.exists(os.path.join(tmp_dir, "Foxquilt"))
