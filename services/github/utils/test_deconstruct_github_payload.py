"""Unit tests for deconstruct_github_payload function."""

from typing import Any, cast
from unittest.mock import patch

import pytest
from config import GITHUB_APP_USER_ID, ISSUE_NUMBER_FORMAT, PRODUCT_ID
from services.github.types.github_types import GitHubLabeledPayload
from services.github.utils.deconstruct_github_payload import deconstruct_github_payload


def create_mock_payload(
    issue_body=None,
    fork=False,
    issuer_name="test-issuer",
    sender_name="test-sender",
    sender_id=12345,
    installation_id=67890,
    default_branch="main",
    issue_number=123,
    issue_title="Test Issue",
) -> GitHubLabeledPayload:
    return cast(GitHubLabeledPayload, {
        "action": "labeled",
        "issue": {
            "user": {"login": issuer_name},
            "body": issue_body,
            "number": issue_number,
            "title": issue_title,
        },
        "repository": {
            "id": 456,
            "name": "test-repo",
            "clone_url": "https://github.com/test-owner/test-repo.git",
            "fork": fork,
            "default_branch": default_branch,
            "owner": {
                "type": "Organization",
                "login": "test-owner",
                "id": 789,
            },
        },
        "sender": {
            "id": sender_id,
            "login": sender_name,
        },
        "installation": {
            "id": installation_id,
        },
    })


@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_email")
@patch("services.github.utils.deconstruct_github_payload.get_parent_issue")
@patch("services.github.utils.deconstruct_github_payload.datetime")
@patch("services.github.utils.deconstruct_github_payload.choices")
def test_deconstruct_github_payload_basic_functionality(
    mock_choices,
    mock_datetime,
    mock_get_parent_issue,
    mock_get_user_public_email,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
):
    """Test basic functionality with all mocked dependencies."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = (["https://github.com"], ["https://example.com"])
    mock_get_user_public_email.return_value = "test@example.com"
    mock_get_parent_issue.return_value = None
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]
    mock_choices.return_value = ["X", "Y", "Z", "W"]

    # Create test payload
    payload = create_mock_payload(issue_body="Test issue body")

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify the result
    assert base_args is not None
    assert base_args["owner_type"] == "Organization"
    assert base_args["owner_id"] == 789
    assert base_args["owner"] == "test-owner"
    assert base_args["repo_id"] == 456
    assert base_args["repo"] == "test-repo"
    assert base_args["clone_url"] == "https://github.com/test-owner/test-repo.git"
    assert base_args["is_fork"] is False
    assert base_args["issue_number"] == 123
    assert base_args["issue_title"] == "Test Issue"
    assert base_args["issue_body"] == "Test issue body"
    assert base_args["issuer_name"] == "test-issuer"
    assert base_args["base_branch"] == "main"
    assert base_args["installation_id"] == 67890
    assert base_args["token"] == "test_token"
    assert base_args["sender_id"] == 12345
    assert base_args["sender_name"] == "test-sender"
    assert base_args["sender_email"] == "test@example.com"
    assert base_args["is_automation"] is False
    assert set(base_args["reviewers"]) == {"test-sender", "test-issuer"}
    assert base_args["github_urls"] == ["https://github.com"]
    assert base_args["other_urls"] == ["https://example.com"]
    assert base_args["input_from"] == "github"
    assert base_args["parent_issue_number"] is None
    assert base_args["parent_issue_title"] is None
    assert base_args["parent_issue_body"] is None

    # Verify _
    assert _ == {"target_branch": None}

    # Verify get_repository was called with owner_id and repo_id
    mock_get_repository.assert_called_once_with(owner_id=789, repo_id=456)


@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
def test_deconstruct_github_payload_no_token_raises_error(
    mock_get_installation_access_token,
):
    """Test that ValueError is raised when no installation token is found."""
    # Setup mock to return None (no token)
    mock_get_installation_access_token.return_value = None

    # Create test payload
    payload = create_mock_payload()

    # Call the function and expect ValueError
    with pytest.raises(ValueError) as excinfo:
        deconstruct_github_payload(payload)
    assert "Installation access token is not found for test-owner/test-repo" in str(
        excinfo.value
    )


@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_email")
@patch("services.github.utils.deconstruct_github_payload.get_parent_issue")
@patch("services.github.utils.deconstruct_github_payload.datetime")
@patch("services.github.utils.deconstruct_github_payload.choices")
def test_deconstruct_github_payload_with_empty_issue_body(
    mock_choices,
    mock_datetime,
    mock_get_parent_issue,
    mock_get_user_public_email,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
):
    """Test handling of empty issue body (None case)."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_email.return_value = "test@example.com"
    mock_get_parent_issue.return_value = None
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]
    mock_choices.return_value = ["A", "B", "C", "D"]

    # Create test payload with None issue body
    payload = create_mock_payload(issue_body=None)

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify empty issue body is converted to empty string
    assert base_args["issue_body"] == ""


