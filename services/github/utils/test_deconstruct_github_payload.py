# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
"""Unit tests for deconstruct_github_payload function."""

from typing import Any, cast
from unittest.mock import patch

import pytest
from services.github.types.github_types import PrLabeledPayload
from services.github.users.get_user_public_email import UserPublicInfo
from services.github.utils.deconstruct_github_payload import deconstruct_github_payload


def create_mock_payload(
    pr_body=None,
    fork=False,
    pr_creator_name="test-creator",
    sender_name="test-sender",
    sender_id=12345,
    installation_id=67890,
    default_branch="main",
    pr_number=123,
    pr_title="Test PR",
    branch_name="gitauto/schedule-123-20241225-143000-XYZW",
    html_url="https://github.com/test-owner/test-repo/pull/123",
    assignees=None,
    requested_reviewers=None,
) -> PrLabeledPayload:
    return cast(
        PrLabeledPayload,
        {
            "action": "labeled",
            "number": pr_number,
            "pull_request": {
                "user": {"login": pr_creator_name},
                "body": pr_body,
                "number": pr_number,
                "title": pr_title,
                "assignees": assignees or [],
                "requested_reviewers": requested_reviewers or [],
                "head": {"ref": branch_name},
                "html_url": html_url,
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
        },
    )


@patch("services.github.utils.deconstruct_github_payload.get_clone_url")
@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_info")
def test_deconstruct_github_payload_basic_functionality(
    mock_get_user_public_info,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_clone_url,
):
    """Test basic functionality with all mocked dependencies."""
    # Setup mocks
    mock_get_clone_url.return_value = (
        "https://x-access-token:test_token@github.com/test-owner/test-repo.git"
    )
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = (["https://github.com"], ["https://example.com"])
    mock_get_user_public_info.return_value = UserPublicInfo(
        email="test@example.com", display_name="Test Sender"
    )

    # Create test payload
    payload = create_mock_payload(pr_body="Test PR body")

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify the result
    assert base_args is not None
    assert base_args["owner_type"] == "Organization"
    assert base_args["owner_id"] == 789
    assert base_args["owner"] == "test-owner"
    assert base_args["repo_id"] == 456
    assert base_args["repo"] == "test-repo"
    # clone_url must have the token embedded for git push auth
    assert base_args["clone_url"] == (
        "https://x-access-token:test_token@github.com/test-owner/test-repo.git"
    )
    mock_get_clone_url.assert_called_once_with("test-owner", "test-repo", "test_token")
    assert base_args["is_fork"] is False
    assert base_args["pr_number"] == 123
    assert base_args["pr_title"] == "Test PR"
    assert base_args["pr_body"] == "Test PR body"
    assert base_args["pr_creator"] == "test-creator"
    assert base_args["base_branch"] == "main"
    assert base_args["new_branch"] == "gitauto/schedule-123-20241225-143000-XYZW"
    assert base_args["installation_id"] == 67890
    assert base_args["token"] == "test_token"
    assert base_args["sender_id"] == 12345
    assert base_args["sender_name"] == "test-sender"
    assert base_args["sender_email"] == "test@example.com"
    assert base_args["sender_display_name"] == "Test Sender"
    assert base_args["reviewers"] == []
    assert base_args["github_urls"] == ["https://github.com"]
    assert base_args["other_urls"] == ["https://example.com"]
    # Placeholder populated by create_user_request downstream; deconstruct emits 0.
    assert base_args["usage_id"] == 0
    # Verify _
    assert _ == {"target_branch": None}

    # Verify get_repository was called with owner_id and repo_id
    mock_get_repository.assert_called_once_with(owner_id=789, repo_id=456)


@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
def test_deconstruct_github_payload_no_token_raises_error(
    mock_get_installation_access_token,
):
    """Test that ValueError is raised when no installation token is found."""
    # Setup mock to raise ValueError (get_installation_access_token now raises)
    mock_get_installation_access_token.side_effect = ValueError(
        "Installation 67890 suspended or deleted"
    )

    # Create test payload
    payload = create_mock_payload()

    # Call the function and expect ValueError to propagate
    with pytest.raises(ValueError) as excinfo:
        deconstruct_github_payload(payload)
    assert str(excinfo.value) == "Installation 67890 suspended or deleted"


@patch("services.github.utils.deconstruct_github_payload.get_clone_url")
@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_info")
def test_deconstruct_github_payload_with_empty_pr_body(
    mock_get_user_public_info,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_clone_url,
):
    """Test handling of empty PR body (None case)."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_info.return_value = UserPublicInfo(
        email="test@example.com", display_name="Test Sender"
    )

    # Create test payload with None PR body
    payload = create_mock_payload(pr_body=None)

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify empty PR body is converted to empty string
    assert base_args["pr_body"] == ""


@patch("services.github.utils.deconstruct_github_payload.get_clone_url")
@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_info")
def test_deconstruct_github_payload_with_fork_repository(
    mock_get_user_public_info,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_clone_url,
):
    """Test handling of fork repository."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_info.return_value = UserPublicInfo(
        email="test@example.com", display_name="Test Sender"
    )

    # Create test payload with fork=True
    payload = create_mock_payload(fork=True)

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify fork flag is set correctly
    assert base_args["is_fork"] is True


