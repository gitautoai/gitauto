from unittest.mock import patch, MagicMock

from services.efs.extract_dependencies import extract_dependencies


def test_extract_dependencies_extracts_tarball():
    def exists_side_effect(path):
        if path == "/mnt/efs/repo/node_modules.tar.gz":
            return True
        if path == "/tmp/repo/node_modules":
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


def test_extract_dependencies_skips_when_tarball_not_exists():
    with (
        patch("os.path.exists", return_value=False),
        patch("subprocess.run") as mock_run,
    ):
        extract_dependencies("/mnt/efs/repo", "/tmp/repo")

        mock_run.assert_not_called()


def test_extract_dependencies_skips_when_node_modules_already_exists():
    with (
        patch("os.path.exists", return_value=True),
        patch("subprocess.run") as mock_run,
    ):
        extract_dependencies("/mnt/efs/repo", "/tmp/repo")

        mock_run.assert_not_called()
