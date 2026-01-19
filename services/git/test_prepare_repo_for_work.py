# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import patch, AsyncMock

import pytest

from services.git.prepare_repo_for_work import prepare_repo_for_work


@pytest.fixture
def mock_get_efs_dir():
    with patch("services.git.prepare_repo_for_work.get_efs_dir") as mock:
        mock.return_value = "/mnt/efs/owner/repo"
        yield mock


@pytest.fixture
def mock_get_clone_url():
    with patch("services.git.prepare_repo_for_work.get_clone_url") as mock:
        mock.return_value = "https://x-access-token:token@github.com/owner/repo.git"
        yield mock


@pytest.fixture
def mock_os_path_exists():
    with patch("services.git.prepare_repo_for_work.os.path.exists") as mock:
        yield mock


@pytest.fixture
def mock_git_fetch():
    with patch(
        "services.git.prepare_repo_for_work.git_fetch",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock:
        yield mock


@pytest.fixture
def mock_git_pull():
    with patch(
        "services.git.prepare_repo_for_work.git_pull",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock:
        yield mock


@pytest.fixture
def mock_git_clone_to_efs():
    with patch(
        "services.git.prepare_repo_for_work.git_clone_to_efs",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.fixture
def mock_git_checkout():
    with patch(
        "services.git.prepare_repo_for_work.git_checkout",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock:
        yield mock


@pytest.fixture
def mock_copy_repo():
    with patch("services.git.prepare_repo_for_work.copy_repo_from_efs_to_tmp") as mock:
        yield mock


@pytest.fixture
def mock_symlink():
    with patch("services.git.prepare_repo_for_work.symlink_dependencies") as mock:
        yield mock


@pytest.mark.asyncio
async def test_prepare_repo_efs_exists_fetches_and_pulls(
    mock_get_efs_dir,
    mock_get_clone_url,
    mock_os_path_exists,
    mock_git_fetch,
    mock_git_pull,
    mock_git_checkout,
    mock_copy_repo,
    mock_symlink,
):
    mock_os_path_exists.return_value = True

    await prepare_repo_for_work(
        owner="owner",
        repo="repo",
        base_branch="main",
        pr_branch="feature",
        token="token",
        clone_dir="/tmp/repo",
    )

    mock_git_fetch.assert_any_call(
        "/mnt/efs/owner/repo",
        "https://x-access-token:token@github.com/owner/repo.git",
        "main",
    )
    mock_git_pull.assert_any_call(
        "/mnt/efs/owner/repo",
        "https://x-access-token:token@github.com/owner/repo.git",
        "main",
    )
    mock_copy_repo.assert_called_once()
    mock_symlink.assert_called_once()


@pytest.mark.asyncio
async def test_prepare_repo_efs_not_exists_clones(
    mock_get_efs_dir,
    mock_get_clone_url,
    mock_os_path_exists,
    mock_git_clone_to_efs,
    mock_git_fetch,
    mock_git_pull,
    mock_git_checkout,
    mock_copy_repo,
    mock_symlink,
):
    mock_os_path_exists.return_value = False

    await prepare_repo_for_work(
        owner="owner",
        repo="repo",
        base_branch="main",
        pr_branch="feature",
        token="token",
        clone_dir="/tmp/repo",
    )

    mock_git_clone_to_efs.assert_called_once_with(
        "/mnt/efs/owner/repo",
        "https://x-access-token:token@github.com/owner/repo.git",
        "main",
    )


@pytest.mark.asyncio
async def test_prepare_repo_fetches_pr_branch(
    mock_get_efs_dir,
    mock_get_clone_url,
    mock_os_path_exists,
    mock_git_fetch,
    mock_git_pull,
    mock_git_checkout,
    mock_copy_repo,
    mock_symlink,
):
    mock_os_path_exists.return_value = True

    await prepare_repo_for_work(
        owner="owner",
        repo="repo",
        base_branch="main",
        pr_branch="feature",
        token="token",
        clone_dir="/tmp/repo",
    )

    mock_git_fetch.assert_any_call(
        "/tmp/repo",
        "https://x-access-token:token@github.com/owner/repo.git",
        "feature",
    )
    mock_git_checkout.assert_called_once_with("/tmp/repo", "feature")
    mock_git_pull.assert_any_call(
        "/tmp/repo",
        "https://x-access-token:token@github.com/owner/repo.git",
        "feature",
    )
