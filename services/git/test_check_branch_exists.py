# pylint: disable=unused-argument
from unittest.mock import MagicMock, patch

import pytest

from services.git.check_branch_exists import check_branch_exists


@pytest.fixture
def mock_run_subprocess():
    with patch("services.git.check_branch_exists.run_subprocess") as mock:
        yield mock


def test_check_branch_exists_returns_true_when_branch_exists(mock_run_subprocess):
    mock_result = MagicMock()
    mock_result.stdout = "abc123def456\trefs/heads/main\n"
    mock_run_subprocess.return_value = mock_result

    result = check_branch_exists(
        clone_url="https://x-access-token:token@github.com/owner/repo.git",
        branch_name="main",
    )

    assert result is True
    mock_run_subprocess.assert_called_once_with(
        args=[
            "git",
            "ls-remote",
            "--heads",
            "https://x-access-token:token@github.com/owner/repo.git",
            "refs/heads/main",
        ],
        cwd="/tmp",
    )


def test_check_branch_exists_returns_false_when_branch_not_found(mock_run_subprocess):
    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_run_subprocess.return_value = mock_result

    result = check_branch_exists(
        clone_url="https://x-access-token:token@github.com/owner/repo.git",
        branch_name="nonexistent",
    )

    assert result is False


@pytest.mark.parametrize("empty_value", ["", None, "   ", "\t", "\n"])
def test_check_branch_exists_returns_false_for_empty_branch_names(
    mock_run_subprocess, empty_value
):
    result = check_branch_exists(
        clone_url="https://x-access-token:token@github.com/owner/repo.git",
        branch_name=empty_value,
    )

    assert result is False
    mock_run_subprocess.assert_not_called()


def test_check_branch_exists_returns_false_on_error(mock_run_subprocess):
    mock_run_subprocess.side_effect = ValueError("Command failed: authentication error")

    result = check_branch_exists(
        clone_url="https://x-access-token:token@github.com/owner/repo.git",
        branch_name="main",
    )

    assert result is False


@pytest.mark.parametrize(
    "branch_name",
    [
        "main",
        "develop",
        "feature/new-feature",
        "hotfix/urgent-fix",
        "release/v1.0.0",
        "user/john/experimental",
        "123-numeric-branch",
    ],
)
def test_check_branch_exists_with_various_branch_names(
    mock_run_subprocess, branch_name
):
    mock_result = MagicMock()
    mock_result.stdout = f"abc123\trefs/heads/{branch_name}\n"
    mock_run_subprocess.return_value = mock_result

    result = check_branch_exists(
        clone_url="https://x-access-token:token@github.com/owner/repo.git",
        branch_name=branch_name,
    )

    assert result is True
    mock_run_subprocess.assert_called_once_with(
        args=[
            "git",
            "ls-remote",
            "--heads",
            "https://x-access-token:token@github.com/owner/repo.git",
            f"refs/heads/{branch_name}",
        ],
        cwd="/tmp",
    )


# --- Integration tests (real git, local bare repo) ---


@pytest.mark.integration
def test_integration_check_branch_exists_true(local_repo):
    bare_url, _ = local_repo
    assert check_branch_exists(clone_url=bare_url, branch_name="main") is True


@pytest.mark.integration
def test_integration_check_branch_exists_with_slash(local_repo):
    bare_url, _ = local_repo
    assert (
        check_branch_exists(clone_url=bare_url, branch_name="feature/test-branch")
        is True
    )


@pytest.mark.integration
def test_integration_check_branch_exists_false(local_repo):
    bare_url, _ = local_repo
    assert check_branch_exists(clone_url=bare_url, branch_name="nonexistent") is False
