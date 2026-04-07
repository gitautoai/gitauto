# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import patch

import pytest

from services.github.types.repository import RepositoryAddedOrRemoved
from services.webhook.process_repositories import process_repositories

SINGLE = "services.webhook.setup_installed_repository"


@pytest.fixture
def mock_get_installation_access_token():
    with patch(f"{SINGLE}.get_installation_access_token") as mock:
        mock.return_value = "ghs_test_token"
        yield mock


@pytest.fixture
def mock_get_clone_url():
    with patch(f"{SINGLE}.get_clone_url") as mock:
        mock.return_value = (
            "https://x-access-token:token@github.com/test-owner/test-repo.git"
        )
        yield mock


@pytest.fixture
def mock_get_clone_dir():
    with patch(f"{SINGLE}.get_clone_dir") as mock:
        mock.return_value = "/tmp/test-owner/test-repo"
        yield mock


@pytest.fixture
def mock_git_clone_to_tmp():
    with patch(f"{SINGLE}.git_clone_to_tmp") as mock:
        yield mock


@pytest.fixture
def mock_ensure_node_packages():
    with patch(f"{SINGLE}.ensure_node_packages") as mock:
        yield mock


@pytest.fixture
def mock_ensure_php_packages():
    with patch(f"{SINGLE}.ensure_php_packages") as mock:
        yield mock


@pytest.fixture
def mock_is_repo_archived():
    with patch(f"{SINGLE}.is_repo_archived", return_value=False) as mock:
        yield mock


@pytest.fixture
def mock_get_default_branch():
    with patch(f"{SINGLE}.get_default_branch") as mock:
        mock.return_value = "main"
        yield mock


@pytest.fixture
def mock_get_repository_stats():
    with patch(f"{SINGLE}.get_repository_stats") as mock:
        yield mock


@pytest.fixture
def mock_upsert_repository():
    with patch(f"{SINGLE}.upsert_repository") as mock:
        yield mock


@pytest.fixture
def mock_sync_files_from_github_to_coverage():
    with patch(f"{SINGLE}.sync_files_from_github_to_coverage") as mock:
        yield mock


@pytest.fixture
def mock_generate_branch_name():
    with patch(f"{SINGLE}.generate_branch_name") as mock:
        mock.return_value = "gitauto/setup-20241224-120000-ABCD"
        yield mock


@pytest.fixture
def mock_get_latest_remote_commit_sha():
    with patch(f"{SINGLE}.get_latest_remote_commit_sha") as mock:
        mock.return_value = "abc123sha"
        yield mock


@pytest.fixture
def mock_create_remote_branch():
    with patch(f"{SINGLE}.create_remote_branch") as mock:
        yield mock


@pytest.fixture
def mock_ensure_tsconfig_relaxed_for_tests():
    with patch(f"{SINGLE}.ensure_tsconfig_relaxed_for_tests") as mock:
        mock.return_value = (None, None)
        yield mock


@pytest.fixture
def mock_os_listdir():
    with patch(f"{SINGLE}.os.listdir") as mock:
        mock.return_value = []
        yield mock


@pytest.fixture
def mock_os_path_isfile():
    with patch(f"{SINGLE}.os.path.isfile") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_is_repo_forked():
    with patch(f"{SINGLE}.is_repo_forked", return_value=False) as mock:
        yield mock


@pytest.fixture
def mock_delete_remote_branch():
    with patch(f"{SINGLE}.delete_remote_branch") as mock:
        yield mock


@pytest.fixture
def mock_create_pull_request():
    with patch(f"{SINGLE}.create_pull_request") as mock:
        mock.return_value = ("https://github.com/test/pr/1", 1)
        yield mock


@pytest.fixture
def mock_has_open_pull_request_by_title():
    with patch(f"{SINGLE}.has_open_pull_request_by_title") as mock:
        mock.return_value = False
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
        "code_lines": 500,
    }


def test_process_repositories_clones_and_installs(
    sample_repositories,
    sample_stats,
    mock_get_installation_access_token,
    mock_get_clone_url,
    mock_get_clone_dir,
    mock_git_clone_to_tmp,
    mock_ensure_node_packages,
    mock_ensure_php_packages,
    mock_is_repo_archived,
    mock_get_default_branch,
    mock_get_repository_stats,
    mock_upsert_repository,
    mock_sync_files_from_github_to_coverage,
    mock_generate_branch_name,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_is_repo_forked,
    mock_ensure_tsconfig_relaxed_for_tests,
    mock_os_listdir,
    mock_os_path_isfile,
    mock_delete_remote_branch,
    mock_has_open_pull_request_by_title,
):
    mock_get_repository_stats.return_value = sample_stats
    mock_get_default_branch.side_effect = ["main", "master"]

    process_repositories(
        owner_id=12345,
        owner_name="test-owner",
        owner_type="Organization",
        repositories=sample_repositories,
        user_id=67890,
        user_name="test-user",
        installation_id=99999,
        sender_email="test@example.com",
        sender_display_name="Test User",
    )

    assert mock_get_default_branch.call_count == 2
    assert mock_git_clone_to_tmp.call_count == 2
    assert mock_ensure_node_packages.call_count == 2
    assert mock_get_repository_stats.call_count == 2
    # 2 repos x 2 calls each (insert without stats + update with stats)
    assert mock_upsert_repository.call_count == 4


