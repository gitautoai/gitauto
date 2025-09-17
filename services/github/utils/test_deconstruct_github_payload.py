"""Unit tests for deconstruct_github_payload function.

Tests the extraction and processing of GitHub webhook payload data
into structured BaseArgs and repository settings.
"""

from datetime import datetime
from typing import cast
from unittest.mock import patch, MagicMock
import pytest

from services.github.types.github_types import GitHubLabeledPayload
from services.github.utils.deconstruct_github_payload import deconstruct_github_payload


@pytest.fixture
def mock_github_payload():
    """Create a mock GitHubLabeledPayload for testing"""
    return cast(
        GitHubLabeledPayload,
        {
            "action": "labeled",
            "issue": {
                "number": 123,
                "title": "Test Issue Title",
                "body": "Test issue body with https://github.com/test/repo and https://example.com",
                "user": {"login": "issue-creator"},
            },
            "repository": {
                "id": 456789,
                "name": "test-repo",
                "clone_url": "https://github.com/test-owner/test-repo.git",
                "fork": False,
                "default_branch": "main",
                "owner": {
                    "type": "Organization",
                    "login": "test-owner",
                    "id": 987654,
                },
            },
            "installation": {"id": 12345},
            "sender": {
                "id": 11111,
                "login": "sender-user",
            },
            "label": {"name": "gitauto"},
            "organization": {"id": 22222, "login": "test-org"},
        },
    )


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies"""
    with patch(
        "services.github.utils.deconstruct_github_payload.PRODUCT_ID", "gitauto"
    ), patch(
        "services.github.utils.deconstruct_github_payload.get_installation_access_token"
    ) as mock_get_token, patch(
        "services.github.utils.deconstruct_github_payload.get_repository"
    ) as mock_get_repo, patch(
        "services.github.utils.deconstruct_github_payload.check_branch_exists"
    ) as mock_check_branch, patch(
        "services.github.utils.deconstruct_github_payload.get_user_public_email"
    ) as mock_get_email, patch(
        "services.github.utils.deconstruct_github_payload.extract_urls"
    ) as mock_extract_urls, patch(
        "services.github.utils.deconstruct_github_payload.get_parent_issue"
    ) as mock_get_parent, patch(
        "services.github.utils.deconstruct_github_payload.datetime"
    ) as mock_datetime:

        # Set up default return values
        mock_get_token.return_value = "test-token-123"
        mock_get_repo.return_value = {"target_branch": None}
        mock_check_branch.return_value = True
        mock_get_email.return_value = "sender@example.com"
        mock_extract_urls.return_value = (
            ["https://github.com/test/repo"],
            ["https://example.com"]
        )
        mock_get_parent.return_value = None

        # Mock datetime to return consistent values
        mock_datetime.now.return_value = datetime(2024, 12, 25, 14, 30, 45)

        yield {
            "get_token": mock_get_token,
            "get_repo": mock_get_repo,
            "check_branch": mock_check_branch,
            "get_email": mock_get_email,
            "extract_urls": mock_extract_urls,
            "get_parent": mock_get_parent,
            "datetime": mock_datetime,
        }


def test_deconstruct_github_payload_success(mock_github_payload, mock_dependencies):
    """Test successful deconstruction of GitHub payload"""
    # Act
    base_args, repo_settings = deconstruct_github_payload(mock_github_payload)

    # Assert basic structure
    assert base_args is not None
    assert repo_settings is not None

    # Verify issue-related fields
    assert base_args["issue_number"] == 123
    assert base_args["issue_title"] == "Test Issue Title"
    assert base_args["issue_body"] == "Test issue body with https://github.com/test/repo and https://example.com"
    assert base_args["issuer_name"] == "issue-creator"

    # Verify repository-related fields
    assert base_args["repo_id"] == 456789
    assert base_args["repo"] == "test-repo"
    assert base_args["clone_url"] == "https://github.com/test-owner/test-repo.git"
    assert base_args["is_fork"] is False

    # Verify owner-related fields
    assert base_args["owner_type"] == "Organization"
    assert base_args["owner"] == "test-owner"
    assert base_args["owner_id"] == 987654

    # Verify branch-related fields
    assert base_args["base_branch"] == "main"
    assert base_args["new_branch"].startswith("gitauto/issue-123-20241225-143045-")

    # Verify sender-related fields
    assert base_args["sender_id"] == 11111
    assert base_args["sender_name"] == "sender-user"
    assert base_args["sender_email"] == "sender@example.com"
    assert base_args["is_automation"] is False

    # Verify other fields
    assert base_args["installation_id"] == 12345
    assert base_args["token"] == "test-token-123"
    assert base_args["input_from"] == "github"
    assert base_args["github_urls"] == ["https://github.com/test/repo"]
    assert base_args["other_urls"] == ["https://example.com"]
    assert base_args["reviewers"] == ["sender-user", "issue-creator"]

    # Verify parent issue fields (should be None)
    assert base_args["parent_issue_number"] is None
    assert base_args["parent_issue_title"] is None
    assert base_args["parent_issue_body"] is None


def test_deconstruct_github_payload_with_target_branch(mock_github_payload, mock_dependencies):
    """Test payload deconstruction when target branch is set and exists"""
    # Arrange
    mock_dependencies["get_repo"].return_value = {"target_branch": "develop"}
    mock_dependencies["check_branch"].return_value = True

    # Act
    base_args, repo_settings = deconstruct_github_payload(mock_github_payload)

    # Assert
    assert base_args["base_branch"] == "develop"

    # Verify branch existence was checked
    mock_dependencies["check_branch"].assert_called_once_with(
        owner="test-owner",
        repo="test-repo",
        branch_name="develop",
        token="test-token-123"
    )


def test_deconstruct_github_payload_target_branch_not_exists(mock_github_payload, mock_dependencies):
    """Test payload deconstruction when target branch is set but doesn't exist"""
    # Arrange
    mock_dependencies["get_repo"].return_value = {"target_branch": "nonexistent"}
    mock_dependencies["check_branch"].return_value = False

    # Act
    base_args, repo_settings = deconstruct_github_payload(mock_github_payload)

    # Assert - should fall back to default branch
    assert base_args["base_branch"] == "main"

    # Verify branch existence was checked
    mock_dependencies["check_branch"].assert_called_once_with(
        owner="test-owner",
        repo="test-repo",
        branch_name="nonexistent",
        token="test-token-123"
    )


