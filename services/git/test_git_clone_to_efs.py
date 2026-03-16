# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import patch

import pytest

from services.git.git_clone_to_efs import git_clone_to_efs


@pytest.fixture
def mock_os_makedirs():
    with patch("services.git.git_clone_to_efs.os.makedirs") as mock:
        yield mock


@pytest.fixture
def mock_os_path_exists():
    with patch("services.git.git_clone_to_efs.os.path.exists") as mock:
        mock.return_value = False
        yield mock


@pytest.fixture
def mock_os_listdir():
    with patch("services.git.git_clone_to_efs.os.listdir") as mock:
        mock.return_value = []
        yield mock


def test_git_clone_to_efs_success(
    mock_os_makedirs, mock_os_path_exists, mock_os_listdir
):
    with patch("services.git.git_clone_to_efs.run_subprocess") as mock_run:
        result = git_clone_to_efs(
            "/mnt/efs/repo", "https://github.com/owner/repo.git", "main"
        )

        assert result == "/mnt/efs/repo"
        # safe.directory + init + remote add + fetch + checkout
        assert mock_run.call_count == 5
        calls = [call[0][0] for call in mock_run.call_args_list]
        assert calls[0] == [
            "git",
            "config",
            "--global",
            "--add",
            "safe.directory",
            "/mnt/efs/repo",
        ]


def test_git_clone_skips_when_git_dir_exists(mock_os_makedirs, mock_os_listdir):
    with patch("services.git.git_clone_to_efs.os.path.exists") as mock_exists, patch(
        "services.git.git_clone_to_efs.run_subprocess"
    ):
        mock_exists.return_value = True

        result = git_clone_to_efs(
            "/mnt/efs/repo", "https://github.com/owner/repo.git", "main"
        )

        assert result == "/mnt/efs/repo"


def test_git_clone_uses_init_fetch_when_dir_not_empty(
    mock_os_makedirs, mock_os_path_exists
):
    with patch("services.git.git_clone_to_efs.os.listdir") as mock_listdir:
        mock_listdir.return_value = ["node_modules", "package.json"]

        with patch("services.git.git_clone_to_efs.run_subprocess") as mock_run:
            result = git_clone_to_efs(
                "/mnt/efs/repo", "https://github.com/owner/repo.git", "main"
            )

            assert result == "/mnt/efs/repo"
            # safe.directory + init + remote add + fetch + checkout
            assert mock_run.call_count == 5


def test_git_clone_skips_reset_when_fetch_fails(mock_os_makedirs):
    """When .git exists but fetch fails, reset should NOT be called."""
    with patch("services.git.git_clone_to_efs.os.path.exists") as mock_exists:
        mock_exists.return_value = True

        with patch("services.git.git_clone_to_efs.run_subprocess") as mock_run:
            # safe.directory succeeds, get-url succeeds, set-url succeeds, fetch fails
            mock_run.side_effect = [None, None, None, ValueError("auth failed")]

            result = git_clone_to_efs(
                "/mnt/efs/repo", "https://github.com/owner/repo.git", "main"
            )

            assert result == "/mnt/efs/repo"
            # safe.directory + get-url + set-url + fetch (NOT reset)
            assert mock_run.call_count == 4
            calls = [call[0][0] for call in mock_run.call_args_list]
            assert calls[0] == [
                "git",
                "config",
                "--global",
                "--add",
                "safe.directory",
                "/mnt/efs/repo",
            ]
            assert calls[1] == ["git", "remote", "get-url", "origin"]
            assert calls[2] == [
                "git",
                "remote",
                "set-url",
                "origin",
                "https://github.com/owner/repo.git",
            ]
            assert calls[3] == ["git", "fetch", "--depth", "1", "origin", "main"]


