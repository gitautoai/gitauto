# pyright: reportUnusedVariable=false
import os
import subprocess
import tempfile
from unittest.mock import call, patch

import pytest

from services.git.git_clone_to_tmp import git_clone_to_tmp


class TestGitCloneToTmpUnit:
    """Unit tests with mocked run_subprocess."""

    @patch("services.git.git_clone_to_tmp.set_git_identity")
    @patch("services.git.git_clone_to_tmp.run_subprocess")
    def test_fresh_clone(self, mock_run, _mock_identity):
        """Fresh clone when .git does not exist."""
        with tempfile.TemporaryDirectory() as clone_dir:
            result = git_clone_to_tmp(clone_dir, "https://github.com/o/r.git", "main")

            assert result == clone_dir
            mock_run.assert_called_once_with(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "-b",
                    "main",
                    "https://github.com/o/r.git",
                    clone_dir,
                ],
                clone_dir,
            )

    @patch("services.git.git_clone_to_tmp.set_git_identity")
    @patch("services.git.git_clone_to_tmp.run_subprocess")
    def test_existing_clone_updates(self, mock_run, _mock_identity):
        """When .git exists, fetch + checkout instead of clone."""
        with tempfile.TemporaryDirectory() as clone_dir:
            os.makedirs(os.path.join(clone_dir, ".git"))

            result = git_clone_to_tmp(
                clone_dir, "https://github.com/o/r.git", "feature"
            )

            assert result == clone_dir
            calls = mock_run.call_args_list
            # Should NOT call git clone
            clone_calls = [c for c in calls if "clone" in c[0][0]]
            assert clone_calls == []
            # Should call fetch, checkout
            assert (
                call(["git", "fetch", "--depth", "1", "origin", "feature"], clone_dir)
                in calls
            )
            assert (
                call(
                    ["git", "checkout", "-f", "-B", "feature", "FETCH_HEAD"], clone_dir
                )
                in calls
            )

    @patch("services.git.git_clone_to_tmp.set_git_identity")
    @patch("services.git.git_clone_to_tmp.run_subprocess")
    def test_existing_clone_adds_origin_when_missing(self, mock_run, _mock_identity):
        """When origin remote is missing, add it instead of set-url."""
        with tempfile.TemporaryDirectory() as clone_dir:
            os.makedirs(os.path.join(clone_dir, ".git"))

            # First call to get-url raises ValueError (origin missing)
            def side_effect(args, cwd):  # pylint: disable=unused-argument
                if args == ["git", "remote", "get-url", "origin"]:
                    raise ValueError("No such remote 'origin'")

            mock_run.side_effect = side_effect

            result = git_clone_to_tmp(clone_dir, "https://github.com/o/r.git", "main")

            assert result == clone_dir
            assert (
                call(
                    ["git", "remote", "add", "origin", "https://github.com/o/r.git"],
                    clone_dir,
                )
                in mock_run.call_args_list
            )

    @patch("services.git.git_clone_to_tmp.set_git_identity")
    @patch("services.git.git_clone_to_tmp.run_subprocess")
    def test_creates_parent_dirs(
        self, mock_run, _mock_identity
    ):  # pylint: disable=unused-argument
        """makedirs is called for fresh clone when parent doesn't exist."""
        with tempfile.TemporaryDirectory() as base:
            clone_dir = os.path.join(base, "owner", "repo")
            result = git_clone_to_tmp(clone_dir, "https://github.com/o/r.git", "main")

            assert result == clone_dir
            assert os.path.isdir(clone_dir)


@pytest.mark.integration
class TestGitCloneToTmpIntegration:
    """Integration tests against a real local bare repo."""

    def test_fresh_clone_then_update(self, local_repo):
        """Clone a local repo, then update it (simulating Lambda reuse)."""
        bare_url, _work_dir = local_repo

        with tempfile.TemporaryDirectory() as clone_dir:
            # Fresh clone
            result = git_clone_to_tmp(clone_dir, bare_url, "main")
            assert result == clone_dir
            assert os.path.isfile(os.path.join(clone_dir, "README.md"))
            assert os.path.isfile(os.path.join(clone_dir, "src", "main.py"))

            # Update (simulates second Lambda invocation reusing /tmp)
            result2 = git_clone_to_tmp(clone_dir, bare_url, "main")
            assert result2 == clone_dir
            assert os.path.isfile(os.path.join(clone_dir, "README.md"))

    def test_clone_feature_branch(self, local_repo):
        """Clone a non-default branch."""
        bare_url, _work_dir = local_repo

        with tempfile.TemporaryDirectory() as clone_dir:
            result = git_clone_to_tmp(clone_dir, bare_url, "feature/test-branch")
            assert result == clone_dir
            assert os.path.isdir(os.path.join(clone_dir, ".git"))

    def test_switch_branch(self, local_repo):
        """Clone main, then switch to feature branch via update."""
        bare_url, _work_dir = local_repo

        with tempfile.TemporaryDirectory() as clone_dir:
            git_clone_to_tmp(clone_dir, bare_url, "main")
            assert os.path.isfile(os.path.join(clone_dir, "README.md"))

            # Switch to feature branch
            result = git_clone_to_tmp(clone_dir, bare_url, "feature/test-branch")
            assert result == clone_dir

            # Verify we're on the feature branch
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=clone_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            assert branch_result.stdout.strip() == "feature/test-branch"
