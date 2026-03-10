# pylint: disable=unused-argument
import subprocess

from unittest.mock import MagicMock, patch

import pytest

from services.git.get_reference import get_reference


@pytest.fixture
def mock_run_subprocess():
    with patch("services.git.get_reference.run_subprocess") as mock:
        yield mock


def test_get_reference_success(mock_run_subprocess):
    mock_result = MagicMock()
    mock_result.stdout = "abc123def456\trefs/heads/test-branch\n"
    mock_run_subprocess.return_value = mock_result

    result = get_reference(
        clone_url="https://x-access-token:token@github.com/owner/repo.git",
        branch="test-branch",
    )

    assert result == "abc123def456"
    mock_run_subprocess.assert_called_once_with(
        args=[
            "git",
            "ls-remote",
            "https://x-access-token:token@github.com/owner/repo.git",
            "refs/heads/test-branch",
        ],
        cwd="/tmp",
    )


def test_get_reference_returns_none_when_not_found(mock_run_subprocess):
    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_run_subprocess.return_value = mock_result

    result = get_reference(
        clone_url="https://x-access-token:token@github.com/owner/repo.git",
        branch="nonexistent",
    )

    assert result is None


def test_get_reference_returns_none_on_error(mock_run_subprocess):
    mock_run_subprocess.side_effect = ValueError("Command failed")

    result = get_reference(
        clone_url="https://x-access-token:token@github.com/owner/repo.git",
        branch="test-branch",
    )

    assert result is None


@pytest.mark.parametrize(
    "branch_name",
    [
        "main",
        "feature/new-feature",
        "bugfix-123",
        "release/v1.0.0",
        "hotfix_urgent_fix",
    ],
)
def test_get_reference_with_different_branch_names(mock_run_subprocess, branch_name):
    mock_result = MagicMock()
    mock_result.stdout = f"abc123def456\trefs/heads/{branch_name}\n"
    mock_run_subprocess.return_value = mock_result

    result = get_reference(
        clone_url="https://x-access-token:token@github.com/owner/repo.git",
        branch=branch_name,
    )

    assert result == "abc123def456"
    mock_run_subprocess.assert_called_once_with(
        args=[
            "git",
            "ls-remote",
            "https://x-access-token:token@github.com/owner/repo.git",
            f"refs/heads/{branch_name}",
        ],
        cwd="/tmp",
    )


def test_get_reference_returns_string_sha(mock_run_subprocess):
    mock_result = MagicMock()
    mock_result.stdout = "1234567890abcdef\trefs/heads/main\n"
    mock_run_subprocess.return_value = mock_result

    result = get_reference(
        clone_url="https://x-access-token:token@github.com/owner/repo.git",
        branch="main",
    )

    assert result == "1234567890abcdef"
    assert isinstance(result, str)


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
def test_integration_get_reference_returns_correct_sha(local_repo):
    bare_url, work_dir = local_repo
    expected_sha = _get_sha(work_dir, "feature/test-branch")
    result = get_reference(clone_url=bare_url, branch="feature/test-branch")
    assert result == expected_sha


@pytest.mark.integration
def test_integration_get_reference_nonexistent(local_repo):
    bare_url, _ = local_repo
    assert get_reference(clone_url=bare_url, branch="nonexistent") is None