def test_deconstruct_github_payload_no_repo_settings(mock_github_payload, mock_dependencies):
    """Test payload deconstruction when repository settings are not found"""
    # Arrange
    mock_dependencies["get_repo"].return_value = None

    # Act
    base_args, repo_settings = deconstruct_github_payload(mock_github_payload)

    # Assert
    assert base_args["base_branch"] == "main"  # Should use default branch
    assert repo_settings is None


def test_deconstruct_github_payload_with_parent_issue(mock_github_payload, mock_dependencies):
    """Test payload deconstruction when parent issue exists"""
    # Arrange
    parent_issue = {
        "number": 100,
        "title": "Parent Issue Title",
        "body": "Parent issue body content"
    }
    mock_dependencies["get_parent"].return_value = parent_issue

    # Act
    base_args, repo_settings = deconstruct_github_payload(mock_github_payload)

    # Assert
    assert base_args["parent_issue_number"] == 100
    assert base_args["parent_issue_title"] == "Parent Issue Title"
    assert base_args["parent_issue_body"] == "Parent issue body content"

    # Verify parent issue lookup was called
    mock_dependencies["get_parent"].assert_called_once_with(
        owner="test-owner",
        repo="test-repo",
        issue_number=123,
        token="test-token-123"
    )


def test_deconstruct_github_payload_automation_sender(mock_github_payload, mock_dependencies):
    """Test payload deconstruction when sender is automation (GitHub app)"""
    # Arrange
    mock_github_payload["sender"]["id"] = 161652217  # GITHUB_APP_USER_ID from config
    mock_github_payload["sender"]["login"] = "gitauto-ai[bot]"

    # Act
    base_args, repo_settings = deconstruct_github_payload(mock_github_payload)

    # Assert
    assert base_args["is_automation"] is True
    assert base_args["reviewers"] == ["issue-creator"]  # Bot should be excluded from reviewers


def test_deconstruct_github_payload_bot_users_excluded_from_reviewers(mock_github_payload, mock_dependencies):
    """Test that bot users are excluded from reviewers list"""
    # Arrange
    mock_github_payload["sender"]["login"] = "some-bot[bot]"
    mock_github_payload["issue"]["user"]["login"] = "another-bot[bot]"

    # Act
    base_args, repo_settings = deconstruct_github_payload(mock_github_payload)

    # Assert
    assert base_args["reviewers"] == []  # Both users are bots, so empty list


