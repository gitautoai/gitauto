import pytest
from unittest.mock import patch, MagicMock

from services.github.comments.update_comment import update_comment
from tests.constants import OWNER, REPO, TOKEN


def test_update_comment_success():
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 123, "body": "Updated comment"}
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "comment_url": "https://api.github.com/repos/owner/repo/issues/comments/123"
    }
    
    # Act
    with patch("services.github.comments.update_comment.patch") as mock_patch:
        mock_patch.return_value = mock_response
        result = update_comment("Updated comment", base_args)
    
    # Assert
    mock_patch.assert_called_once()
    assert result == {"id": 123, "body": "Updated comment"}
    assert mock_patch.call_args[1]["json"] == {"body": "Updated comment"}


def test_update_comment_none_url():
    # Arrange
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "comment_url": None
    }
    
    # Act
    with patch("services.github.comments.update_comment.patch") as mock_patch:
        result = update_comment("Test comment", base_args)
    
    # Assert
    mock_patch.assert_not_called()
    assert result is None


def test_update_comment_request_error():
    # Arrange
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("API error")
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "comment_url": "https://api.github.com/repos/owner/repo/issues/comments/123"
    }
    
    # Act
    with patch("services.github.comments.update_comment.patch") as mock_patch:
        mock_patch.return_value = mock_response
        result = update_comment("Test comment", base_args)
    
    # Assert
    mock_patch.assert_called_once()
    assert result is None  # The handle_exceptions decorator should return None on error


def test_update_comment_empty_body():
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 123, "body": ""}
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "comment_url": "https://api.github.com/repos/owner/repo/issues/comments/123"
    }
    
    # Act
    with patch("services.github.comments.update_comment.patch") as mock_patch:
        mock_patch.return_value = mock_response
        result = update_comment("", base_args)
    
    # Assert
    mock_patch.assert_called_once()
    assert result == {"id": 123, "body": ""}
    assert mock_patch.call_args[1]["json"] == {"body": ""}


def test_update_comment_with_headers():
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 123, "body": "Test comment"}
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "comment_url": "https://api.github.com/repos/owner/repo/issues/comments/123"
    }
    
    # Act
    with patch("services.github.comments.update_comment.patch") as mock_patch, \
         patch("services.github.comments.update_comment.create_headers") as mock_create_headers:
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_patch.return_value = mock_response
        result = update_comment("Test comment", base_args)
    
    # Assert
    mock_create_headers.assert_called_once_with(token=TOKEN)
    mock_patch.assert_called_once()
    assert mock_patch.call_args[1]["headers"] == {"Authorization": f"Bearer {TOKEN}"}
    assert result == {"id": 123, "body": "Test comment"}
def test_update_comment_missing_comment_url_key():
    # Arrange
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN
    }

    # Act
    with patch("services.github.comments.update_comment.patch") as mock_patch:
        result = update_comment("Test comment", base_args)

    # Assert
