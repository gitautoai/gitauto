from unittest.mock import AsyncMock, patch

import pytest

from services.git.git_reset import git_reset


@pytest.mark.asyncio
async def test_git_reset_success():
    with patch(
        "services.git.git_reset.run_subprocess_async", new_callable=AsyncMock
    ) as mock_run, patch(
        "services.git.git_reset.os.path.exists", return_value=False
    ), patch(
        "services.git.git_reset.remove_stale_git_locks"
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
        "services.git.git_reset.os.path.exists", return_value=False
    ), patch(
        "services.git.git_reset.remove_stale_git_locks"
    ):
        mock_run.return_value = (1, "fatal: reset failed")
        result = await git_reset("/tmp/repo")

        assert result is False
        assert mock_run.call_count == 1


@pytest.mark.asyncio
async def test_git_reset_waits_for_fresh_lock_then_skips():
    """Fresh lock disappears after one poll — skip reset since other process did it."""
    exists_calls = [True, False]  # Lock exists, then gone

    with patch(
        "services.git.git_reset.run_subprocess_async", new_callable=AsyncMock
    ) as mock_run, patch(
        "services.git.git_reset.os.path.exists", side_effect=exists_calls
    ), patch(
        "services.git.git_reset.asyncio.sleep", new_callable=AsyncMock
    ), patch(
        "services.git.git_reset.remove_stale_git_locks"
    ):
        result = await git_reset("/tmp/repo")

        assert result is True
        mock_run.assert_not_called()


@pytest.mark.asyncio
async def test_git_reset_calls_remove_stale_git_locks():
    """Verify remove_stale_git_locks is called with the .git directory."""
    with patch(
        "services.git.git_reset.run_subprocess_async", new_callable=AsyncMock
    ) as mock_run, patch(
        "services.git.git_reset.os.path.exists", return_value=False
    ), patch(
        "services.git.git_reset.remove_stale_git_locks"
    ) as mock_remove:
        mock_run.return_value = (0, "")
        await git_reset("/tmp/repo")

        mock_remove.assert_called_once_with("/tmp/repo/.git")
