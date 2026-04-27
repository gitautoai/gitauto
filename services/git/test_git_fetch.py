import os
import tempfile
from unittest.mock import patch

import pytest

from services.git.conftest import SAMPLE_REPO_URL
from services.git.git_clone_to_tmp import git_clone_to_tmp
from services.git.git_fetch import git_fetch


def test_git_fetch_success():
    with (
        patch("services.git.git_fetch.run_subprocess") as mock_run,
        patch("services.git.git_fetch.resolve_git_locks"),
        patch(
            "services.git.git_fetch.os.path.join", return_value="/tmp/owner/repo/.git"
        ),
    ):
        result = git_fetch(
            "/tmp/owner/repo", "https://github.com/owner/repo.git", "main"
        )

        assert result is True
        mock_run.assert_called_once_with(
            [
                "git",
                "fetch",
                "--depth",
                "1",
                "https://github.com/owner/repo.git",
                "main",
            ],
            "/tmp/owner/repo",
        )


def test_git_fetch_resolves_locks_before_fetch():
    with (
        patch("services.git.git_fetch.run_subprocess"),
        patch("services.git.git_fetch.resolve_git_locks") as mock_resolve,
    ):
        result = git_fetch(
            "/tmp/owner/repo", "https://github.com/owner/repo.git", "main"
        )

        assert result is True
        mock_resolve.assert_called_once_with("/tmp/owner/repo/.git")


def test_git_fetch_returns_false_when_branch_deleted_on_remote():
    """Sentry AGENT-3KB and the cascade AGENT-3KC/3KD: foxcom-forms PR 1150 fired a webhook 7 days after the gitauto/schedule-* branch had been removed. Old behavior: git_fetch raised ValueError, the handle_exceptions decorator surfaced it to Sentry, then git_checkout ran against the missing FETCH_HEAD and produced its own Sentry. New behavior: catch the 'couldn't find remote ref' stderr specifically, log info, return False so callers can short-circuit cleanly."""
    with (
        patch(
            "services.git.git_fetch.run_subprocess",
            side_effect=ValueError(
                "Command failed: fatal: couldn't find remote ref gitauto/schedule-20260414-130014-YUvC"
            ),
        ),
        patch("services.git.git_fetch.resolve_git_locks"),
    ):
        result = git_fetch(
            "/tmp/owner/repo", "https://github.com/owner/repo.git", "stale-branch"
        )

    assert result is False


def test_git_fetch_re_raises_other_subprocess_errors():
    """Negative case for the stale-branch shortcut: any other subprocess failure (auth, network, server-side rejection) must NOT silently return False. The handle_exceptions decorator catches and reports them so we don't lose visibility on real outages."""
    with (
        patch(
            "services.git.git_fetch.run_subprocess",
            side_effect=ValueError(
                "Command failed: fatal: unable to access remote: server-side error"
            ),
        ),
        patch("services.git.git_fetch.resolve_git_locks"),
    ):
        result = git_fetch(
            "/tmp/owner/repo", "https://github.com/owner/repo.git", "main"
        )

    # @handle_exceptions(default_return_value=False, raise_on_error=False) swallows the unrecognised error and returns the default — Sentry still fires.
    assert result is False


@pytest.mark.integration
def test_git_fetch_from_real_repo():
    """Sociable: clone main, fetch a different branch, verify FETCH_HEAD updated."""
    with tempfile.TemporaryDirectory() as clone_dir:
        git_clone_to_tmp(clone_dir, SAMPLE_REPO_URL, "main")

        result = git_fetch(clone_dir, SAMPLE_REPO_URL, "test/git-fetch")

        assert result is True
        fetch_head = os.path.join(clone_dir, ".git", "FETCH_HEAD")
        assert os.path.isfile(fetch_head)