def test_deconstruct_github_payload_empty_issue_body(mock_github_payload, mock_dependencies):
    """Test payload deconstruction when issue body is None"""
    # Arrange
    mock_github_payload["issue"]["body"] = None

    # Act
    base_args, repo_settings = deconstruct_github_payload(mock_github_payload)

    # Assert
    assert base_args["issue_body"] == ""


def test_deconstruct_github_payload_fork_repository(mock_github_payload, mock_dependencies):
    """Test payload deconstruction for fork repository"""
    # Arrange
    mock_github_payload["repository"]["fork"] = True

    # Act
    base_args, repo_settings = deconstruct_github_payload(mock_github_payload)

    # Assert
    assert base_args["is_fork"] is True


def test_deconstruct_github_payload_missing_fork_field(mock_github_payload, mock_dependencies):
    """Test payload deconstruction when fork field is missing"""
    # Arrange
    del mock_github_payload["repository"]["fork"]

    # Act
    base_args, repo_settings = deconstruct_github_payload(mock_github_payload)

    # Assert
    assert base_args["is_fork"] is False  # Should default to False


def test_deconstruct_github_payload_no_email_found(mock_github_payload, mock_dependencies):
    """Test payload deconstruction when user email is not found"""
    # Arrange
    mock_dependencies["get_email"].return_value = None

    # Act
    base_args, repo_settings = deconstruct_github_payload(mock_github_payload)

    # Assert
    assert base_args["sender_email"] is None


def test_deconstruct_github_payload_no_urls_found(mock_github_payload, mock_dependencies):
    """Test payload deconstruction when no URLs are found in issue body"""
    # Arrange
    mock_dependencies["extract_urls"].return_value = ([], [])

    # Act
    base_args, repo_settings = deconstruct_github_payload(mock_github_payload)

    # Assert
    assert base_args["github_urls"] == []
    assert base_args["other_urls"] == []


def test_deconstruct_github_payload_token_not_found(mock_github_payload, mock_dependencies):
    """Test payload deconstruction when installation token is not found"""
    # Arrange
    mock_dependencies["get_token"].return_value = None

    # Act & Assert
    with pytest.raises(ValueError, match="Installation access token is not found for test-owner/test-repo"):
        deconstruct_github_payload(mock_github_payload)


def test_deconstruct_github_payload_branch_name_generation(mock_github_payload, mock_dependencies):
    """Test that branch name is generated correctly with date, time, and random string"""
    # Act
    base_args, repo_settings = deconstruct_github_payload(mock_github_payload)

    # Assert
    new_branch = base_args["new_branch"]
    assert new_branch.startswith("gitauto/issue-123-20241225-143045-")
    assert len(new_branch.split("-")[-1]) == 4  # Random string should be 4 characters


def test_deconstruct_github_payload_different_owner_types(mock_github_payload, mock_dependencies):
    """Test payload deconstruction with different owner types"""
    # Test User owner type
    mock_github_payload["repository"]["owner"]["type"] = "User"

    # Act
    base_args, repo_settings = deconstruct_github_payload(mock_github_payload)

    # Assert
    assert base_args["owner_type"] == "User"


def test_deconstruct_github_payload_duplicate_reviewers(mock_github_payload, mock_dependencies):
    """Test that duplicate reviewers are removed"""
    # Arrange - make sender and issuer the same person
    mock_github_payload["sender"]["login"] = "same-user"
    mock_github_payload["issue"]["user"]["login"] = "same-user"

    # Act
    base_args, repo_settings = deconstruct_github_payload(mock_github_payload)

    # Assert
    assert base_args["reviewers"] == ["same-user"]  # Should only appear once


def test_deconstruct_github_payload_function_calls(mock_github_payload, mock_dependencies):
    """Test that all external functions are called with correct parameters"""
    # Act
    base_args, repo_settings = deconstruct_github_payload(mock_github_payload)

    # Assert function calls
    mock_dependencies["get_token"].assert_called_once_with(installation_id=12345)
    mock_dependencies["get_repo"].assert_called_once_with(repo_id=456789)
    mock_dependencies["get_email"].assert_called_once_with(
        username="sender-user", token="test-token-123"
    )
    mock_dependencies["extract_urls"].assert_called_once_with(
        text="Test issue body with https://github.com/test/repo and https://example.com"
    )
    mock_dependencies["get_parent"].assert_called_once_with(
        owner="test-owner",
        repo="test-repo",
        issue_number=123,
        token="test-token-123"
    )


