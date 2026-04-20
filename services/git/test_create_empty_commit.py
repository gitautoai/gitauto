# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import subprocess

from unittest.mock import call, patch

import pytest

from services.git.create_empty_commit import create_empty_commit
from services.git.git_checkout import git_checkout
from services.git.git_fetch import git_fetch


def test_create_empty_commit_with_clone_dir(create_test_base_args):
    base_args_with_clone = create_test_base_args(
        clone_url="https://x-access-token:token@github.com/test-owner/test-repo.git",
        new_branch="feature-branch",
        clone_dir="/tmp/test-owner/test-repo/pr-123",
    )
    with patch("services.git.create_empty_commit.run_subprocess") as mock_subprocess:
        result = create_empty_commit(base_args_with_clone)

        assert result is True
        clone_dir = "/tmp/test-owner/test-repo/pr-123"
        clone_url = "https://x-access-token:token@github.com/test-owner/test-repo.git"
        calls = mock_subprocess.call_args_list
        # First call is git commit (identity is set by git_clone_to_tmp before this function)
        assert calls[0] == call(
            args=[
                "git",
                "commit",
                "--allow-empty",
                "--no-verify",
                "-m",
                "Empty commit to trigger final tests",
            ],
            cwd=clone_dir,
        )
        assert calls[1] == call(
            args=["git", "push", clone_url, "HEAD:refs/heads/feature-branch"],
            cwd=clone_dir,
        )


def test_create_empty_commit_skips_pre_commit_hooks(create_test_base_args):
    """Reproduces production failure: repos with pre-commit hooks (e.g. lint-staged)
    fail in Lambda because npm can't mkdir in /home/sbx_user1051. --no-verify skips hooks.
    """
    base_args_with_clone = create_test_base_args(
        clone_url="https://x-access-token:token@github.com/test-owner/test-repo.git",
        new_branch="feature-branch",
        clone_dir="/tmp/test-owner/test-repo/pr-123",
    )
    with patch("services.git.create_empty_commit.run_subprocess") as mock_subprocess:
        create_empty_commit(base_args_with_clone)

        commit_call = mock_subprocess.call_args_list[0]
        assert commit_call[1]["args"] == [
            "git",
            "commit",
            "--allow-empty",
            "--no-verify",
            "-m",
            "Empty commit to trigger final tests",
        ]


def test_create_empty_commit_failure(create_test_base_args):
    base_args_with_clone = create_test_base_args(
        clone_url="https://x-access-token:token@github.com/test-owner/test-repo.git",
        new_branch="feature-branch",
        clone_dir="/tmp/test-owner/test-repo/pr-123",
    )
    with patch("services.git.create_empty_commit.run_subprocess") as mock_subprocess:
        # Commit fails
        mock_subprocess.side_effect = [
            ValueError("commit failed"),
        ]

        result = create_empty_commit(base_args_with_clone)

        assert result is False


def test_create_empty_commit_bails_on_non_fast_forward(create_test_base_args):
    """Reproduces AGENT-36Y/30K: a concurrent push (human or another GitAuto
    invocation) landed a commit on the branch while the agent loop was
    running. create_empty_commit runs at the tail of the handler, so we
    return False and let the remote state stand; no need to kill the whole
    invocation since no subsequent step will mutate the branch."""
    base_args_with_clone = create_test_base_args(
        clone_url="https://x-access-token:token@github.com/test-owner/test-repo.git",
        new_branch="gitauto/schedule-20260413-133550-Bk54",
        clone_dir="/tmp/test-owner/test-repo/pr-514",
    )
    with patch("services.git.create_empty_commit.run_subprocess") as mock_subprocess:
        reject_err = ValueError(
            "Command failed: To https://github.com/test-owner/test-repo.git\n"
            " ! [rejected]        HEAD -> gitauto/schedule-20260413-133550-Bk54 (fetch first)\n"
            "error: failed to push some refs to 'https://github.com/test-owner/test-repo.git'\n"
            "hint: Updates were rejected because the remote contains work that you do not\n"
            "hint: have locally."
        )
        mock_subprocess.side_effect = [
            None,  # commit
            reject_err,  # push (rejected)
        ]

        result = create_empty_commit(base_args_with_clone)

        assert result is False
        clone_dir = "/tmp/test-owner/test-repo/pr-514"
        clone_url = "https://x-access-token:token@github.com/test-owner/test-repo.git"
        branch = "gitauto/schedule-20260413-133550-Bk54"
        assert mock_subprocess.call_args_list == [
            call(
                args=[
                    "git",
                    "commit",
                    "--allow-empty",
                    "--no-verify",
                    "-m",
                    "Empty commit to trigger final tests",
                ],
                cwd=clone_dir,
            ),
            call(
                args=["git", "push", clone_url, f"HEAD:refs/heads/{branch}"],
                cwd=clone_dir,
            ),
        ]


def test_create_empty_commit_does_not_retry_on_non_race_failure(create_test_base_args):
    """A push failure that is not a non-fast-forward rejection should NOT trigger the
    fetch-and-retry path — we'd just paper over real issues (auth, network, etc.)."""
    base_args_with_clone = create_test_base_args(
        clone_url="https://x-access-token:token@github.com/test-owner/test-repo.git",
        new_branch="feature-branch",
        clone_dir="/tmp/test-owner/test-repo/pr-123",
    )
    with patch("services.git.create_empty_commit.run_subprocess") as mock_subprocess:
        mock_subprocess.side_effect = [
            None,  # commit
            ValueError("Command failed: fatal: Authentication failed"),  # push
        ]

        result = create_empty_commit(base_args_with_clone)

        assert result is False
        assert len(mock_subprocess.call_args_list) == 2


