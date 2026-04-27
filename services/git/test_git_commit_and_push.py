# pyright: reportAttributeAccessIssue=false, reportUnusedVariable=false
# pylint: disable=unused-argument
import os
import subprocess
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from services.git.git_clone_to_tmp import git_clone_to_tmp
from services.git.git_commit_and_push import GitCommitResult, git_commit_and_push
from utils.error.handle_exceptions import TRANSIENT_MAX_ATTEMPTS


def test_git_commit_and_push_success(create_test_base_args):
    with patch("services.git.git_commit_and_push.run_subprocess"):
        result = git_commit_and_push(
            base_args=create_test_base_args(),
            message="Replace content of src/app.py",
            files=["src/app.py"],
        )
        assert result.success is True
        assert result.concurrent_push_detected is False


def test_git_commit_and_push_add_fails(create_test_base_args):
    """Non-retryable git-add failure propagates now that git_commit_and_push uses raise_on_error=True (no silent False default)."""
    call_count = 0

    def mock_run(args, cwd):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("Command failed: fatal: pathspec 'bad.py' did not match")
        return MagicMock(returncode=0, stdout="")

    with patch("services.git.git_commit_and_push.run_subprocess", side_effect=mock_run):
        with pytest.raises(ValueError, match="pathspec 'bad.py' did not match"):
            git_commit_and_push(
                base_args=create_test_base_args(),
                message="Replace content of bad.py",
                files=["bad.py"],
            )


def test_git_commit_and_push_commit_fails(create_test_base_args):
    """Non-retryable git-commit failure propagates (raise_on_error=True)."""

    def mock_run(args, cwd):
        if args[:2] == ["git", "commit"]:
            raise ValueError("Command failed: nothing to commit")
        return MagicMock(returncode=0, stdout="")

    with patch("services.git.git_commit_and_push.run_subprocess", side_effect=mock_run):
        with pytest.raises(ValueError, match="nothing to commit"):
            git_commit_and_push(
                base_args=create_test_base_args(),
                message="Update file.py",
                files=["file.py"],
            )


def test_git_commit_and_push_push_fails(create_test_base_args):
    """Non-concurrent-push push failure propagates (raise_on_error=True)."""

    def mock_run(args, cwd):
        if args[:2] == ["git", "push"]:
            raise ValueError("Command failed: failed to push")
        return MagicMock(returncode=0, stdout="")

    with patch("services.git.git_commit_and_push.run_subprocess", side_effect=mock_run):
        with pytest.raises(ValueError, match="failed to push"):
            git_commit_and_push(
                base_args=create_test_base_args(),
                message="Update file.py",
                files=["file.py"],
            )


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
        assert result.success is True
        assert result.concurrent_push_detected is False
        # commit_args_captured[3] is the full message: "<subject> [skip ci]" followed by a "\n\nCo-Authored-By: ..." trailer appended by format_commit_message.
        # Assert the subject line (first line) exactly.
        assert commit_args_captured[:3] == ["git", "commit", "-m"]
        assert commit_args_captured[3].splitlines()[0] == "Update file.py [skip ci]"


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
        assert result.success is True
        assert result.concurrent_push_detected is False
        assert add_args_captured == ["git", "add", "old.py", "new.py"]


def test_git_commit_and_push_force_push(create_test_base_args):
    push_args_captured = []

    def mock_run(args, cwd):
        nonlocal push_args_captured
        if args[:2] == ["git", "push"]:
            push_args_captured = args
        return MagicMock(returncode=0, stdout="")

    base_args = create_test_base_args(
        clone_url="https://x-access-token:tok@github.com/o/r.git",
        new_branch="feature/force-push",
    )

    with patch("services.git.git_commit_and_push.run_subprocess", side_effect=mock_run):
        result = git_commit_and_push(
            base_args=base_args,
            message="Rebase onto release/20260422",
            files=["app.py"],
            force=True,
        )
        assert result.success is True
        assert result.concurrent_push_detected is False
        assert push_args_captured == [
            "git",
            "push",
            "--force-with-lease",
            "origin",
            "HEAD:refs/heads/feature/force-push",
        ]


def test_git_commit_and_push_no_force_by_default(create_test_base_args):
    push_args_captured = []

    def mock_run(args, cwd):
        nonlocal push_args_captured
        if args[:2] == ["git", "push"]:
            push_args_captured = args
        return MagicMock(returncode=0, stdout="")

    base_args = create_test_base_args(
        clone_url="https://x-access-token:tok@github.com/o/r.git",
        new_branch="feature/normal-push",
    )

    with patch("services.git.git_commit_and_push.run_subprocess", side_effect=mock_run):
        result = git_commit_and_push(
            base_args=base_args,
            message="Normal push",
            files=["app.py"],
        )
        assert result.success is True
        assert result.concurrent_push_detected is False
        assert push_args_captured == [
            "git",
            "push",
            "origin",
            "HEAD:refs/heads/feature/normal-push",
        ]


