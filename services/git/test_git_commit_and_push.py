# pylint: disable=unused-argument
from typing import cast
from unittest.mock import MagicMock, patch

from services.git.git_commit_and_push import git_commit_and_push
from services.github.types.github_types import BaseArgs


def _make_base_args():
    return cast(
        BaseArgs,
        {
            "owner_type": "Organization",
            "owner_id": 123,
            "owner": "test-owner",
            "repo_id": 456,
            "repo": "test-repo",
            "clone_url": "https://x-access-token:token@github.com/test-owner/test-repo.git",
            "is_fork": False,
            "base_branch": "main",
            "new_branch": "gitauto/issue-1",
            "installation_id": 789,
            "token": "test-token",
            "sender_id": 1,
            "sender_name": "test-user",
            "sender_email": "test@example.com",
            "sender_display_name": "Test User",
            "reviewers": [],
            "github_urls": [],
            "other_urls": [],
            "clone_dir": "/tmp/test-owner/test-repo/pr-1",
            "pr_number": 1,
            "pr_title": "Test PR",
            "pr_body": "",
            "pr_comments": [],
            "pr_creator": "test-user",
        },
    )


def test_git_commit_and_push_success():
    with patch("services.git.git_commit_and_push.run_subprocess"):
        result = git_commit_and_push(
            base_args=_make_base_args(),
            message="Replace content of src/app.py",
            files=["src/app.py"],
        )
        assert result is True


def test_git_commit_and_push_add_fails():
    call_count = 0

    def mock_run(args, cwd):
        nonlocal call_count
        call_count += 1
        # First two calls are git config (user.name, user.email), third is git add
        if call_count == 3:
            raise ValueError("Command failed: fatal: pathspec 'bad.py' did not match")
        return MagicMock(returncode=0, stdout="")

    with patch("services.git.git_commit_and_push.run_subprocess", side_effect=mock_run):
        result = git_commit_and_push(
            base_args=_make_base_args(),
            message="Replace content of bad.py",
            files=["bad.py"],
        )
        assert result is False


def test_git_commit_and_push_commit_fails():
    def mock_run(args, cwd):
        if args[:2] == ["git", "commit"]:
            raise ValueError("Command failed: nothing to commit")
        return MagicMock(returncode=0, stdout="")

    with patch("services.git.git_commit_and_push.run_subprocess", side_effect=mock_run):
        result = git_commit_and_push(
            base_args=_make_base_args(),
            message="Update file.py",
            files=["file.py"],
        )
        assert result is False


def test_git_commit_and_push_push_fails():
    def mock_run(args, cwd):
        if args[:2] == ["git", "push"]:
            raise ValueError("Command failed: failed to push")
        return MagicMock(returncode=0, stdout="")

    with patch("services.git.git_commit_and_push.run_subprocess", side_effect=mock_run):
        result = git_commit_and_push(
            base_args=_make_base_args(),
            message="Update file.py",
            files=["file.py"],
        )
        assert result is False


def test_git_commit_and_push_skip_ci():
    commit_args_captured = []

    def mock_run(args, cwd):
        nonlocal commit_args_captured
        if args[:2] == ["git", "commit"]:
            commit_args_captured = args
        return MagicMock(returncode=0, stdout="")

    base_args = _make_base_args()
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


def test_git_commit_and_push_stages_specific_files():
    add_args_captured = []

    def mock_run(args, cwd):
        nonlocal add_args_captured
        if args[:2] == ["git", "add"]:
            add_args_captured = args
        return MagicMock(returncode=0, stdout="")

    with patch("services.git.git_commit_and_push.run_subprocess", side_effect=mock_run):
        result = git_commit_and_push(
            base_args=_make_base_args(),
            message="Update old.py, new.py",
            files=["old.py", "new.py"],
        )
        assert result is True
        assert "old.py" in add_args_captured
        assert "new.py" in add_args_captured
