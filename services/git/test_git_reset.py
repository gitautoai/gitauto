from unittest.mock import AsyncMock, patch

import pytest

from services.git.git_reset import git_reset


@pytest.mark.asyncio
async def test_git_reset_success():
    with patch(
        "services.git.git_reset.run_subprocess_async", new_callable=AsyncMock
    ) as mock_run, patch(
        "services.git.git_reset.resolve_git_locks", new_callable=AsyncMock
    ):
        mock_run.return_value = (0, "")
        result = await git_reset("/tmp/repo")

        assert result is True
        assert mock_run.call_count == 1


@pytest.mark.asyncio
async def test_git_reset_failure():
    with patch(
        "services.git.git_reset.run_subprocess_async", new_callable=AsyncMock
    ) as mock_run, patch(
        "services.git.git_reset.resolve_git_locks", new_callable=AsyncMock
    ):
        mock_run.return_value = (1, "fatal: reset failed")
        result = await git_reset("/tmp/repo")

        assert result is False
        assert mock_run.call_count == 1


@pytest.mark.asyncio
async def test_git_reset_calls_resolve_git_locks():
    with patch(
        "services.git.git_reset.run_subprocess_async", new_callable=AsyncMock
    ) as mock_run, patch(
        "services.git.git_reset.resolve_git_locks", new_callable=AsyncMock
    ) as mock_clear:
        mock_run.return_value = (0, "")
        await git_reset("/tmp/repo")

        mock_clear.assert_called_once_with("/tmp/repo/.git")
