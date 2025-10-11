from unittest.mock import patch

import pytest
from config import ISSUE_NUMBER_FORMAT, PRODUCT_ID
from services.jira.deconstruct_jira_payload import deconstruct_jira_payload
from services.jira.types import JiraPayload


def create_mock_jira_payload(
    issue_id="JIRA-123",
    issue_key="JIRA-123",
    issue_title="Test Jira Issue",
    issue_body="Test issue body",
    issue_comments=None,
    creator_id="jira-user-123",
    creator_display_name="John Doe",
    creator_email="john.doe@example.com",
    owner_id=789,
    owner_name="test-owner",
    repo_id=456,
    repo_name="test-repo",
) -> JiraPayload:
    """Create a mock Jira payload for testing."""
    if issue_comments is None:
        issue_comments = []

    return {
        "cloudId": "cloud-123",
        "projectId": "project-456",
        "issue": {
            "id": issue_id,
            "key": issue_key,
            "title": issue_title,
            "body": issue_body,
            "comments": issue_comments,
        },
        "creator": {
            "id": creator_id,
            "displayName": creator_display_name,
            "email": creator_email,
        },
        "reporter": {
            "id": "reporter-123",
            "displayName": "Reporter Name",
            "email": "reporter@example.com",
        },
        "owner": {
            "id": owner_id,
            "name": owner_name,
        },
        "repo": {
            "id": repo_id,
            "name": repo_name,
        },
    }


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_basic_functionality(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test basic functionality with all mocked dependencies."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "Organization",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123def456")
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = (["https://github.com"], ["https://example.com"])
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]

    payload = create_mock_jira_payload()

    base_args, repo_settings = deconstruct_jira_payload(payload)

    assert base_args is not None
    assert base_args["input_from"] == "jira"
    assert base_args["owner_type"] == "Organization"
    assert base_args["owner_id"] == 789
    assert base_args["owner"] == "test-owner"
    assert base_args["repo_id"] == 456
    assert base_args["repo"] == "test-repo"
    assert base_args["clone_url"] == ""
    assert base_args["is_fork"] is False
    assert base_args["issue_number"] == "JIRA-123"
    assert base_args["issue_title"] == "Test Jira Issue"
    assert base_args["issue_body"] == "Test issue body"
    assert base_args["issue_comments"] == []
    assert base_args["issuer_name"] == "John Doe"
    assert base_args["issuer_email"] == "john.doe@example.com"
    assert base_args["base_branch"] == "main"
    assert base_args["latest_commit_sha"] == "abc123def456"
    assert base_args["installation_id"] == 67890
    assert base_args["token"] == "test_token"
    assert base_args["sender_id"] == "jira-user-123"
    assert base_args["sender_name"] == "John Doe"
    assert base_args["sender_email"] == "john.doe@example.com"
    assert base_args["is_automation"] is False
    assert base_args["reviewers"] == []
    assert base_args["github_urls"] == ["https://github.com"]
    assert base_args["other_urls"] == ["https://example.com"]
    assert repo_settings == {"target_branch": None}

    expected_branch = f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}JIRA-123-20241225-143000"
    assert base_args["new_branch"] == expected_branch


