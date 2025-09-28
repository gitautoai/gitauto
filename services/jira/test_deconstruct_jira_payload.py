from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from config import ISSUE_NUMBER_FORMAT, PRODUCT_ID
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
            "key": "JIRA-123",
            "title": "Test Issue Title",
            "body": "Test issue body with https://github.com/owner/repo/issues/1 and https://example.com",
            "comments": ["Comment 1", "Comment 2"],
        },
        "creator": {
            "id": "jira-user-123",
            "displayName": "John Doe",
            "email": "john.doe@example.com",
        },
        "reporter": {
            "id": "jira-reporter-123",
            "displayName": "Jane Reporter",
            "email": "jane.reporter@example.com",
        },
        "owner": {"id": 12345, "name": "test-owner"},
        "repo": {"id": 67890, "name": "test-repo"},
    }


@pytest.fixture
def mock_installation():
    """Fixture providing a mock installation."""
    return {
        "installation_id": 98765,
        "owner_type": "Organization",
        "owner_id": 12345,
        "owner_name": "test-owner",
        "created_at": datetime.now(),
        "uninstalled_at": None,
        "created_by": "test-user",
        "uninstalled_by": None,
    }


@pytest.fixture
def mock_repository():
    """Fixture providing a mock repository settings."""
    return {
        "id": 1,
        "owner_id": 12345,
        "repo_id": 67890,
        "repo_name": "test-repo",
        "target_branch": "develop",
        "created_at": datetime.now(),
        "created_by": "test-user",
        "updated_at": datetime.now(),
        "updated_by": "test-user",
        "use_screenshots": False,
        "production_url": None,
        "local_port": None,
        "startup_commands": None,
        "web_urls": None,
        "file_paths": None,
        "repo_rules": None,
        "file_count": 100,
        "blank_lines": 10,
        "comment_lines": 20,
        "code_lines": 70,
        "trigger_on_review_comment": True,
        "trigger_on_test_failure": True,
        "trigger_on_commit": True,
        "trigger_on_merged": True,
        "trigger_on_schedule": False,
        "schedule_frequency": None,
        "schedule_minute": None,
        "schedule_time": None,
        "schedule_day_of_week": None,
        "schedule_include_weekends": False,
        "structured_rules": None,
        "trigger_on_pr_change": True,
        "schedule_execution_count": 0,
        "schedule_interval_minutes": 60,
    }


