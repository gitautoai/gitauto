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

    def test_returns_none_when_repo_disabled(self, mock_run_subprocess):
        """Sentry AGENT-30B and the cascade AGENT-3KQ/AGENT-3J5 (qenex-ai/metamask-extension): the customer disabled the repo, GitHub returns 403 with 'Repository ... is disabled. Please ask the owner to check their account.' Old behavior: ValueError propagated to @handle_exceptions and surfaced to Sentry every time the repo's webhook still fired. New behavior: catch the 'is disabled' marker, log info, return None — callers already treat None like an empty repo and skip the flow."""
        mock_run_subprocess.side_effect = ValueError(
            "Command failed: remote: Repository 'qenex-ai/metamask-extension' is disabled.\n"
            "remote: Please ask the owner to check their account.\n"
            "fatal: unable to access 'https://github.com/qenex-ai/metamask-extension.git/': The requested URL returned error: 403"
        )

        branch = get_default_branch(
            clone_url="https://github.com/qenex-ai/metamask-extension.git"
        )

        assert branch is None

    def test_re_raises_unrelated_value_error(self, mock_run_subprocess):
        """Negative case for the disabled-repo shortcut: any other ValueError (auth failure, DNS error, server-side issue) must NOT silently return None. Let it propagate so the @handle_exceptions decorator captures real outages."""
        mock_run_subprocess.side_effect = ValueError(
            "Command failed: fatal: Authentication failed"
        )

        with pytest.raises(ValueError, match="Authentication failed"):
            get_default_branch(clone_url="https://github.com/owner/repo.git")


# --- Integration tests (real git, local bare repo) ---


@pytest.mark.integration
def test_integration_get_default_branch_returns_main(local_repo):
    bare_url, _ = local_repo
    branch = get_default_branch(clone_url=bare_url)
    assert branch == "main"