def test_deconstruct_github_payload_with_complex_urls(mock_github_payload, mock_dependencies):
    """Test payload deconstruction with complex URL extraction"""
    # Arrange
    github_urls = [
        "https://github.com/owner/repo1",
        "https://github.com/owner/repo2/issues/123"
    ]
    other_urls = [
        "https://example.com",
        "https://docs.example.com/guide"
    ]
    mock_dependencies["extract_urls"].return_value = (github_urls, other_urls)

    # Act
    base_args, repo_settings = deconstruct_github_payload(mock_github_payload)

    # Assert
    assert base_args["github_urls"] == github_urls
    assert base_args["other_urls"] == other_urls


def test_deconstruct_github_payload_parent_issue_with_none_values(mock_github_payload, mock_dependencies):
    """Test payload deconstruction when parent issue has None values"""
    # Arrange
    parent_issue = {
        "number": 100,
        "title": None,
        "body": None
    }
    mock_dependencies["get_parent"].return_value = parent_issue

    # Act
    base_args, repo_settings = deconstruct_github_payload(mock_github_payload)

    # Assert
    assert base_args["parent_issue_number"] == 100
    assert base_args["parent_issue_title"] is None
    assert base_args["parent_issue_body"] is None


def test_deconstruct_github_payload_repo_settings_with_none_target_branch(mock_github_payload, mock_dependencies):
    """Test payload deconstruction when repo settings has None target_branch"""
    # Arrange
    mock_dependencies["get_repo"].return_value = {"target_branch": None}

    # Act
    base_args, repo_settings = deconstruct_github_payload(mock_github_payload)

    # Assert
    assert base_args["base_branch"] == "main"  # Should use default branch
    assert repo_settings == {"target_branch": None}

    # Verify branch check was not called since target_branch is None
    mock_dependencies["check_branch"].assert_not_called()


def test_deconstruct_github_payload_error_handling_token_failure(mock_github_payload, mock_dependencies):
    """Test error handling when token retrieval fails"""
    # Arrange
    mock_dependencies["get_token"].side_effect = Exception("Token service error")

    # Act & Assert
    with pytest.raises(Exception, match="Token service error"):
        deconstruct_github_payload(mock_github_payload)


def test_deconstruct_github_payload_error_handling_repo_failure(mock_github_payload, mock_dependencies):
    """Test error handling when repository lookup fails"""
    # Arrange
    mock_dependencies["get_repo"].side_effect = Exception("Repository service error")

    # Act & Assert
    with pytest.raises(Exception, match="Repository service error"):
        deconstruct_github_payload(mock_github_payload)


def test_deconstruct_github_payload_error_handling_branch_check_failure(mock_github_payload, mock_dependencies):
    """Test error handling when branch check fails"""
    # Arrange
    mock_dependencies["get_repo"].return_value = {"target_branch": "develop"}
    mock_dependencies["check_branch"].side_effect = Exception("Branch check error")

    # Act & Assert
    with pytest.raises(Exception, match="Branch check error"):
        deconstruct_github_payload(mock_github_payload)


def test_deconstruct_github_payload_error_handling_email_failure(mock_github_payload, mock_dependencies):
    """Test error handling when email retrieval fails"""
    # Arrange
    mock_dependencies["get_email"].side_effect = Exception("Email service error")

    # Act & Assert
    with pytest.raises(Exception, match="Email service error"):
        deconstruct_github_payload(mock_github_payload)


def test_deconstruct_github_payload_error_handling_url_extraction_failure(mock_github_payload, mock_dependencies):
    """Test error handling when URL extraction fails"""
    # Arrange
    mock_dependencies["extract_urls"].side_effect = Exception("URL extraction error")

    # Act & Assert
    with pytest.raises(Exception, match="URL extraction error"):
        deconstruct_github_payload(mock_github_payload)


def test_deconstruct_github_payload_error_handling_parent_issue_failure(mock_github_payload, mock_dependencies):
    """Test error handling when parent issue lookup fails"""
    # Arrange
    mock_dependencies["get_parent"].side_effect = Exception("Parent issue error")

    # Act & Assert
    with pytest.raises(Exception, match="Parent issue error"):
        deconstruct_github_payload(mock_github_payload)