class TestDeconstructJiraPayload:
    """Test class for deconstruct_jira_payload function."""

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    @patch("services.jira.deconstruct_jira_payload.datetime")
    def test_deconstruct_jira_payload_success_with_target_branch(
        self,
        mock_datetime,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        sample_jira_payload,
        mock_installation,
        mock_repository,
    ):
        """Test successful payload deconstruction with target branch that exists."""
        # Setup mocks
        mock_datetime.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241225",
            "%H%M%S": "143000",
        }[format]

        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "abc123")
        mock_get_repository.return_value = mock_repository
        mock_check_branch_exists.return_value = True  # Target branch exists
        mock_extract_urls.return_value = (
            ["https://github.com/owner/repo/issues/1"],
            ["https://example.com"],
        )

        # Call the function
        base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

        # Verify the result
        assert base_args is not None
        assert repo_settings == mock_repository

        # Verify base_args structure
        assert base_args["input_from"] == "jira"
        assert base_args["owner_type"] == "Organization"
        assert base_args["owner_id"] == 12345
        assert base_args["owner"] == "test-owner"
        assert base_args["repo_id"] == 67890
        assert base_args["repo"] == "test-repo"
        assert base_args["clone_url"] == ""
        assert base_args["is_fork"] is False
        assert base_args["issue_number"] == "JIRA-123"
        assert base_args["issue_title"] == "Test Issue Title"
        assert base_args["issue_body"] == "Test issue body with https://github.com/owner/repo/issues/1 and https://example.com"
        assert base_args["issue_comments"] == ["Comment 1", "Comment 2"]
        assert base_args["issuer_name"] == "John Doe"
        assert base_args["issuer_email"] == "john.doe@example.com"
        assert base_args["base_branch"] == "develop"  # Should use target branch
        assert base_args["latest_commit_sha"] == "abc123"
        assert base_args["new_branch"] == f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}JIRA-123-20241225-143000"
        assert base_args["installation_id"] == 98765
        assert base_args["token"] == "test-token"
        assert base_args["sender_id"] == "jira-user-123"
        assert base_args["sender_name"] == "John Doe"
        assert base_args["sender_email"] == "john.doe@example.com"
        assert base_args["is_automation"] is False
        assert base_args["reviewers"] == []
        assert base_args["github_urls"] == ["https://github.com/owner/repo/issues/1"]
        assert base_args["other_urls"] == ["https://example.com"]

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
        mock_check_branch_exists.assert_called_once_with(
            owner="test-owner", repo="test-repo", branch_name="develop", token="test-token"
        )
        mock_extract_urls.assert_called_once_with(
            text="Test issue body with https://github.com/owner/repo/issues/1 and https://example.com"
        )

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    @patch("services.jira.deconstruct_jira_payload.datetime")
    def test_deconstruct_jira_payload_success_without_target_branch(
        self,
        mock_datetime,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        sample_jira_payload,
        mock_installation,
        mock_repository,
    ):
        """Test successful payload deconstruction when target branch doesn't exist."""
        # Setup mocks
        mock_datetime.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241225",
            "%H%M%S": "143000",
        }[format]

        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = True  # Test forked repo
        mock_get_default_branch.return_value = ("main", "abc123")
        mock_get_repository.return_value = mock_repository
        mock_check_branch_exists.return_value = False  # Target branch doesn't exist
        mock_extract_urls.return_value = ([], [])

        # Call the function
        base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

        # Verify the result
        assert base_args is not None
        assert repo_settings == mock_repository
        assert base_args["base_branch"] == "main"  # Should use default branch
        assert base_args["is_fork"] is True
        assert base_args["github_urls"] == []
        assert base_args["other_urls"] == []

        # Verify branch check was called
        mock_check_branch_exists.assert_called_once_with(
            owner="test-owner", repo="test-repo", branch_name="develop", token="test-token"
        )

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    @patch("services.jira.deconstruct_jira_payload.datetime")
    def test_deconstruct_jira_payload_no_repository_settings(
        self,
        mock_datetime,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        sample_jira_payload,
        mock_installation,
    ):
        """Test payload deconstruction when repository settings are not found."""
        # Setup mocks
        mock_datetime.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241225",
            "%H%M%S": "143000",
        }[format]

        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "abc123")
        mock_get_repository.return_value = None  # No repository settings
        mock_extract_urls.return_value = ([], [])

        # Call the function
        base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

        # Verify the result
        assert base_args is not None
        assert repo_settings is None
        assert base_args["base_branch"] == "main"  # Should use default branch

        # Verify branch check was not called since no target branch
        mock_check_branch_exists.assert_not_called()

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    @patch("services.jira.deconstruct_jira_payload.datetime")
    def test_deconstruct_jira_payload_no_target_branch_in_settings(
        self,
        mock_datetime,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        sample_jira_payload,
        mock_installation,
    ):
        """Test payload deconstruction when repository settings exist but no target branch."""
        # Setup mocks
        mock_datetime.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241225",
            "%H%M%S": "143000",
        }[format]

        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "abc123")

        # Repository settings without target branch
        repo_settings_no_target = {
            "id": 1,
            "owner_id": 12345,
            "repo_id": 67890,
            "target_branch": None,  # No target branch
        }
        mock_get_repository.return_value = repo_settings_no_target
        mock_extract_urls.return_value = ([], [])

        # Call the function
        base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

        # Verify the result
        assert base_args is not None
        assert repo_settings == repo_settings_no_target
        assert base_args["base_branch"] == "main"  # Should use default branch

        # Verify branch check was not called since no target branch
        mock_check_branch_exists.assert_not_called()

    @patch("services.jira.deconstruct_jira_payload.get_installation")
    def test_deconstruct_jira_payload_installation_not_found(
        self, mock_get_installation, sample_jira_payload
    ):
        """Test error handling when installation is not found."""
        # Setup mock to return None
        mock_get_installation.return_value = None

        # Call the function and expect ValueError
        with pytest.raises(ValueError, match="Installation not found for owner_id: 12345"):
            deconstruct_jira_payload(sample_jira_payload)

        # Verify function call
        mock_get_installation.assert_called_once_with(owner_id=12345)

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    @patch("services.jira.deconstruct_jira_payload.datetime")
    def test_deconstruct_jira_payload_user_owner_type(
        self,
        mock_datetime,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        sample_jira_payload,
    ):
        """Test payload deconstruction with User owner type."""
        # Setup mocks
        mock_datetime.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241225",
            "%H%M%S": "143000",
        }[format]

        # Installation with User owner type
        user_installation = {
            "installation_id": 98765,
            "owner_type": "User",
            "owner_id": 12345,
            "owner_name": "test-user",
            "created_at": datetime.now(),
            "uninstalled_at": None,
            "created_by": "test-user",
            "uninstalled_by": None,
        }

        mock_get_installation.return_value = user_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "abc123")
        mock_get_repository.return_value = None
        mock_extract_urls.return_value = ([], [])

        # Call the function
        base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

        # Verify the result
        assert base_args is not None
        assert base_args["owner_type"] == "User"

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    @patch("services.jira.deconstruct_jira_payload.datetime")
    def test_deconstruct_jira_payload_empty_issue_body(
        self,
        mock_datetime,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        mock_installation,
    ):
        """Test payload deconstruction with empty issue body."""
        # Setup mocks
        mock_datetime.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241225",
            "%H%M%S": "143000",
        }[format]

        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "abc123")
        mock_get_repository.return_value = None
        mock_extract_urls.return_value = ([], [])

        # Payload with empty issue body
        payload_empty_body = {
            "cloudId": "test-cloud-id",
            "projectId": "test-project-id",
            "issue": {
                "id": "JIRA-123",
                "key": "JIRA-123",
                "title": "Test Issue Title",
                "body": "",  # Empty body
                "comments": [],
            },
            "creator": {
                "id": "jira-user-123",
                "displayName": "John Doe",
                "email": "john.doe@example.com",
            },
            "reporter": {
                "id": "jira-reporter-123",
                "displayName": "Jane Reporter",
                "email": "jane.reporter@example.com",
            },
            "owner": {"id": 12345, "name": "test-owner"},
            "repo": {"id": 67890, "name": "test-repo"},
        }

        # Call the function
        base_args, repo_settings = deconstruct_jira_payload(payload_empty_body)

        # Verify the result
        assert base_args is not None
        assert base_args["issue_body"] == ""
        assert base_args["issue_comments"] == []
        assert base_args["github_urls"] == []
        assert base_args["other_urls"] == []

        # Verify extract_urls was called with empty string
        mock_extract_urls.assert_called_once_with(text="")

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    @patch("services.jira.deconstruct_jira_payload.datetime")
    def test_deconstruct_jira_payload_target_branch_empty_string(
        self,
        mock_datetime,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        mock_installation,
    ):
        """Test payload deconstruction when target branch is empty string."""
        # Setup mocks
        mock_datetime.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241225",
            "%H%M%S": "143000",
        }[format]

        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "abc123")

        # Repository settings with empty target branch
        repo_settings_empty_target = {
            "id": 1,
            "owner_id": 12345,
            "repo_id": 67890,
            "target_branch": "",  # Empty string
        }
        mock_get_repository.return_value = repo_settings_empty_target
        mock_extract_urls.return_value = ([], [])

        # Payload
        payload = {
            "cloudId": "test-cloud-id",
            "projectId": "test-project-id",
            "issue": {
                "id": "JIRA-123",
                "key": "JIRA-123",
                "title": "Test Issue Title",
                "body": "Test body",
                "comments": [],
            },
            "creator": {
                "id": "jira-user-123",
                "displayName": "John Doe",
                "email": "john.doe@example.com",
            },
            "reporter": {
                "id": "jira-reporter-123",
                "displayName": "Jane Reporter",
                "email": "jane.reporter@example.com",
            },
            "owner": {"id": 12345, "name": "test-owner"},
            "repo": {"id": 67890, "name": "test-repo"},
        }

        # Call the function
        base_args, repo_settings = deconstruct_jira_payload(payload)

        # Verify the result
        assert base_args is not None
        assert base_args["base_branch"] == "main"  # Should use default branch

        # Verify branch check was not called since target branch is empty
        mock_check_branch_exists.assert_not_called()

    @patch("services.jira.deconstruct_jira_payload.get_installation")
    def test_deconstruct_jira_payload_exception_handling(
        self, mock_get_installation, sample_jira_payload
    ):
        """Test exception handling with handle_exceptions decorator."""
        # Setup mock to raise an exception
        mock_get_installation.side_effect = Exception("Database connection failed")

        # Call the function and expect the exception to be re-raised due to raise_on_error=True
        with pytest.raises(Exception, match="Database connection failed"):
            deconstruct_jira_payload(sample_jira_payload)

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    @patch("services.jira.deconstruct_jira_payload.datetime")
    def test_deconstruct_jira_payload_different_datetime_formats(
        self,
        mock_datetime,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        sample_jira_payload,
        mock_installation,
    ):
        """Test payload deconstruction with different datetime formats."""
        # Setup mocks with different datetime values
        mock_datetime.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20250101",  # New Year
            "%H%M%S": "000000",    # Midnight
        }[format]

        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "abc123")
        mock_get_repository.return_value = None
        mock_extract_urls.return_value = ([], [])

        # Call the function
        base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

        # Verify the result
        assert base_args is not None
        assert base_args["new_branch"] == f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}JIRA-123-20250101-000000"

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    @patch("services.jira.deconstruct_jira_payload.datetime")
    def test_deconstruct_jira_payload_all_fields_populated(
        self,
        mock_datetime,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        mock_installation,
        mock_repository,
    ):
        """Test that all BaseArgs fields are properly populated."""
        # Setup mocks
        mock_datetime.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241225",
            "%H%M%S": "143000",
        }[format]

        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = True
        mock_get_default_branch.return_value = ("develop", "def456")
        mock_get_repository.return_value = mock_repository
        mock_check_branch_exists.return_value = True
        mock_extract_urls.return_value = (["https://github.com/test/repo"], ["https://example.com"])

        # Complete payload
        complete_payload = {
            "cloudId": "complete-cloud-id",
            "projectId": "complete-project-id",
            "issue": {
                "id": "COMPLETE-456",
                "key": "COMPLETE-456",
                "title": "Complete Test Issue",
                "body": "Complete test body with URLs",
                "comments": ["Complete comment 1", "Complete comment 2"],
            },
            "creator": {
                "id": "complete-user-456",
                "displayName": "Complete User",
                "email": "complete.user@example.com",
            },
            "reporter": {
                "id": "complete-reporter-456",
                "displayName": "Complete Reporter",
                "email": "complete.reporter@example.com",
            },
            "owner": {"id": 54321, "name": "complete-owner"},
            "repo": {"id": 98765, "name": "complete-repo"},
        }

        # Call the function
        base_args, repo_settings = deconstruct_jira_payload(complete_payload)

        # Verify all required BaseArgs fields are present and correct
        expected_fields = {
            "input_from": "jira",
            "owner_type": "Organization",
            "owner_id": 54321,
            "owner": "complete-owner",
            "repo_id": 98765,
            "repo": "complete-repo",
            "clone_url": "",
            "is_fork": True,
            "issue_number": "COMPLETE-456",
            "issue_title": "Complete Test Issue",
            "issue_body": "Complete test body with URLs",
            "issue_comments": ["Complete comment 1", "Complete comment 2"],
            "latest_commit_sha": "def456",
            "issuer_name": "Complete User",
            "base_branch": "develop",  # Target branch exists
            "new_branch": f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}COMPLETE-456-20241225-143000",
            "installation_id": 98765,
            "token": "test-token",
            "sender_id": "complete-user-456",
            "sender_name": "Complete User",
            "sender_email": "complete.user@example.com",
            "is_automation": False,
            "reviewers": [],
            "github_urls": ["https://github.com/test/repo"],
            "other_urls": ["https://example.com"],
        }

        for field, expected_value in expected_fields.items():
            assert base_args[field] == expected_value, f"Field {field} mismatch: expected {expected_value}, got {base_args[field]}"

        # Verify repo_settings is returned correctly
        assert repo_settings == mock_repository

        # Verify all mocked functions were called with correct parameters
        mock_get_installation.assert_called_once_with(owner_id=54321)
        mock_get_token.assert_called_once_with(installation_id=98765)
        mock_is_forked.assert_called_once_with(
            owner="complete-owner", repo="complete-repo", token="test-token"
        )
        mock_get_default_branch.assert_called_once_with(
            owner="complete-owner", repo="complete-repo", token="test-token"
        )
        mock_get_repository.assert_called_once_with(repo_id=98765)
        mock_check_branch_exists.assert_called_once_with(
            owner="complete-owner", repo="complete-repo", branch_name="develop", token="test-token"
        )
        mock_extract_urls.assert_called_once_with(text="Complete test body with URLs")

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    @patch("services.jira.deconstruct_jira_payload.datetime")
    def test_deconstruct_jira_payload_edge_cases(
        self,
        mock_datetime,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        mock_installation,
    ):
        """Test edge cases with special characters and values."""
        # Setup mocks
        mock_datetime.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241225",
            "%H%M%S": "143000",
        }[format]

        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "abc123")
        mock_get_repository.return_value = None
        mock_extract_urls.return_value = ([], [])

        # Payload with special characters
        edge_case_payload = {
            "cloudId": "test-cloud-id",
            "projectId": "test-project-id",
            "issue": {
                "id": "SPECIAL-123!@#",
                "key": "SPECIAL-123!@#",
                "title": "Issue with special chars: !@#$%^&*()",
                "body": "Body with unicode: 你好世界 and emojis: 🚀🎉",
                "comments": ["Comment with special chars: <>?:\"{}|"],
            },
            "creator": {
                "id": "user-with-special-chars!@#",
                "displayName": "User Name with Spaces & Chars",
                "email": "user+test@example.com",
            },
            "reporter": {
                "id": "reporter-123",
                "displayName": "Reporter Name",
                "email": "reporter@example.com",
            },
            "owner": {"id": 12345, "name": "owner-with-dashes"},
            "repo": {"id": 67890, "name": "repo_with_underscores"},
        }

        # Call the function
        base_args, repo_settings = deconstruct_jira_payload(edge_case_payload)

        # Verify the result handles special characters correctly
        assert base_args is not None
        assert base_args["issue_number"] == "SPECIAL-123!@#"
        assert base_args["issue_title"] == "Issue with special chars: !@#$%^&*()"
        assert base_args["issue_body"] == "Body with unicode: 你好世界 and emojis: 🚀🎉"
        assert base_args["issue_comments"] == ["Comment with special chars: <>?:\"{}|"]
        assert base_args["sender_id"] == "user-with-special-chars!@#"
        assert base_args["sender_name"] == "User Name with Spaces & Chars"
        assert base_args["sender_email"] == "user+test@example.com"
        assert base_args["owner"] == "owner-with-dashes"
        assert base_args["repo"] == "repo_with_underscores"

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    @patch("services.jira.deconstruct_jira_payload.datetime")
    def test_deconstruct_jira_payload_cast_operations(
        self,
        mock_datetime,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        sample_jira_payload,
    ):
        """Test that cast operations work correctly for installation_id and owner_type."""
        # Setup mocks
        mock_datetime.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241225",
            "%H%M%S": "143000",
        }[format]

        # Installation with string values that need casting
        installation_with_strings = {
            "installation_id": "98765",  # String that should be cast to int
            "owner_type": "Organization",  # Should be cast to OwnerType
            "owner_id": 12345,
            "owner_name": "test-owner",
            "created_at": datetime.now(),
            "uninstalled_at": None,
            "created_by": "test-user",
            "uninstalled_by": None,
        }

        mock_get_installation.return_value = installation_with_strings
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "abc123")
        mock_get_repository.return_value = None
        mock_extract_urls.return_value = ([], [])

        # Call the function
        base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

        # Verify the result - cast operations should work
        assert base_args is not None
        assert base_args["installation_id"] == 98765  # Should be cast to int
        assert base_args["owner_type"] == "Organization"  # Should be cast to OwnerType

    @patch("services.jira.deconstruct_jira_payload.extract_urls")
    @patch("services.jira.deconstruct_jira_payload.check_branch_exists")
    @patch("services.jira.deconstruct_jira_payload.get_repository")
    @patch("services.jira.deconstruct_jira_payload.get_default_branch")
    @patch("services.jira.deconstruct_jira_payload.is_repo_forked")
    @patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
    @patch("services.jira.deconstruct_jira_payload.get_installation")
    @patch("services.jira.deconstruct_jira_payload.datetime")
    def test_deconstruct_jira_payload_repository_target_branch_cast(
        self,
        mock_datetime,
        mock_get_installation,
        mock_get_token,
        mock_is_forked,
        mock_get_default_branch,
        mock_get_repository,
        mock_check_branch_exists,
        mock_extract_urls,
        sample_jira_payload,
        mock_installation,
    ):
        """Test that target_branch casting works correctly."""
        # Setup mocks
        mock_datetime.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241225",
            "%H%M%S": "143000",
        }[format]

        mock_get_installation.return_value = mock_installation
        mock_get_token.return_value = "test-token"
        mock_is_forked.return_value = False
        mock_get_default_branch.return_value = ("main", "abc123")

        # Repository settings with target_branch that needs casting
        repo_settings_with_cast = {
            "id": 1,
            "owner_id": 12345,
            "repo_id": 67890,
            "target_branch": "feature-branch",  # String that should be cast
        }
        mock_get_repository.return_value = repo_settings_with_cast
        mock_check_branch_exists.return_value = True
        mock_extract_urls.return_value = ([], [])

        # Call the function
        base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

        # Verify the result
        assert base_args is not None
        assert base_args["base_branch"] == "feature-branch"  # Should use cast target branch

        # Verify branch check was called with cast value
        mock_check_branch_exists.assert_called_once_with(
            owner="test-owner", repo="test-repo", branch_name="feature-branch", token="test-token"
        )
