# pylint: disable=unused-argument
from unittest.mock import patch

import pytest

from services.git.check_branch_exists import check_branch_exists
from services.git.delete_remote_branch import delete_remote_branch


@pytest.fixture
def base_args(create_test_base_args):
    return create_test_base_args(
        clone_url="https://x-access-token:token@github.com/test-owner/test-repo.git",
        new_branch="feature-branch",
        clone_dir="/tmp/test-owner/test-repo/pr-123",
    )


def test_delete_remote_branch_success(base_args):
    with patch("services.git.delete_remote_branch.run_subprocess") as mock_subprocess:
        result = delete_remote_branch(base_args)

        assert result is True
        mock_subprocess.assert_called_once_with(
            args=[
                "git",
                "push",
                "https://x-access-token:token@github.com/test-owner/test-repo.git",
                "--delete",
                "feature-branch",
            ],
            cwd="/tmp/test-owner/test-repo/pr-123",
        )


def test_delete_remote_branch_failure(base_args):
    with patch("services.git.delete_remote_branch.run_subprocess") as mock_subprocess:
        mock_subprocess.side_effect = ValueError("Command failed: branch not found")

        result = delete_remote_branch(base_args)

        assert result is False


def test_delete_remote_branch_uses_correct_branch(create_test_base_args):
    args = create_test_base_args(
        clone_url="https://x-access-token:token@github.com/owner/repo.git",
        new_branch="gitauto/issue-42",
        clone_dir="/tmp/owner/repo/pr-42",
    )

    with patch("services.git.delete_remote_branch.run_subprocess") as mock_subprocess:
        delete_remote_branch(args)

        mock_subprocess.assert_called_once_with(
            args=[
                "git",
                "push",
                "https://x-access-token:token@github.com/owner/repo.git",
                "--delete",
                "gitauto/issue-42",
            ],
            cwd="/tmp/owner/repo/pr-42",
        )


# --- Integration tests (real git, local bare repo) ---


@pytest.mark.integration
def test_integration_delete_remote_branch(local_repo, create_test_base_args):
    bare_url, work_dir = local_repo
    assert (
        check_branch_exists(clone_url=bare_url, branch_name="feature/test-branch")
        is True
    )

    base_args = create_test_base_args(
        clone_url=bare_url,
        new_branch="feature/test-branch",
        clone_dir=work_dir,
    )
    result = delete_remote_branch(base_args)
    assert result is True
    assert (
        check_branch_exists(clone_url=bare_url, branch_name="feature/test-branch")
        is False
    )
