import pytest
from unittest.mock import patch, MagicMock
import requests

from services.github.comments.create_comment import create_comment
from tests.constants import OWNER, REPO, TOKEN


def test_create_comment_connection_error():
    """Test that connection errors are properly handled"""
    # Arrange
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123,
        "input_from": "github"
    }
    
    # Act
    with patch("services.github.comments.create_comment.requests.post") as mock_post:
        mock_post.side_effect = requests.ConnectionError("Connection refused")
        result = create_comment("Test comment", base_args)
    
    # Assert
    assert result is None  # The handle_exceptions decorator should return None on error


def test_create_comment_timeout_error():
    """Test that timeout errors are properly handled"""
    # Arrange
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": 123,
        "input_from": "github"
    }
    
    # Act
    with patch("services.github.comments.create_comment.requests.post") as mock_post:
        mock_post.side_effect = requests.Timeout("Request timed out")
        result = create_comment("Test comment", base_args)
    
    # Assert
    assert result is None  # The handle_exceptions decorator should return None on error