@patch("services.jira.deconstruct_jira_payload.get_installation")
def test_deconstruct_jira_payload_no_installation_raises_error(
    mock_get_installation,
):
    """Test that ValueError is raised when installation is not found."""
    mock_get_installation.return_value = None

    payload = create_mock_jira_payload()

    with pytest.raises(ValueError) as excinfo:
        deconstruct_jira_payload(payload)
    assert "Installation not found for owner_id: 789" in str(excinfo.value)


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_with_fork_repository(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test handling of fork repository."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "User",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = True
    mock_get_default_branch.return_value = ("main", "abc123def456")
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]

    payload = create_mock_jira_payload()

    base_args, _ = deconstruct_jira_payload(payload)

    assert base_args["is_fork"] is True
    assert base_args["owner_type"] == "User"


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_with_target_branch_exists(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test using target branch when it exists in repository."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "Organization",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123def456")
    mock_get_repository.return_value = {"target_branch": "develop"}
    mock_check_branch_exists.return_value = True
    mock_extract_urls.return_value = ([], [])
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]

    payload = create_mock_jira_payload()

    base_args, _ = deconstruct_jira_payload(payload)

    assert base_args["base_branch"] == "develop"


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_with_target_branch_not_exists(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test falling back to default branch when target branch doesn't exist."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "Organization",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123def456")
    mock_get_repository.return_value = {"target_branch": "develop"}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]

    payload = create_mock_jira_payload()

    base_args, _ = deconstruct_jira_payload(payload)

    assert base_args["base_branch"] == "main"


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_no_repo_settings(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test handling when repository settings are None."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "Organization",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123def456")
    mock_get_repository.return_value = None
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]

    payload = create_mock_jira_payload()

    base_args, repo_settings = deconstruct_jira_payload(payload)

    assert base_args["base_branch"] == "main"
    assert repo_settings is None
    mock_check_branch_exists.assert_not_called()


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_no_target_branch_in_settings(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test handling when target_branch is None in repository settings."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "Organization",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123def456")
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]

    payload = create_mock_jira_payload()

    base_args, _ = deconstruct_jira_payload(payload)

    assert base_args["base_branch"] == "main"
    mock_check_branch_exists.assert_not_called()


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_with_comments(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test handling of issue comments."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "Organization",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123def456")
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]

    comments = ["Comment 1", "Comment 2", "Comment 3"]
    payload = create_mock_jira_payload(issue_comments=comments)

    base_args, _ = deconstruct_jira_payload(payload)

    assert base_args["issue_comments"] == comments


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_branch_name_generation(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test branch name generation with specific date/time values."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "Organization",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123def456")
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_datetime.now.return_value.strftime.side_effect = ["20250101", "120000"]

    payload = create_mock_jira_payload(issue_id="PROJ-999")

    base_args, _ = deconstruct_jira_payload(payload)

    expected_branch = f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}PROJ-999-20250101-120000"
    assert base_args["new_branch"] == expected_branch


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_url_extraction(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test URL extraction from issue body."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "Organization",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123def456")
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    github_urls = ["https://github.com/owner/repo", "https://github.com/owner/repo2"]
    other_urls = ["https://example.com", "https://test.com"]
    mock_extract_urls.return_value = (github_urls, other_urls)
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]

    payload = create_mock_jira_payload(
        issue_body="Check https://github.com/owner/repo and https://example.com"
    )

    base_args, _ = deconstruct_jira_payload(payload)

    assert base_args["github_urls"] == github_urls
    assert base_args["other_urls"] == other_urls
    mock_extract_urls.assert_called_once_with(
        text="Check https://github.com/owner/repo and https://example.com"
    )


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_different_owner_types(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test handling of different owner types (User vs Organization)."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "User",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123def456")
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]

    payload = create_mock_jira_payload()

    base_args, _ = deconstruct_jira_payload(payload)

    assert base_args["owner_type"] == "User"


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_empty_issue_body(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test handling of empty issue body."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "Organization",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123def456")
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]

    payload = create_mock_jira_payload(issue_body="")

    base_args, _ = deconstruct_jira_payload(payload)

    assert base_args["issue_body"] == ""
    mock_extract_urls.assert_called_once_with(text="")


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_different_default_branches(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test handling of different default branch names."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "Organization",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = False
    mock_get_default_branch.return_value = ("master", "xyz789abc123")
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]

    payload = create_mock_jira_payload()

    base_args, _ = deconstruct_jira_payload(payload)

    assert base_args["base_branch"] == "master"
    assert base_args["latest_commit_sha"] == "xyz789abc123"


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_all_fields_populated(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test with all fields populated to ensure complete coverage."""
    mock_get_installation.return_value = {
        "installation_id": 12345,
        "owner_type": "Organization",
    }
    mock_get_installation_access_token.return_value = "access_token_xyz"
    mock_is_repo_forked.return_value = True
    mock_get_default_branch.return_value = ("develop", "commit_sha_123")
    mock_get_repository.return_value = {"target_branch": "staging"}
    mock_check_branch_exists.return_value = True
    mock_extract_urls.return_value = (
        ["https://github.com/test/repo"],
        ["https://docs.example.com"],
    )
    mock_datetime.now.return_value.strftime.side_effect = ["20250315", "093045"]

    payload = create_mock_jira_payload(
        issue_id="PROJ-456",
        issue_key="PROJ-456",
        issue_title="Complex Issue Title",
        issue_body="Detailed issue description with URLs",
        issue_comments=["Comment A", "Comment B"],
        creator_id="user-abc-123",
        creator_display_name="Jane Smith",
        creator_email="jane.smith@company.com",
        owner_id=999,
        owner_name="complex-owner",
        repo_id=888,
        repo_name="complex-repo",
    )


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_with_empty_issue_comments(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test handling of empty issue comments list."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "Organization",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123")
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]

    payload = create_mock_jira_payload(issue_comments=[])

    base_args, _ = deconstruct_jira_payload(payload)

    assert base_args["issue_comments"] == []


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_with_multiple_issue_comments(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test handling of multiple issue comments."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "Organization",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123")
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]

    comments = ["Comment 1", "Comment 2", "Comment 3"]
    payload = create_mock_jira_payload(issue_comments=comments)

    base_args, _ = deconstruct_jira_payload(payload)

    assert base_args["issue_comments"] == comments


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_with_special_characters_in_issue_body(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test handling of special characters in issue body."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "Organization",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123")
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]

    special_body = "Test with special chars: @#$%^&*()[]{}|\\<>?/~`"
    payload = create_mock_jira_payload(issue_body=special_body)

    base_args, _ = deconstruct_jira_payload(payload)

    assert base_args["issue_body"] == special_body


@patch("services.jira.deconstruct_jira_payload.get_installation")
def test_deconstruct_jira_payload_installation_not_found_error_message(
    mock_get_installation,
):
    """Test that the error message includes the owner_id when installation is not found."""
    mock_get_installation.return_value = None

    payload = create_mock_jira_payload()

    with pytest.raises(ValueError) as excinfo:
        deconstruct_jira_payload(payload)
    assert "Installation not found for owner_id: 789" in str(excinfo.value)


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_with_user_owner_type(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test handling of User owner type."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "User",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123")
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]

    payload = create_mock_jira_payload()

    base_args, _ = deconstruct_jira_payload(payload)

    assert base_args["owner_type"] == "User"


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_with_different_issue_id(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test handling of different issue IDs."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "Organization",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123")
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]

    payload = create_mock_jira_payload(issue_id="PROJ-999")

    base_args, _ = deconstruct_jira_payload(payload)

    assert base_args["issue_number"] == "PROJ-999"
    assert "PROJ-999" in base_args["new_branch"]


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_with_different_default_branch(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test handling of different default branch names."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "Organization",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = False
    mock_get_default_branch.return_value = ("master", "def456")
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]

    payload = create_mock_jira_payload()

    base_args, _ = deconstruct_jira_payload(payload)

    assert base_args["base_branch"] == "master"
    assert base_args["latest_commit_sha"] == "def456"


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_verifies_all_base_args_fields(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test that all BaseArgs fields are properly set."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "Organization",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = True
    mock_get_default_branch.return_value = ("main", "abc123")
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = (["https://github.com"], ["https://example.com"])
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]

    payload = create_mock_jira_payload()

    base_args, _ = deconstruct_jira_payload(payload)

    # Verify all required fields are present
    required_fields = [
        "input_from", "owner_type", "owner_id", "owner", "repo_id", "repo",
        "clone_url", "is_fork", "issue_number", "issue_title", "issue_body",
        "issue_comments", "issuer_name", "issuer_email", "base_branch",
        "latest_commit_sha", "new_branch", "installation_id", "token",
        "sender_id", "sender_name", "sender_email", "is_automation",
        "reviewers", "github_urls", "other_urls"
    ]

    for field in required_fields:
        assert field in base_args, f"Field {field} is missing from base_args"



@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_with_empty_comments(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test handling of empty comments list."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "Organization",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123")
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]

    payload = create_mock_jira_payload(issue_comments=[])

    base_args, _ = deconstruct_jira_payload(payload)

    assert base_args["issue_comments"] == []


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_with_multiple_comments(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test handling of multiple comments."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "Organization",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123")
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]

    comments = ["Comment 1", "Comment 2", "Comment 3"]
    payload = create_mock_jira_payload(issue_comments=comments)

    base_args, _ = deconstruct_jira_payload(payload)

    assert base_args["issue_comments"] == comments


@patch("services.jira.deconstruct_jira_payload.get_installation")
@patch("services.jira.deconstruct_jira_payload.get_installation_access_token")
@patch("services.jira.deconstruct_jira_payload.is_repo_forked")
@patch("services.jira.deconstruct_jira_payload.get_default_branch")
@patch("services.jira.deconstruct_jira_payload.get_repository")
@patch("services.jira.deconstruct_jira_payload.check_branch_exists")
@patch("services.jira.deconstruct_jira_payload.extract_urls")
@patch("services.jira.deconstruct_jira_payload.datetime")
def test_deconstruct_jira_payload_clone_url_is_empty(
    mock_datetime,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_default_branch,
    mock_is_repo_forked,
    mock_get_installation_access_token,
    mock_get_installation,
):
    """Test that clone_url is always empty string for Jira payloads."""
    mock_get_installation.return_value = {
        "installation_id": 67890,
        "owner_type": "Organization",
    }
    mock_get_installation_access_token.return_value = "test_token"
    mock_is_repo_forked.return_value = False
    mock_get_default_branch.return_value = ("main", "abc123def456")
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = (["https://github.com"], ["https://example.com"])
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]
    base_args, repo_settings = deconstruct_jira_payload(payload)

    # Verify clone_url is empty string
    assert base_args is not None
    assert base_args["input_from"] == "jira"
    assert base_args["clone_url"] == ""
