# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import subprocess

from unittest.mock import call, patch

import pytest

from services.git.create_empty_commit import create_empty_commit


@pytest.fixture
def base_args_with_clone(create_test_base_args):
    return create_test_base_args(
        clone_url="https://x-access-token:token@github.com/test-owner/test-repo.git",
        new_branch="feature-branch",
        clone_dir="/tmp/test-owner/test-repo/pr-123",
    )


@pytest.fixture
def base_args_without_clone(create_test_base_args):
    return create_test_base_args(
        clone_url="https://x-access-token:token@github.com/test-owner/test-repo.git",
        new_branch="feature-branch",
        clone_dir="",
    )


def test_create_empty_commit_with_clone_dir(base_args_with_clone):
    with patch(
        "services.git.create_empty_commit.run_subprocess"
    ) as mock_subprocess, patch(
        "services.git.create_empty_commit.os.path.isdir", return_value=True
    ) as _mock_isdir:  # noqa: F841
        result = create_empty_commit(base_args_with_clone)

        assert result is True
        clone_dir = "/tmp/test-owner/test-repo/pr-123"
        calls = mock_subprocess.call_args_list
        # First two calls are git config (user.name, user.email)
        assert calls[0][0][0][:3] == ["git", "config", "user.name"]
        assert calls[1][0][0][:3] == ["git", "config", "user.email"]
        assert calls[2] == call(
            args=[
                "git",
                "commit",
                "--allow-empty",
                "-m",
                "Empty commit to trigger final tests",
            ],
            cwd=clone_dir,
        )
        assert calls[3] == call(
            args=[
                "git",
                "push",
                "https://x-access-token:token@github.com/test-owner/test-repo.git",
                "HEAD:refs/heads/feature-branch",
            ],
            cwd=clone_dir,
        )


def test_create_empty_commit_without_clone_dir(base_args_without_clone):
    with patch(
        "services.git.create_empty_commit.run_subprocess"
    ) as mock_subprocess, patch(
        "services.git.create_empty_commit.tempfile.mkdtemp",
        return_value="/tmp/gitauto-tmp",
    ) as _mock_mkdtemp, patch(  # noqa: F841
        "services.git.create_empty_commit.shutil.rmtree"
    ) as mock_rmtree:
        result = create_empty_commit(base_args_without_clone)

        assert result is True
        # First call: clone
        assert mock_subprocess.call_args_list[0] == call(
            args=[
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                "feature-branch",
                "https://x-access-token:token@github.com/test-owner/test-repo.git",
                "/tmp/gitauto-tmp",
            ],
            cwd="/tmp",
        )
        # Cleanup temp dir
        mock_rmtree.assert_called_once_with("/tmp/gitauto-tmp", ignore_errors=True)


def test_create_empty_commit_failure(base_args_with_clone):
    with patch(
        "services.git.create_empty_commit.run_subprocess"
    ) as mock_subprocess, patch(
        "services.git.create_empty_commit.os.path.isdir", return_value=True
    ) as _mock_isdir:  # noqa: F841
        # Config succeeds, commit fails
        mock_subprocess.side_effect = [None, None, ValueError("commit failed")]

        result = create_empty_commit(base_args_with_clone)

        assert result is False


def test_create_empty_commit_custom_message(base_args_with_clone):
    with patch(
        "services.git.create_empty_commit.run_subprocess"
    ) as mock_subprocess, patch(
        "services.git.create_empty_commit.os.path.isdir", return_value=True
    ) as _mock_isdir:  # noqa: F841
        create_empty_commit(base_args_with_clone, message="Custom message")

        commit_call = mock_subprocess.call_args_list[2]
        assert commit_call == call(
            args=["git", "commit", "--allow-empty", "-m", "Custom message"],
            cwd="/tmp/test-owner/test-repo/pr-123",
        )


def test_create_empty_commit_temp_clone_cleanup_on_failure(base_args_without_clone):
    with patch(
        "services.git.create_empty_commit.run_subprocess"
    ) as mock_subprocess, patch(
        "services.git.create_empty_commit.tempfile.mkdtemp",
        return_value="/tmp/gitauto-tmp",
    ) as _mock_mkdtemp, patch(  # noqa: F841
        "services.git.create_empty_commit.shutil.rmtree"
    ) as mock_rmtree:
        # Clone succeeds, config succeeds, commit fails
        mock_subprocess.side_effect = [None, None, None, ValueError("commit failed")]

        result = create_empty_commit(base_args_without_clone)

        assert result is False
        # Temp dir should still be cleaned up
        mock_rmtree.assert_called_once_with("/tmp/gitauto-tmp", ignore_errors=True)


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
        clone_url=bare_url, new_branch="main", clone_dir=work_dir
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
def test_integration_create_empty_commit_without_clone(
    local_repo, create_test_base_args
):
    bare_url, work_dir = local_repo
    sha_before = _get_sha(work_dir, "main")

    base_args = create_test_base_args(
        clone_url=bare_url, new_branch="main", clone_dir=""
    )
    result = create_empty_commit(base_args, message="Temp clone test")
    assert result is True

    subprocess.run(["git", "pull"], cwd=work_dir, check=True, capture_output=True)
    sha_after = _get_sha(work_dir, "main")
    assert sha_after != sha_before
