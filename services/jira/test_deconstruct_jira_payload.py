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
            "key": "PROJ-456",
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
            "id": "jira-reporter-456",
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
        "trigger_on_commit": False,
        "trigger_on_merged": False,
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


@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_success(
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
    """Test successful deconstruction of JIRA payload."""
    # Setup mocks
    mock_get_installation.return_value = mock_installation
    mock_get_token.return_value = "test-token"
    mock_is_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123")
    mock_get_repository.return_value = mock_repository
    mock_check_branch_exists.return_value = True
    mock_extract_urls.return_value = (
        ["https://github.com/owner/repo/issues/1"],
        ["https://example.com"],
    )

    # Mock datetime
    mock_now = MagicMock()
    mock_now.strftime.side_effect = lambda format: {
        "%Y%m%d": "20241224",
        "%H%M%S": "120000"
    }[format]
    mock_datetime.now.return_value = mock_now

    # Call the function
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
    mock_check_branch_exists.assert_called_once_with(
        owner="test-owner", repo="test-repo", branch_name="develop", token="test-token"
    )
    mock_extract_urls.assert_called_once_with(
        text="Test issue body with https://github.com/owner/repo/issues/1 and https://example.com"
    )

    # Verify return values
    assert base_args is not None
    assert repo_settings == mock_repository

    # Verify base_args structure
    expected_new_branch = f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}JIRA-123-20241224-120000"
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
    assert base_args["base_branch"] == "develop"  # target branch exists, so it's used
    assert base_args["latest_commit_sha"] == "abc123"
    assert base_args["new_branch"] == expected_new_branch
    assert base_args["installation_id"] == 98765
    assert base_args["token"] == "test-token"
    assert base_args["sender_id"] == "jira-user-123"
    assert base_args["sender_name"] == "John Doe"
    assert base_args["sender_email"] == "john.doe@example.com"
    assert base_args["is_automation"] is False
    assert base_args["reviewers"] == []
    assert base_args["github_urls"] == ["https://github.com/owner/repo/issues/1"]
    assert base_args["other_urls"] == ["https://example.com"]


@patch("services.jira.deconstruct_jira_payload.get_installation")
def test_deconstruct_jira_payload_installation_not_found(
    mock_get_installation, sample_jira_payload
):
    """Test error when installation is not found."""
    mock_get_installation.return_value = None

    with pytest.raises(ValueError, match="Installation not found for owner_id: 12345"):
        deconstruct_jira_payload(sample_jira_payload)

    mock_get_installation.assert_called_once_with(owner_id=12345)


