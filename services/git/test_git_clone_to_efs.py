# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import patch, AsyncMock

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


@pytest.mark.asyncio
async def test_git_clone_to_efs_success(
    mock_os_makedirs, mock_os_path_exists, mock_os_listdir
):
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate.return_value = (b"", b"")

    with patch(
        "asyncio.create_subprocess_exec", return_value=mock_process
    ) as mock_exec:
        result = await git_clone_to_efs(
            "/mnt/efs/repo", "https://github.com/owner/repo.git", "main"
        )

        assert result == "/mnt/efs/repo"
        # Always uses init + fetch + checkout (not git clone) to avoid race condition
        assert mock_exec.call_count == 4
        calls = mock_exec.call_args_list
        assert calls[0][0] == ("git", "init")
        assert calls[1][0] == (
            "git",
            "remote",
            "add",
            "origin",
            "https://github.com/owner/repo.git",
        )
        assert calls[2][0] == ("git", "fetch", "--depth", "1", "origin", "main")
        assert calls[3][0] == ("git", "checkout", "-f", "main")


@pytest.mark.asyncio
async def test_git_clone_to_efs_failure(
    mock_os_makedirs, mock_os_path_exists, mock_os_listdir
):
    mock_process = AsyncMock()
    mock_process.returncode = 1
    mock_process.communicate.return_value = (b"", b"fatal: could not clone")

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        result = await git_clone_to_efs(
            "/mnt/efs/repo", "https://github.com/owner/repo.git", "main"
        )

        assert result is None


@pytest.mark.asyncio
async def test_git_clone_skips_when_git_dir_exists(mock_os_makedirs, mock_os_listdir):
    with patch("services.git.git_clone_to_efs.os.path.exists") as mock_exists:
        mock_exists.return_value = True

        result = await git_clone_to_efs(
            "/mnt/efs/repo", "https://github.com/owner/repo.git", "main"
        )

        assert result == "/mnt/efs/repo"


@pytest.mark.asyncio
async def test_git_clone_uses_init_fetch_when_dir_not_empty(
    mock_os_makedirs, mock_os_path_exists
):
    with patch("services.git.git_clone_to_efs.os.listdir") as mock_listdir:
        mock_listdir.return_value = ["node_modules", "package.json"]

        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"", b"")

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ) as mock_exec:
            result = await git_clone_to_efs(
                "/mnt/efs/repo", "https://github.com/owner/repo.git", "main"
            )

            assert result == "/mnt/efs/repo"
            assert mock_exec.call_count == 4

            calls = mock_exec.call_args_list
            assert calls[0][0] == ("git", "init")
            assert calls[1][0] == (
                "git",
                "remote",
                "add",
                "origin",
                "https://github.com/owner/repo.git",
            )
            assert calls[2][0] == ("git", "fetch", "--depth", "1", "origin", "main")
            assert calls[3][0] == ("git", "checkout", "-f", "main")


@pytest.mark.asyncio
async def test_git_clone_init_fetch_failure_returns_none(
    mock_os_makedirs, mock_os_path_exists
):
    with patch("services.git.git_clone_to_efs.os.listdir") as mock_listdir:
        mock_listdir.return_value = ["node_modules"]

        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b"", b"fatal: error")

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await git_clone_to_efs(
                "/mnt/efs/repo", "https://github.com/owner/repo.git", "main"
            )

            assert result is None
