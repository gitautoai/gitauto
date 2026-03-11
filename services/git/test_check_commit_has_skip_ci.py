# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from services.git.check_commit_has_skip_ci import check_commit_has_skip_ci


@pytest.fixture
def mock_run_subprocess():
    with patch("services.git.check_commit_has_skip_ci.run_subprocess") as mock:
        yield mock


class TestCheckCommitHasSkipCi:
    def test_returns_true_when_skip_ci_present(self, mock_run_subprocess):
        result = MagicMock()
        result.stdout = "Initial empty commit to create PR [skip ci]\n"
        mock_run_subprocess.return_value = result

        assert (
            check_commit_has_skip_ci(
                commit_sha="abc123",
                clone_dir="/mnt/efs/owner/repo",
            )
            is True
        )

    def test_returns_false_when_no_skip_ci(self, mock_run_subprocess):
        result = MagicMock()
        result.stdout = "Add feature X\n"
        mock_run_subprocess.return_value = result

        assert (
            check_commit_has_skip_ci(
                commit_sha="abc123",
                clone_dir="/mnt/efs/owner/repo",
            )
            is False
        )

    def test_fetches_commit_first(self, mock_run_subprocess):
        result = MagicMock()
        result.stdout = "Some commit\n"
        mock_run_subprocess.return_value = result

        check_commit_has_skip_ci(
            commit_sha="abc123",
            clone_dir="/mnt/efs/owner/repo",
        )

        # First call should be git fetch
        fetch_call = mock_run_subprocess.call_args_list[0]
        assert fetch_call[1]["args"] == ["git", "fetch", "origin", "abc123"]


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


@pytest.mark.integration
def test_integration_skip_ci_commit_detected(local_repo):
    _, work_dir = local_repo
    # HEAD on main is the [skip ci] commit
    sha = _get_sha(work_dir, "HEAD")
    assert check_commit_has_skip_ci(commit_sha=sha, clone_dir=work_dir) is True


@pytest.mark.integration
def test_integration_normal_commit_not_detected(local_repo):
    _, work_dir = local_repo
    # HEAD~1 is "Add source files" (no [skip ci])
    sha = _get_sha(work_dir, "HEAD~1")
    assert check_commit_has_skip_ci(commit_sha=sha, clone_dir=work_dir) is False