@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_email")
@patch("services.github.utils.deconstruct_github_payload.get_parent_issue")
@patch("services.github.utils.deconstruct_github_payload.datetime")
@patch("services.github.utils.deconstruct_github_payload.choices")
def test_deconstruct_github_payload_with_fork_repository(
    mock_choices,
    mock_datetime,
    mock_get_parent_issue,
    mock_get_user_public_email,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
):
    """Test handling of fork repository."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_email.return_value = "test@example.com"
    mock_get_parent_issue.return_value = None
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]
    mock_choices.return_value = ["A", "B", "C", "D"]

    # Create test payload with fork=True
    payload = create_mock_payload(fork=True)

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify fork flag is set correctly
    assert base_args["is_fork"] is True


@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_email")
@patch("services.github.utils.deconstruct_github_payload.get_parent_issue")
@patch("services.github.utils.deconstruct_github_payload.datetime")
@patch("services.github.utils.deconstruct_github_payload.choices")
def test_deconstruct_github_payload_with_bot_users(
    mock_choices,
    mock_datetime,
    mock_get_parent_issue,
    mock_get_user_public_email,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
):
    """Test filtering of bot users from reviewers."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_email.return_value = "test@example.com"
    mock_get_parent_issue.return_value = None
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]
    mock_choices.return_value = ["A", "B", "C", "D"]

    # Create test payload with bot users
    payload = create_mock_payload(
        issuer_name="test-issuer[bot]", sender_name="test-sender[bot]"
    )

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify bot users are filtered out from reviewers
    assert not base_args["reviewers"]


@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_email")
@patch("services.github.utils.deconstruct_github_payload.get_parent_issue")
@patch("services.github.utils.deconstruct_github_payload.datetime")
@patch("services.github.utils.deconstruct_github_payload.choices")
def test_deconstruct_github_payload_with_target_branch_exists(
    mock_choices,
    mock_datetime,
    mock_get_parent_issue,
    mock_get_user_public_email,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
):
    """Test using target branch when it exists in repository."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": "develop"}
    mock_check_branch_exists.return_value = True  # Target branch exists
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_email.return_value = "test@example.com"
    mock_get_parent_issue.return_value = None
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]
    mock_choices.return_value = ["A", "B", "C", "D"]

    # Create test payload
    payload = create_mock_payload()

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify target branch is used as base branch
    assert base_args["base_branch"] == "develop"


@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_email")
@patch("services.github.utils.deconstruct_github_payload.get_parent_issue")
@patch("services.github.utils.deconstruct_github_payload.datetime")
@patch("services.github.utils.deconstruct_github_payload.choices")
def test_deconstruct_github_payload_with_target_branch_not_exists(
    mock_choices,
    mock_datetime,
    mock_get_parent_issue,
    mock_get_user_public_email,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
):
    """Test falling back to default branch when target branch doesn't exist."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": "develop"}
    mock_check_branch_exists.return_value = False  # Target branch doesn't exist
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_email.return_value = "test@example.com"
    mock_get_parent_issue.return_value = None
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]
    mock_choices.return_value = ["A", "B", "C", "D"]

    # Create test payload
    payload = create_mock_payload()

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify default branch is used when target branch doesn't exist
    assert base_args["base_branch"] == "main"


@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_email")
@patch("services.github.utils.deconstruct_github_payload.get_parent_issue")
@patch("services.github.utils.deconstruct_github_payload.datetime")
@patch("services.github.utils.deconstruct_github_payload.choices")
def test_deconstruct_github_payload_with_parent_issue_data(
    mock_choices,
    mock_datetime,
    mock_get_parent_issue,
    mock_get_user_public_email,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
):
    """Test handling of parent issue data."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_email.return_value = "test@example.com"
    parent_issue = {
        "number": 456,
        "title": "Parent Issue",
        "body": "Parent issue body",
    }
    mock_get_parent_issue.return_value = parent_issue
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]
    mock_choices.return_value = ["A", "B", "C", "D"]

    # Create test payload
    payload = create_mock_payload()

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify parent issue data is extracted correctly
    assert base_args["parent_issue_number"] == 456
    assert base_args["parent_issue_title"] == "Parent Issue"
    assert base_args["parent_issue_body"] == "Parent issue body"


@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_email")
@patch("services.github.utils.deconstruct_github_payload.get_parent_issue")
@patch("services.github.utils.deconstruct_github_payload.datetime")
@patch("services.github.utils.deconstruct_github_payload.choices")
def test_deconstruct_github_payload_with_automation_user(
    mock_choices,
    mock_datetime,
    mock_get_parent_issue,
    mock_get_user_public_email,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
):
    """Test detection of automation user."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_email.return_value = "test@example.com"
    mock_get_parent_issue.return_value = None
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]
    mock_choices.return_value = ["A", "B", "C", "D"]

    # Create test payload with automation user (using GITHUB_APP_USER_ID from config)
    payload = create_mock_payload(sender_id=GITHUB_APP_USER_ID)

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify automation is detected
    assert base_args["is_automation"] is True


