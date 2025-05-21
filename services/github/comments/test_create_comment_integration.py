import pytest
import responses
from unittest.mock import patch

from services.github.comments.create_comment import create_comment
from tests.constants import OWNER, REPO, TOKEN
from config import GITHUB_API_URL


@pytest.mark.integration
class TestCreateCommentIntegration:
    """Integration tests for create_comment function using responses library"""

    @responses.activate
    def test_create_comment_success(self):
        # Arrange
        issue_number = 123
        comment_body = "Test integration comment"
        expected_url = f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/issues/{issue_number}/comments"
        
        # Mock the GitHub API response
        responses.add(
            responses.POST,
            expected_url,
            json={"url": "https://api.github.com/repos/owner/repo/issues/comments/456"},
            status=201
        )
        
        base_args = {
            "owner": OWNER,
            "repo": REPO,
            "token": TOKEN,
            "issue_number": issue_number
        }
        
        # Act
        result = create_comment(comment_body, base_args)
        
        # Assert
        assert result == "https://api.github.com/repos/owner/repo/issues/comments/456"
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == expected_url

    @responses.activate
    def test_create_comment_server_error(self):
        # Arrange
        issue_number = 123
        responses.add(
            responses.POST,
            f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/issues/{issue_number}/comments",
            status=500
        )
        
        base_args = {"owner": OWNER, "repo": REPO, "token": TOKEN, "issue_number": issue_number}
        
        # Act & Assert
        result = create_comment("Test comment with server error", base_args)
        assert result is None