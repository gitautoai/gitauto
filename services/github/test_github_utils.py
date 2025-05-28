import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from services.github.github_utils import create_permission_url, deconstruct_github_payload
from services.github.github_types import GitHubLabeledPayload
from config import PRODUCT_ID, ISSUE_NUMBER_FORMAT, GITHUB_APP_USER_ID


class TestCreatePermissionUrl:
    """Test cases for create_permission_url function."""

    def test_create_permission_url_organization(self):
        """Test creating permission URL for organization."""
        # Arrange
        owner_type = "Organization"
        owner_name = "test-org"
        installation_id = 12345

        # Act
        result = create_permission_url(owner_type, owner_name, installation_id)

        # Assert
        expected = "https://github.com/organizations/test-org/settings/installations/12345/permissions/update"
        assert result == expected

    def test_create_permission_url_user(self):
        """Test creating permission URL for user."""
        # Arrange
        owner_type = "User"
        owner_name = "test-user"
        installation_id = 67890

        # Act
        result = create_permission_url(owner_type, owner_name, installation_id)

        # Assert
        expected = "https://github.com/settings/installations/67890/permissions/update"
        assert result == expected

    def test_create_permission_url_different_installation_ids(self):
        """Test creating permission URLs with different installation IDs."""
        # Test Organization
        org_result = create_permission_url("Organization", "org", 111)
        assert "111" in org_result
        assert "organizations/org" in org_result

        # Test User
        user_result = create_permission_url("User", "user", 222)
        assert "222" in user_result
        assert "organizations" not in user_result


