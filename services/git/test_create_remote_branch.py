# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import subprocess
from unittest.mock import patch

import pytest

from services.git.create_remote_branch import create_remote_branch


class TestCreateRemoteBranch:
    @patch("services.git.create_remote_branch.run_subprocess")
    def test_fetches_then_pushes(self, mock_run, create_test_base_args, tmp_path):
        base_args = create_test_base_args(
            owner="test_owner",
            repo="test_repo",
            clone_url="https://x-access-token:tok@github.com/test_owner/test_repo.git",
            new_branch="gitauto/test-branch",
            clone_dir=str(tmp_path),
            token="tok",
        )
        create_remote_branch(sha="abc123", base_args=base_args)

        assert mock_run.call_count == 2
        mock_run.assert_any_call(
            args=[
                "git",
                "fetch",
                "https://x-access-token:tok@github.com/test_owner/test_repo.git",
                "main",
            ],
            cwd=base_args["clone_dir"],
        )
        mock_run.assert_any_call(
            args=[
                "git",
                "push",
                "https://x-access-token:tok@github.com/test_owner/test_repo.git",
                "abc123:refs/heads/gitauto/test-branch",
            ],
            cwd=base_args["clone_dir"],
        )


# --- Integration tests (real git, local bare repo) ---


def _get_sha(work_dir: str, ref: str):
    result = subprocess.run(
        ["git", "rev-parse", ref],
        cwd=work_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _branch_exists_in_bare(bare_url: str, branch: str):
    result = subprocess.run(
        ["git", "ls-remote", "--heads", bare_url, f"refs/heads/{branch}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


@pytest.mark.integration
def test_integration_create_remote_branch(local_repo, create_test_base_args):
    bare_url, work_dir = local_repo
    sha = _get_sha(work_dir, "main")
    args = create_test_base_args(
        owner="test",
        repo="test",
        clone_url=bare_url,
        new_branch="gitauto/integration-test",
        clone_dir=work_dir,
        token="unused",
    )

    create_remote_branch(sha=sha, base_args=args)

    assert _branch_exists_in_bare(bare_url, "gitauto/integration-test") is True


@pytest.mark.integration
def test_integration_shallow_clone_missing_sha(
    local_repo, tmp_path, create_test_base_args
):
    """Reproduces production failure: shallow repo (--depth 1) doesn't
    have the latest SHA that was pushed to the remote after the shallow clone."""
    bare_url, work_dir = local_repo

    # 1. Create a shallow clone (--depth 1)
    shallow_dir = str(tmp_path / "shallow")
    subprocess.run(
        ["git", "clone", "--depth", "1", bare_url, shallow_dir],
        check=True,
        capture_output=True,
    )

    # 2. Push a new commit to the bare repo from work_dir (simulates Foxquilt pushing code)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "new commit after shallow clone"],
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

    # 3. Get the latest SHA from the remote (simulates get_latest_remote_commit_sha)
    latest_sha = subprocess.run(
        ["git", "ls-remote", bare_url, "refs/heads/main"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split("\t")[0]

    # 4. Try to create a branch from the shallow clone using the new SHA
    args = create_test_base_args(
        owner="test",
        repo="test",
        clone_url=bare_url,
        new_branch="gitauto/shallow-test",
        clone_dir=shallow_dir,
        token="unused",
    )

    create_remote_branch(sha=latest_sha, base_args=args)

    assert _branch_exists_in_bare(bare_url, "gitauto/shallow-test") is True
