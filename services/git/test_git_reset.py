from unittest.mock import patch, AsyncMock

import pytest

from services.git.git_reset import git_reset


@pytest.mark.asyncio
async def test_git_reset_success():
    with patch(
        "services.git.git_reset.run_subprocess_async", new_callable=AsyncMock
    ) as mock_run:
        mock_run.return_value = (0, "")
        result = await git_reset("/tmp/repo")

        assert result is True
        assert mock_run.call_count == 1


@pytest.mark.asyncio
async def test_git_reset_failure():
    with patch(
        "services.git.git_reset.run_subprocess_async", new_callable=AsyncMock
    ) as mock_run:
        mock_run.return_value = (1, "fatal: reset failed")
        result = await git_reset("/tmp/repo")

        assert result is False
        assert mock_run.call_count == 1