class TestDeconstructGitHubPayload:
    """Test cases for deconstruct_github_payload function."""

    def create_mock_payload(self, **overrides) -> GitHubLabeledPayload:
        """Create a mock GitHub payload with default values."""
        default_payload = {
            "action": "labeled",
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test issue body with https://github.com/test/repo and http://example.com",
                "user": {"login": "test-user"}
            },
            "repository": {
                "id": 456,
                "name": "test-repo",
                "clone_url": "https://github.com/test-owner/test-repo.git",
                "fork": False,
                "default_branch": "main",
                "owner": {
                    "type": "Organization",
                    "login": "test-owner",
                    "id": 789
                }
            },
            "installation": {"id": 12345},
            "sender": {
                "id": 999,
                "login": "sender-user"
            },
            "label": {"name": "test-label"},
            "organization": {"login": "test-org"}
        }
        
        # Apply overrides
        for key, value in overrides.items():
            if "." in key:
                # Handle nested keys like "issue.body"
                keys = key.split(".")
                current = default_payload
                for k in keys[:-1]:
                    current = current[k]
                current[keys[-1]] = value
            else:
                default_payload[key] = value
        
        return default_payload

    @patch('services.github.github_utils.get_installation_access_token')
    @patch('services.github.github_utils.get_repository_settings')
    @patch('services.github.github_utils.check_branch_exists')
    @patch('services.github.github_utils.extract_urls')
    @patch('services.github.github_utils.get_user_public_email')
    @patch('services.github.github_utils.get_parent_issue')
    @patch('services.github.github_utils.datetime')
    @patch('services.github.github_utils.choices')
    def test_deconstruct_github_payload_success(
        self, mock_choices, mock_datetime, mock_get_parent_issue, 
        mock_get_user_public_email, mock_extract_urls, mock_check_branch_exists,
        mock_get_repository_settings, mock_get_installation_access_token
    ):
        """Test successful deconstruction of GitHub payload."""
        # Arrange
        payload = self.create_mock_payload()
        
        # Mock dependencies
        mock_get_installation_access_token.return_value = "test-token"
        mock_get_repository_settings.return_value = {"target_branch": "develop"}
        mock_check_branch_exists.return_value = True
        mock_extract_urls.return_value = (["https://github.com/test/repo"], ["http://example.com"])
        mock_get_user_public_email.return_value = "sender@example.com"
        mock_get_parent_issue.return_value = {
            "number": 100,
            "title": "Parent Issue",
            "body": "Parent issue body"
        }
        
        # Mock datetime
        mock_datetime_instance = MagicMock()
        mock_datetime_instance.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241224",
            "%H%M%S": "120000"
        }[format]
        mock_datetime.now = mock_datetime_instance.now
        
        # Mock random string generation
        mock_choices.return_value = ["A", "B", "C", "D"]

        # Act
        result = deconstruct_github_payload(payload)

        # Assert
        assert result["input_from"] == "github"
        assert result["owner_type"] == "Organization"
        assert result["owner_id"] == 789
        assert result["owner"] == "test-owner"
        assert result["repo_id"] == 456
        assert result["repo"] == "test-repo"
        assert result["clone_url"] == "https://github.com/test-owner/test-repo.git"
        assert result["is_fork"] is False
        assert result["issue_number"] == 123
        assert result["issue_title"] == "Test Issue"
        assert result["issue_body"] == "Test issue body with https://github.com/test/repo and http://example.com"
        assert result["issuer_name"] == "test-user"
        assert result["parent_issue_number"] == 100
        assert result["parent_issue_title"] == "Parent Issue"
        assert result["parent_issue_body"] == "Parent issue body"
        assert result["base_branch"] == "develop"  # Should use target branch
        assert result["new_branch"] == f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}123-20241224-120000-ABCD"
        assert result["installation_id"] == 12345
        assert result["token"] == "test-token"
        assert result["sender_id"] == 999
        assert result["sender_name"] == "sender-user"
        assert result["sender_email"] == "sender@example.com"
        assert result["is_automation"] is False
        assert result["reviewers"] == ["sender-user", "test-user"]
        assert result["github_urls"] == ["https://github.com/test/repo"]
        assert result["other_urls"] == ["http://example.com"]
        assert result["target_branch"] == "develop"

    @patch('services.github.github_utils.get_installation_access_token')
    @patch('services.github.github_utils.get_repository_settings')
    @patch('services.github.github_utils.check_branch_exists')
    @patch('services.github.github_utils.extract_urls')
    @patch('services.github.github_utils.get_user_public_email')
    @patch('services.github.github_utils.get_parent_issue')
    @patch('services.github.github_utils.datetime')
    @patch('services.github.github_utils.choices')
    def test_deconstruct_github_payload_no_target_branch(
        self, mock_choices, mock_datetime, mock_get_parent_issue, 
        mock_get_user_public_email, mock_extract_urls, mock_check_branch_exists,
        mock_get_repository_settings, mock_get_installation_access_token
    ):
        """Test payload deconstruction when no target branch is set."""
        # Arrange
        payload = self.create_mock_payload()
        
        # Mock dependencies
        mock_get_installation_access_token.return_value = "test-token"
        mock_get_repository_settings.return_value = None  # No repository settings
        mock_extract_urls.return_value = ([], [])
        mock_get_user_public_email.return_value = None
        mock_get_parent_issue.return_value = None
        
        # Mock datetime
        mock_datetime_instance = MagicMock()
        mock_datetime_instance.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241224",
            "%H%M%S": "120000"
        }[format]
        mock_datetime.now = mock_datetime_instance.now
        
        # Mock random string generation
        mock_choices.return_value = ["X", "Y", "Z", "1"]

        # Act
        result = deconstruct_github_payload(payload)

        # Assert
        assert result["base_branch"] == "main"  # Should use default branch
        assert result["new_branch"] == f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}123-20241224-120000-XYZ1"
        assert result["parent_issue_number"] is None
        assert result["parent_issue_title"] is None
        assert result["parent_issue_body"] is None
        assert result["sender_email"] is None
        assert result["github_urls"] == []
        assert result["other_urls"] == []
        
        # check_branch_exists should not be called when no target branch
        mock_check_branch_exists.assert_not_called()

    @patch('services.github.github_utils.get_installation_access_token')
    @patch('services.github.github_utils.get_repository_settings')
    @patch('services.github.github_utils.check_branch_exists')
    @patch('services.github.github_utils.extract_urls')
    @patch('services.github.github_utils.get_user_public_email')
    @patch('services.github.github_utils.get_parent_issue')
    @patch('services.github.github_utils.datetime')
    @patch('services.github.github_utils.choices')
    def test_deconstruct_github_payload_target_branch_not_exists(
        self, mock_choices, mock_datetime, mock_get_parent_issue, 
        mock_get_user_public_email, mock_extract_urls, mock_check_branch_exists,
        mock_get_repository_settings, mock_get_installation_access_token
    ):
        """Test payload deconstruction when target branch doesn't exist."""
        # Arrange
        payload = self.create_mock_payload()
        
        # Mock dependencies
        mock_get_installation_access_token.return_value = "test-token"
        mock_get_repository_settings.return_value = {"target_branch": "nonexistent"}
        mock_check_branch_exists.return_value = False  # Branch doesn't exist
        mock_extract_urls.return_value = ([], [])
        mock_get_user_public_email.return_value = None
        mock_get_parent_issue.return_value = None
        
        # Mock datetime
        mock_datetime_instance = MagicMock()
        mock_datetime_instance.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241224",
            "%H%M%S": "120000"
        }[format]
        mock_datetime.now = mock_datetime_instance.now
        
        # Mock random string generation
        mock_choices.return_value = ["1", "2", "3", "4"]

        # Act
        result = deconstruct_github_payload(payload)

        # Assert
        assert result["base_branch"] == "main"  # Should fall back to default branch
        mock_check_branch_exists.assert_called_once_with(
            owner="test-owner", repo="test-repo", branch_name="nonexistent", token="test-token"
        )

    @patch('services.github.github_utils.get_installation_access_token')
    def test_deconstruct_github_payload_no_token(self, mock_get_installation_access_token):
        """Test payload deconstruction when installation token is not found."""
        # Arrange
        payload = self.create_mock_payload()
        mock_get_installation_access_token.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Installation access token is not found for test-owner/test-repo"):
            deconstruct_github_payload(payload)

    @patch('services.github.github_utils.get_installation_access_token')
    @patch('services.github.github_utils.get_repository_settings')
    @patch('services.github.github_utils.extract_urls')
    @patch('services.github.github_utils.get_user_public_email')
    @patch('services.github.github_utils.get_parent_issue')
    @patch('services.github.github_utils.datetime')
    @patch('services.github.github_utils.choices')
    def test_deconstruct_github_payload_automation_sender(
        self, mock_choices, mock_datetime, mock_get_parent_issue, 
        mock_get_user_public_email, mock_extract_urls,
        mock_get_repository_settings, mock_get_installation_access_token
    ):
        """Test payload deconstruction when sender is automation (GitHub App)."""
        # Arrange
        payload = self.create_mock_payload()
        payload["sender"]["id"] = GITHUB_APP_USER_ID  # Set sender as GitHub App
        
        # Mock dependencies
        mock_get_installation_access_token.return_value = "test-token"
        mock_get_repository_settings.return_value = None
        mock_extract_urls.return_value = ([], [])
        mock_get_user_public_email.return_value = None
        mock_get_parent_issue.return_value = None
        
        # Mock datetime
        mock_datetime_instance = MagicMock()
        mock_datetime_instance.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241224",
            "%H%M%S": "120000"
        }[format]
        mock_datetime.now = mock_datetime_instance.now
        
        # Mock random string generation
        mock_choices.return_value = ["A", "B", "C", "D"]

        # Act
        result = deconstruct_github_payload(payload)

        # Assert
        assert result["is_automation"] is True
        assert result["sender_id"] == GITHUB_APP_USER_ID

    @patch('services.github.github_utils.get_installation_access_token')
    @patch('services.github.github_utils.get_repository_settings')
    @patch('services.github.github_utils.extract_urls')
    @patch('services.github.github_utils.get_user_public_email')
    @patch('services.github.github_utils.get_parent_issue')
    @patch('services.github.github_utils.datetime')
    @patch('services.github.github_utils.choices')
    def test_deconstruct_github_payload_bot_reviewers_filtered(
        self, mock_choices, mock_datetime, mock_get_parent_issue, 
        mock_get_user_public_email, mock_extract_urls,
        mock_get_repository_settings, mock_get_installation_access_token
    ):
        """Test that bot users are filtered out from reviewers."""
        # Arrange
        payload = self.create_mock_payload()
        payload["sender"]["login"] = "bot-user[bot]"
        payload["issue"]["user"]["login"] = "another-bot[bot]"
        
        # Mock dependencies
        mock_get_installation_access_token.return_value = "test-token"
        mock_get_repository_settings.return_value = None
        mock_extract_urls.return_value = ([], [])
        mock_get_user_public_email.return_value = None
        mock_get_parent_issue.return_value = None
        
        # Mock datetime
        mock_datetime_instance = MagicMock()
        mock_datetime_instance.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241224",
            "%H%M%S": "120000"
        }[format]
        mock_datetime.now = mock_datetime_instance.now
        
        # Mock random string generation
        mock_choices.return_value = ["A", "B", "C", "D"]

        # Act
        result = deconstruct_github_payload(payload)

        # Assert
        assert result["reviewers"] == []  # Both users are bots, so no reviewers

    @patch('services.github.github_utils.get_installation_access_token')
    @patch('services.github.github_utils.get_repository_settings')
    @patch('services.github.github_utils.extract_urls')
    @patch('services.github.github_utils.get_user_public_email')
    @patch('services.github.github_utils.get_parent_issue')
    @patch('services.github.github_utils.datetime')
    @patch('services.github.github_utils.choices')
    def test_deconstruct_github_payload_forked_repo(
        self, mock_choices, mock_datetime, mock_get_parent_issue, 
        mock_get_user_public_email, mock_extract_urls,
        mock_get_repository_settings, mock_get_installation_access_token
    ):
        """Test payload deconstruction for forked repository."""
        # Arrange
        payload = self.create_mock_payload()
        payload["repository"]["fork"] = True
        
        # Mock dependencies
        mock_get_installation_access_token.return_value = "test-token"
        mock_get_repository_settings.return_value = None
        mock_extract_urls.return_value = ([], [])
        mock_get_user_public_email.return_value = None
        mock_get_parent_issue.return_value = None
        
        # Mock datetime
        mock_datetime_instance = MagicMock()
        mock_datetime_instance.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241224",
            "%H%M%S": "120000"
        }[format]
        mock_datetime.now = mock_datetime_instance.now
        
        # Mock random string generation
        mock_choices.return_value = ["A", "B", "C", "D"]

        # Act
        result = deconstruct_github_payload(payload)

        # Assert
        assert result["is_fork"] is True

    @patch('services.github.github_utils.get_installation_access_token')
    @patch('services.github.github_utils.get_repository_settings')
    @patch('services.github.github_utils.extract_urls')
    @patch('services.github.github_utils.get_user_public_email')
    @patch('services.github.github_utils.get_parent_issue')
    @patch('services.github.github_utils.datetime')
    @patch('services.github.github_utils.choices')
    def test_deconstruct_github_payload_empty_issue_body(
        self, mock_choices, mock_datetime, mock_get_parent_issue, 
        mock_get_user_public_email, mock_extract_urls,
        mock_get_repository_settings, mock_get_installation_access_token
    ):
        """Test payload deconstruction with empty issue body."""
        # Arrange
        payload = self.create_mock_payload()
        payload["issue"]["body"] = None  # Empty body
        
        # Mock dependencies
        mock_get_installation_access_token.return_value = "test-token"
        mock_get_repository_settings.return_value = None
        mock_extract_urls.return_value = ([], [])
        mock_get_user_public_email.return_value = None
        mock_get_parent_issue.return_value = None
        
        # Mock datetime
        mock_datetime_instance = MagicMock()
        mock_datetime_instance.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241224",
            "%H%M%S": "120000"
        }[format]
        mock_datetime.now = mock_datetime_instance.now
        
        # Mock random string generation
        mock_choices.return_value = ["A", "B", "C", "D"]

        # Act
        result = deconstruct_github_payload(payload)

        # Assert
        assert result["issue_body"] == ""  # Should default to empty string
        mock_extract_urls.assert_called_once_with(text="")

    @patch('services.github.github_utils.get_installation_access_token')
    @patch('services.github.github_utils.get_repository_settings')
    @patch('services.github.github_utils.extract_urls')
    @patch('services.github.github_utils.get_user_public_email')
    @patch('services.github.github_utils.get_parent_issue')
    @patch('services.github.github_utils.datetime')
    @patch('services.github.github_utils.choices')
    def test_deconstruct_github_payload_user_owner_type(
        self, mock_choices, mock_datetime, mock_get_parent_issue, 
        mock_get_user_public_email, mock_extract_urls,
        mock_get_repository_settings, mock_get_installation_access_token
    ):
        """Test payload deconstruction with User owner type."""
        # Arrange
        payload = self.create_mock_payload()
        payload["repository"]["owner"]["type"] = "User"
        
        # Mock dependencies
        mock_get_installation_access_token.return_value = "test-token"
        mock_get_repository_settings.return_value = None
        mock_extract_urls.return_value = ([], [])
        mock_get_user_public_email.return_value = None
        mock_get_parent_issue.return_value = None
        
        # Mock datetime
        mock_datetime_instance = MagicMock()
        mock_datetime_instance.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241224",
            "%H%M%S": "120000"
        }[format]
        mock_datetime.now = mock_datetime_instance.now
        
        # Mock random string generation
        mock_choices.return_value = ["A", "B", "C", "D"]

        # Act
        result = deconstruct_github_payload(payload)

        # Assert
        assert result["owner_type"] == "User"
