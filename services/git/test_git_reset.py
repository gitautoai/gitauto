import subprocess
import tempfile
from unittest.mock import patch

import pytest

from services.git.conftest import SAMPLE_REPO_URL
from services.git.git_clone_to_tmp import git_clone_to_tmp
from services.git.git_fetch import git_fetch
from services.git.git_reset import git_reset


def test_git_reset_success():
    with patch("services.git.git_reset.run_subprocess") as mock_run, patch(
        "services.git.git_reset.resolve_git_locks"
    ):
        result = git_reset("/tmp/repo")

        assert result is True
        assert mock_run.call_count == 1


def test_git_reset_calls_resolve_git_locks():
    with patch("services.git.git_reset.run_subprocess"), patch(
        "services.git.git_reset.resolve_git_locks"
    ) as mock_clear:
        result = git_reset("/tmp/repo")

        assert result is True
        mock_clear.assert_called_once_with("/tmp/repo/.git")


@pytest.mark.integration
def test_git_reset_after_fetch():
    """Sociable: clone main, fetch test branch, reset to FETCH_HEAD, verify commit."""
    with tempfile.TemporaryDirectory() as clone_dir:
        git_clone_to_tmp(clone_dir, SAMPLE_REPO_URL, "main")
        git_fetch(clone_dir, SAMPLE_REPO_URL, "test/git-reset")

        result = git_reset(clone_dir)

        assert result is True
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=clone_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        fetch_head = subprocess.run(
            ["git", "rev-parse", "FETCH_HEAD"],
            cwd=clone_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        assert head.stdout.strip() == fetch_head.stdout.strip()
