# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import patch, AsyncMock

import pytest

from services.github.types.repository import RepositoryAddedOrRemoved
from services.webhook.process_repositories import process_repositories


@pytest.fixture
def mock_get_efs_dir():
    with patch("services.webhook.process_repositories.get_efs_dir") as mock:
        mock.return_value = "/mnt/efs/test-owner/test-repo"
        yield mock


@pytest.fixture
def mock_get_clone_url():
    with patch("services.webhook.process_repositories.get_clone_url") as mock:
        mock.return_value = (
            "https://x-access-token:token@github.com/test-owner/test-repo.git"
        )
        yield mock


@pytest.fixture
def mock_git_clone_to_efs():
    with patch(
        "services.webhook.process_repositories.git_clone_to_efs",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.fixture
def mock_git_fetch():
    with patch(
        "services.webhook.process_repositories.git_fetch",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock:
        yield mock


@pytest.fixture
def mock_git_reset():
    with patch(
        "services.webhook.process_repositories.git_reset",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock:
        yield mock


@pytest.fixture
def mock_os_path_exists():
    with patch("services.webhook.process_repositories.os.path.exists") as mock:
        yield mock


@pytest.fixture
def mock_get_default_branch():
    with patch("services.webhook.process_repositories.get_default_branch") as mock:
        mock.return_value = ("main", False)
        yield mock


@pytest.fixture
def mock_get_repository_stats():
    with patch("services.webhook.process_repositories.get_repository_stats") as mock:
        yield mock


@pytest.fixture
def mock_upsert_repository():
    with patch("services.webhook.process_repositories.upsert_repository") as mock:
        yield mock


@pytest.fixture
def sample_repositories():
    return [
        {
            "id": 111,
            "node_id": "R_1",
            "name": "test-repo-1",
            "full_name": "test-owner/test-repo-1",
            "private": False,
        },
        {
            "id": 222,
            "node_id": "R_2",
            "name": "test-repo-2",
            "full_name": "test-owner/test-repo-2",
            "private": True,
        },
    ]


@pytest.fixture
def sample_stats():
    return {
        "file_count": 25,
        "blank_lines": 150,
        "comment_lines": 75,
        "code_lines": 500,
    }


@pytest.mark.asyncio
async def test_process_repositories_efs_exists_fetches(
    sample_repositories,
    sample_stats,
    mock_get_efs_dir,
    mock_get_clone_url,
    mock_git_fetch,
    mock_git_reset,
    mock_os_path_exists,
    mock_get_default_branch,
    mock_get_repository_stats,
    mock_upsert_repository,
):
    mock_os_path_exists.return_value = True
    mock_get_repository_stats.return_value = sample_stats
    mock_get_default_branch.side_effect = [("main", False), ("master", False)]

    await process_repositories(
        owner_id=12345,
        owner_name="test-owner",
        owner_type="Organization",
        repositories=sample_repositories,
        token="ghs_test_token",
        user_id=67890,
        user_name="test-user",
    )

    assert mock_get_default_branch.call_count == 2
    assert mock_git_fetch.call_count == 2
    assert mock_git_reset.call_count == 2
    assert mock_get_repository_stats.call_count == 2
    assert mock_upsert_repository.call_count == 4  # 2 repos x 2 calls (insert + update)


@pytest.mark.asyncio
async def test_process_repositories_efs_not_exists_clones(
    sample_repositories,
    sample_stats,
    mock_get_efs_dir,
    mock_get_clone_url,
    mock_git_clone_to_efs,
    mock_os_path_exists,
    mock_get_default_branch,
    mock_get_repository_stats,
    mock_upsert_repository,
):
    mock_os_path_exists.return_value = False
    mock_get_repository_stats.return_value = sample_stats

    await process_repositories(
        owner_id=12345,
        owner_name="test-owner",
        owner_type="Organization",
        repositories=sample_repositories,
        token="ghs_test_token",
        user_id=67890,
        user_name="test-user",
    )

    assert mock_git_clone_to_efs.call_count == 2
    assert mock_upsert_repository.call_count == 4  # 2 repos x 2 calls (insert + update)


@pytest.mark.asyncio
async def test_process_repositories_empty_list(
    mock_get_efs_dir,
    mock_get_clone_url,
    mock_git_fetch,
    mock_git_reset,
    mock_os_path_exists,
    mock_get_default_branch,
    mock_get_repository_stats,
    mock_upsert_repository,
):
    await process_repositories(
        owner_id=12345,
        owner_name="test-owner",
        owner_type="Organization",
        repositories=[],
        token="ghs_test_token",
        user_id=67890,
        user_name="test-user",
    )

    mock_get_default_branch.assert_not_called()
    mock_git_fetch.assert_not_called()
    mock_git_reset.assert_not_called()
    mock_get_repository_stats.assert_not_called()
    mock_upsert_repository.assert_not_called()


@pytest.mark.asyncio
async def test_process_repositories_stats_saved_correctly(
    sample_stats,
    mock_get_efs_dir,
    mock_get_clone_url,
    mock_git_fetch,
    mock_git_reset,
    mock_os_path_exists,
    mock_get_default_branch,
    mock_get_repository_stats,
    mock_upsert_repository,
):
    mock_os_path_exists.return_value = True
    mock_get_repository_stats.return_value = sample_stats
    single_repo = cast(
        list[RepositoryAddedOrRemoved],
        [
            {
                "id": 333,
                "node_id": "R_3",
                "name": "single-repo",
                "full_name": "test-owner/single-repo",
                "private": False,
            }
        ],
    )

    await process_repositories(
        owner_id=12345,
        owner_name="test-owner",
        owner_type="Organization",
        repositories=single_repo,
        token="ghs_test_token",
        user_id=67890,
        user_name="test-user",
    )

    assert mock_upsert_repository.call_count == 2
    # Second call should have stats
    mock_upsert_repository.assert_called_with(
        owner_id=12345,
        owner_name="test-owner",
        owner_type="Organization",
        repo_id=333,
        repo_name="single-repo",
        user_id=67890,
        user_name="test-user",
        file_count=25,
        blank_lines=150,
        comment_lines=75,
        code_lines=500,
    )


@pytest.mark.asyncio
async def test_process_repositories_empty_repo_skips_clone(
    mock_get_efs_dir,
    mock_get_clone_url,
    mock_git_clone_to_efs,
    mock_git_fetch,
    mock_git_reset,
    mock_os_path_exists,
    mock_get_default_branch,
    mock_get_repository_stats,
    mock_upsert_repository,
):
    mock_get_default_branch.return_value = ("main", True)
    single_repo = cast(
        list[RepositoryAddedOrRemoved],
        [
            {
                "id": 444,
                "node_id": "R_4",
                "name": "empty-repo",
                "full_name": "test-owner/empty-repo",
                "private": False,
            }
        ],
    )

    await process_repositories(
        owner_id=12345,
        owner_name="test-owner",
        owner_type="Organization",
        repositories=single_repo,
        token="ghs_test_token",
        user_id=67890,
        user_name="test-user",
    )

    mock_get_default_branch.assert_called_once()
    mock_git_clone_to_efs.assert_not_called()
    mock_git_fetch.assert_not_called()
    mock_git_reset.assert_not_called()
    mock_get_repository_stats.assert_not_called()
    # Only called once without stats (empty repo skips clone)
    mock_upsert_repository.assert_called_once_with(
        owner_id=12345,
        owner_name="test-owner",
        owner_type="Organization",
        repo_id=444,
        repo_name="empty-repo",
        user_id=67890,
        user_name="test-user",
    )
