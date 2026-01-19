from unittest.mock import patch, AsyncMock

import pytest

from services.git.git_fetch_to_efs import git_fetch


@pytest.mark.asyncio
async def test_git_fetch_success():
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate.return_value = (b"", b"")

    with patch(
        "asyncio.create_subprocess_exec", return_value=mock_process
    ) as mock_exec:
        result = await git_fetch(
            "/mnt/efs/repo", "https://github.com/owner/repo.git", "main"
        )

        assert result is True
        mock_exec.assert_called_once_with(
            "git",
            "-C",
            "/mnt/efs/repo",
            "fetch",
            "--depth",
            "1",
            "https://github.com/owner/repo.git",
            "main",
            stdout=-1,
            stderr=-1,
        )


@pytest.mark.asyncio
async def test_git_fetch_failure():
    mock_process = AsyncMock()
    mock_process.returncode = 1
    mock_process.communicate.return_value = (b"", b"fatal: could not fetch")

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        result = await git_fetch(
            "/mnt/efs/repo", "https://github.com/owner/repo.git", "main"
        )

        assert result is False
