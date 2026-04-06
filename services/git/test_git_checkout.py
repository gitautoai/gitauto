import subprocess
import tempfile
from unittest.mock import patch

import pytest

from services.git.conftest import SAMPLE_REPO_URL
from services.git.git_checkout import git_checkout
from services.git.git_clone_to_tmp import git_clone_to_tmp
from services.git.git_fetch import git_fetch


def test_git_checkout_success():
    with patch("services.git.git_checkout.run_subprocess") as mock_run:
        result = git_checkout("/tmp/repo", "feature-branch")

        assert result is True
        mock_run.assert_called_once_with(
            ["git", "checkout", "-f", "-B", "feature-branch", "FETCH_HEAD"],
            "/tmp/repo",
        )


@pytest.mark.integration
def test_git_checkout_switches_branch():
    """Sociable: clone main, fetch test branch, checkout, verify working tree."""
    with tempfile.TemporaryDirectory() as clone_dir:
        git_clone_to_tmp(clone_dir, SAMPLE_REPO_URL, "main")
        git_fetch(clone_dir, SAMPLE_REPO_URL, "test/git-checkout")

        result = git_checkout(clone_dir, "test/git-checkout")

        assert result is True
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=clone_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        assert branch_result.stdout.strip() == "test/git-checkout"