def test_git_clone_updates_origin_url_before_fetch(mock_os_makedirs):
    """When .git exists with expired token, set-url updates origin with fresh token before fetch."""
    with patch("services.git.git_clone_to_efs.os.path.exists") as mock_exists:
        mock_exists.return_value = True

        with patch("services.git.git_clone_to_efs.run_subprocess") as mock_run:
            fresh_url = "https://x-access-token:fresh_token@github.com/owner/repo.git"
            # FETCH_HEAD exists, HEAD already on main → checkout -B skipped
            with patch(
                "services.git.git_clone_to_efs.read_local_file",
                side_effect=lambda f, _d: (
                    "abc123\tbranch 'main'"
                    if f == "FETCH_HEAD"
                    else "ref: refs/heads/main"
                ),
            ):
                result = git_clone_to_efs("/mnt/efs/repo", fresh_url, "main")

            assert result == "/mnt/efs/repo"
            # safe.directory + get-url + set-url + fetch + reset (no checkout -B, branch unchanged)
            assert mock_run.call_count == 5
            calls = [call[0][0] for call in mock_run.call_args_list]
            assert calls[0] == [
                "git",
                "config",
                "--global",
                "--add",
                "safe.directory",
                "/mnt/efs/repo",
            ]
            assert calls[1] == ["git", "remote", "get-url", "origin"]
            assert calls[2] == ["git", "remote", "set-url", "origin", fresh_url]
            assert calls[3] == ["git", "fetch", "--depth", "1", "origin", "main"]
            assert calls[4] == ["git", "reset", "--hard", "FETCH_HEAD"]


def test_git_clone_switches_branch_when_target_changes(mock_os_makedirs):
    """When target branch changed (e.g. master → release/20260408), checkout -B updates HEAD."""
    with patch("services.git.git_clone_to_efs.os.path.exists") as mock_exists:
        mock_exists.return_value = True

        with patch("services.git.git_clone_to_efs.run_subprocess") as mock_run:
            clone_url = "https://github.com/owner/repo.git"
            # HEAD on master, but fetching release/20260408 → checkout -B runs
            with patch(
                "services.git.git_clone_to_efs.read_local_file",
                side_effect=lambda f, _d: (
                    "abc123\tbranch 'release/20260408'"
                    if f == "FETCH_HEAD"
                    else "ref: refs/heads/master"
                ),
            ):
                result = git_clone_to_efs(
                    "/mnt/efs/repo", clone_url, "release/20260408"
                )

            assert result == "/mnt/efs/repo"
            # safe.directory + get-url + set-url + fetch + reset + checkout -B
            assert mock_run.call_count == 6
            calls = [call[0][0] for call in mock_run.call_args_list]
            assert calls[4] == ["git", "reset", "--hard", "FETCH_HEAD"]
            assert calls[5] == [
                "git",
                "checkout",
                "-B",
                "release/20260408",
                "FETCH_HEAD",
            ]


def test_git_clone_adds_origin_when_missing(mock_os_makedirs):
    """When .git exists but origin remote is missing, add origin instead of set-url."""
    with patch("services.git.git_clone_to_efs.os.path.exists") as mock_exists:
        mock_exists.return_value = True

        with patch("services.git.git_clone_to_efs.run_subprocess") as mock_run:
            # safe.directory succeeds, get-url fails (no origin), add succeeds, fetch succeeds, reset succeeds
            mock_run.side_effect = [
                None,
                ValueError("No such remote 'origin'"),
                None,
                None,
                None,
            ]

            clone_url = "https://github.com/owner/repo.git"
            # HEAD already on main → checkout -B skipped
            with patch(
                "services.git.git_clone_to_efs.read_local_file",
                side_effect=lambda f, _d: (
                    "abc123\tbranch 'main'"
                    if f == "FETCH_HEAD"
                    else "ref: refs/heads/main"
                ),
            ):
                result = git_clone_to_efs("/mnt/efs/repo", clone_url, "main")

            assert result == "/mnt/efs/repo"
            # safe.directory + get-url + add + fetch + reset (no checkout -B, branch unchanged)
            assert mock_run.call_count == 5
            calls = [call[0][0] for call in mock_run.call_args_list]
            assert calls[1] == ["git", "remote", "get-url", "origin"]
            assert calls[2] == ["git", "remote", "add", "origin", clone_url]
            assert calls[3] == ["git", "fetch", "--depth", "1", "origin", "main"]
            assert calls[4] == ["git", "reset", "--hard", "FETCH_HEAD"]
