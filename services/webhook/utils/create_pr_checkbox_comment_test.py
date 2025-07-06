import pytest
from unittest.mock import patch

from services.webhook.utils.create_pr_checkbox_comment import create_pr_checkbox_comment


class TestCreatePrCheckboxComment:
    """Test cases for create_pr_checkbox_comment function."""

    @patch("services.webhook.utils.create_pr_checkbox_comment.get_repository")
    def test_skips_bot_users(self, mock_get_repository):
        """Test that the function skips processing for bot users."""
        payload = {
            "pull_request": {
                "number": 123,
                "url": "https://api.github.com/repos/owner/repo/pulls/123",
                "head": {"ref": "feature-branch"},
            },
            "sender": {"login": "dependabot[bot]"},
            "repository": {
                "id": 456,
                "name": "test-repo",
                "owner": {
                    "id": 789,
                    "type": "Organization",
                    "login": "test-owner",
                },
            },
            "installation": {"id": 101112},
        }
        
        result = create_pr_checkbox_comment(payload)
        
        assert result is None
        # Verify that no further processing was done
        mock_get_repository.assert_not_called()

    @patch("services.webhook.utils.create_pr_checkbox_comment.get_installation_access_token")
    @patch("services.webhook.utils.create_pr_checkbox_comment.get_repository")
    def test_skips_when_trigger_disabled(self, mock_get_repository, mock_get_token):
        """Test that the function skips processing when trigger_on_pr_change is disabled."""
        mock_get_repository.return_value = {"trigger_on_pr_change": False}
        
        payload = {
            "pull_request": {
                "number": 123,
                "url": "https://api.github.com/repos/owner/repo/pulls/123",
                "head": {"ref": "feature-branch"},
            },
            "sender": {"login": "test-user"},
            "repository": {
                "id": 456,
                "name": "test-repo",
                "owner": {
                    "id": 789,
                    "type": "Organization",
                    "login": "test-owner",
                },
            },
            "installation": {"id": 101112},
        }
        
        result = create_pr_checkbox_comment(payload)
        
        assert result is None
        mock_get_repository.assert_called_once_with(repo_id=456)
        # Verify that no further processing was done
        mock_get_token.assert_not_called()