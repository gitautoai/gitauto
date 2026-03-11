# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import patch, MagicMock

import pytest

from services.git.get_default_branch import get_default_branch


@pytest.fixture
def mock_run_subprocess():
    with patch("services.git.get_default_branch.run_subprocess") as mock:
        yield mock


class TestGetDefaultBranch:
    def test_returns_default_branch_main(self, mock_run_subprocess):
        result = MagicMock()
        result.stdout = "ref: refs/heads/main\tHEAD\nabc123\tHEAD\n"
        mock_run_subprocess.return_value = result

        branch = get_default_branch(clone_url="https://github.com/owner/repo.git")

        assert branch == "main"

    def test_returns_default_branch_develop(self, mock_run_subprocess):
        result = MagicMock()
        result.stdout = "ref: refs/heads/develop\tHEAD\nabc123\tHEAD\n"
        mock_run_subprocess.return_value = result

        branch = get_default_branch(clone_url="https://github.com/owner/repo.git")

        assert branch == "develop"

    def test_returns_none_for_empty_repo(self, mock_run_subprocess):
        result = MagicMock()
        result.stdout = ""
        mock_run_subprocess.return_value = result

        branch = get_default_branch(clone_url="https://github.com/owner/repo.git")

        assert branch is None

    def test_returns_none_for_no_output(self, mock_run_subprocess):
        result = MagicMock()
        result.stdout = None
        mock_run_subprocess.return_value = result

        branch = get_default_branch(clone_url="https://github.com/owner/repo.git")

        assert branch is None

    def test_fallback_to_main_when_no_symref_line(self, mock_run_subprocess):
        result = MagicMock()
        result.stdout = "abc123\tHEAD\n"
        mock_run_subprocess.return_value = result

        branch = get_default_branch(clone_url="https://github.com/owner/repo.git")

        assert branch == "main"

    def test_calls_git_ls_remote(self, mock_run_subprocess):
        result = MagicMock()
        result.stdout = "ref: refs/heads/main\tHEAD\nabc123\tHEAD\n"
        mock_run_subprocess.return_value = result

        get_default_branch(clone_url="https://example.com/repo.git")

        mock_run_subprocess.assert_called_once_with(
            args=[
                "git",
                "ls-remote",
                "--symref",
                "https://example.com/repo.git",
                "HEAD",
            ],
            cwd="/tmp",
        )

    def test_handles_branch_with_slashes(self, mock_run_subprocess):
        result = MagicMock()
        result.stdout = "ref: refs/heads/release/v2\tHEAD\nabc123\tHEAD\n"
        mock_run_subprocess.return_value = result

        branch = get_default_branch(clone_url="https://github.com/owner/repo.git")

        assert branch == "release/v2"


# --- Integration tests (real git, local bare repo) ---


@pytest.mark.integration
def test_integration_get_default_branch_returns_main(local_repo):
    bare_url, _ = local_repo
    branch = get_default_branch(clone_url=bare_url)
    assert branch == "main"