@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_email")
@patch("services.github.utils.deconstruct_github_payload.get_parent_issue")
@patch("services.github.utils.deconstruct_github_payload.datetime")
@patch("services.github.utils.deconstruct_github_payload.choices")
def test_deconstruct_github_payload_no__(
    mock_choices,
    mock_datetime,
    mock_get_parent_issue,
    mock_get_user_public_email,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
):
    """Test handling when repository settings are None."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = None  # No repo settings
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_email.return_value = "test@example.com"
    mock_get_parent_issue.return_value = None
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]
    mock_choices.return_value = ["A", "B", "C", "D"]

    # Create test payload
    payload = create_mock_payload()

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify the result
    assert base_args["base_branch"] == "main"  # Should use default branch
    assert _ is None


@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_email")
@patch("services.github.utils.deconstruct_github_payload.get_parent_issue")
@patch("services.github.utils.deconstruct_github_payload.datetime")
@patch("services.github.utils.deconstruct_github_payload.choices")
def test_deconstruct_github_payload_no_target_branch_in_settings(
    mock_choices,
    mock_datetime,
    mock_get_parent_issue,
    mock_get_user_public_email,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
):
    """Test handling when target_branch is None in repository settings."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_email.return_value = "test@example.com"
    mock_get_parent_issue.return_value = None
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]
    mock_choices.return_value = ["A", "B", "C", "D"]

    # Create test payload
    payload = create_mock_payload()

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify the result
    assert base_args["base_branch"] == "main"  # Should use default branch
    # check_branch_exists should not be called when target_branch is None
    mock_check_branch_exists.assert_not_called()


@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_email")
@patch("services.github.utils.deconstruct_github_payload.get_parent_issue")
@patch("services.github.utils.deconstruct_github_payload.datetime")
@patch("services.github.utils.deconstruct_github_payload.choices")
def test_deconstruct_github_payload_branch_name_generation(
    mock_choices,
    mock_datetime,
    mock_get_parent_issue,
    mock_get_user_public_email,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
):
    """Test branch name generation with specific date/time/random values."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_email.return_value = "test@example.com"
    mock_get_parent_issue.return_value = None

    # Mock specific datetime values
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]
    mock_choices.return_value = ["X", "Y", "Z", "W"]

    # Create test payload with specific issue number
    payload = create_mock_payload(issue_number=456)

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify branch name generation
    expected_branch = f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}456-20241225-143000-XYZW"
    assert base_args["new_branch"] == expected_branch


@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_email")
@patch("services.github.utils.deconstruct_github_payload.get_parent_issue")
@patch("services.github.utils.deconstruct_github_payload.datetime")
@patch("services.github.utils.deconstruct_github_payload.choices")
def test_deconstruct_github_payload_duplicate_reviewers(
    mock_choices,
    mock_datetime,
    mock_get_parent_issue,
    mock_get_user_public_email,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
):
    """Test handling of duplicate reviewers (sender and issuer are the same)."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_email.return_value = "test@example.com"
    mock_get_parent_issue.return_value = None
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]
    mock_choices.return_value = ["A", "B", "C", "D"]

    # Create test payload where sender and issuer are the same
    payload = create_mock_payload(issuer_name="same-user", sender_name="same-user")

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify duplicate reviewers are handled (set removes duplicates)
    assert base_args["reviewers"] == ["same-user"]


@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_email")
@patch("services.github.utils.deconstruct_github_payload.get_parent_issue")
@patch("services.github.utils.deconstruct_github_payload.datetime")
@patch("services.github.utils.deconstruct_github_payload.choices")
def test_deconstruct_github_payload_missing_fork_key(
    mock_choices,
    mock_datetime,
    mock_get_parent_issue,
    mock_get_user_public_email,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
):
    """Test handling when fork key is missing from repository (defaults to False)."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_email.return_value = "test@example.com"
    mock_get_parent_issue.return_value = None
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]
    mock_choices.return_value = ["A", "B", "C", "D"]

    payload: Any = create_mock_payload()
    del payload["repository"]["fork"]

    base_args, _ = deconstruct_github_payload(payload)

    # Verify fork defaults to False when key is missing
    assert base_args["is_fork"] is False


@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_email")
@patch("services.github.utils.deconstruct_github_payload.get_parent_issue")
@patch("services.github.utils.deconstruct_github_payload.datetime")
@patch("services.github.utils.deconstruct_github_payload.choices")
@patch("builtins.print")
def test_deconstruct_github_payload_target_branch_print_statement(
    mock_print,
    mock_choices,
    mock_datetime,
    mock_get_parent_issue,
    mock_get_user_public_email,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
):
    """Test that print statement is called when using target branch."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": "develop"}
    mock_check_branch_exists.return_value = True  # Target branch exists
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_email.return_value = "test@example.com"
    mock_get_parent_issue.return_value = None
    mock_datetime.now.return_value.strftime.side_effect = ["20241225", "143000"]
    mock_choices.return_value = ["A", "B", "C", "D"]

    # Create test payload
    payload = create_mock_payload()

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify print statement was called
    mock_print.assert_called_once_with("Using target branch: develop")
    assert base_args["base_branch"] == "develop"
