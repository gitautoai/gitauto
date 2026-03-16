from unittest.mock import patch

from services.git.git_fetch import git_fetch


def test_git_fetch_success():
    with (
        patch("services.git.git_fetch.run_subprocess") as mock_run,
        patch("services.git.git_fetch.resolve_git_locks"),
        patch("services.git.git_fetch.os.path.join", return_value="/mnt/efs/repo/.git"),
    ):
        result = git_fetch("/mnt/efs/repo", "https://github.com/owner/repo.git", "main")

        assert result is True
        mock_run.assert_called_once_with(
            [
                "git",
                "fetch",
                "--depth",
                "1",
                "https://github.com/owner/repo.git",
                "main",
            ],
            "/mnt/efs/repo",
        )


def test_git_fetch_resolves_locks_before_fetch():
    with (
        patch("services.git.git_fetch.run_subprocess"),
        patch("services.git.git_fetch.resolve_git_locks") as mock_resolve,
    ):
        result = git_fetch("/mnt/efs/repo", "https://github.com/owner/repo.git", "main")

        assert result is True
        mock_resolve.assert_called_once_with("/mnt/efs/repo/.git")
