import pytest
from unittest.mock import patch

from services.github.github_utils import deconstruct_github_payload
from services.github.github_types import GitHubLabeledPayload
from tests.constants import OWNER, REPO, INSTALLATION_ID, TOKEN
from config import PRODUCT_ID, ISSUE_NUMBER_FORMAT


class TestDeconstructGitHubPayloadIntegration:
    """Integration tests for deconstruct_github_payload function."""

    def create_real_payload(self) -> GitHubLabeledPayload:
        """Create a realistic GitHub payload for integration testing."""
        return {
            "action": "labeled",
            "issue": {
                "number": 999,
                "title": "Integration Test Issue",
                "body": "This is a test issue for integration testing with https://github.com/example/repo",
                "user": {"login": "test-integration-user"}
            },
            "repository": {
                "id": 123456789,
                "name": REPO,
                "clone_url": f"https://github.com/{OWNER}/{REPO}.git",
                "fork": False,
                "default_branch": "main",
                "owner": {
                    "type": "Organization",
                    "login": OWNER,
                    "id": 159883862
                }
            },
            "installation": {"id": INSTALLATION_ID},
            "sender": {
                "id": 12345,
                "login": "integration-test-sender"
            },
            "label": {"name": "test-label"},
            "organization": {"login": OWNER}
        }

    @patch('services.github.github_utils.get_installation_access_token')
    def test_integration_deconstruct_github_payload_with_real_dependencies(
        self, mock_get_installation_access_token
    ):
        """Integration test with real dependencies (mocking only the token)."""
        # Arrange
        payload = self.create_real_payload()
        mock_get_installation_access_token.return_value = TOKEN

        # Act
        result = deconstruct_github_payload(payload)

        # Assert basic structure
        assert isinstance(result, dict)
        assert result["input_from"] == "github"
        assert result["owner_type"] == "Organization"
        assert result["owner"] == OWNER
        assert result["repo"] == REPO
        assert result["issue_number"] == 999
        assert result["issue_title"] == "Integration Test Issue"
        assert result["installation_id"] == INSTALLATION_ID
        assert result["token"] == TOKEN
        assert result["sender_name"] == "integration-test-sender"
        assert result["issuer_name"] == "test-integration-user"
        
        # Check that branch name follows expected format
        assert result["new_branch"].startswith(f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}999-")
        assert len(result["new_branch"].split("-")) == 4  # product/issue-number-date-time-random
        
        # Check URL extraction worked
        assert "https://github.com/example/repo" in result["github_urls"]
        
        # Check reviewers (should exclude bots)
        assert "integration-test-sender" in result["reviewers"]
        assert "test-integration-user" in result["reviewers"]
        assert len(result["reviewers"]) == 2

    def test_integration_create_permission_url_formats(self):
        """Integration test for permission URL creation with various inputs."""
        from services.github.github_utils import create_permission_url
        
        # Test Organization URL
        org_url = create_permission_url("Organization", "test-org", 12345)
        assert org_url == "https://github.com/organizations/test-org/settings/installations/12345/permissions/update"
        
        # Test User URL
        user_url = create_permission_url("User", "test-user", 67890)
        assert user_url == "https://github.com/settings/installations/67890/permissions/update"
