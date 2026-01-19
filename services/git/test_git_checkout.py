from unittest.mock import patch, AsyncMock

import pytest

from services.git.git_checkout import git_checkout


@pytest.mark.asyncio
async def test_git_checkout_success():
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate.return_value = (b"", b"")

    with patch(
        "asyncio.create_subprocess_exec", return_value=mock_process
    ) as mock_exec:
        result = await git_checkout("/tmp/repo", "feature-branch")

        assert result is True
        mock_exec.assert_called_once_with(
            "git",
            "-C",
            "/tmp/repo",
            "checkout",
            "-f",
            "-B",
            "feature-branch",
            "FETCH_HEAD",
            stdout=-1,
            stderr=-1,
        )


@pytest.mark.asyncio
async def test_git_checkout_failure():
    mock_process = AsyncMock()
    mock_process.returncode = 1
    mock_process.communicate.return_value = (
        b"",
        b"error: pathspec 'branch' did not match",
    )

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        result = await git_checkout("/tmp/repo", "nonexistent-branch")

        assert result is False