@patch("services.github.utils.deconstruct_github_payload.get_clone_url")
@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_info")
def test_deconstruct_github_payload_with_bot_users(
    mock_get_user_public_info,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_clone_url,
):
    """Test filtering of bot users from reviewers."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_info.return_value = UserPublicInfo(
        email="test@example.com", display_name="Test Sender"
    )

    # Create test payload with bot users
    payload = create_mock_payload(
        pr_creator_name="test-creator[bot]", sender_name="test-sender[bot]"
    )

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify bot users are filtered out from reviewers
    assert not base_args["reviewers"]


@patch("services.github.utils.deconstruct_github_payload.get_clone_url")
@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_info")
def test_deconstruct_github_payload_with_target_branch_exists(
    mock_get_user_public_info,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_clone_url,
):
    """Test using target branch when it exists in repository."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": "develop"}
    mock_check_branch_exists.return_value = True  # Target branch exists
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_info.return_value = UserPublicInfo(
        email="test@example.com", display_name="Test Sender"
    )

    # Create test payload
    payload = create_mock_payload()

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify target branch is used as base branch
    assert base_args["base_branch"] == "develop"


@patch("services.github.utils.deconstruct_github_payload.get_clone_url")
@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_info")
def test_deconstruct_github_payload_with_target_branch_not_exists(
    mock_get_user_public_info,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_clone_url,
):
    """Test falling back to default branch when target branch doesn't exist."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": "develop"}
    mock_check_branch_exists.return_value = False  # Target branch doesn't exist
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_info.return_value = UserPublicInfo(
        email="test@example.com", display_name="Test Sender"
    )

    # Create test payload
    payload = create_mock_payload()

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify default branch is used when target branch doesn't exist
    assert base_args["base_branch"] == "main"


@patch("services.github.utils.deconstruct_github_payload.get_clone_url")
@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_info")
def test_deconstruct_github_payload_no__(
    mock_get_user_public_info,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_clone_url,
):
    """Test handling when repository settings are None."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = None  # No repo settings
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_info.return_value = UserPublicInfo(
        email="test@example.com", display_name="Test Sender"
    )

    # Create test payload
    payload = create_mock_payload()

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify the result
    assert base_args["base_branch"] == "main"  # Should use default branch
    assert _ is None


@patch("services.github.utils.deconstruct_github_payload.get_clone_url")
@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_info")
def test_deconstruct_github_payload_no_target_branch_in_settings(
    mock_get_user_public_info,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_clone_url,
):
    """Test handling when target_branch is None in repository settings."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_info.return_value = UserPublicInfo(
        email="test@example.com", display_name="Test Sender"
    )

    # Create test payload
    payload = create_mock_payload()

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify the result
    assert base_args["base_branch"] == "main"  # Should use default branch
    # check_branch_exists should not be called when target_branch is None
    mock_check_branch_exists.assert_not_called()


@patch("services.github.utils.deconstruct_github_payload.get_clone_url")
@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_info")
def test_deconstruct_github_payload_duplicate_reviewers(
    mock_get_user_public_info,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_clone_url,
):
    """Test handling of duplicate reviewers (sender and PR creator are the same)."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_info.return_value = UserPublicInfo(
        email="test@example.com", display_name="Test Sender"
    )

    # Create test payload where sender and PR creator are the same
    payload = create_mock_payload(pr_creator_name="same-user", sender_name="same-user")

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # No requested_reviewers on the PR, so reviewers is empty
    assert base_args["reviewers"] == []


