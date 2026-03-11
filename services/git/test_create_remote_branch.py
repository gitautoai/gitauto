# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import subprocess
from typing import cast
from unittest.mock import patch

import pytest

from services.git.create_remote_branch import create_remote_branch
from services.types.base_args import BaseArgs


@pytest.fixture
def base_args(tmp_path):
    return cast(
        BaseArgs,
        {
            "owner": "test_owner",
            "repo": "test_repo",
            "clone_url": "https://x-access-token:tok@github.com/test_owner/test_repo.git",
            "new_branch": "gitauto/test-branch",
            "base_branch": "main",
            "clone_dir": str(tmp_path),
            "token": "tok",
        },
    )


class TestCreateRemoteBranch:
    @patch("services.git.create_remote_branch.run_subprocess")
    def test_pushes_sha_to_ref(self, mock_run, base_args):
        create_remote_branch(sha="abc123", base_args=base_args)

        mock_run.assert_called_once_with(
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
def test_integration_create_remote_branch(local_repo):
    bare_url, work_dir = local_repo
    sha = _get_sha(work_dir, "main")
    args = cast(
        BaseArgs,
        {
            "owner": "test",
            "repo": "test",
            "clone_url": bare_url,
            "new_branch": "gitauto/integration-test",
            "base_branch": "main",
            "clone_dir": work_dir,
            "token": "unused",
        },
    )

    create_remote_branch(sha=sha, base_args=args)

    assert _branch_exists_in_bare(bare_url, "gitauto/integration-test") is True
