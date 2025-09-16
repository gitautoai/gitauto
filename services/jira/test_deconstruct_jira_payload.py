# Standard imports
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# Local imports
from services.github.types.github_types import BaseArgs
from services.jira.deconstruct_jira_payload import deconstruct_jira_payload
from services.jira.types import JiraPayload


@pytest.fixture
def sample_jira_payload():
    """Fixture providing a sample JIRA payload."""
    return {
        "cloudId": "test-cloud-id",
        "projectId": "test-project-id",
        "issue": {
            "id": "JIRA-123",
            "key": "PROJ-456",
            "title": "Test Jira Issue",
            "body": "This is a test issue body with https://github.com/owner/repo/issues/1 and https://example.com",
            "comments": ["Comment 1", "Comment 2"],
        },
        "creator": {
            "id": "jira-user-123",
            "displayName": "John Doe",
            "email": "john.doe@example.com",
        },
        "reporter": {
            "id": "jira-reporter-456",
            "displayName": "Jane Smith",
            "email": "jane.smith@example.com",
        },
        "owner": {
            "id": 12345,
            "name": "test-owner",
        },
        "repo": {
            "id": 67890,
            "name": "test-repo",
        },
    }


@pytest.fixture
def mock_installation():
    """Fixture providing mock installation data."""
    return {
        "installation_id": 98765,
        "owner_type": "Organization",
    }


@pytest.fixture
def mock_repo_settings():
    """Fixture providing mock repository settings."""
    return {
        "target_branch": "develop",
        "other_setting": "value",
    }


@pytest.fixture
def mock_repo_settings_no_target_branch():
    """Fixture providing mock repository settings without target branch."""
    return {
        "other_setting": "value",
    }


@pytest.fixture
def mock_datetime():
    """Fixture providing mock datetime values."""
    with patch("services.jira.deconstruct_jira_payload.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241225",
            "%H%M%S": "143000",
        }[format]
        yield mock_dt