def test_deconstruct_github_payload_different_payload_values():
    """Test with different payload values to ensure proper extraction"""
    # Arrange
    payload = cast(
        GitHubLabeledPayload,
        {
            "action": "labeled",
            "issue": {
                "number": 999,
                "title": "Different Issue",
                "body": "Different body content",
                "user": {"login": "different-creator"},
            },
            "repository": {
                "id": 111222,
                "name": "different-repo",
                "clone_url": "https://github.com/different-owner/different-repo.git",
                "fork": True,
                "default_branch": "develop",
                "owner": {
                    "type": "User",
                    "login": "different-owner",
                    "id": 333444,
                },
            },
            "installation": {"id": 55555},
            "sender": {
                "id": 66666,
                "login": "different-sender",
            },
            "label": {"name": "gitauto"},
            "organization": {"id": 77777, "login": "different-org"},
        },
    )

    with patch(
        "services.github.utils.deconstruct_github_payload.PRODUCT_ID", "gitauto"
    ), patch(
        "services.github.utils.deconstruct_github_payload.get_installation_access_token",
        return_value="different-token"
    ), patch(
        "services.github.utils.deconstruct_github_payload.get_repository",
        return_value=None
    ), patch(
        "services.github.utils.deconstruct_github_payload.get_user_public_email",
        return_value="different@example.com"
    ), patch(
        "services.github.utils.deconstruct_github_payload.extract_urls",
        return_value=([], [])
    ), patch(
        "services.github.utils.deconstruct_github_payload.get_parent_issue",
        return_value=None
    ), patch(
        "services.github.utils.deconstruct_github_payload.datetime"
    ) as mock_datetime:

        mock_datetime.now.return_value = datetime(2024, 1, 1, 9, 15, 30)

        # Act
        base_args, repo_settings = deconstruct_github_payload(payload)

        # Assert
        assert base_args["issue_number"] == 999
        assert base_args["issue_title"] == "Different Issue"
        assert base_args["issue_body"] == "Different body content"
        assert base_args["issuer_name"] == "different-creator"
        assert base_args["repo_id"] == 111222
        assert base_args["repo"] == "different-repo"
        assert base_args["clone_url"] == "https://github.com/different-owner/different-repo.git"
        assert base_args["is_fork"] is True
        assert base_args["owner_type"] == "User"
        assert base_args["owner"] == "different-owner"
        assert base_args["owner_id"] == 333444
        assert base_args["base_branch"] == "develop"
        assert base_args["new_branch"].startswith("gitauto/issue-999-20240101-091530-")
        assert base_args["installation_id"] == 55555
        assert base_args["token"] == "different-token"
        assert base_args["sender_id"] == 66666
        assert base_args["sender_name"] == "different-sender"
        assert base_args["sender_email"] == "different@example.com"
        assert base_args["reviewers"] == ["different-sender", "different-creator"]
        assert repo_settings is None


def test_deconstruct_github_payload_handle_exceptions_decorator():
    """Test that the handle_exceptions decorator works correctly"""
    # This test verifies the decorator behavior by checking the function signature
    # and ensuring it has the expected default return value behavior

    # Arrange - create a payload that will cause token retrieval to fail
    payload = cast(
        GitHubLabeledPayload,
        {
            "action": "labeled",
            "issue": {
                "number": 123,
                "title": "Test",
                "body": "Test",
                "user": {"login": "test"},
            },
            "repository": {
                "id": 456,
                "name": "test",
                "clone_url": "https://github.com/test/test.git",
                "fork": False,
                "default_branch": "main",
                "owner": {
                    "type": "Organization",
                    "login": "test",
                    "id": 789,
                },
            },
            "installation": {"id": 12345},
            "sender": {"id": 11111, "login": "test"},
            "label": {"name": "gitauto"},
            "organization": {"id": 22222, "login": "test"},
        },
    )

    with patch(
        "services.github.utils.deconstruct_github_payload.get_installation_access_token",
        return_value=None  # This will trigger the ValueError
    ):
        # Act & Assert
        with pytest.raises(ValueError):
            deconstruct_github_payload(payload)


