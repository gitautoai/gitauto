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
    with patch(
        "services.git.git_clone_to_efs.run_subprocess_async", new_callable=AsyncMock
    ) as mock_run:
        mock_run.return_value = (0, "")
        result = await git_clone_to_efs(
            "/mnt/efs/repo", "https://github.com/owner/repo.git", "main"
        )

        assert result == "/mnt/efs/repo"
        # Always uses init + fetch + checkout (not git clone) to avoid race condition
        assert mock_run.call_count == 4


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

        with patch(
            "services.git.git_clone_to_efs.run_subprocess_async", new_callable=AsyncMock
        ) as mock_run:
            mock_run.return_value = (0, "")
            result = await git_clone_to_efs(
                "/mnt/efs/repo", "https://github.com/owner/repo.git", "main"
            )

            assert result == "/mnt/efs/repo"
            assert mock_run.call_count == 4