@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_no_target_branch(
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
    """Test when repository has no target branch set."""
    # Setup mocks
    mock_get_installation.return_value = mock_installation
    mock_get_token.return_value = "test-token"
    mock_is_forked.return_value = True
    mock_get_default_branch.return_value = ("main", "def456")
    mock_get_repository.return_value = None  # No repository settings
    mock_extract_urls.return_value = ([], [])

    # Mock datetime
    mock_now = MagicMock()
    mock_now.strftime.side_effect = lambda format: {
        "%Y%m%d": "20241225",
        "%H%M%S": "130000"
    }[format]
    mock_datetime.now.return_value = mock_now

    # Call the function
    base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

    # Verify that check_branch_exists was not called since no target branch
    mock_check_branch_exists.assert_not_called()

    # Verify base branch is the default branch
    assert base_args["base_branch"] == "main"
    assert base_args["is_fork"] is True
    assert repo_settings is None


@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_target_branch_not_exists(
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
    """Test when target branch is set but doesn't exist in repository."""
    # Setup mocks
    mock_get_installation.return_value = mock_installation
    mock_get_token.return_value = "test-token"
    mock_is_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "ghi789")
    mock_get_repository.return_value = mock_repository
    mock_check_branch_exists.return_value = False  # Target branch doesn't exist
    mock_extract_urls.return_value = ([], [])

    # Mock datetime
    mock_now = MagicMock()
    mock_now.strftime.side_effect = lambda format: {
        "%Y%m%d": "20241226",
        "%H%M%S": "140000"
    }[format]
    mock_datetime.now.return_value = mock_now

    # Call the function
    base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

    # Verify that check_branch_exists was called
    mock_check_branch_exists.assert_called_once_with(
        owner="test-owner", repo="test-repo", branch_name="develop", token="test-token"
    )

    # Verify base branch is the default branch since target doesn't exist
    assert base_args["base_branch"] == "main"


@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_empty_target_branch(
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
    """Test when target branch is empty string."""
    # Setup repository with empty target branch
    mock_repo = {
        "target_branch": "",
        "repo_id": 67890,
    }

    # Setup mocks
    mock_get_installation.return_value = mock_installation
    mock_get_token.return_value = "test-token"
    mock_is_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "jkl012")
    mock_get_repository.return_value = mock_repo
    mock_extract_urls.return_value = ([], [])

    # Mock datetime
    mock_now = MagicMock()
    mock_now.strftime.side_effect = lambda format: {
        "%Y%m%d": "20241227",
        "%H%M%S": "150000"
    }[format]
    mock_datetime.now.return_value = mock_now

    # Call the function
    base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

    # Verify that check_branch_exists was not called since target branch is empty
    mock_check_branch_exists.assert_not_called()

    # Verify base branch is the default branch
    assert base_args["base_branch"] == "main"


@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_none_target_branch(
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
    """Test when target branch is None."""
    # Setup repository with None target branch
    mock_repo = {
        "target_branch": None,
        "repo_id": 67890,
    }

    # Setup mocks
    mock_get_installation.return_value = mock_installation
    mock_get_token.return_value = "test-token"
    mock_is_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "mno345")
    mock_get_repository.return_value = mock_repo
    mock_extract_urls.return_value = ([], [])

    # Mock datetime
    mock_now = MagicMock()
    mock_now.strftime.side_effect = lambda format: {
        "%Y%m%d": "20241228",
        "%H%M%S": "160000"
    }[format]
    mock_datetime.now.return_value = mock_now

    # Call the function
    base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

    # Verify that check_branch_exists was not called since target branch is None
    mock_check_branch_exists.assert_not_called()

    # Verify base branch is the default branch
    assert base_args["base_branch"] == "main"


def test_deconstruct_jira_payload_minimal_payload():
    """Test with minimal JIRA payload structure."""
    minimal_payload = {
        "cloudId": "minimal-cloud",
        "projectId": "minimal-project",
        "issue": {
            "id": "MIN-1",
            "key": "MIN-KEY",
            "title": "Minimal Title",
            "body": "Minimal body",
            "comments": [],
        },
        "creator": {
            "id": "min-user",
            "displayName": "Min User",
            "email": "min@example.com",
        },
        "reporter": {
            "id": "min-reporter",
            "displayName": "Min Reporter",
            "email": "min.reporter@example.com",
        },
        "owner": {"id": 1, "name": "min-owner"},
        "repo": {"id": 1, "name": "min-repo"},
    }

    with patch("services.jira.deconstruct_jira_payload.get_installation") as mock_get_installation:
        mock_get_installation.return_value = None

        with pytest.raises(ValueError, match="Installation not found for owner_id: 1"):
            deconstruct_jira_payload(minimal_payload)


@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_user_owner_type(
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
    """Test with User owner type instead of Organization."""
    # Setup installation with User owner type
    mock_installation = {
        "installation_id": 11111,
        "owner_type": "User",
        "owner_id": 12345,
        "owner_name": "test-user",
        "created_at": datetime.now(),
        "uninstalled_at": None,
        "created_by": "test-user",
        "uninstalled_by": None,
    }

    # Setup mocks
    mock_get_installation.return_value = mock_installation
    mock_get_token.return_value = "user-token"
    mock_is_forked.return_value = False
    mock_get_default_branch.return_value = ("master", "user123")
    mock_get_repository.return_value = None
    mock_extract_urls.return_value = ([], [])

    # Mock datetime
    mock_now = MagicMock()
    mock_now.strftime.side_effect = lambda format: {
        "%Y%m%d": "20241229",
        "%H%M%S": "170000"
    }[format]
    mock_datetime.now.return_value = mock_now

    # Call the function
    base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

    # Verify owner type is User
    assert base_args["owner_type"] == "User"
    assert base_args["installation_id"] == 11111
    assert base_args["token"] == "user-token"
    assert base_args["base_branch"] == "master"
    assert base_args["latest_commit_sha"] == "user123"


@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_complex_issue_body(
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
    """Test with complex issue body containing multiple URLs and special characters."""
    complex_payload = {
        "cloudId": "complex-cloud",
        "projectId": "complex-project",
        "issue": {
            "id": "COMPLEX-999",
            "key": "COMP-999",
            "title": "Complex Issue with Special Characters: @#$%^&*()",
            "body": """
            This is a complex issue body with:
            - Multiple GitHub URLs: https://github.com/owner1/repo1/issues/1, https://github.com/owner2/repo2/pull/2
            - External URLs: https://example.com, https://test.org/path?param=value
            - Special characters: @#$%^&*()
            - Unicode: 🚀 🎉 ✨
            - Code blocks: `code here`
            - Line breaks and formatting
            """,
            "comments": [
                "First comment with https://github.com/comment/url",
                "Second comment with special chars: @#$%",
                "Third comment with unicode: 🔥",
            ],
        },
        "creator": {
            "id": "complex-user-id",
            "displayName": "Complex User Name",
            "email": "complex.user@example.com",
        },
        "reporter": {
            "id": "complex-reporter-id",
            "displayName": "Complex Reporter",
            "email": "complex.reporter@example.com",
        },
        "owner": {"id": 99999, "name": "complex-owner"},
        "repo": {"id": 88888, "name": "complex-repo"},
    }

    # Setup mocks
    mock_get_installation.return_value = mock_installation
    mock_get_token.return_value = "complex-token"
    mock_is_forked.return_value = True
    mock_get_default_branch.return_value = ("develop", "complex123")
    mock_get_repository.return_value = None
    mock_extract_urls.return_value = (
        [
            "https://github.com/owner1/repo1/issues/1",
            "https://github.com/owner2/repo2/pull/2",
            "https://github.com/comment/url",
        ],
        ["https://example.com", "https://test.org/path?param=value"],
    )

    # Mock datetime
    mock_now = MagicMock()
    mock_now.strftime.side_effect = lambda format: {
        "%Y%m%d": "20241230",
        "%H%M%S": "180000"
    }[format]
    mock_datetime.now.return_value = mock_now

    # Call the function
    base_args, repo_settings = deconstruct_jira_payload(complex_payload)

    # Verify complex data is handled correctly
    assert base_args["issue_number"] == "COMPLEX-999"
    assert base_args["issue_title"] == "Complex Issue with Special Characters: @#$%^&*()"
    assert "Unicode: 🚀 🎉 ✨" in base_args["issue_body"]
    assert len(base_args["issue_comments"]) == 3
    assert "🔥" in base_args["issue_comments"][2]
    assert base_args["github_urls"] == [
        "https://github.com/owner1/repo1/issues/1",
        "https://github.com/owner2/repo2/pull/2",
        "https://github.com/comment/url",
    ]
    assert base_args["other_urls"] == [
        "https://example.com",
        "https://test.org/path?param=value",
    ]


@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_edge_case_empty_strings(
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
    """Test with edge case of empty strings in payload."""
    edge_case_payload = {
        "cloudId": "",
        "projectId": "",
        "issue": {
            "id": "",
            "key": "",
            "title": "",
            "body": "",
            "comments": [],
        },
        "creator": {
            "id": "",
            "displayName": "",
            "email": "",
        },
        "reporter": {
            "id": "",
            "displayName": "",
            "email": "",
        },
        "owner": {"id": 12345, "name": ""},
        "repo": {"id": 67890, "name": ""},
    }

    # Setup mocks
    mock_get_installation.return_value = mock_installation
    mock_get_token.return_value = "edge-token"
    mock_is_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "edge123")
    mock_get_repository.return_value = None
    mock_extract_urls.return_value = ([], [])

    # Mock datetime
    mock_now = MagicMock()
    mock_now.strftime.side_effect = lambda format: {
        "%Y%m%d": "20241231",
        "%H%M%S": "190000"
    }[format]
    mock_datetime.now.return_value = mock_now

    # Call the function
    base_args, repo_settings = deconstruct_jira_payload(edge_case_payload)

    # Verify empty strings are handled
    assert base_args["issue_number"] == ""
    assert base_args["issue_title"] == ""
    assert base_args["issue_body"] == ""
    assert base_args["issue_comments"] == []
    assert base_args["issuer_name"] == ""
    assert base_args["issuer_email"] == ""
    assert base_args["owner"] == ""
    assert base_args["repo"] == ""
    assert base_args["sender_id"] == ""
    assert base_args["sender_name"] == ""
    assert base_args["sender_email"] == ""
    assert base_args["github_urls"] == []
    assert base_args["other_urls"] == []


@patch("services.jira.deconstruct_jira_payload.get_installation")
def test_deconstruct_jira_payload_installation_exception(
    mock_get_installation, sample_jira_payload
):
    """Test when get_installation raises an exception."""
    mock_get_installation.side_effect = Exception("Database connection error")

    # Since the function is decorated with @handle_exceptions(raise_on_error=True),
    # it should re-raise the exception
    with pytest.raises(Exception, match="Database connection error"):
        deconstruct_jira_payload(sample_jira_payload)


@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.get_installation")
def test_deconstruct_jira_payload_token_exception(
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
    """Test when get_installation_access_token raises an exception."""
    mock_get_installation.return_value = mock_installation
    mock_get_token.side_effect = Exception("Token generation failed")

    with pytest.raises(Exception, match="Token generation failed"):
        deconstruct_jira_payload(sample_jira_payload)


@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.get_installation")
def test_deconstruct_jira_payload_is_repo_forked_exception(
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
    """Test when is_repo_forked raises an exception."""
    mock_get_installation.return_value = mock_installation
    mock_get_token.return_value = "test-token"
    mock_is_forked.side_effect = Exception("GitHub API error")

    with pytest.raises(Exception, match="GitHub API error"):
        deconstruct_jira_payload(sample_jira_payload)


@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.get_installation")
def test_deconstruct_jira_payload_get_default_branch_exception(
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
    """Test when get_default_branch raises an exception."""
    mock_get_installation.return_value = mock_installation
    mock_get_token.return_value = "test-token"
    mock_is_forked.return_value = False
    mock_get_default_branch.side_effect = Exception("Branch fetch error")

    with pytest.raises(Exception, match="Branch fetch error"):
        deconstruct_jira_payload(sample_jira_payload)


@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.get_installation")
def test_deconstruct_jira_payload_get_repository_exception(
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
    """Test when get_repository raises an exception."""
    mock_get_installation.return_value = mock_installation
    mock_get_token.return_value = "test-token"
    mock_is_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123")
    mock_get_repository.side_effect = Exception("Repository fetch error")

    with pytest.raises(Exception, match="Repository fetch error"):
        deconstruct_jira_payload(sample_jira_payload)


@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.get_installation")
def test_deconstruct_jira_payload_check_branch_exists_exception(
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
    """Test when check_branch_exists raises an exception."""
    mock_get_installation.return_value = mock_installation
    mock_get_token.return_value = "test-token"
    mock_is_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123")
    mock_get_repository.return_value = mock_repository
    mock_check_branch_exists.side_effect = Exception("Branch check error")

    with pytest.raises(Exception, match="Branch check error"):
        deconstruct_jira_payload(sample_jira_payload)


@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_extract_urls_exception(
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
    """Test when extract_urls raises an exception."""
    mock_get_installation.return_value = mock_installation
    mock_get_token.return_value = "test-token"
    mock_is_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123")
    mock_get_repository.return_value = None
    mock_extract_urls.side_effect = Exception("URL extraction error")

    # Mock datetime
    mock_now = MagicMock()
    mock_now.strftime.side_effect = lambda format: {
        "%Y%m%d": "20241224",
        "%H%M%S": "120000"
    }[format]
    mock_datetime.now.return_value = mock_now

    with pytest.raises(Exception, match="URL extraction error"):
        deconstruct_jira_payload(sample_jira_payload)


@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_datetime_exception(
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
    """Test when datetime operations raise an exception."""
    mock_get_installation.return_value = mock_installation
    mock_get_token.return_value = "test-token"
    mock_is_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123")
    mock_get_repository.return_value = None
    mock_extract_urls.return_value = ([], [])
    mock_datetime.now.side_effect = Exception("Datetime error")

    with pytest.raises(Exception, match="Datetime error"):
        deconstruct_jira_payload(sample_jira_payload)


@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_branch_name_generation(
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
    """Test branch name generation with different date/time formats."""
    mock_get_installation.return_value = mock_installation
    mock_get_token.return_value = "test-token"
    mock_is_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123")
    mock_get_repository.return_value = None
    mock_extract_urls.return_value = ([], [])

    # Mock datetime with specific values
    mock_now = MagicMock()
    mock_now.strftime.side_effect = lambda format: {
        "%Y%m%d": "20250101",
        "%H%M%S": "000000"
    }[format]
    mock_datetime.now.return_value = mock_now

    # Call the function
    base_args, _ = deconstruct_jira_payload(sample_jira_payload)

    # Verify branch name format
    expected_branch = f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}JIRA-123-20250101-000000"
    assert base_args["new_branch"] == expected_branch


@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_special_characters_in_issue_id(
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
    """Test with special characters in issue ID."""
    special_payload = {
        "cloudId": "special-cloud",
        "projectId": "special-project",
        "issue": {
            "id": "SPECIAL-123_TEST@ISSUE",
            "key": "SPEC-123",
            "title": "Special Issue",
            "body": "Special body",
            "comments": [],
        },
        "creator": {
            "id": "special-user",
            "displayName": "Special User",
            "email": "special@example.com",
        },
        "reporter": {
            "id": "special-reporter",
            "displayName": "Special Reporter",
            "email": "special.reporter@example.com",
        },
        "owner": {"id": 12345, "name": "special-owner"},
        "repo": {"id": 67890, "name": "special-repo"},
    }

    mock_get_installation.return_value = mock_installation
    mock_get_token.return_value = "test-token"
    mock_is_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123")
    mock_get_repository.return_value = None
    mock_extract_urls.return_value = ([], [])

    # Mock datetime
    mock_now = MagicMock()
    mock_now.strftime.side_effect = lambda format: {
        "%Y%m%d": "20250102",
        "%H%M%S": "123456"
    }[format]
    mock_datetime.now.return_value = mock_now

    # Call the function
    base_args, _ = deconstruct_jira_payload(special_payload)

    # Verify special characters are preserved in issue number and branch name
    assert base_args["issue_number"] == "SPECIAL-123_TEST@ISSUE"
    expected_branch = f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}SPECIAL-123_TEST@ISSUE-20250102-123456"
    assert base_args["new_branch"] == expected_branch


def test_deconstruct_jira_payload_type_casting():
    """Test type casting of installation data."""
    payload = {
        "cloudId": "cast-cloud",
        "projectId": "cast-project",
        "issue": {
            "id": "CAST-1",
            "key": "CAST-KEY",
            "title": "Cast Title",
            "body": "Cast body",
            "comments": [],
        },
        "creator": {
            "id": "cast-user",
            "displayName": "Cast User",
            "email": "cast@example.com",
        },
        "reporter": {
            "id": "cast-reporter",
            "displayName": "Cast Reporter",
            "email": "cast.reporter@example.com",
        },
        "owner": {"id": 12345, "name": "cast-owner"},
        "repo": {"id": 67890, "name": "cast-repo"},
    }

    # Test with string values that should be cast to int
    mock_installation = {
        "installation_id": "98765",  # String instead of int
        "owner_type": "Organization",
        "owner_id": 12345,
        "owner_name": "cast-owner",
        "created_at": datetime.now(),
        "uninstalled_at": None,
        "created_by": "test-user",
        "uninstalled_by": None,
    }

    with patch("services.jira.deconstruct_jira_payload.get_installation") as mock_get_installation:
        with patch("services.jira.deconstruct_jira_payload.get_installation_access_token") as mock_get_token:
            with patch("services.jira.deconstruct_jira_payload.is_repo_forked") as mock_is_forked:
                with patch("services.jira.deconstruct_jira_payload.get_default_branch") as mock_get_default_branch:
                    with patch("services.jira.deconstruct_jira_payload.get_repository") as mock_get_repository:
                        with patch("services.jira.deconstruct_jira_payload.extract_urls") as mock_extract_urls:
                            with patch("services.jira.deconstruct_jira_payload.datetime") as mock_datetime:

                                mock_get_installation.return_value = mock_installation
                                mock_get_token.return_value = "cast-token"
                                mock_is_forked.return_value = False
                                mock_get_default_branch.return_value = ("main", "cast123")
                                mock_get_repository.return_value = None
                                mock_extract_urls.return_value = ([], [])

                                # Mock datetime
                                mock_now = MagicMock()
                                mock_now.strftime.side_effect = lambda format: {
                                    "%Y%m%d": "20250103",
                                    "%H%M%S": "000000"
                                }[format]
                                mock_datetime.now.return_value = mock_now

                                # Call the function
                                base_args, _ = deconstruct_jira_payload(payload)

                                # Verify type casting worked
                                assert isinstance(base_args["installation_id"], int)
                                assert base_args["installation_id"] == 98765


@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_all_fields_populated(
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
    """Test that all BaseArgs fields are properly populated."""
    # Setup mocks
    mock_get_installation.return_value = mock_installation
    mock_get_token.return_value = "complete-token"
    mock_is_forked.return_value = True
    mock_get_default_branch.return_value = ("main", "complete123")
    mock_get_repository.return_value = mock_repository
    mock_check_branch_exists.return_value = True
    mock_extract_urls.return_value = (["github.com/test"], ["example.com"])

    # Mock datetime
    mock_now = MagicMock()
    mock_now.strftime.side_effect = lambda format: {
        "%Y%m%d": "20250104",
        "%H%M%S": "235959"
    }[format]
    mock_datetime.now.return_value = mock_now

    # Call the function
    base_args, repo_settings = deconstruct_jira_payload(sample_jira_payload)

    # Verify all required BaseArgs fields are present and have correct types
    required_fields = [
        "input_from", "owner_type", "owner_id", "owner", "repo_id", "repo",
        "clone_url", "is_fork", "issue_number", "issue_title", "issue_body",
        "issue_comments", "latest_commit_sha", "issuer_name", "base_branch",
        "new_branch", "installation_id", "token", "sender_id", "sender_name",
        "sender_email", "is_automation", "reviewers", "github_urls", "other_urls"
    ]

    for field in required_fields:
        assert field in base_args, f"Required field '{field}' is missing from base_args"

    # Verify specific field types and values
    assert isinstance(base_args["owner_id"], int)
    assert isinstance(base_args["repo_id"], int)
    assert isinstance(base_args["installation_id"], int)
    assert isinstance(base_args["is_fork"], bool)
    assert isinstance(base_args["is_automation"], bool)
    assert isinstance(base_args["issue_comments"], list)
    assert isinstance(base_args["reviewers"], list)
    assert isinstance(base_args["github_urls"], list)
    assert isinstance(base_args["other_urls"], list)

    # Verify specific values
    assert base_args["input_from"] == "jira"
    assert base_args["clone_url"] == ""
    assert base_args["is_automation"] is False
    assert base_args["reviewers"] == []
