from unittest.mock import patch, AsyncMock

import pytest

from utils.command.run_subprocess_async import run_subprocess_async


@pytest.mark.asyncio
async def test_run_subprocess_async_success():
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate.return_value = (b"output", b"")

    with patch(
        "asyncio.create_subprocess_exec", return_value=mock_process
    ) as mock_exec:
        await run_subprocess_async(["git", "status"], "/tmp/repo")

        mock_exec.assert_called_once()


@pytest.mark.asyncio
async def test_run_subprocess_async_failure_raises():
    mock_process = AsyncMock()
    mock_process.returncode = 1
    mock_process.communicate.return_value = (b"", b"error message")

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        with pytest.raises(RuntimeError, match="Command git failed"):
            await run_subprocess_async(["git", "status"], "/tmp/repo")