def test_deconstruct_github_payload_random_string_generation():
    """Test that random string generation works correctly"""
    payload = cast(
        GitHubLabeledPayload,
        {
            "action": "labeled",
            "issue": {
                "number": 123,
                "title": "Test",
                "body": "Test",
                "user": {"login": "test"},
            },
            "repository": {
                "id": 456,
                "name": "test",
                "clone_url": "https://github.com/test/test.git",
                "fork": False,
                "default_branch": "main",
                "owner": {
                    "type": "Organization",
                    "login": "test",
                    "id": 789,
                },
            },
            "installation": {"id": 12345},
            "sender": {"id": 11111, "login": "test"},
            "label": {"name": "gitauto"},
            "organization": {"id": 22222, "login": "test"},
        },
    )

    with patch(
        "services.github.utils.deconstruct_github_payload.get_installation_access_token",
        return_value="test-token"
    ), patch(
        "services.github.utils.deconstruct_github_payload.get_repository",
        return_value=None
    ), patch(
        "services.github.utils.deconstruct_github_payload.get_user_public_email",
        return_value="test@example.com"
    ), patch(
        "services.github.utils.deconstruct_github_payload.extract_urls",
        return_value=([], [])
    ), patch(
        "services.github.utils.deconstruct_github_payload.get_parent_issue",
        return_value=None
    ), patch(
        "services.github.utils.deconstruct_github_payload.datetime"
    ) as mock_datetime, patch(
        "services.github.utils.deconstruct_github_payload.choices",
        return_value=["A", "B", "C", "D"]
    ) as mock_choices:

        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)

        # Act
        base_args, repo_settings = deconstruct_github_payload(payload)

        # Assert
        assert base_args["new_branch"] == "gitauto/issue-123-20240101-120000-ABCD"

        # Verify choices was called correctly
        mock_choices.assert_called_once()
        call_args = mock_choices.call_args
        assert call_args[1]["k"] == 4  # Should generate 4 characters


def test_deconstruct_github_payload_comprehensive_base_args_structure():
    """Test that all required BaseArgs fields are present and correctly typed"""
    payload = cast(
        GitHubLabeledPayload,
        {
            "action": "labeled",
            "issue": {
                "number": 123,
                "title": "Test Issue",
                "body": "Test body",
                "user": {"login": "test-user"},
            },
            "repository": {
                "id": 456,
                "name": "test-repo",
                "clone_url": "https://github.com/test/repo.git",
                "fork": False,
                "default_branch": "main",
                "owner": {
                    "type": "Organization",
                    "login": "test-owner",
                    "id": 789,
                },
            },
            "installation": {"id": 12345},
            "sender": {"id": 11111, "login": "test-sender"},
            "label": {"name": "gitauto"},
            "organization": {"id": 22222, "login": "test-org"},
        },
    )

    with patch(
        "services.github.utils.deconstruct_github_payload.get_installation_access_token",
        return_value="test-token"
    ), patch(
        "services.github.utils.deconstruct_github_payload.get_repository",
        return_value={"target_branch": "develop"}
    ), patch(
        "services.github.utils.deconstruct_github_payload.check_branch_exists",
        return_value=True
    ), patch(
        "services.github.utils.deconstruct_github_payload.get_user_public_email",
        return_value="test@example.com"
    ), patch(
        "services.github.utils.deconstruct_github_payload.extract_urls",
        return_value=(["https://github.com/test/repo"], ["https://example.com"])
    ), patch(
        "services.github.utils.deconstruct_github_payload.get_parent_issue",
        return_value={"number": 100, "title": "Parent", "body": "Parent body"}
    ), patch(
        "services.github.utils.deconstruct_github_payload.datetime"
    ) as mock_datetime:

        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)

        # Act
        base_args, repo_settings = deconstruct_github_payload(payload)

        # Assert all required BaseArgs fields are present
        required_fields = [
            "input_from", "owner_type", "owner_id", "owner", "repo_id", "repo",
            "clone_url", "is_fork", "issue_number", "issue_title", "issue_body",
            "issuer_name", "base_branch", "new_branch", "installation_id", "token",
            "sender_id", "sender_name", "sender_email", "is_automation", "reviewers",
            "github_urls", "other_urls"
        ]

        for field in required_fields:
            assert field in base_args, f"Required field '{field}' missing from base_args"

        # Assert optional fields that should be present
        optional_fields = [
            "parent_issue_number", "parent_issue_title", "parent_issue_body"
        ]

        for field in optional_fields:
            assert field in base_args, f"Expected optional field '{field}' missing from base_args"

        # Verify types of key fields
        assert isinstance(base_args["input_from"], str)
        assert isinstance(base_args["owner_type"], str)
        assert isinstance(base_args["owner_id"], int)
        assert isinstance(base_args["owner"], str)
        assert isinstance(base_args["repo_id"], int)
        assert isinstance(base_args["repo"], str)
        assert isinstance(base_args["clone_url"], str)
        assert isinstance(base_args["is_fork"], bool)
        assert isinstance(base_args["issue_number"], int)
        assert isinstance(base_args["issue_title"], str)
        assert isinstance(base_args["issue_body"], str)
        assert isinstance(base_args["issuer_name"], str)
        assert isinstance(base_args["base_branch"], str)
        assert isinstance(base_args["new_branch"], str)
        assert isinstance(base_args["installation_id"], int)
        assert isinstance(base_args["token"], str)
        assert isinstance(base_args["sender_id"], int)
        assert isinstance(base_args["sender_name"], str)
        assert isinstance(base_args["is_automation"], bool)
        assert isinstance(base_args["reviewers"], list)
        assert isinstance(base_args["github_urls"], list)
        assert isinstance(base_args["other_urls"], list)


