from concurrent.futures import Future
from unittest.mock import patch

from services.efs.is_efs_install_ready import is_efs_install_ready


def test_is_efs_install_ready_returns_true_when_install_succeeds():
    future = Future()
    future.set_result(True)

    with patch(
        "services.efs.is_efs_install_ready.install_futures",
        {"/mnt/efs/owner/repo": {"node": future}},
    ):
        with patch(
            "services.efs.is_efs_install_ready.get_efs_dir",
            return_value="/mnt/efs/owner/repo",
        ):
            result = is_efs_install_ready("owner", "repo", "node")

    assert result is True


def test_is_efs_install_ready_returns_false_when_install_fails():
    future = Future()
    future.set_result(False)

    with patch(
        "services.efs.is_efs_install_ready.install_futures",
        {"/mnt/efs/owner/repo": {"node": future}},
    ):
        with patch(
            "services.efs.is_efs_install_ready.get_efs_dir",
            return_value="/mnt/efs/owner/repo",
        ):
            result = is_efs_install_ready("owner", "repo", "node")

    assert result is False


def test_is_efs_install_ready_returns_false_when_no_future():
    with patch("services.efs.is_efs_install_ready.install_futures", {}):
        with patch(
            "services.efs.is_efs_install_ready.get_efs_dir",
            return_value="/mnt/efs/owner/repo",
        ):
            result = is_efs_install_ready("owner", "repo", "node")

    assert result is False


def test_is_efs_install_ready_returns_false_when_wrong_installer():
    future = Future()
    future.set_result(True)

    with patch(
        "services.efs.is_efs_install_ready.install_futures",
        {"/mnt/efs/owner/repo": {"python": future}},
    ):
        with patch(
            "services.efs.is_efs_install_ready.get_efs_dir",
            return_value="/mnt/efs/owner/repo",
        ):
            result = is_efs_install_ready("owner", "repo", "node")

    assert result is False


def test_is_efs_install_ready_uses_default_timeout():
    future = Future()
    future.set_result(True)

    with patch(
        "services.efs.is_efs_install_ready.install_futures",
        {"/mnt/efs/owner/repo": {"node": future}},
    ):
        with patch(
            "services.efs.is_efs_install_ready.get_efs_dir",
            return_value="/mnt/efs/owner/repo",
        ):
            result = is_efs_install_ready("owner", "repo")

    assert result is True
