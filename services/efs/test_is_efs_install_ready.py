from unittest.mock import patch

from services.efs.is_efs_install_ready import is_efs_install_ready


def test_is_efs_install_ready_returns_true_when_bin_exists():
    with patch(
        "services.efs.is_efs_install_ready.get_efs_dir",
        return_value="/mnt/efs/owner/repo",
    ):
        with patch(
            "services.efs.is_efs_install_ready.os.path.exists", return_value=True
        ):
            with patch(
                "services.efs.is_efs_install_ready.os.listdir",
                return_value=["eslint", "prettier"],
            ):
                result = is_efs_install_ready("owner", "repo", "node")

    assert result is True


def test_is_efs_install_ready_returns_false_when_bin_empty():
    with patch(
        "services.efs.is_efs_install_ready.get_efs_dir",
        return_value="/mnt/efs/owner/repo",
    ):
        with patch(
            "services.efs.is_efs_install_ready.os.path.exists", return_value=True
        ):
            with patch("services.efs.is_efs_install_ready.os.listdir", return_value=[]):
                result = is_efs_install_ready("owner", "repo", "node")

    assert result is False


def test_is_efs_install_ready_returns_false_when_bin_not_exists():
    with patch(
        "services.efs.is_efs_install_ready.get_efs_dir",
        return_value="/mnt/efs/owner/repo",
    ):
        with patch(
            "services.efs.is_efs_install_ready.os.path.exists", return_value=False
        ):
            result = is_efs_install_ready("owner", "repo", "node")

    assert result is False