def test_git_commit_and_push_retries_on_github_500(create_test_base_args):
    """Sentry AGENT-36Z/36J: GitHub returns transient 500 on push. Retry and succeed."""
    attempts = {"push": 0}

    def mock_run(args, cwd):
        if args[:2] == ["git", "push"]:
            attempts["push"] += 1
            if attempts["push"] == 1:
                raise ValueError(
                    "Command failed: remote: Internal Server Error\n"
                    "To https://github.com/org/repo.git\n"
                    " ! [remote rejected] HEAD -> branch (Internal Server Error)"
                )
        return MagicMock(returncode=0, stdout="")

    with (
        patch("services.git.git_commit_and_push.run_subprocess", side_effect=mock_run),
        patch("utils.error.handle_exceptions.time.sleep"),
    ):
        result = git_commit_and_push(
            base_args=create_test_base_args(),
            message="Update file.py",
            files=["file.py"],
        )
        assert result.success is True
        assert result.concurrent_push_detected is False
        assert attempts["push"] == 2


def test_git_commit_and_push_gives_up_after_max_github_500s(create_test_base_args):
    """If GitHub keeps 500-ing past the retry budget, the error propagates (raise_on_error=True)."""
    attempts = {"push": 0}

    def mock_run(args, cwd):
        if args[:2] == ["git", "push"]:
            attempts["push"] += 1
            raise ValueError(
                "Command failed: remote: Internal Server Error\n"
                " ! [remote rejected] HEAD -> branch (Internal Server Error)"
            )
        return MagicMock(returncode=0, stdout="")

    with (
        patch("services.git.git_commit_and_push.run_subprocess", side_effect=mock_run),
        patch("utils.error.handle_exceptions.time.sleep"),
    ):
        with pytest.raises(ValueError, match="Internal Server Error"):
            git_commit_and_push(
                base_args=create_test_base_args(),
                message="Update file.py",
                files=["file.py"],
            )
        assert attempts["push"] == TRANSIENT_MAX_ATTEMPTS


def test_git_commit_and_push_bails_on_non_fast_forward(create_test_base_args):
    """Sentry AGENT-36T: a concurrent push (human or another GitAuto) landed
    a commit on our branch between earlier work and this push. git_commit_and_push
    returns GitCommitResult(concurrent_push_detected=True) without raising; the
    caller chain (tool wrapper → chat_with_agent → handler) bails cleanly, runs
    normal cleanup, and posts a truthful PR comment. The racer author is looked
    up via the get_branch_head_author helper for logging only."""
    calls = []

    def mock_run(args, cwd):
        calls.append(args)
        if args[:2] == ["git", "push"]:
            raise ValueError(
                "Command failed: To https://github.com/org/repo.git\n"
                " ! [rejected]        HEAD -> branch (fetch first)\n"
                "error: failed to push some refs"
            )
        return MagicMock(returncode=0, stdout="")

    base_args = create_test_base_args(
        clone_url="https://x-access-token:tok@github.com/org/repo.git",
        new_branch="feature/raced",
    )

    with patch(
        "services.git.git_commit_and_push.run_subprocess", side_effect=mock_run
    ), patch(
        "services.git.git_commit_and_push.get_branch_head_author",
        return_value="Some Human <human@example.com>",
    ) as mock_author:
        result = git_commit_and_push(
            base_args=base_args,
            message="Update file.py",
            files=["file.py"],
        )

    assert isinstance(result, GitCommitResult)
    assert result.success is False
    assert result.concurrent_push_detected is True
    mock_author.assert_called_once_with(
        base_args["clone_dir"],
        "https://x-access-token:tok@github.com/org/repo.git",
        "feature/raced",
    )
    # Exact sequence stopped at the failed push: no rebase, no retry.
    assert calls[0][:2] == ["git", "add"]
    assert calls[1][:2] == ["git", "commit"]
    assert calls[2][:3] == ["git", "remote", "set-url"]
    assert calls[3][:2] == ["git", "push"]
    assert len(calls) == 4


