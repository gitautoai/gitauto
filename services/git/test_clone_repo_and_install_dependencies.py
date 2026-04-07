# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import os
import subprocess
import tempfile
from unittest.mock import patch

import pytest

from services.git.clone_repo_and_install_dependencies import (
    clone_repo_and_install_dependencies,
)
from services.git.conftest import SAMPLE_REPO_URL


@pytest.fixture
def mock_get_clone_url():
    with patch(
        "services.git.clone_repo_and_install_dependencies.get_clone_url"
    ) as mock:
        mock.return_value = "https://x-access-token:token@github.com/owner/repo.git"
        yield mock


@pytest.fixture
def mock_git_clone_to_tmp():
    with patch(
        "services.git.clone_repo_and_install_dependencies.git_clone_to_tmp"
    ) as mock:
        mock.return_value = "/tmp/repo"
        yield mock


@pytest.fixture
def mock_git_fetch():
    with patch("services.git.clone_repo_and_install_dependencies.git_fetch") as mock:
        yield mock


@pytest.fixture
def mock_git_checkout():
    with patch("services.git.clone_repo_and_install_dependencies.git_checkout") as mock:
        yield mock


@pytest.fixture
def mock_s3_extract():
    with patch(
        "services.git.clone_repo_and_install_dependencies.download_and_extract_s3_deps"
    ) as mock:
        yield mock


@pytest.fixture
def mock_copy_config():
    with patch(
        "services.git.clone_repo_and_install_dependencies.copy_config_templates"
    ) as mock:
        yield mock


def test_prepare_repo_clones_base_then_checks_out_pr(
    mock_get_clone_url,
    mock_git_clone_to_tmp,
    mock_git_fetch,
    mock_git_checkout,
    mock_s3_extract,
    mock_copy_config,
):
    clone_url = "https://x-access-token:token@github.com/owner/repo.git"

    clone_repo_and_install_dependencies(
        owner="owner",
        repo="repo",
        base_branch="main",
        pr_branch="feature",
        token="token",
        clone_dir="/tmp/repo",
    )

    mock_git_clone_to_tmp.assert_called_once_with("/tmp/repo", clone_url, "main")
    mock_git_fetch.assert_called_once_with("/tmp/repo", clone_url, "feature")
    mock_git_checkout.assert_called_once_with("/tmp/repo", "feature")
    mock_s3_extract.assert_called_once_with("owner", "repo", "/tmp/repo")
    mock_copy_config.assert_called_once_with("/tmp/repo")


SAMPLE_PR_BRANCH = "test/clone-integration"


@pytest.mark.integration
def test_clone_repo_checks_out_pr_branch():
    """Sociable test: clone base, fetch+checkout PR branch, verify working tree."""
    with tempfile.TemporaryDirectory() as clone_dir:
        with patch(
            "services.git.clone_repo_and_install_dependencies.get_clone_url"
        ) as mock_url, patch(
            "services.git.clone_repo_and_install_dependencies.download_and_extract_s3_deps"
        ):
            mock_url.return_value = SAMPLE_REPO_URL

            clone_repo_and_install_dependencies(
                owner="gitautoai",
                repo="sample-calculator",
                base_branch="main",
                pr_branch=SAMPLE_PR_BRANCH,
                token="fake",
                clone_dir=clone_dir,
            )

        # Verify we're on the PR branch
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=clone_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == SAMPLE_PR_BRANCH

        # Verify files from the repo are present
        assert os.path.isfile(os.path.join(clone_dir, "README.md"))
        assert os.path.isfile(os.path.join(clone_dir, "calculator.py"))
