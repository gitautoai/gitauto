# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import patch

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
def mock_git_fetch():
    with patch(
        "services.git.prepare_repo_for_work.git_fetch",
        return_value=True,
    ) as mock:
        yield mock


@pytest.fixture
def mock_git_reset():
    with patch(
        "services.git.prepare_repo_for_work.git_reset",
        return_value=True,
    ) as mock:
        yield mock


@pytest.fixture
def mock_git_checkout():
    with patch(
        "services.git.prepare_repo_for_work.git_checkout",
        return_value=True,
    ) as mock:
        yield mock


@pytest.fixture
def mock_copy_repo():
    with patch("services.git.prepare_repo_for_work.copy_repo_from_efs_to_tmp") as mock:
        yield mock


@pytest.fixture
def mock_extract():
    with patch("services.git.prepare_repo_for_work.extract_dependencies") as mock:
        yield mock


def test_prepare_repo_copies_and_extracts(
    mock_get_efs_dir,
    mock_get_clone_url,
    mock_git_fetch,
    mock_git_reset,
    mock_git_checkout,
    mock_copy_repo,
    mock_extract,
):
    prepare_repo_for_work(
        owner="owner",
        repo="repo",
        pr_branch="feature",
        token="token",
        clone_dir="/tmp/repo",
    )

    mock_copy_repo.assert_called_once_with("/mnt/efs/owner/repo", "/tmp/repo")
    mock_extract.assert_called_once_with("/mnt/efs/owner/repo", "/tmp/repo")


def test_prepare_repo_fetches_pr_branch(
    mock_get_efs_dir,
    mock_get_clone_url,
    mock_git_fetch,
    mock_git_reset,
    mock_git_checkout,
    mock_copy_repo,
    mock_extract,
):
    prepare_repo_for_work(
        owner="owner",
        repo="repo",
        pr_branch="feature",
        token="token",
        clone_dir="/tmp/repo",
    )

    mock_git_fetch.assert_called_once_with(
        "/tmp/repo",
        "https://x-access-token:token@github.com/owner/repo.git",
        "feature",
    )
    mock_git_checkout.assert_called_once_with("/tmp/repo", "feature")
    mock_git_reset.assert_called_once_with("/tmp/repo")
