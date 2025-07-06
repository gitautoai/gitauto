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

    @patch("services.webhook.utils.create_pr_checkbox_comment.get_repository")
    def test_skips_when_no_repo_settings(self, mock_get_repository):
        """Test that the function skips processing when repository settings are not found."""
        mock_get_repository.return_value = None
        
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

    @patch("services.webhook.utils.create_pr_checkbox_comment.get_coverages")
    @patch("services.webhook.utils.create_pr_checkbox_comment.is_code_file")
    @patch("services.webhook.utils.create_pr_checkbox_comment.get_pull_request_files")
    @patch("services.webhook.utils.create_pr_checkbox_comment.get_installation_access_token")
    @patch("services.webhook.utils.create_pr_checkbox_comment.get_repository")
    def test_skips_when_no_code_files_changed(self, mock_get_repository, mock_get_token, 
                                            mock_get_files, mock_is_code_file, mock_get_coverages):
        """Test that the function skips processing when no code files were changed."""
        mock_get_repository.return_value = {"trigger_on_pr_change": True}
        mock_get_token.return_value = "mock_token"
        mock_get_files.return_value = [
            {"filename": "README.md", "status": "modified"},
            {"filename": "docs/guide.txt", "status": "added"},
        ]
        mock_is_code_file.return_value = False
        
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
        # Verify that coverage data was not fetched
        mock_get_coverages.assert_not_called()

    @patch("services.webhook.utils.create_pr_checkbox_comment.get_repository")
    def test_different_bot_name_patterns(self, mock_get_repository):
        """Test that different bot name patterns are correctly identified."""
        bot_names = [
            "dependabot[bot]",
            "github-actions[bot]",
            "renovate[bot]",
            "codecov[bot]",
            "custom-bot[bot]",
        ]
        
        for bot_name in bot_names:
            payload = {
                "pull_request": {
                    "number": 123,
                    "url": "https://api.github.com/repos/owner/repo/pulls/123",
                    "head": {"ref": "feature-branch"},
                },
                "sender": {"login": bot_name},
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
            # Reset mock for next iteration
            mock_get_repository.reset_mock()
