# pylint: disable=unused-argument
import subprocess

from unittest.mock import MagicMock, patch

import pytest

from services.git.get_branch_head import get_branch_head


def test_get_branch_head_returns_sha():
    mock_result = MagicMock()
    mock_result.stdout = "abc1234567890def\trefs/heads/main\n"

    with patch("services.git.get_branch_head.run_subprocess") as mock_subprocess:
        mock_subprocess.return_value = mock_result

        result = get_branch_head(
            clone_url="https://x-access-token:token@github.com/owner/repo.git",
            branch="main",
        )

        assert result == "abc1234567890def"
        mock_subprocess.assert_called_once_with(
            args=[
                "git",
                "ls-remote",
                "https://x-access-token:token@github.com/owner/repo.git",
                "refs/heads/main",
            ],
            cwd="/tmp",
        )


def test_get_branch_head_returns_none_when_branch_not_found():
    mock_result = MagicMock()
    mock_result.stdout = ""

    with patch("services.git.get_branch_head.run_subprocess") as mock_subprocess:
        mock_subprocess.return_value = mock_result

        result = get_branch_head(
            clone_url="https://x-access-token:token@github.com/owner/repo.git",
            branch="nonexistent",
        )

        assert result is None


def test_get_branch_head_returns_none_on_error():
    with patch("services.git.get_branch_head.run_subprocess") as mock_subprocess:
        mock_subprocess.side_effect = ValueError("Command failed")

        result = get_branch_head(
            clone_url="https://x-access-token:token@github.com/owner/repo.git",
            branch="main",
        )

        assert result is None


def test_get_branch_head_logs_sha():
    mock_result = MagicMock()
    mock_result.stdout = "deadbeef12345678\trefs/heads/develop\n"

    with patch("services.git.get_branch_head.run_subprocess") as mock_subprocess, patch(
        "services.git.get_branch_head.logger"
    ) as mock_logger:
        mock_subprocess.return_value = mock_result

        result = get_branch_head(
            clone_url="https://x-access-token:token@github.com/owner/repo.git",
            branch="develop",
        )

        assert result == "deadbeef12345678"
        mock_logger.info.assert_called_once_with(
            "Branch %s head SHA: %s", "develop", "deadbeef12345678"
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
def test_integration_get_branch_head_returns_correct_sha(local_repo):
    bare_url, work_dir = local_repo
    expected_sha = _get_sha(work_dir, "main")
    result = get_branch_head(clone_url=bare_url, branch="main")
    assert result is not None
    assert result == expected_sha
    assert len(result) == 40
    assert all(c in "0123456789abcdef" for c in result)


@pytest.mark.integration
def test_integration_get_branch_head_nonexistent(local_repo):
    bare_url, _ = local_repo
    assert get_branch_head(clone_url=bare_url, branch="nonexistent") is None