def test_process_repositories_empty_list(
    mock_get_installation_access_token,
    mock_get_clone_url,
    mock_get_clone_dir,
    mock_git_clone_to_tmp,
    mock_ensure_node_packages,
    mock_ensure_php_packages,
    mock_is_repo_archived,
    mock_get_default_branch,
    mock_get_repository_stats,
    mock_upsert_repository,
):
    process_repositories(
        owner_id=12345,
        owner_name="test-owner",
        owner_type="Organization",
        repositories=[],
        user_id=67890,
        user_name="test-user",
        installation_id=99999,
        sender_email="test@example.com",
        sender_display_name="Test User",
    )

    mock_get_default_branch.assert_not_called()
    mock_git_clone_to_tmp.assert_not_called()
    mock_ensure_node_packages.assert_not_called()
    mock_get_repository_stats.assert_not_called()
    mock_upsert_repository.assert_not_called()


def test_process_repositories_stats_saved_correctly(
    sample_stats,
    mock_get_installation_access_token,
    mock_get_clone_url,
    mock_get_clone_dir,
    mock_git_clone_to_tmp,
    mock_ensure_node_packages,
    mock_ensure_php_packages,
    mock_is_repo_archived,
    mock_get_default_branch,
    mock_get_repository_stats,
    mock_upsert_repository,
    mock_sync_files_from_github_to_coverage,
    mock_generate_branch_name,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_is_repo_forked,
    mock_ensure_tsconfig_relaxed_for_tests,
    mock_os_listdir,
    mock_os_path_isfile,
    mock_delete_remote_branch,
    mock_has_open_pull_request_by_title,
):
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

    process_repositories(
        owner_id=12345,
        owner_name="test-owner",
        owner_type="Organization",
        repositories=single_repo,
        user_id=67890,
        user_name="test-user",
        installation_id=99999,
        sender_email="test@example.com",
        sender_display_name="Test User",
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
        code_lines=500,
    )


def test_process_repositories_empty_repo_skips_clone(
    mock_get_installation_access_token,
    mock_get_clone_url,
    mock_get_clone_dir,
    mock_git_clone_to_tmp,
    mock_ensure_node_packages,
    mock_ensure_php_packages,
    mock_is_repo_archived,
    mock_get_default_branch,
    mock_get_repository_stats,
    mock_upsert_repository,
    mock_sync_files_from_github_to_coverage,
    mock_generate_branch_name,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_is_repo_forked,
    mock_ensure_tsconfig_relaxed_for_tests,
    mock_os_listdir,
    mock_os_path_isfile,
    mock_delete_remote_branch,
    mock_has_open_pull_request_by_title,
):
    mock_get_default_branch.return_value = None
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

    process_repositories(
        owner_id=12345,
        owner_name="test-owner",
        owner_type="Organization",
        repositories=single_repo,
        user_id=67890,
        user_name="test-user",
        installation_id=99999,
        sender_email="test@example.com",
        sender_display_name="Test User",
    )

    mock_get_default_branch.assert_called_once()
    mock_git_clone_to_tmp.assert_not_called()
    mock_ensure_node_packages.assert_not_called()
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


def test_process_repositories_non_typescript_deletes_branch_no_pr(
    sample_stats,
    mock_get_installation_access_token,
    mock_get_clone_url,
    mock_get_clone_dir,
    mock_git_clone_to_tmp,
    mock_ensure_node_packages,
    mock_ensure_php_packages,
    mock_is_repo_archived,
    mock_get_default_branch,
    mock_get_repository_stats,
    mock_upsert_repository,
    mock_sync_files_from_github_to_coverage,
    mock_generate_branch_name,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_is_repo_forked,
    mock_ensure_tsconfig_relaxed_for_tests,
    mock_os_listdir,
    mock_os_path_isfile,
    mock_delete_remote_branch,
    mock_create_pull_request,
    mock_has_open_pull_request_by_title,
):
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

    process_repositories(
        owner_id=12345,
        owner_name="test-owner",
        owner_type="Organization",
        repositories=single_repo,
        user_id=67890,
        user_name="test-user",
        installation_id=99999,
        sender_email="test@example.com",
        sender_display_name="Test User",
    )

    mock_create_remote_branch.assert_called_once()
    mock_delete_remote_branch.assert_called_once()
    mock_create_pull_request.assert_not_called()


def test_process_repositories_typescript_creates_pr(
    sample_stats,
    mock_get_installation_access_token,
    mock_get_clone_url,
    mock_get_clone_dir,
    mock_git_clone_to_tmp,
    mock_ensure_node_packages,
    mock_ensure_php_packages,
    mock_is_repo_archived,
    mock_get_default_branch,
    mock_get_repository_stats,
    mock_upsert_repository,
    mock_sync_files_from_github_to_coverage,
    mock_generate_branch_name,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_is_repo_forked,
    mock_ensure_tsconfig_relaxed_for_tests,
    mock_os_listdir,
    mock_os_path_isfile,
    mock_delete_remote_branch,
    mock_create_pull_request,
    mock_has_open_pull_request_by_title,
):
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

    process_repositories(
        owner_id=12345,
        owner_name="test-owner",
        owner_type="Organization",
        repositories=single_repo,
        user_id=67890,
        user_name="test-user",
        installation_id=99999,
        sender_email="test@example.com",
        sender_display_name="Test User",
    )

    mock_create_remote_branch.assert_called_once()
    mock_delete_remote_branch.assert_not_called()
    mock_create_pull_request.assert_called_once()
