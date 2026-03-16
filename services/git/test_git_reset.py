from unittest.mock import patch

from services.git.git_reset import git_reset


def test_git_reset_success():
    with patch("services.git.git_reset.run_subprocess") as mock_run, patch(
        "services.git.git_reset.resolve_git_locks"
    ):
        result = git_reset("/tmp/repo")

        assert result is True
        assert mock_run.call_count == 1


def test_git_reset_calls_resolve_git_locks():
    with patch("services.git.git_reset.run_subprocess"), patch(
        "services.git.git_reset.resolve_git_locks"
    ) as mock_clear:
        result = git_reset("/tmp/repo")

        assert result is True
        mock_clear.assert_called_once_with("/tmp/repo/.git")
