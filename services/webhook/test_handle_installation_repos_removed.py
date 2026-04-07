from typing import cast
from unittest.mock import patch

from services.github.types.github_types import InstallationRepositoriesPayload
from services.webhook.handle_installation_repos_removed import (
    handle_installation_repos_removed,
)

MODULE = "services.webhook.handle_installation_repos_removed"


def test_cleans_up_s3_and_efs():
    payload = {
        "installation": {"id": 123, "account": {"login": "test-owner"}},
        "repositories_removed": [{"name": "repo1"}, {"name": "repo2"}],
    }

    with patch(f"{MODULE}.is_installation_valid") as mock_valid:
        with patch(f"{MODULE}.cleanup_s3_deps") as mock_s3:
            with patch(f"{MODULE}.cleanup_repo_efs") as mock_efs:
                mock_valid.return_value = True

                handle_installation_repos_removed(
                    cast(InstallationRepositoriesPayload, payload)
                )

                assert mock_s3.call_count == 2
                assert mock_efs.call_count == 2
                mock_s3.assert_any_call(owner="test-owner", repo="repo1")
                mock_efs.assert_any_call(owner="test-owner", repo="repo1")


def test_skips_invalid_installation():
    payload = {
        "installation": {"id": 123, "account": {"login": "test-owner"}},
        "repositories_removed": [{"name": "repo1"}],
    }

    with patch(f"{MODULE}.is_installation_valid") as mock_valid:
        with patch(f"{MODULE}.cleanup_s3_deps") as mock_s3:
            with patch(f"{MODULE}.cleanup_repo_efs") as mock_efs:
                mock_valid.return_value = False

                handle_installation_repos_removed(
                    cast(InstallationRepositoriesPayload, payload)
                )

                mock_s3.assert_not_called()
                mock_efs.assert_not_called()