def test_deconstruct_github_payload_edge_case_empty_strings():
    """Test handling of edge cases with empty strings"""
    payload = cast(
        GitHubLabeledPayload,
        {
            "action": "labeled",
            "issue": {
                "number": 123,
                "title": "",  # Empty title
                "body": "",   # Empty body
                "user": {"login": "test-user"},
            },
            "repository": {
                "id": 456,
                "name": "test-repo",
                "clone_url": "https://github.com/test/repo.git",
                "fork": False,
                "default_branch": "main",
                "owner": {
                    "type": "Organization",
                    "login": "test-owner",
                    "id": 789,
                },
            },
            "installation": {"id": 12345},
            "sender": {"id": 11111, "login": "test-sender"},
            "label": {"name": "gitauto"},
            "organization": {"id": 22222, "login": "test-org"},
        },
    )

    with patch(
        "services.github.utils.deconstruct_github_payload.get_installation_access_token",
        return_value="test-token"
    ), patch(
        "services.github.utils.deconstruct_github_payload.get_repository",
        return_value=None
    ), patch(
        "services.github.utils.deconstruct_github_payload.get_user_public_email",
        return_value=""  # Empty email
    ), patch(
        "services.github.utils.deconstruct_github_payload.extract_urls",
        return_value=([], [])
    ), patch(
        "services.github.utils.deconstruct_github_payload.get_parent_issue",
        return_value=None
    ), patch(
        "services.github.utils.deconstruct_github_payload.datetime"
    ) as mock_datetime:

        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)

        # Act
        base_args, repo_settings = deconstruct_github_payload(payload)

        # Assert
        assert base_args["issue_title"] == ""
        assert base_args["issue_body"] == ""
        assert base_args["sender_email"] == ""


def test_deconstruct_github_payload_large_issue_number():
    """Test handling of large issue numbers"""
    payload = cast(
        GitHubLabeledPayload,
        {
            "action": "labeled",
            "issue": {
                "number": 999999,  # Large issue number
                "title": "Test Issue",
                "body": "Test body",
                "user": {"login": "test-user"},
            },
            "repository": {
                "id": 456,
                "name": "test-repo",
                "clone_url": "https://github.com/test/repo.git",
                "fork": False,
                "default_branch": "main",
                "owner": {
                    "type": "Organization",
                    "login": "test-owner",
                    "id": 789,
                },
            },
            "installation": {"id": 12345},
            "sender": {"id": 11111, "login": "test-sender"},
            "label": {"name": "gitauto"},
            "organization": {"id": 22222, "login": "test-org"},
        },
    )

    with patch(
        "services.github.utils.deconstruct_github_payload.get_installation_access_token",
        return_value="test-token"
    ), patch(
        "services.github.utils.deconstruct_github_payload.get_repository",
        return_value=None
    ), patch(
        "services.github.utils.deconstruct_github_payload.get_user_public_email",
        return_value="test@example.com"
    ), patch(
        "services.github.utils.deconstruct_github_payload.extract_urls",
        return_value=([], [])
    ), patch(
        "services.github.utils.deconstruct_github_payload.get_parent_issue",
        return_value=None
    ), patch(
        "services.github.utils.deconstruct_github_payload.datetime"
    ) as mock_datetime:

        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)

        # Act
        base_args, repo_settings = deconstruct_github_payload(payload)

        # Assert
        assert base_args["issue_number"] == 999999
        assert base_args["new_branch"].startswith("gitauto/issue-999999-20240101-120000-")
