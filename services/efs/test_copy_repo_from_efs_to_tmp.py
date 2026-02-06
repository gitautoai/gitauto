from unittest.mock import patch

from services.efs.copy_repo_from_efs_to_tmp import (
    IGNORE_EFS_FILES,
    copy_repo_from_efs_to_tmp,
)


def test_copy_repo_reuses_existing_clone():
    with patch("os.path.exists", return_value=True), patch(
        "shutil.copytree"
    ) as mock_copytree:
        result = copy_repo_from_efs_to_tmp("/mnt/efs/repo", "/tmp/repo")

        assert result == "/tmp/repo"
        mock_copytree.assert_not_called()


def test_copy_repo_copies_with_ignore_patterns():
    def exists_side_effect(path):
        if path == "/tmp/repo/.git":
            return False
        return False

    with patch("os.path.exists", side_effect=exists_side_effect), patch(
        "shutil.copytree"
    ) as mock_copytree:
        result = copy_repo_from_efs_to_tmp("/mnt/efs/repo", "/tmp/repo")

        assert result == "/tmp/repo"
        mock_copytree.assert_called_once_with(
            "/mnt/efs/repo",
            "/tmp/repo",
            ignore=IGNORE_EFS_FILES,
            dirs_exist_ok=True,
        )


def test_ignore_patterns_excludes_correct_files():
    # IGNORE_EFS_FILES is a function returned by shutil.ignore_patterns
    # that takes (directory, files) and returns files to ignore
    files = ["file.py", "node_modules.tar.gz", "index.lock", "package-lock.json"]
    ignored = IGNORE_EFS_FILES("/some/dir", files)

    assert "node_modules.tar.gz" in ignored
    assert "index.lock" in ignored
    assert "file.py" not in ignored
    assert "package-lock.json" not in ignored
