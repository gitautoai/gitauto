from unittest.mock import patch, MagicMock

from services.efs.extract_dependencies import extract_dependencies


def test_extract_dependencies_extracts_node_modules_tarball():
    def exists_side_effect(path):
        if path == "/mnt/efs/repo/node_modules.tar.gz":
            return True
        if path == "/tmp/repo/node_modules":
            return False
        if path == "/mnt/efs/repo/vendor.tar.gz":
            return False
        return False

    with (
        patch("os.path.exists", side_effect=exists_side_effect),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)
        extract_dependencies("/mnt/efs/repo", "/tmp/repo")

        mock_run.assert_called_once_with(
            ["tar", "-xzf", "/mnt/efs/repo/node_modules.tar.gz", "-C", "/tmp/repo"],
            check=True,
            capture_output=True,
        )


def test_extract_dependencies_extracts_vendor_tarball():
    def exists_side_effect(path):
        if path == "/mnt/efs/repo/node_modules.tar.gz":
            return False
        if path == "/mnt/efs/repo/vendor.tar.gz":
            return True
        if path == "/tmp/repo/vendor":
            return False
        return False

    with (
        patch("os.path.exists", side_effect=exists_side_effect),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)
        extract_dependencies("/mnt/efs/repo", "/tmp/repo")

        mock_run.assert_called_once_with(
            ["tar", "-xzf", "/mnt/efs/repo/vendor.tar.gz", "-C", "/tmp/repo"],
            check=True,
            capture_output=True,
        )


def test_extract_dependencies_extracts_both_tarballs():
    def exists_side_effect(path):
        if path in (
            "/mnt/efs/repo/node_modules.tar.gz",
            "/mnt/efs/repo/vendor.tar.gz",
        ):
            return True
        if path in ("/tmp/repo/node_modules", "/tmp/repo/vendor"):
            return False
        return False

    with (
        patch("os.path.exists", side_effect=exists_side_effect),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)
        extract_dependencies("/mnt/efs/repo", "/tmp/repo")

        assert mock_run.call_count == 2


def test_extract_dependencies_skips_when_no_tarballs():
    with (
        patch("os.path.exists", return_value=False),
        patch("subprocess.run") as mock_run,
    ):
        extract_dependencies("/mnt/efs/repo", "/tmp/repo")

        mock_run.assert_not_called()


def test_extract_dependencies_skips_when_targets_already_exist():
    with (
        patch("os.path.exists", return_value=True),
        patch("subprocess.run") as mock_run,
    ):
        extract_dependencies("/mnt/efs/repo", "/tmp/repo")

        mock_run.assert_not_called()
