# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import MagicMock, patch

import pytest

from services.git.get_latest_remote_commit_sha import get_latest_remote_commit_sha


def test_get_latest_remote_commit_sha_success(
    test_owner, test_repo, test_token, create_test_base_args
):
    base_args = create_test_base_args(
        owner=test_owner,
        repo=test_repo,
        token=test_token,
        base_branch="main",
    )
    mock_result = MagicMock()
    mock_result.stdout = "abc123def456789\trefs/heads/main\n"

    with patch(
        "services.git.get_latest_remote_commit_sha.run_subprocess"
    ) as mock_subprocess:
        mock_subprocess.return_value = mock_result

        result = get_latest_remote_commit_sha(
            "https://x-access-token:token@github.com/owner/repo.git", base_args
        )

        assert result == "abc123def456789"
        mock_subprocess.assert_called_once_with(
            args=[
                "git",
                "ls-remote",
                "https://x-access-token:token@github.com/owner/repo.git",
                f"refs/heads/{base_args['base_branch']}",
            ],
            cwd="/tmp",
        )


def test_get_latest_remote_commit_sha_empty_repository(
    test_owner, test_repo, test_token, create_test_base_args
):
    base_args = create_test_base_args(
        owner=test_owner,
        repo=test_repo,
        token=test_token,
        base_branch="main",
    )
    mock_result_empty = MagicMock()
    mock_result_empty.stdout = ""

    mock_result_success = MagicMock()
    mock_result_success.stdout = "new_commit_sha_123\trefs/heads/main\n"

    with patch(
        "services.git.get_latest_remote_commit_sha.run_subprocess"
    ) as mock_subprocess, patch(
        "services.git.get_latest_remote_commit_sha.initialize_repo"
    ) as mock_initialize, patch(
        "services.git.get_latest_remote_commit_sha.logger.info"
    ) as _mock_logger_info:  # noqa: F841
        mock_subprocess.side_effect = [mock_result_empty, mock_result_success]

        clone_url = "https://x-access-token:token@github.com/owner/repo.git"
        result = get_latest_remote_commit_sha(clone_url, base_args)

        expected_repo_path = f"/tmp/repo/{base_args['owner']}-{base_args['repo']}"
        mock_initialize.assert_called_once_with(
            repo_path=expected_repo_path,
            remote_url=clone_url,
            token=base_args["token"],
        )
        assert mock_subprocess.call_count == 2
        assert result == "new_commit_sha_123"


def test_get_latest_remote_commit_sha_network_error(
    test_owner, test_repo, test_token, create_test_base_args
):
    base_args = create_test_base_args(
        owner=test_owner,
        repo=test_repo,
        token=test_token,
        base_branch="main",
    )
    with patch(
        "services.git.get_latest_remote_commit_sha.run_subprocess"
    ) as mock_subprocess, patch(
        "services.git.get_latest_remote_commit_sha.update_comment"
    ) as _mock_update_comment:  # noqa: F841
        mock_subprocess.side_effect = ValueError("Command failed: network error")

        with pytest.raises(RuntimeError) as exc_info:
            get_latest_remote_commit_sha(
                "https://x-access-token:token@github.com/owner/repo.git", base_args
            )

        assert (
            "Error: Could not get the latest commit SHA in get_latest_remote_commit_sha"
            in str(exc_info.value)
        )


@pytest.mark.parametrize(
    "branch_name",
    [
        "main",
        "develop",
        "feature/new-feature",
        "hotfix/bug-fix",
        "release/v1.0.0",
    ],
)
def test_get_latest_remote_commit_sha_various_branch_names(
    test_owner, test_repo, test_token, branch_name, create_test_base_args
):
    mock_result = MagicMock()
    mock_result.stdout = f"abc123def456\trefs/heads/{branch_name}\n"

    with patch(
        "services.git.get_latest_remote_commit_sha.run_subprocess"
    ) as mock_subprocess:
        mock_subprocess.return_value = mock_result

        custom_base_args = create_test_base_args(
            owner=test_owner,
            repo=test_repo,
            token=test_token,
            base_branch=branch_name,
        )

        result = get_latest_remote_commit_sha(
            "https://x-access-token:token@github.com/owner/repo.git",
            custom_base_args,
        )

        assert result == "abc123def456"
        mock_subprocess.assert_called_once_with(
            args=[
                "git",
                "ls-remote",
                "https://x-access-token:token@github.com/owner/repo.git",
                f"refs/heads/{branch_name}",
            ],
            cwd="/tmp",
        )


def test_get_latest_remote_commit_sha_recursive_call_failure(
    test_owner, test_repo, test_token, create_test_base_args
):
    base_args = create_test_base_args(
        owner=test_owner,
        repo=test_repo,
        token=test_token,
        base_branch="main",
    )
    mock_result_empty = MagicMock()
    mock_result_empty.stdout = ""

    with patch(
        "services.git.get_latest_remote_commit_sha.run_subprocess"
    ) as mock_subprocess, patch(
        "services.git.get_latest_remote_commit_sha.initialize_repo"
    ) as _mock_initialize, patch(  # noqa: F841
        "services.git.get_latest_remote_commit_sha.update_comment"
    ) as _mock_update_comment:  # noqa: F841
        # First call returns empty, second call fails
        mock_subprocess.side_effect = [
            mock_result_empty,
            ValueError("Command failed: network error on retry"),
        ]

        clone_url = "https://x-access-token:token@github.com/owner/repo.git"

        with pytest.raises(RuntimeError) as exc_info:
            get_latest_remote_commit_sha(clone_url, base_args)

        assert (
            "Error: Could not get the latest commit SHA in get_latest_remote_commit_sha"
            in str(exc_info.value)
        )
        assert mock_subprocess.call_count == 2
