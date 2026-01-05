from typing import cast
from unittest.mock import patch

from services.github.types.github_types import GitHubInstallationRepositoriesPayload
from services.webhook.handle_installation_repos_removed import (
    handle_installation_repos_removed,
)


def test_handle_installation_repos_removed_cleans_up_efs():
    payload = {
        "installation": {"id": 123, "account": {"login": "test-owner"}},
        "repositories_removed": [{"name": "repo1"}, {"name": "repo2"}],
    }

    with patch(
        "services.webhook.handle_installation_repos_removed.is_installation_valid"
    ) as mock_valid:
        with patch(
            "services.webhook.handle_installation_repos_removed.cleanup_repo_efs"
        ) as mock_cleanup:
            mock_valid.return_value = True

            handle_installation_repos_removed(
                cast(GitHubInstallationRepositoriesPayload, payload)
            )

            assert mock_cleanup.call_count == 2
            mock_cleanup.assert_any_call(owner="test-owner", repo="repo1")
            mock_cleanup.assert_any_call(owner="test-owner", repo="repo2")


def test_handle_installation_repos_removed_skips_invalid_installation():
    payload = {
        "installation": {"id": 123, "account": {"login": "test-owner"}},
        "repositories_removed": [{"name": "repo1"}],
    }

    with patch(
        "services.webhook.handle_installation_repos_removed.is_installation_valid"
    ) as mock_valid:
        with patch(
            "services.webhook.handle_installation_repos_removed.cleanup_repo_efs"
        ) as mock_cleanup:
            mock_valid.return_value = False

            handle_installation_repos_removed(
                cast(GitHubInstallationRepositoriesPayload, payload)
            )

            mock_cleanup.assert_not_called()
