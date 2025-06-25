import pytest
import logging
from unittest.mock import patch, MagicMock, Mock

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


def test_update_comment_404_not_found():
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 404
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "comment_url": "https://api.github.com/repos/owner/repo/issues/comments/123"
    }
    
    # Act
    with patch("services.github.comments.update_comment.patch") as mock_patch, \
         patch("services.github.comments.update_comment.logging") as mock_logging:
        mock_patch.return_value = mock_response
        result = update_comment("Test comment", base_args)
    
    # Assert
    mock_patch.assert_called_once()
    mock_logging.info.assert_called_once_with("Comment %s not found", base_args["comment_url"])
    assert result is None


def test_update_comment_missing_comment_url_key():
    # Arrange - test when comment_url key is missing from base_args
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN
        # comment_url is missing
    }
    
    # Act
    with patch("services.github.comments.update_comment.patch") as mock_patch:
        result = update_comment("Test comment", base_args)
    
    # Assert
    mock_patch.assert_not_called()
    assert result is None


def test_update_comment_timeout_parameter():
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
         patch("services.github.comments.update_comment.TIMEOUT", 120) as mock_timeout:
        mock_patch.return_value = mock_response
        result = update_comment("Test comment", base_args)
    
    # Assert
    mock_patch.assert_called_once()
    # Verify timeout parameter is passed correctly
    call_kwargs = mock_patch.call_args[1]
    assert call_kwargs["timeout"] == 120
    assert result == {"id": 123, "body": "Test comment"}


def test_update_comment_print_output():
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
         patch("builtins.print") as mock_print:
        mock_patch.return_value = mock_response
        result = update_comment("Test comment body", base_args)
    
    # Assert
    mock_patch.assert_called_once()
    mock_print.assert_called_once_with("Test comment body\n")
    assert result == {"id": 123, "body": "Test comment"}


def test_update_comment_all_parameters():
    # Arrange - test that all parameters are passed correctly to the patch request
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 456, "body": "Complete test"}
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "comment_url": "https://api.github.com/repos/test/repo/issues/comments/456"
    }
    
    # Act
    with patch("services.github.comments.update_comment.patch") as mock_patch, \
         patch("services.github.comments.update_comment.create_headers") as mock_create_headers, \
         patch("services.github.comments.update_comment.TIMEOUT", 120):
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
        mock_patch.return_value = mock_response
        result = update_comment("Complete test body", base_args)
    
    # Assert
    mock_patch.assert_called_once()
    call_args = mock_patch.call_args
    
    # Verify all parameters
    assert call_args[1]["url"] == base_args["comment_url"]
    assert call_args[1]["headers"] == {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    assert call_args[1]["json"] == {"body": "Complete test body"}
    assert call_args[1]["timeout"] == 120
    assert result == {"id": 456, "body": "Complete test"}


def test_update_comment_empty_comment_url():
    # Arrange - test when comment_url is an empty string
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "comment_url": ""
    }
    
    # Act
    with patch("services.github.comments.update_comment.patch") as mock_patch:
        result = update_comment("Test comment", base_args)
    
    # Assert
    mock_patch.assert_not_called()
    assert result is None


def test_update_comment_non_404_error_status():
    # Arrange - test other HTTP error status codes (not 404)
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.raise_for_status.side_effect = Exception("Forbidden")
    
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
    # Should call raise_for_status and handle_exceptions should return None
    assert result is None


def test_update_comment_long_body():
    # Arrange - test with a very long comment body
    mock_response = MagicMock()
    long_body = "A" * 1000  # 1000 character string
    mock_response.json.return_value = {"id": 123, "body": long_body}
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "comment_url": "https://api.github.com/repos/owner/repo/issues/comments/123"
    }
    
    # Act
    with patch("services.github.comments.update_comment.patch") as mock_patch:
        mock_patch.return_value = mock_response
        result = update_comment(long_body, base_args)
    
    # Assert
    mock_patch.assert_called_once()
    assert result == {"id": 123, "body": long_body}
    assert mock_patch.call_args[1]["json"] == {"body": long_body}


def test_update_comment_special_characters():
    # Arrange - test with special characters in the body
    mock_response = MagicMock()
    special_body = "Test with special chars: @#$%^&*()[]{}|\\:;\"'<>,.?/~`"
    mock_response.json.return_value = {"id": 123, "body": special_body}
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "comment_url": "https://api.github.com/repos/owner/repo/issues/comments/123"
    }
    
    # Act
    with patch("services.github.comments.update_comment.patch") as mock_patch:
        mock_patch.return_value = mock_response
        result = update_comment(special_body, base_args)
    
    # Assert
    mock_patch.assert_called_once()
    assert result == {"id": 123, "body": special_body}
    assert mock_patch.call_args[1]["json"] == {"body": special_body}


def test_update_comment_404_logging_behavior():
    # Arrange - test the specific logging behavior for 404 errors
    mock_response = MagicMock()
    mock_response.status_code = 404
    comment_url = "https://api.github.com/repos/owner/repo/issues/comments/999"
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "comment_url": comment_url
    }
    
    # Act
    with patch("services.github.comments.update_comment.patch") as mock_patch, \
         patch("services.github.comments.update_comment.logging.info") as mock_log_info:
        mock_patch.return_value = mock_response
        result = update_comment("Test comment", base_args)
    
    # Assert
    mock_patch.assert_called_once()
    # Verify the exact logging call
    mock_log_info.assert_called_once_with("Comment %s not found", comment_url)
    assert result is None
    # Verify that raise_for_status is NOT called for 404
    mock_response.raise_for_status.assert_not_called()