def test_git_commit_and_push_rejects_gitignored_path(create_test_base_args):
    """Sentry AGENT-3J4 (Foxquilt/foxden-policy-document-backend PR 1410,
    2026-04-20): agent ran search_and_replace on node_modules/test-exclude/index.js
    (an installed dependency), then git_commit_and_push tried to `git add` it.
    Git rejected with 'paths are ignored by one of your .gitignore files'. The
    guard catches this up-front via git check-ignore and returns a structured
    result so the caller can decide (typically: tell the agent to stop editing
    ignored paths). No run_subprocess for git add/commit/push should fire."""
    calls = []

    def mock_run(args, cwd):
        calls.append(args)
        return MagicMock(returncode=0, stdout="")

    with patch(
        "services.git.git_commit_and_push.run_subprocess", side_effect=mock_run
    ), patch(
        "services.git.git_commit_and_push.is_path_gitignored",
        return_value=True,
    ) as mock_ignored:
        result = git_commit_and_push(
            base_args=create_test_base_args(),
            message="Edit installed dep",
            files=["node_modules/test-exclude/index.js"],
        )

    assert isinstance(result, GitCommitResult)
    assert result.success is False
    assert result.gitignored_paths == ["node_modules/test-exclude/index.js"]
    assert result.concurrent_push_detected is False
    mock_ignored.assert_called_once()
    assert not calls


def test_git_commit_and_push_drops_gitignored_and_commits_rest(create_test_base_args):
    """When a multi-file commit mixes gitignored and tracked paths, drop the
    ignored ones and commit the rest. Today every caller passes a single-element
    list so this is forward-looking — but the contract accepts list[str], so the
    behavior must be correct under the type signature."""
    add_args_captured = []

    def mock_run(args, cwd):
        if args[:2] == ["git", "add"]:
            add_args_captured.extend(args)
        return MagicMock(returncode=0, stdout="")

    def fake_check_ignore(_clone_dir, path):
        return path.startswith("node_modules/")

    with patch(
        "services.git.git_commit_and_push.run_subprocess", side_effect=mock_run
    ), patch(
        "services.git.git_commit_and_push.is_path_gitignored",
        side_effect=fake_check_ignore,
    ):
        result = git_commit_and_push(
            base_args=create_test_base_args(),
            message="Mixed update",
            files=["node_modules/x/y.js", "src/app.py", "src/util.py"],
        )

    assert result.success is True
    # All gitignored paths are surfaced (currently one) so the caller can warn the agent.
    assert result.gitignored_paths == ["node_modules/x/y.js"]
    # `git add` only saw the non-ignored ones, in original order.
    assert add_args_captured == ["git", "add", "src/app.py", "src/util.py"]


def test_git_commit_and_push_allows_non_gitignored_path(create_test_base_args):
    """Negative case for the gitignore guard: when the guard returns False the
    normal add/commit/push sequence must still run end-to-end."""
    calls = []

    def mock_run(args, cwd):
        calls.append(args)
        return MagicMock(returncode=0, stdout="")

    with patch(
        "services.git.git_commit_and_push.run_subprocess", side_effect=mock_run
    ), patch("services.git.git_commit_and_push.is_path_gitignored", return_value=False):
        result = git_commit_and_push(
            base_args=create_test_base_args(),
            message="Normal edit",
            files=["src/app.py"],
        )

    assert result == GitCommitResult(success=True, gitignored_paths=[])
    assert [c[:2] for c in calls] == [
        ["git", "add"],
        ["git", "commit"],
        ["git", "remote"],
        ["git", "push"],
    ]


def test_git_commit_and_push_does_not_retry_non_transient(create_test_base_args):
    """A 'pathspec did not match' or similar non-transient failure must NOT retry — otherwise we'd waste time on errors that will never succeed."""
    attempts = {"push": 0}

    def mock_run(args, cwd):
        if args[:2] == ["git", "push"]:
            attempts["push"] += 1
            raise ValueError(
                "Command failed: error: src refspec main does not match any"
            )
        return MagicMock(returncode=0, stdout="")

    with (
        patch("services.git.git_commit_and_push.run_subprocess", side_effect=mock_run),
        patch("utils.error.handle_exceptions.time.sleep"),
    ):
        with pytest.raises(ValueError, match="src refspec main does not match"):
            git_commit_and_push(
                base_args=create_test_base_args(),
                message="Update file.py",
                files=["file.py"],
            )
        assert attempts["push"] == 1


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

        assert result.success is True
        assert result.concurrent_push_detected is False

        bare_dir = bare_url.replace("file://", "")
        log = subprocess.run(
            ["git", "log", "--format=%s", "feature/sociable-push", "-1"],
            cwd=bare_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        # Commit message has a trailer appended by format_commit_message; assert the subject line (first line) matches exactly.
        assert log.stdout.strip().splitlines()[0] == "Add new file"
