from unittest.mock import patch, AsyncMock

import pytest

from services.git.git_fetch import git_fetch


@pytest.mark.asyncio
async def test_git_fetch_success():
    with (
        patch(
            "services.git.git_fetch.run_subprocess_async", new_callable=AsyncMock
        ) as mock_run,
        patch("services.git.git_fetch.resolve_git_locks", new_callable=AsyncMock),
        patch("services.git.git_fetch.os.path.join", return_value="/mnt/efs/repo/.git"),
    ):
        mock_run.return_value = (0, "")
        result = await git_fetch(
            "/mnt/efs/repo", "https://github.com/owner/repo.git", "main"
        )

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


@pytest.mark.asyncio
async def test_git_fetch_failure():
    with (
        patch(
            "services.git.git_fetch.run_subprocess_async", new_callable=AsyncMock
        ) as mock_run,
        patch("services.git.git_fetch.resolve_git_locks", new_callable=AsyncMock),
        patch("services.git.git_fetch.os.path.join", return_value="/mnt/efs/repo/.git"),
    ):
        mock_run.return_value = (1, "fatal: could not fetch")
        result = await git_fetch(
            "/mnt/efs/repo", "https://github.com/owner/repo.git", "main"
        )

        assert result is False


@pytest.mark.asyncio
async def test_git_fetch_resolves_locks_before_fetch():
    with (
        patch(
            "services.git.git_fetch.run_subprocess_async", new_callable=AsyncMock
        ) as mock_run,
        patch(
            "services.git.git_fetch.resolve_git_locks", new_callable=AsyncMock
        ) as mock_resolve,
    ):
        mock_run.return_value = (0, "")
        result = await git_fetch(
            "/mnt/efs/repo", "https://github.com/owner/repo.git", "main"
        )

        assert result is True
        mock_resolve.assert_called_once_with("/mnt/efs/repo/.git")
