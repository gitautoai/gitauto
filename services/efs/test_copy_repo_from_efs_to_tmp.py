from unittest.mock import patch, MagicMock

from services.efs.copy_repo_from_efs_to_tmp import copy_repo_from_efs_to_tmp


def test_copy_repo_reuses_existing_clone():
    with patch("os.path.exists", return_value=True), patch(
        "shutil.copytree"
    ) as mock_copytree:
        result = copy_repo_from_efs_to_tmp("/mnt/efs/repo", "/tmp/repo")

        assert result == "/tmp/repo"
        mock_copytree.assert_not_called()


def test_copy_repo_copies_when_not_exists():
    def exists_side_effect(path):
        if path == "/tmp/repo/.git":
            return False
        if path == "/mnt/efs/repo/node_modules":
            return True
        return False

    with patch("os.path.exists", side_effect=exists_side_effect), patch(
        "shutil.copytree"
    ) as mock_copytree, patch(
        "shutil.ignore_patterns", return_value=MagicMock()
    ) as mock_ignore:
        result = copy_repo_from_efs_to_tmp("/mnt/efs/repo", "/tmp/repo")

        assert result == "/tmp/repo"
        mock_ignore.assert_called_once_with("node_modules")
        mock_copytree.assert_called_once()


def test_copy_repo_no_dependency_dirs_to_skip():
    def exists_side_effect(path):
        if path == "/tmp/repo/.git":
            return False
        return False

    with patch("os.path.exists", side_effect=exists_side_effect), patch(
        "shutil.copytree"
    ) as mock_copytree, patch(
        "shutil.ignore_patterns", return_value=MagicMock()
    ) as mock_ignore:
        result = copy_repo_from_efs_to_tmp("/mnt/efs/repo", "/tmp/repo")

        assert result == "/tmp/repo"
        mock_ignore.assert_called_once_with()
        mock_copytree.assert_called_once()


def test_copy_repo_uses_dirs_exist_ok():
    def exists_side_effect(path):
        if path == "/tmp/repo/.git":
            return False
        return False

    with patch("os.path.exists", side_effect=exists_side_effect), patch(
        "shutil.copytree"
    ) as mock_copytree, patch(
        "shutil.ignore_patterns", return_value=MagicMock()
    ) as mock_ignore:
        result = copy_repo_from_efs_to_tmp("/mnt/efs/repo", "/tmp/repo")

        assert result == "/tmp/repo"
        mock_copytree.assert_called_once_with(
            "/mnt/efs/repo",
            "/tmp/repo",
            ignore=mock_ignore.return_value,
            dirs_exist_ok=True,
        )