@patch("services.github.utils.deconstruct_github_payload.get_clone_url")
@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_info")
def test_deconstruct_github_payload_missing_fork_key(
    mock_get_user_public_info,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_clone_url,
):
    """Test handling when fork key is missing from repository (defaults to False)."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_info.return_value = UserPublicInfo(
        email="test@example.com", display_name="Test Sender"
    )

    payload: Any = create_mock_payload()
    del payload["repository"]["fork"]

    base_args, _ = deconstruct_github_payload(payload)

    # Verify fork defaults to False when key is missing
    assert base_args["is_fork"] is False


@patch("services.github.utils.deconstruct_github_payload.get_clone_url")
@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_info")
def test_deconstruct_github_payload_target_branch_used(
    mock_get_user_public_info,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_clone_url,
):
    """Test that target branch is used when it exists."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": "develop"}
    mock_check_branch_exists.return_value = True  # Target branch exists
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_info.return_value = UserPublicInfo(
        email="test@example.com", display_name="Test Sender"
    )

    # Create test payload
    payload = create_mock_payload()

    # Call the function
    base_args, _ = deconstruct_github_payload(payload)

    # Verify target branch is used
    assert base_args["base_branch"] == "develop"


@patch("services.github.utils.deconstruct_github_payload.get_clone_url")
@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_info")
def test_deconstruct_github_payload_schedule_trigger_uses_assignees_as_reviewers(
    mock_get_user_public_info,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_clone_url,
):
    """Test that schedule-triggered PRs use assignees as reviewers when sender/creator are bots."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_info.return_value = UserPublicInfo(
        email="test@example.com", display_name="Test Sender"
    )

    # Schedule trigger: both sender and PR creator are bots, but PR has a human requested reviewer
    payload = create_mock_payload(
        pr_creator_name="gitauto-ai[bot]",
        sender_name="gitauto-ai[bot]",
        requested_reviewers=[{"login": "takamori-san"}],
    )

    base_args, _ = deconstruct_github_payload(payload)

    # Verify the human requested reviewer is in the reviewers list
    assert base_args["reviewers"] == ["takamori-san"]


@patch("services.github.utils.deconstruct_github_payload.get_clone_url")
@patch("services.github.utils.deconstruct_github_payload.get_installation_access_token")
@patch("services.github.utils.deconstruct_github_payload.get_repository")
@patch("services.github.utils.deconstruct_github_payload.check_branch_exists")
@patch("services.github.utils.deconstruct_github_payload.extract_urls")
@patch("services.github.utils.deconstruct_github_payload.get_user_public_info")
def test_deconstruct_github_payload_branch_from_pr_head(
    mock_get_user_public_info,
    mock_extract_urls,
    mock_check_branch_exists,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_clone_url,
):
    """Test that branch name comes from pull_request head ref."""
    # Setup mocks
    mock_get_installation_access_token.return_value = "test_token"
    mock_get_repository.return_value = {"target_branch": None}
    mock_check_branch_exists.return_value = False
    mock_extract_urls.return_value = ([], [])
    mock_get_user_public_info.return_value = UserPublicInfo(
        email="test@example.com", display_name="Test Sender"
    )

    expected_branch = "gitauto/schedule-456-20241225-143000-XYZW"
    payload = create_mock_payload(pr_number=456, branch_name=expected_branch)

    base_args, _ = deconstruct_github_payload(payload)

    # Verify branch name comes directly from the PR head ref
    assert base_args["new_branch"] == expected_branch
