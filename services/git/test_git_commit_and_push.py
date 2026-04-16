# pylint: disable=unused-argument
import os
import subprocess
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from services.git.git_clone_to_tmp import git_clone_to_tmp
from services.git.git_commit_and_push import git_commit_and_push


def test_git_commit_and_push_success(create_test_base_args):
    with patch("services.git.git_commit_and_push.run_subprocess"):
        result = git_commit_and_push(
            base_args=create_test_base_args(),
            message="Replace content of src/app.py",
            files=["src/app.py"],
        )
        assert result is True


def test_git_commit_and_push_add_fails(create_test_base_args):
    call_count = 0

    def mock_run(args, cwd):
        nonlocal call_count
        call_count += 1
        # First call is git add (identity is set upstream in clone_repo_and_install_dependencies)
        if call_count == 1:
            raise ValueError("Command failed: fatal: pathspec 'bad.py' did not match")
        return MagicMock(returncode=0, stdout="")

    with patch("services.git.git_commit_and_push.run_subprocess", side_effect=mock_run):
        result = git_commit_and_push(
            base_args=create_test_base_args(),
            message="Replace content of bad.py",
            files=["bad.py"],
        )
        assert result is False


def test_git_commit_and_push_commit_fails(create_test_base_args):
    def mock_run(args, cwd):
        if args[:2] == ["git", "commit"]:
            raise ValueError("Command failed: nothing to commit")
        return MagicMock(returncode=0, stdout="")

    with patch("services.git.git_commit_and_push.run_subprocess", side_effect=mock_run):
        result = git_commit_and_push(
            base_args=create_test_base_args(),
            message="Update file.py",
            files=["file.py"],
        )
        assert result is False


def test_git_commit_and_push_push_fails(create_test_base_args):
    def mock_run(args, cwd):
        if args[:2] == ["git", "push"]:
            raise ValueError("Command failed: failed to push")
        return MagicMock(returncode=0, stdout="")

    with patch("services.git.git_commit_and_push.run_subprocess", side_effect=mock_run):
        result = git_commit_and_push(
            base_args=create_test_base_args(),
            message="Update file.py",
            files=["file.py"],
        )
        assert result is False


def test_git_commit_and_push_skip_ci(create_test_base_args):
    commit_args_captured = []

    def mock_run(args, cwd):
        nonlocal commit_args_captured
        if args[:2] == ["git", "commit"]:
            commit_args_captured = args
        return MagicMock(returncode=0, stdout="")

    base_args = create_test_base_args()
    base_args["skip_ci"] = True

    with patch("services.git.git_commit_and_push.run_subprocess", side_effect=mock_run):
        result = git_commit_and_push(
            base_args=base_args,
            message="Update file.py",
            files=["file.py"],
        )
        assert result is True
        # -m is at index 2, message is at index 3
        assert "[skip ci]" in commit_args_captured[3]


def test_git_commit_and_push_stages_specific_files(create_test_base_args):
    add_args_captured = []

    def mock_run(args, cwd):
        nonlocal add_args_captured
        if args[:2] == ["git", "add"]:
            add_args_captured = args
        return MagicMock(returncode=0, stdout="")

    with patch("services.git.git_commit_and_push.run_subprocess", side_effect=mock_run):
        result = git_commit_and_push(
            base_args=create_test_base_args(),
            message="Update old.py, new.py",
            files=["old.py", "new.py"],
        )
        assert result is True
        assert "old.py" in add_args_captured
        assert "new.py" in add_args_captured


def test_git_commit_and_push_force_push(create_test_base_args):
    push_args_captured = []

    def mock_run(args, cwd):
        nonlocal push_args_captured
        if args[:2] == ["git", "push"]:
            push_args_captured = args
        return MagicMock(returncode=0, stdout="")

    with patch("services.git.git_commit_and_push.run_subprocess", side_effect=mock_run):
        result = git_commit_and_push(
            base_args=create_test_base_args(),
            message="Rebase onto release/20260422",
            files=["app.py"],
            force=True,
        )
        assert result is True
        assert "--force-with-lease" in push_args_captured


def test_git_commit_and_push_no_force_by_default(create_test_base_args):
    push_args_captured = []

    def mock_run(args, cwd):
        nonlocal push_args_captured
        if args[:2] == ["git", "push"]:
            push_args_captured = args
        return MagicMock(returncode=0, stdout="")

    with patch("services.git.git_commit_and_push.run_subprocess", side_effect=mock_run):
        result = git_commit_and_push(
            base_args=create_test_base_args(),
            message="Normal push",
            files=["app.py"],
        )
        assert result is True
        assert "--force-with-lease" not in push_args_captured


@pytest.mark.integration
def test_git_commit_and_push_to_local_bare(local_repo, create_test_base_args):
    """Sociable: clone local repo, create file, commit+push, verify in bare repo."""
    bare_url, _work_dir = local_repo

    with tempfile.TemporaryDirectory() as clone_dir:
        git_clone_to_tmp(clone_dir, bare_url, "main")

        base_args = create_test_base_args(
            clone_dir=clone_dir,
            clone_url=bare_url,
            new_branch="feature/sociable-push",
        )

        with open(os.path.join(clone_dir, "new_file.py"), "w", encoding="utf-8") as f:
            f.write("print('hello')\n")

        result = git_commit_and_push(
            base_args=base_args,
            message="Add new file",
            files=["new_file.py"],
        )

        assert result is True

        bare_dir = bare_url.replace("file://", "")
        log = subprocess.run(
            ["git", "log", "--oneline", "feature/sociable-push", "-1"],
            cwd=bare_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        assert "Add new file" in log.stdout
