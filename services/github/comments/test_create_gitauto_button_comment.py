from unittest.mock import patch
import pytest

from services.github.comments.create_gitauto_button_comment import (
    create_gitauto_button_comment,
)


@pytest.fixture
def mock_github_labeled_payload():
    """Create a mock GitHubLabeledPayload for testing"""
    return {
        "action": "labeled",
        "installation": {"id": 12345},
        "repository": {
            "owner": {"id": 67890, "login": "test-owner"},
            "name": "test-repo",
        },
        "issue": {"number": 123},
        "sender": {"id": 11111, "login": "test-user"},
        "label": {"name": "gitauto"},
        "organization": {"id": 22222, "login": "test-org"},
    }


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies"""
    with patch(
        "services.github.comments.create_gitauto_button_comment.get_installation_access_token"
    ) as mock_get_token, patch(
        "services.github.comments.create_gitauto_button_comment.get_user_public_email"
    ) as mock_get_email, patch(
        "services.github.comments.create_gitauto_button_comment.upsert_user"
    ) as mock_upsert_user, patch(
        "services.github.comments.create_gitauto_button_comment.combine_and_create_comment"
    ) as mock_combine_comment:
        mock_get_token.return_value = "test-token"
        mock_get_email.return_value = "test@example.com"

        yield {
            "get_token": mock_get_token,
            "get_email": mock_get_email,
            "upsert_user": mock_upsert_user,
            "combine_comment": mock_combine_comment,
        }


def test_create_gitauto_button_comment_success(
    mock_github_labeled_payload, mock_dependencies
):
    """Test successful creation of GitAuto button comment"""
    # Act
    result = create_gitauto_button_comment(mock_github_labeled_payload)

    # Assert
    assert result is None  # Function returns None on success

    # Verify token retrieval
    mock_dependencies["get_token"].assert_called_once_with(installation_id=12345)

    # Verify email retrieval
    mock_dependencies["get_email"].assert_called_once_with(
        username="test-user", token="test-token"
    )

    # Verify user upsert
    mock_dependencies["upsert_user"].assert_called_once_with(
        user_id=11111, user_name="test-user", email="test@example.com"
    )

    # Verify comment creation with correct parameters
    mock_dependencies["combine_comment"].assert_called_once()
    call_args = mock_dependencies["combine_comment"].call_args

    # Check base_comment format
    assert (
        "Click the checkbox below to generate a PR!" in call_args.kwargs["base_comment"]
    )
    assert "- [ ] Generate PR" in call_args.kwargs["base_comment"]

    # Check other parameters
    assert call_args.kwargs["installation_id"] == 12345
    assert call_args.kwargs["owner_id"] == 67890
    assert call_args.kwargs["owner_name"] == "test-owner"
    assert call_args.kwargs["sender_name"] == "test-user"

    # Check base_args structure
    base_args = call_args.kwargs["base_args"]
    assert base_args["owner"] == "test-owner"
    assert base_args["repo"] == "test-repo"
    assert base_args["issue_number"] == 123
    assert base_args["token"] == "test-token"


def test_create_gitauto_button_comment_with_null_email(
    mock_github_labeled_payload, mock_dependencies
):
    """Test comment creation when user email is None"""
    # Arrange
    mock_dependencies["get_email"].return_value = None

    # Act
    result = create_gitauto_button_comment(mock_github_labeled_payload)

    # Assert
    assert result is None

    # Verify user upsert with None email
    mock_dependencies["upsert_user"].assert_called_once_with(
        user_id=11111, user_name="test-user", email=None
    )

    # Verify other functions were still called
    mock_dependencies["get_token"].assert_called_once()
    mock_dependencies["combine_comment"].assert_called_once()


def test_create_gitauto_button_comment_token_error(
    mock_github_labeled_payload, mock_dependencies
):
    """Test behavior when token retrieval fails"""
    # Arrange
    mock_dependencies["get_token"].side_effect = Exception("Token error")

    # Act
    result = create_gitauto_button_comment(mock_github_labeled_payload)

    # Assert - handle_exceptions decorator should return None on error
    assert result is None

    # Verify token retrieval was attempted
    mock_dependencies["get_token"].assert_called_once_with(installation_id=12345)

    # Verify subsequent functions were not called due to exception
    mock_dependencies["get_email"].assert_not_called()
    mock_dependencies["upsert_user"].assert_not_called()
    mock_dependencies["combine_comment"].assert_not_called()


def test_create_gitauto_button_comment_email_error(
    mock_github_labeled_payload, mock_dependencies
):
    """Test behavior when email retrieval fails"""
    # Arrange
    mock_dependencies["get_email"].side_effect = Exception("Email error")

    # Act
    result = create_gitauto_button_comment(mock_github_labeled_payload)

    # Assert - handle_exceptions decorator should return None on error
    assert result is None

    # Verify functions called before error
    mock_dependencies["get_token"].assert_called_once()
    mock_dependencies["get_email"].assert_called_once()

    # Verify subsequent functions were not called due to exception
    mock_dependencies["upsert_user"].assert_not_called()
    mock_dependencies["combine_comment"].assert_not_called()


def test_create_gitauto_button_comment_upsert_user_error(
    mock_github_labeled_payload, mock_dependencies
):
    """Test behavior when user upsert fails"""
    # Arrange
    mock_dependencies["upsert_user"].side_effect = Exception("Upsert error")

    # Act
    result = create_gitauto_button_comment(mock_github_labeled_payload)

    # Assert - handle_exceptions decorator should return None on error
    assert result is None

    # Verify functions called before error
    mock_dependencies["get_token"].assert_called_once()
    mock_dependencies["get_email"].assert_called_once()
    mock_dependencies["upsert_user"].assert_called_once()

    # Verify subsequent function was not called due to exception
    mock_dependencies["combine_comment"].assert_not_called()


def test_create_gitauto_button_comment_combine_comment_error(
    mock_github_labeled_payload, mock_dependencies
):
    """Test behavior when combine_and_create_comment fails"""
    # Arrange
    mock_dependencies["combine_comment"].side_effect = Exception("Comment error")

    # Act
    result = create_gitauto_button_comment(mock_github_labeled_payload)

    # Assert - handle_exceptions decorator should return None on error
    assert result is None

    # Verify all functions were called
    mock_dependencies["get_token"].assert_called_once()
    mock_dependencies["get_email"].assert_called_once()
    mock_dependencies["upsert_user"].assert_called_once()
    mock_dependencies["combine_comment"].assert_called_once()


def test_create_gitauto_button_comment_different_payload_values():
    """Test with different payload values to ensure proper extraction"""
    # Arrange
    payload = {
        "action": "labeled",
        "installation": {"id": 99999},
        "repository": {
            "owner": {"id": 88888, "login": "different-owner"},
            "name": "different-repo",
        },
        "issue": {"number": 456},
        "sender": {"id": 77777, "login": "different-user"},
        "label": {"name": "gitauto"},
        "organization": {"id": 66666, "login": "different-org"},
    }

    with patch(
        "services.github.comments.create_gitauto_button_comment.get_installation_access_token"
    ) as mock_get_token, patch(
        "services.github.comments.create_gitauto_button_comment.get_user_public_email"
    ) as mock_get_email, patch(
        "services.github.comments.create_gitauto_button_comment.upsert_user"
    ) as mock_upsert_user, patch(
        "services.github.comments.create_gitauto_button_comment.combine_and_create_comment"
    ) as mock_combine_comment:
        mock_get_token.return_value = "different-token"
        mock_get_email.return_value = "different@example.com"

        # Act
        result = create_gitauto_button_comment(payload)

        # Assert
        assert result is None

        # Verify correct values were extracted and used
        mock_get_token.assert_called_once_with(installation_id=99999)
        mock_get_email.assert_called_once_with(
            username="different-user", token="different-token"
        )
        mock_upsert_user.assert_called_once_with(
            user_id=77777, user_name="different-user", email="different@example.com"
        )

        # Verify combine_and_create_comment called with correct values
        call_args = mock_combine_comment.call_args
        assert call_args.kwargs["installation_id"] == 99999
        assert call_args.kwargs["owner_id"] == 88888
        assert call_args.kwargs["owner_name"] == "different-owner"
        assert call_args.kwargs["sender_name"] == "different-user"

        base_args = call_args.kwargs["base_args"]
        assert base_args["owner"] == "different-owner"
        assert base_args["repo"] == "different-repo"
        assert base_args["issue_number"] == 456
        assert base_args["token"] == "different-token"


def test_create_gitauto_button_comment_base_comment_format():
    """Test that the base comment is formatted correctly"""
    payload = {
        "action": "labeled",
        "installation": {"id": 12345},
        "repository": {
            "owner": {"id": 67890, "login": "test-owner"},
            "name": "test-repo",
        },
        "issue": {"number": 123},
        "sender": {"id": 11111, "login": "test-user"},
        "label": {"name": "gitauto"},
        "organization": {"id": 22222, "login": "test-org"},
    }

    with patch(
        "services.github.comments.create_gitauto_button_comment.get_installation_access_token",
        return_value="test-token",
    ) as mock_get_token, patch(
        "services.github.comments.create_gitauto_button_comment.get_user_public_email",
        return_value="test@example.com",
    ) as mock_get_email, patch(
        "services.github.comments.create_gitauto_button_comment.upsert_user"
    ) as mock_upsert_user, patch(
        "services.github.comments.create_gitauto_button_comment.combine_and_create_comment"
    ) as mock_combine_comment:

        # Act
        result = create_gitauto_button_comment(payload)

        # Assert
        assert result is None

        # Verify the base comment format
        call_args = mock_combine_comment.call_args
        base_comment = call_args.kwargs["base_comment"]

        # Check that the comment contains the expected elements
        assert "Click the checkbox below to generate a PR!" in base_comment
        assert "- [ ] Generate PR" in base_comment

        # Verify the exact format
        expected_comment = (
            "Click the checkbox below to generate a PR!\n- [ ] Generate PR"
        )
        assert base_comment == expected_comment
