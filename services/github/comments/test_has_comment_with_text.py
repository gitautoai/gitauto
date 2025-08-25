from unittest.mock import patch

import pytest

from config import GITHUB_APP_USER_NAME
from services.github.comments.has_comment_with_text import has_comment_with_text
from tests.constants import OWNER, REPO, TOKEN


@pytest.fixture
def base_args():
    """Fixture providing base arguments for testing."""
    return {"owner": OWNER, "repo": REPO, "token": TOKEN, "issue_number": 123}


@pytest.fixture
def mock_get_all_comments():
    """Fixture to mock get_all_comments function."""
    with patch(
        "services.github.comments.has_comment_with_text.get_all_comments"
    ) as mock:
        yield mock


def test_has_comment_with_text_found_single_text(base_args, mock_get_all_comments):
    """Test that function returns True when text is found in GitAuto comment."""
    # Arrange
    mock_comments = [
        {
            "user": {"login": GITHUB_APP_USER_NAME},
            "body": "This is a test comment with specific text",
        },
        {"user": {"login": "other_user"}, "body": "This comment should be ignored"},
    ]
    mock_get_all_comments.return_value = mock_comments
    texts = ["specific text"]

    # Act
    result = has_comment_with_text(base_args, texts)

    # Assert
    assert result is True
    mock_get_all_comments.assert_called_once_with(base_args)


def test_has_comment_with_text_found_multiple_texts(base_args, mock_get_all_comments):
    """Test that function returns True when any of multiple texts is found."""
    # Arrange
    mock_comments = [
        {
            "user": {"login": GITHUB_APP_USER_NAME},
            "body": "This comment contains the second text",
        }
    ]
    mock_get_all_comments.return_value = mock_comments
    texts = ["first text", "second text", "third text"]

    # Act
    result = has_comment_with_text(base_args, texts)

    # Assert
    assert result is True


def test_has_comment_with_text_not_found(base_args, mock_get_all_comments):
    """Test that function returns False when text is not found."""
    # Arrange
    mock_comments = [
        {
            "user": {"login": GITHUB_APP_USER_NAME},
            "body": "This is a comment without the target",
        }
    ]
    mock_get_all_comments.return_value = mock_comments
    texts = ["missing text"]

    # Act
    result = has_comment_with_text(base_args, texts)

    # Assert
    assert result is False


def test_has_comment_with_text_wrong_user(base_args, mock_get_all_comments):
    """Test that function ignores comments from users other than GitAuto."""
    # Arrange
    mock_comments = [
        {"user": {"login": "other_user"}, "body": "This comment has the target text"}
    ]
    mock_get_all_comments.return_value = mock_comments
    texts = ["target text"]

    # Act
    result = has_comment_with_text(base_args, texts)

    # Assert
    assert result is False


def test_has_comment_with_text_empty_comments(base_args, mock_get_all_comments):
    """Test that function returns False when no comments exist."""
    # Arrange
    mock_get_all_comments.return_value = []
    texts = ["any text"]

    # Act
    result = has_comment_with_text(base_args, texts)

    # Assert
    assert result is False


def test_has_comment_with_text_empty_texts_list(base_args, mock_get_all_comments):
    """Test that function returns False when texts list is empty."""
    # Arrange
    mock_comments = [
        {"user": {"login": GITHUB_APP_USER_NAME}, "body": "This is a comment"}
    ]
    mock_get_all_comments.return_value = mock_comments
    texts = []

    # Act
    result = has_comment_with_text(base_args, texts)

    # Assert
    assert result is False


def test_has_comment_with_text_missing_user_field(base_args, mock_get_all_comments):
    """Test that function handles comments with missing user field gracefully."""
    # Arrange
    mock_comments = [
        {"body": "Comment without user field"},
        {
            "user": {"login": GITHUB_APP_USER_NAME},
            "body": "This comment has the target text",
        },
    ]
    mock_get_all_comments.return_value = mock_comments
    texts = ["target text"]

    # Act
    result = has_comment_with_text(base_args, texts)

    # Assert
    assert result is True


def test_has_comment_with_text_missing_login_field(base_args, mock_get_all_comments):
    """Test that function handles comments with missing login field gracefully."""
    # Arrange
    mock_comments = [
        {"user": {}, "body": "Comment without login field"},
        {
            "user": {"login": GITHUB_APP_USER_NAME},
            "body": "This comment has the target text",
        },
    ]
    mock_get_all_comments.return_value = mock_comments
    texts = ["target text"]

    # Act
    result = has_comment_with_text(base_args, texts)

    # Assert
    assert result is True


def test_has_comment_with_text_missing_body_field(base_args, mock_get_all_comments):
    """Test that function handles comments with missing body field gracefully."""
    # Arrange
    mock_comments = [
        {
            "user": {"login": GITHUB_APP_USER_NAME}
            # Missing body field
        }
    ]
    mock_get_all_comments.return_value = mock_comments
    texts = ["any text"]

    # Act
    result = has_comment_with_text(base_args, texts)

    # Assert
    assert result is False


def test_has_comment_with_text_case_sensitive(base_args, mock_get_all_comments):
    """Test that text matching is case sensitive."""
    # Arrange
    mock_comments = [
        {
            "user": {"login": GITHUB_APP_USER_NAME},
            "body": "This comment has UPPERCASE text",
        }
    ]
    mock_get_all_comments.return_value = mock_comments
    texts = ["uppercase text"]  # lowercase

    # Act
    result = has_comment_with_text(base_args, texts)

    # Assert
    assert result is False


def test_has_comment_with_text_partial_match(base_args, mock_get_all_comments):
    """Test that partial text matching works correctly."""
    # Arrange
    mock_comments = [
        {
            "user": {"login": GITHUB_APP_USER_NAME},
            "body": "This is a comprehensive test message",
        }
    ]
    mock_get_all_comments.return_value = mock_comments
    texts = ["comprehensive"]

    # Act
    result = has_comment_with_text(base_args, texts)

    # Assert
    assert result is True


def test_has_comment_with_text_get_all_comments_exception(
    base_args, mock_get_all_comments
):
    """Test that function handles exceptions from get_all_comments gracefully."""
    # Arrange
    mock_get_all_comments.side_effect = Exception("API error")
    texts = ["any text"]

    # Act
    result = has_comment_with_text(base_args, texts)

    # Assert
    assert (
        result is False
    )  # Should return default value due to handle_exceptions decorator
