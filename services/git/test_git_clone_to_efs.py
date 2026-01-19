from unittest.mock import patch, AsyncMock

import pytest

from services.git.git_clone_to_efs import git_clone_to_efs


@pytest.mark.asyncio
async def test_git_clone_to_efs_success():
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate.return_value = (b"", b"")

    with patch("os.makedirs"), patch(
        "asyncio.create_subprocess_exec", return_value=mock_process
    ) as mock_exec:
        result = await git_clone_to_efs(
            "/mnt/efs/repo", "https://github.com/owner/repo.git", "main"
        )

        assert result == "/mnt/efs/repo"
        mock_exec.assert_called_once_with(
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            "main",
            "https://github.com/owner/repo.git",
            "/mnt/efs/repo",
            stdout=-1,
            stderr=-1,
        )


@pytest.mark.asyncio
async def test_git_clone_to_efs_failure():
    mock_process = AsyncMock()
    mock_process.returncode = 1
    mock_process.communicate.return_value = (b"", b"fatal: could not clone")

    with patch("os.makedirs"), patch(
        "asyncio.create_subprocess_exec", return_value=mock_process
    ):
        result = await git_clone_to_efs(
            "/mnt/efs/repo", "https://github.com/owner/repo.git", "main"
        )

        assert result is None
