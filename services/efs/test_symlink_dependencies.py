from unittest.mock import patch

from services.efs.symlink_dependencies import symlink_dependencies


def test_symlink_dependencies_creates_symlink():
    def exists_side_effect(path):
        if path == "/mnt/efs/repo/node_modules":
            return True
        if path == "/tmp/repo/node_modules":
            return False
        return False

    with patch("os.path.exists", side_effect=exists_side_effect), patch(
        "os.symlink"
    ) as mock_symlink:
        symlink_dependencies("/mnt/efs/repo", "/tmp/repo")

        mock_symlink.assert_called_once_with(
            "/mnt/efs/repo/node_modules", "/tmp/repo/node_modules"
        )


def test_symlink_dependencies_skips_when_efs_not_exists():
    def exists_side_effect(_path):
        return False

    with patch("os.path.exists", side_effect=exists_side_effect), patch(
        "os.symlink"
    ) as mock_symlink:
        symlink_dependencies("/mnt/efs/repo", "/tmp/repo")

        mock_symlink.assert_not_called()


def test_symlink_dependencies_skips_when_clone_already_exists():
    def exists_side_effect(_path):
        return True

    with patch("os.path.exists", side_effect=exists_side_effect), patch(
        "os.symlink"
    ) as mock_symlink:
        symlink_dependencies("/mnt/efs/repo", "/tmp/repo")

        mock_symlink.assert_not_called()