def test_create_empty_commit_custom_message(create_test_base_args):
    base_args_with_clone = create_test_base_args(
        clone_url="https://x-access-token:token@github.com/test-owner/test-repo.git",
        new_branch="feature-branch",
        clone_dir="/tmp/test-owner/test-repo/pr-123",
    )
    with patch("services.git.create_empty_commit.run_subprocess") as mock_subprocess:
        create_empty_commit(base_args_with_clone, message="Custom message")

        commit_call = mock_subprocess.call_args_list[0]
        assert commit_call == call(
            args=[
                "git",
                "commit",
                "--allow-empty",
                "--no-verify",
                "-m",
                "Custom message",
            ],
            cwd="/tmp/test-owner/test-repo/pr-123",
        )


# --- Integration tests (real git, local bare repo) ---


def _get_sha(work_dir: str, branch: str):
    result = subprocess.run(
        ["git", "rev-parse", branch],
        cwd=work_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


@pytest.mark.integration
def test_integration_create_empty_commit_with_clone(local_repo, create_test_base_args):
    bare_url, work_dir = local_repo
    sha_before = _get_sha(work_dir, "main")

    base_args = create_test_base_args(
        clone_url=bare_url,
        new_branch="main",
        clone_dir=work_dir,
    )
    result = create_empty_commit(base_args, message="Integration test empty commit")
    assert result is True

    subprocess.run(["git", "pull"], cwd=work_dir, check=True, capture_output=True)
    sha_after = _get_sha(work_dir, "main")
    assert sha_after != sha_before

    log_result = subprocess.run(
        ["git", "log", "-1", "--format=%s"],
        cwd=work_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    assert log_result.stdout.strip() == "Integration test empty commit"


@pytest.mark.integration
def test_integration_empty_commit_on_shallow_clone_with_new_branch(
    local_repo, tmp_path, create_test_base_args
):
    """Reproduces production failure: schedule_handler creates a remote branch from
    the latest SHA, then tries to push an empty commit from a shallow clone whose
    HEAD is on an old commit - causing non-fast-forward rejection."""
    bare_url, work_dir = local_repo

    # 1. Create a shallow clone (--depth 1)
    shallow_dir = str(tmp_path / "shallow")
    subprocess.run(
        ["git", "clone", "--depth", "1", bare_url, shallow_dir],
        check=True,
        capture_output=True,
    )
    # git_clone_to_tmp sets identity after clone; CI runners have no global git config
    subprocess.run(
        ["git", "config", "user.name", "test"],
        cwd=shallow_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=shallow_dir,
        check=True,
        capture_output=True,
    )

    # 2. Push a new commit to bare repo (simulates Foxquilt pushing code)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "new commit"],
        cwd=work_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "push", "origin", "main"],
        cwd=work_dir,
        check=True,
        capture_output=True,
    )

    # 3. Create a remote branch at the latest SHA (simulates create_remote_branch)
    latest_sha = subprocess.run(
        ["git", "ls-remote", bare_url, "refs/heads/main"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split("\t")[0]
    subprocess.run(
        ["git", "push", bare_url, f"{latest_sha}:refs/heads/gitauto/schedule-test"],
        cwd=work_dir,
        check=True,
        capture_output=True,
    )

    # 4. Fetch and checkout the new branch (like schedule_handler does)
    git_fetch(shallow_dir, bare_url, "gitauto/schedule-test")
    git_checkout(shallow_dir, "gitauto/schedule-test")

    # 5. Try empty commit from the shallow clone onto the new branch
    base_args = create_test_base_args(
        clone_url=bare_url,
        new_branch="gitauto/schedule-test",
        clone_dir=shallow_dir,
    )
    result = create_empty_commit(base_args, message="Initial empty commit [skip ci]")
    assert result is True


@pytest.mark.integration
def test_integration_empty_commit_races_with_concurrent_push(
    local_repo, tmp_path, create_test_base_args
):
    """Reproduces AGENT-36Y/30K: while our agent loop is running, another
    handler (or a human) pushes a commit to the same branch. create_empty_commit
    must bail rather than retrigger CI on their state — return False and leave
    their push as the remote tip."""
    bare_url, _ = local_repo

    # Our agent's working clone
    agent_dir = str(tmp_path / "agent")
    subprocess.run(
        ["git", "clone", bare_url, agent_dir], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "gitauto"],
        cwd=agent_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "gitauto@test.com"],
        cwd=agent_dir,
        check=True,
        capture_output=True,
    )

    # A concurrent handler (separate clone) pushes a commit to main after ours is
    # cloned but before our empty-commit push.
    concurrent_dir = str(tmp_path / "concurrent")
    subprocess.run(
        ["git", "clone", bare_url, concurrent_dir], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "other"],
        cwd=concurrent_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "other@test.com"],
        cwd=concurrent_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "racing commit"],
        cwd=concurrent_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "push", "origin", "main"],
        cwd=concurrent_dir,
        check=True,
        capture_output=True,
    )
    racing_sha = _get_sha(concurrent_dir, "HEAD")

    # Our agent tries an empty commit — push is rejected, create_empty_commit returns False so the caller can post an accurate comment.
    base_args = create_test_base_args(
        clone_url=bare_url,
        new_branch="main",
        clone_dir=agent_dir,
    )
    result = create_empty_commit(
        base_args, message="Empty commit to trigger final tests"
    )
    assert result is False

    # Remote head must still be the racing commit — we did not touch it.
    subprocess.run(["git", "fetch"], cwd=agent_dir, check=True, capture_output=True)
    remote_tip = _get_sha(agent_dir, "origin/main")
    assert remote_tip == racing_sha
