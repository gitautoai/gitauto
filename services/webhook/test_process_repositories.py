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
def mock_run_install_via_codebuild():
    with patch(
        "services.webhook.process_repositories.run_install_via_codebuild"
    ) as mock:
        yield mock


@pytest.fixture
def mock_detect_package_manager():
    with patch("services.webhook.process_repositories.detect_package_manager") as mock:
        mock.return_value = ("npm", "package-lock.json", "lock content")
        yield mock


@pytest.fixture
def mock_sync_files_from_github_to_coverage():
    with patch(
        "services.webhook.process_repositories.sync_files_from_github_to_coverage"
    ) as mock:
        yield mock


@pytest.fixture
def mock_generate_branch_name():
    with patch("services.webhook.process_repositories.generate_branch_name") as mock:
        mock.return_value = "gitauto/setup-20241224-120000-ABCD"
        yield mock


@pytest.fixture
def mock_get_latest_remote_commit_sha():
    with patch(
        "services.webhook.process_repositories.get_latest_remote_commit_sha"
    ) as mock:
        mock.return_value = "abc123sha"
        yield mock


@pytest.fixture
def mock_create_remote_branch():
    with patch("services.webhook.process_repositories.create_remote_branch") as mock:
        yield mock


@pytest.fixture
def mock_ensure_tsconfig_relaxed_for_tests():
    with patch(
        "services.webhook.process_repositories.ensure_tsconfig_relaxed_for_tests"
    ) as mock:
        mock.return_value = (None, None)
        yield mock


@pytest.fixture
def mock_get_file_tree():
    with patch("services.webhook.process_repositories.get_file_tree") as mock:
        mock.return_value = []
        yield mock


@pytest.fixture
def mock_delete_remote_branch():
    with patch("services.webhook.process_repositories.delete_remote_branch") as mock:
        yield mock


@pytest.fixture
def mock_create_pull_request():
    with patch("services.webhook.process_repositories.create_pull_request") as mock:
        mock.return_value = ("https://github.com/test/pr/1", 1)
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
    mock_run_install_via_codebuild,
    mock_detect_package_manager,
    mock_sync_files_from_github_to_coverage,
    mock_generate_branch_name,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_ensure_tsconfig_relaxed_for_tests,
    mock_get_file_tree,
    mock_delete_remote_branch,
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
    assert mock_run_install_via_codebuild.call_count == 2


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
    mock_run_install_via_codebuild,
    mock_detect_package_manager,
    mock_sync_files_from_github_to_coverage,
    mock_generate_branch_name,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_ensure_tsconfig_relaxed_for_tests,
    mock_get_file_tree,
    mock_delete_remote_branch,
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
    assert mock_run_install_via_codebuild.call_count == 2


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
    mock_run_install_via_codebuild,
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
    mock_run_install_via_codebuild.assert_not_called()


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
    mock_run_install_via_codebuild,
    mock_detect_package_manager,
    mock_sync_files_from_github_to_coverage,
    mock_generate_branch_name,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_ensure_tsconfig_relaxed_for_tests,
    mock_get_file_tree,
    mock_delete_remote_branch,
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
    mock_run_install_via_codebuild,
    mock_detect_package_manager,
    mock_sync_files_from_github_to_coverage,
    mock_generate_branch_name,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_ensure_tsconfig_relaxed_for_tests,
    mock_get_file_tree,
    mock_delete_remote_branch,
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
    mock_run_install_via_codebuild.assert_not_called()
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


@pytest.mark.asyncio
async def test_process_repositories_non_typescript_deletes_branch_no_pr(
    sample_stats,
    mock_get_efs_dir,
    mock_get_clone_url,
    mock_git_fetch,
    mock_git_reset,
    mock_os_path_exists,
    mock_get_default_branch,
    mock_get_repository_stats,
    mock_upsert_repository,
    mock_run_install_via_codebuild,
    mock_detect_package_manager,
    mock_sync_files_from_github_to_coverage,
    mock_generate_branch_name,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_ensure_tsconfig_relaxed_for_tests,
    mock_delete_remote_branch,
    mock_create_pull_request,
):
    mock_os_path_exists.return_value = True
    mock_get_repository_stats.return_value = sample_stats
    mock_ensure_tsconfig_relaxed_for_tests.return_value = (None, None)
    single_repo = cast(
        list[RepositoryAddedOrRemoved],
        [
            {
                "id": 555,
                "node_id": "R_5",
                "name": "python-repo",
                "full_name": "test-owner/python-repo",
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

    mock_create_remote_branch.assert_called_once()
    mock_delete_remote_branch.assert_called_once()
    mock_create_pull_request.assert_not_called()


@pytest.mark.asyncio
async def test_process_repositories_typescript_creates_pr(
    sample_stats,
    mock_get_efs_dir,
    mock_get_clone_url,
    mock_git_fetch,
    mock_git_reset,
    mock_os_path_exists,
    mock_get_default_branch,
    mock_get_repository_stats,
    mock_upsert_repository,
    mock_run_install_via_codebuild,
    mock_detect_package_manager,
    mock_sync_files_from_github_to_coverage,
    mock_generate_branch_name,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_ensure_tsconfig_relaxed_for_tests,
    mock_get_file_tree,
    mock_delete_remote_branch,
    mock_create_pull_request,
):
    mock_os_path_exists.return_value = True
    mock_get_repository_stats.return_value = sample_stats
    mock_ensure_tsconfig_relaxed_for_tests.return_value = (
        "tsconfig.test.json",
        "added",
    )
    single_repo = cast(
        list[RepositoryAddedOrRemoved],
        [
            {
                "id": 666,
                "node_id": "R_6",
                "name": "typescript-repo",
                "full_name": "test-owner/typescript-repo",
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

    mock_create_remote_branch.assert_called_once()
    mock_delete_remote_branch.assert_not_called()
    mock_create_pull_request.assert_called_once()