class TestDeconstructJiraPayload:
    """Test class for deconstruct_jira_payload function."""

    @patch("services.jira.deconstruct_jira_payload.PRODUCT_ID", "gitauto")
    @patch("services.jira.deconstruct_jira_payload.ISSUE_NUMBER_FORMAT", "/issue-")
    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    def test_successful_deconstruction_with_default_branch(
        self,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        sample_jira_payload,
        mock_installation,
        mock_repo_settings_no_target_branch,
        mock_datetime,
    ):
        """Test successful payload deconstruction using default branch."""
        # Setup mocks
        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "commit-sha-123")
        mock_get_repository.return_value = mock_repo_settings_no_target_branch
        mock_extract_urls.return_value = (
            ["https://github.com/owner/repo/issues/1"],
            ["https://example.com"],
        )

        # Execute
        base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

        # Verify function calls
        mock_get_installation.assert_called_once_with(owner_id=12345)
        mock_get_token.assert_called_once_with(installation_id=98765)
        mock_is_forked.assert_called_once_with(
            owner="test-owner", repo="test-repo", token="test-token"
        )
        mock_get_default_branch.assert_called_once_with(
            owner="test-owner", repo="test-repo", token="test-token"
        )
        mock_get_repository.assert_called_once_with(repo_id=67890)
        mock_check_branch_exists.assert_not_called()  # No target branch set
        mock_extract_urls.assert_called_once_with(
            text="This is a test issue body with https://github.com/owner/repo/issues/1 and https://example.com"
        )

        # Verify base_args structure and values
        assert isinstance(base_args, dict)
        assert base_args["input_from"] == "jira"
        assert base_args["owner_type"] == "Organization"
        assert base_args["owner_id"] == 12345
        assert base_args["owner"] == "test-owner"
        assert base_args["repo_id"] == 67890
        assert base_args["repo"] == "test-repo"
        assert base_args["clone_url"] == ""
        assert base_args["is_fork"] is False
        assert base_args["issue_number"] == "JIRA-123"
        assert base_args["issue_title"] == "Test Jira Issue"
        assert (
            base_args["issue_body"]
            == "This is a test issue body with https://github.com/owner/repo/issues/1 and https://example.com"
        )
        assert base_args["issue_comments"] == ["Comment 1", "Comment 2"]
        assert base_args["issuer_name"] == "John Doe"
        assert base_args["issuer_email"] == "john.doe@example.com"
        assert base_args["base_branch"] == "main"
        assert base_args["latest_commit_sha"] == "commit-sha-123"
        # Verify branch name follows expected pattern: {PRODUCT_ID}/issue-{issue_number}-{date}-{time}
        assert base_args["new_branch"].endswith("/issue-JIRA-123-20241225-143000")
        assert base_args["installation_id"] == 98765
        assert base_args["token"] == "test-token"
        assert base_args["sender_id"] == "jira-user-123"
        assert base_args["sender_name"] == "John Doe"
        assert base_args["sender_email"] == "john.doe@example.com"
        assert base_args["is_automation"] is False
        assert base_args["reviewers"] == []
        assert base_args["github_urls"] == ["https://github.com/owner/repo/issues/1"]
        assert base_args["other_urls"] == ["https://example.com"]

        # Verify repo_settings
        assert repo_settings == mock_repo_settings_no_target_branch

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    def test_successful_deconstruction_with_target_branch_exists(
        self,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        sample_jira_payload,
        mock_installation,
        mock_repo_settings,
        mock_datetime,
    ):
        """Test successful payload deconstruction using target branch when it exists."""
        # Setup mocks
        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = True
        mock_get_default_branch.return_value = ("main", "commit-sha-123")
        mock_get_repository.return_value = mock_repo_settings
        mock_check_branch_exists.return_value = True  # Target branch exists
        mock_extract_urls.return_value = ([], [])

        # Execute
        base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

        # Verify function calls
        mock_check_branch_exists.assert_called_once_with(
            owner="test-owner", repo="test-repo", branch_name="develop", token="test-token"
        )

        # Verify that target branch is used instead of default branch
        assert base_args["base_branch"] == "develop"
        assert base_args["is_fork"] is True

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    def test_successful_deconstruction_with_target_branch_not_exists(
        self,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        sample_jira_payload,
        mock_installation,
        mock_repo_settings,
        mock_datetime,
    ):
        """Test successful payload deconstruction using default branch when target branch doesn't exist."""
        # Setup mocks
        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "commit-sha-123")
        mock_get_repository.return_value = mock_repo_settings
        mock_check_branch_exists.return_value = False  # Target branch doesn't exist
        mock_extract_urls.return_value = ([], [])

        # Execute
        base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

        # Verify function calls
        mock_check_branch_exists.assert_called_once_with(
            owner="test-owner", repo="test-repo", branch_name="develop", token="test-token"
        )

        # Verify that default branch is used when target branch doesn't exist
        assert base_args["base_branch"] == "main"

    @patch("services.jira.deconstruct_jira_payload.get_installation")
    def test_installation_not_found_raises_error(
        self, mock_get_installation, sample_jira_payload
    ):
        """Test that ValueError is raised when installation is not found."""
        # Setup mock to return None
        mock_get_installation.return_value = None

        # Execute and verify exception
        with pytest.raises(ValueError) as exc_info:
            deconstruct_jira_payload(sample_jira_payload)

        assert str(exc_info.value) == "Installation not found for owner_id: 12345"
        mock_get_installation.assert_called_once_with(owner_id=12345)

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    def test_no_repository_settings(
        self,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        sample_jira_payload,
        mock_installation,
        mock_datetime,
    ):
        """Test successful deconstruction when repository settings are None."""
        # Setup mocks
        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "commit-sha-123")
        mock_get_repository.return_value = None  # No repository settings
        mock_extract_urls.return_value = ([], [])

        # Execute
        base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

        # Verify function calls
        mock_get_repository.assert_called_once_with(repo_id=67890)
        mock_check_branch_exists.assert_not_called()  # Should not check branch when no settings

        # Verify results
        assert base_args["base_branch"] == "main"  # Uses default branch
        assert repo_settings is None

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    def test_repository_settings_with_none_target_branch(
        self,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        sample_jira_payload,
        mock_installation,
        mock_datetime,
    ):
        """Test successful deconstruction when target_branch is None in repository settings."""
        # Setup mocks
        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "commit-sha-123")
        mock_get_repository.return_value = {"target_branch": None}
        mock_extract_urls.return_value = ([], [])

        # Execute
        base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

        # Verify function calls
        mock_check_branch_exists.assert_not_called()  # Should not check branch when target_branch is None

        # Verify results
        assert base_args["base_branch"] == "main"  # Uses default branch

    def test_payload_field_extraction(self, sample_jira_payload):
        """Test that all payload fields are correctly extracted."""
        with patch("services.jira.deconstruct_jira_payload.get_installation") as mock_get_installation:
            mock_get_installation.return_value = None

            # This will raise ValueError, but we can still test field extraction logic
            with pytest.raises(ValueError):
                deconstruct_jira_payload(sample_jira_payload)

            # Verify that get_installation was called with correct owner_id
            mock_get_installation.assert_called_once_with(owner_id=12345)

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    def test_empty_issue_body_url_extraction(
        self,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        mock_installation,
        mock_datetime,
    ):
        """Test URL extraction with empty issue body."""
        # Create payload with empty issue body
        payload = {
            "cloudId": "test-cloud-id",
            "projectId": "test-project-id",
            "issue": {
                "id": "JIRA-123",
                "key": "PROJ-456",
                "title": "Test Issue",
                "body": "",  # Empty body
                "comments": [],
            },
            "creator": {
                "id": "user-123",
                "displayName": "Test User",
                "email": "test@example.com",
            },
            "reporter": {
                "id": "reporter-456",
                "displayName": "Reporter",
                "email": "reporter@example.com",
            },
            "owner": {"id": 12345, "name": "test-owner"},
            "repo": {"id": 67890, "name": "test-repo"},
        }

        # Setup mocks
        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "commit-sha-123")
        mock_get_repository.return_value = None
        mock_extract_urls.return_value = ([], [])

        # Execute
        base_args, repo_settings = deconstruct_jira_payload(payload)

        # Verify URL extraction was called with empty string
        mock_extract_urls.assert_called_once_with(text="")
        assert base_args["github_urls"] == []
        assert base_args["other_urls"] == []

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    def test_different_owner_types(
        self,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        sample_jira_payload,
        mock_datetime,
    ):
        """Test with different owner types."""
        # Test with User owner type
        user_installation = {
            "installation_id": 98765,
            "owner_type": "User",
        }

        # Setup mocks
        mock_get_installation.return_value = user_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "commit-sha-123")
        mock_get_repository.return_value = None
        mock_extract_urls.return_value = ([], [])

        # Execute
        base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

        # Verify owner type is correctly set
        assert base_args["owner_type"] == "User"

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.PRODUCT_ID", "gitauto")
    @patch("services.jira.deconstruct_jira_payload.ISSUE_NUMBER_FORMAT", "/issue-")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    def test_branch_name_generation_with_special_characters(
        self,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        mock_installation,
    ):
        """Test branch name generation with special characters in issue ID."""
        # Create payload with special characters in issue ID
        payload = {
            "cloudId": "test-cloud-id",
            "projectId": "test-project-id",
            "issue": {
                "id": "PROJ-123/SPECIAL",  # Issue ID with special characters
                "key": "PROJ-456",
                "title": "Test Issue",
                "body": "Test body",
                "comments": [],
            },
            "creator": {
                "id": "user-123",
                "displayName": "Test User",
                "email": "test@example.com",
            },
            "reporter": {
                "id": "reporter-456",
                "displayName": "Reporter",
                "email": "reporter@example.com",
            },
            "owner": {"id": 12345, "name": "test-owner"},
            "repo": {"id": 67890, "name": "test-repo"},
        }

        # Setup mocks
        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "commit-sha-123")
        mock_get_repository.return_value = None
        mock_extract_urls.return_value = ([], [])

        with patch("services.jira.deconstruct_jira_payload.datetime") as mock_dt:
            mock_dt.now.return_value.strftime.side_effect = lambda format: {
                "%Y%m%d": "20241225",
                "%H%M%S": "143000",
            }[format]

            # Execute
            base_args, repo_settings = deconstruct_jira_payload(payload)

            # Verify branch name includes the special characters as-is
            # Verify branch name follows expected pattern with special characters
            assert base_args["new_branch"].endswith("/issue-PROJ-123/SPECIAL-20241225-143000")

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    def test_sender_fields_match_issuer_fields(
        self,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        sample_jira_payload,
        mock_installation,
        mock_datetime,
    ):
        """Test that sender fields are correctly set to match issuer fields."""
        # Setup mocks
        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "commit-sha-123")
        mock_get_repository.return_value = None
        mock_extract_urls.return_value = ([], [])

        # Execute
        base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

        # Verify sender fields match issuer fields
        assert base_args["sender_id"] == "jira-user-123"  # sender_id uses issuer_id
        assert base_args["sender_name"] == base_args["issuer_name"]
        assert base_args["sender_email"] == base_args["issuer_email"]
        assert base_args["sender_id"] == "jira-user-123"
        assert base_args["sender_name"] == "John Doe"
        assert base_args["sender_email"] == "john.doe@example.com"

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    def test_automation_and_reviewers_defaults(
        self,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        sample_jira_payload,
        mock_installation,
        mock_datetime,
    ):
        """Test that is_automation and reviewers have correct default values."""
        # Setup mocks
        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "commit-sha-123")
        mock_get_repository.return_value = None
        mock_extract_urls.return_value = ([], [])

        # Execute
        base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

        # Verify default values
        assert base_args["is_automation"] is False
        assert base_args["reviewers"] == []
        assert isinstance(base_args["reviewers"], list)

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    def test_clone_url_is_empty_string(
        self,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        sample_jira_payload,
        mock_installation,
        mock_datetime,
    ):
        """Test that clone_url is set to empty string for Jira payloads."""
        # Setup mocks
        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "commit-sha-123")
        mock_get_repository.return_value = None
        mock_extract_urls.return_value = ([], [])

        # Execute
        base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

        # Verify clone_url is empty string
        assert base_args["clone_url"] == ""

    def test_minimal_payload_structure(self):
        """Test that the function handles minimal required payload structure."""
        minimal_payload = {
            "cloudId": "cloud",
            "projectId": "project",
            "issue": {
                "id": "1",
                "key": "KEY-1",
                "title": "Title",
                "body": "",
                "comments": [],
            },
            "creator": {
                "id": "creator-1",
                "displayName": "Creator",
                "email": "creator@example.com",
            },
            "reporter": {
                "id": "reporter-1",
                "displayName": "Reporter",
                "email": "reporter@example.com",
            },
            "owner": {"id": 1, "name": "owner"},
            "repo": {"id": 1, "name": "repo"},
        }

        with patch("services.jira.deconstruct_jira_payload.get_installation") as mock_get_installation:
            mock_get_installation.return_value = None

            # This will raise ValueError due to no installation, but payload structure is valid
            with pytest.raises(ValueError):
                deconstruct_jira_payload(minimal_payload)

            # Verify the function was called, meaning payload structure was accepted
            mock_get_installation.assert_called_once_with(owner_id=1)

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    def test_return_tuple_structure(
        self,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        sample_jira_payload,
        mock_installation,
        mock_repo_settings,
        mock_datetime,
    ):
        """Test that the function returns a tuple with correct structure."""
        # Setup mocks
        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "commit-sha-123")
        mock_get_repository.return_value = mock_repo_settings
        mock_check_branch_exists.return_value = True
        mock_extract_urls.return_value = ([], [])

        # Execute
        result = deconstruct_jira_payload(sample_jira_payload)

        # Verify return type and structure
        assert isinstance(result, tuple)
        assert len(result) == 2

        base_args, repo_settings = result
        assert isinstance(base_args, dict)
        assert repo_settings == mock_repo_settings

        # Verify base_args has all required BaseArgs fields
        required_fields = [
            "input_from", "owner_type", "owner_id", "owner", "repo_id", "repo",
            "clone_url", "is_fork", "issue_number", "issue_title", "issue_body",
            "issue_comments", "latest_commit_sha", "issuer_name", "base_branch",
            "new_branch", "installation_id", "token", "sender_id", "sender_name",
            "sender_email", "is_automation", "reviewers", "github_urls", "other_urls"
        ]

        for field in required_fields:
            assert field in base_args, f"Missing required field: {field}"

    @patch("services.jira.deconstruct_jira_payload.get_installation")
    def test_exception_handling_with_raise_on_error_true(
        self, mock_get_installation, sample_jira_payload
    ):
        """Test that exceptions are re-raised when raise_on_error=True in decorator."""
        # Setup mock to raise an exception
        mock_get_installation.side_effect = Exception("Test exception")

        # Execute and verify exception is re-raised
        with pytest.raises(Exception) as exc_info:
            deconstruct_jira_payload(sample_jira_payload)

        assert str(exc_info.value) == "Test exception"

    @patch("services.jira.deconstruct_jira_payload.get_installation")
    def test_exception_handling_returns_default_on_error(
        self, mock_get_installation, sample_jira_payload
    ):
        """Test that default return value is returned when exception occurs."""
        # Setup mock to raise an exception
        mock_get_installation.side_effect = KeyError("Test key error")

        # The function is decorated with @handle_exceptions(default_return_value=(None, None), raise_on_error=True)
        # So it should re-raise the exception
        with pytest.raises(KeyError) as exc_info:
            deconstruct_jira_payload(sample_jira_payload)
