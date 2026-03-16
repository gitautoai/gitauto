from unittest.mock import patch

from services.git.git_checkout import git_checkout


def test_git_checkout_success():
    with patch("services.git.git_checkout.run_subprocess") as mock_run:
        result = git_checkout("/tmp/repo", "feature-branch")

        assert result is True
        mock_run.assert_called_once_with(
            ["git", "checkout", "-f", "-B", "feature-branch", "FETCH_HEAD"],
            "/tmp/repo",
        )
