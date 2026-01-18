# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import patch, AsyncMock

import pytest

from services.github.types.repository import RepositoryAddedOrRemoved
from services.webhook.process_repositories import process_repositories


@pytest.fixture
def mock_clone_repo():
    with patch(
        "services.webhook.process_repositories.clone_repo",
        new_callable=AsyncMock,
        return_value="/tmp/test-owner/test-repo",
    ) as mock:
        yield mock


@pytest.fixture
def mock_get_default_branch():
    with patch("services.webhook.process_repositories.get_default_branch") as mock:
        mock.return_value = ("main", "abc123")
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
def mock_shutil():
    with patch("services.webhook.process_repositories.shutil.rmtree") as mock:
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


class TestProcessRepositories:

    @pytest.mark.asyncio
    async def test_process_repositories_success(
        self,
        sample_repositories,
        sample_stats,
        mock_clone_repo,
        mock_get_default_branch,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_shutil,
    ):
        mock_get_repository_stats.return_value = sample_stats
        mock_get_default_branch.side_effect = [("main", "sha1"), ("master", "sha2")]
        mock_clone_repo.side_effect = [
            "/tmp/test-owner/test-repo-1",
            "/tmp/test-owner/test-repo-2",
        ]

        coro = process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=sample_repositories,
            token="ghs_test_token",
            user_id=67890,
            user_name="test-user",
        )
        assert coro is not None
        await coro

        assert mock_get_default_branch.call_count == 2
        assert mock_clone_repo.call_count == 2
        mock_clone_repo.assert_any_call(
            owner="test-owner",
            repo="test-repo-1",
            pr_number=None,
            branch="main",
            token="ghs_test_token",
        )
        mock_clone_repo.assert_any_call(
            owner="test-owner",
            repo="test-repo-2",
            pr_number=None,
            branch="master",
            token="ghs_test_token",
        )

        assert mock_get_repository_stats.call_count == 2
        assert mock_upsert_repository.call_count == 2
        assert mock_shutil.call_count == 2

    @pytest.mark.asyncio
    async def test_process_repositories_empty_list(
        self,
        mock_clone_repo,
        mock_get_default_branch,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_shutil,
    ):
        coro = process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=[],
            token="ghs_test_token",
            user_id=67890,
            user_name="test-user",
        )
        assert coro is not None
        await coro

        mock_get_default_branch.assert_not_called()
        mock_clone_repo.assert_not_called()
        mock_get_repository_stats.assert_not_called()
        mock_upsert_repository.assert_not_called()
        mock_shutil.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_repositories_clone_failure(
        self,
        sample_repositories,
        mock_clone_repo,
        mock_get_default_branch,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_shutil,
    ):
        mock_clone_repo.side_effect = Exception("Clone failed")

        coro = process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=sample_repositories,
            token="ghs_test_token",
            user_id=67890,
            user_name="test-user",
        )
        assert coro is not None
        with pytest.raises(Exception, match="Clone failed"):
            await coro

        assert mock_get_default_branch.call_count == 1
        assert mock_clone_repo.call_count == 1
        mock_get_repository_stats.assert_not_called()
        mock_upsert_repository.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_repositories_stats_failure(
        self,
        sample_repositories,
        mock_clone_repo,
        mock_get_default_branch,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_shutil,
    ):
        mock_clone_repo.return_value = "/tmp/test-owner/test-repo-1"
        mock_get_repository_stats.side_effect = Exception("Stats failed")

        coro = process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=sample_repositories,
            token="ghs_test_token",
            user_id=67890,
            user_name="test-user",
        )
        assert coro is not None
        with pytest.raises(Exception, match="Stats failed"):
            await coro

        assert mock_get_default_branch.call_count == 1
        assert mock_clone_repo.call_count == 1
        assert mock_get_repository_stats.call_count == 1
        mock_upsert_repository.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_repositories_cleanup_on_success(
        self,
        sample_stats,
        mock_clone_repo,
        mock_get_default_branch,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_shutil,
    ):
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
        mock_clone_repo.return_value = "/tmp/test-owner/single-repo"
        mock_get_repository_stats.return_value = sample_stats

        coro = process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=single_repo,
            token="ghs_test_token",
            user_id=67890,
            user_name="test-user",
        )
        assert coro is not None
        await coro

        mock_shutil.assert_called_once_with(
            "/tmp/test-owner/single-repo", ignore_errors=True
        )

    @pytest.mark.asyncio
    async def test_process_repositories_with_zero_stats(
        self,
        sample_repositories,
        mock_clone_repo,
        mock_get_default_branch,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_shutil,
    ):
        zero_stats = {
            "file_count": 0,
            "blank_lines": 0,
            "comment_lines": 0,
            "code_lines": 0,
        }
        mock_clone_repo.return_value = "/tmp/test-owner/test-repo"
        mock_get_repository_stats.return_value = zero_stats

        coro = process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=sample_repositories,
            token="ghs_test_token",
            user_id=67890,
            user_name="test-user",
        )
        assert coro is not None
        await coro

        mock_upsert_repository.assert_any_call(
            owner_id=12345,
            owner_name="test-owner",
            repo_id=111,
            repo_name="test-repo-1",
            user_id=67890,
            user_name="test-user",
            file_count=0,
            blank_lines=0,
            comment_lines=0,
            code_lines=0,
        )

    @pytest.mark.asyncio
    async def test_process_repositories_cleanup_when_clone_returns_none(
        self,
        sample_repositories,
        mock_clone_repo,
        mock_get_default_branch,
        mock_get_repository_stats,
        mock_upsert_repository,
        mock_shutil,
    ):
        mock_clone_repo.return_value = None

        coro = process_repositories(
            owner_id=12345,
            owner_name="test-owner",
            repositories=sample_repositories,
            token="ghs_test_token",
            user_id=67890,
            user_name="test-user",
        )
        assert coro is not None
        await coro

        mock_shutil.assert_not_called()
