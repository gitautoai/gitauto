import pytest
from unittest.mock import patch, MagicMock, AsyncMock, call
from typing import Any, Dict
import asyncio

from services.webhook.issue_handler import create_pr_from_issue
from config import PRODUCT_ID, EXCEPTION_OWNERS


@pytest.fixture
def mock_github_payload():
    """Mock GitHub labeled payload."""
    return {
        "label": {"name": PRODUCT_ID},
        "issue": {
            "number": 123,
            "title": "Test Issue",
            "body": "Test issue body",
            "user": {"login": "test-user"}
        },
        "repository": {
            "id": 789,
            "name": "test-repo",
            "clone_url": "https://github.com/owner/test-repo.git",
            "owner": {
                "id": 456,
                "login": "test-owner",
                "type": "Organization"
            }
        },
        "sender": {
            "id": 999,
            "login": "test-sender",
            "email": "test@example.com"
        },
        "installation": {
            "id": 12345
        }
    }


@pytest.fixture
def mock_jira_payload():
    """Mock JIRA payload."""
    return {
        "issue": {
            "number": 123,
            "title": "Test JIRA Issue",
            "body": "Test JIRA issue body"
        },
        "repository": {
            "id": 789,
            "name": "test-repo",
            "owner": {
                "id": 456,
                "login": "test-owner",
                "type": "Organization"
            }
        },
        "sender": {
            "id": 999,
            "login": "test-sender",
            "email": "test@example.com"
        }
    }


@pytest.fixture
def mock_base_args():
    """Mock base args returned by deconstruct functions."""
    return {
        "owner": "test-owner",
        "repo": "test-repo",
        "repo_id": 789,
        "issue_number": 123,
        "issue_title": "Test Issue",
        "issue_body": "Test issue body",
        "issuer_name": "test-user",
        "parent_issue_number": None,
        "parent_issue_title": None,
        "parent_issue_body": None,
        "new_branch": "gitauto/issue-123-test",
        "sender_id": 999,
        "sender_name": "test-sender",
        "sender_email": "test@example.com",
        "github_urls": [],
        "token": "test_token",
        "is_automation": False,
        "installation_id": 12345,
        "owner_id": 456,
        "owner_type": "Organization",
        "clone_url": "https://github.com/owner/test-repo.git"
    }


@pytest.fixture
def mock_repo_settings():
    """Mock repository settings."""
    return {
        "repo_rules": "test rules",
        "target_branch": "main"
    }


class TestCreatePrFromIssue:
    """Test cases for create_pr_from_issue function."""

    @pytest.mark.asyncio
    @patch('services.webhook.issue_handler.deconstruct_github_payload')
    @patch('services.webhook.issue_handler.delete_my_comments')
    @patch('services.webhook.issue_handler.create_comment')
    @patch('services.webhook.issue_handler.get_how_many_requests_left_and_cycle')
    @patch('services.webhook.issue_handler.create_user_request')
    @patch('services.webhook.issue_handler.add_reaction_to_issue')
    @patch('services.webhook.issue_handler.get_remote_file_tree')
    @patch('services.webhook.issue_handler.find_config_files')
    @patch('services.webhook.issue_handler.get_remote_file_content')
    @patch('services.webhook.issue_handler.get_comments')
    @patch('services.webhook.issue_handler.extract_image_urls')
    @patch('services.webhook.issue_handler.get_remote_file_content_by_url')
    @patch('services.webhook.issue_handler.get_latest_remote_commit_sha')
    @patch('services.webhook.issue_handler.create_remote_branch')
    @patch('services.webhook.issue_handler.chat_with_agent')
    @patch('services.webhook.issue_handler.create_pull_request')
    @patch('services.webhook.issue_handler.update_comment')
    @patch('services.webhook.issue_handler.update_usage')
    async def test_create_pr_from_issue_github_success_flow(
        self,
        mock_update_usage,
        mock_update_comment,
        mock_create_pull_request,
        mock_chat_with_agent,
        mock_create_remote_branch,
        mock_get_latest_commit_sha,
        mock_get_remote_file_content_by_url,
        mock_extract_image_urls,
        mock_get_comments,
        mock_get_remote_file_content,
        mock_find_config_files,
        mock_get_remote_file_tree,
        mock_add_reaction_to_issue,
        mock_create_user_request,
        mock_get_requests_left,
        mock_create_comment,
        mock_delete_my_comments,
        mock_deconstruct_github_payload,
        mock_github_payload,
        mock_base_args,
        mock_repo_settings
    ):
        """Test successful GitHub issue to PR creation flow."""
        # Arrange
        mock_deconstruct_github_payload.return_value = (mock_base_args, mock_repo_settings)
        mock_create_comment.return_value = "https://api.github.com/repos/owner/repo/issues/comments/123"
        mock_get_requests_left.return_value = (5, 0, "2024-01-01", False)
        mock_create_user_request.return_value = "usage_record_123"
        mock_add_reaction_to_issue.return_value = AsyncMock()
        mock_get_remote_file_tree.return_value = (["file1.py", "file2.py"], "Found 2 files")
        mock_find_config_files.return_value = ["requirements.txt"]
        mock_get_remote_file_content.return_value = "file content"
        mock_get_comments.return_value = ["comment1", "comment2"]
        mock_extract_image_urls.return_value = []
        mock_get_remote_file_content_by_url.return_value = "url content"
        mock_get_latest_commit_sha.return_value = "abc123"
        
        # Mock chat_with_agent to simulate exploration and commit phases
        mock_chat_with_agent.side_effect = [
            # First call (exploration)
            ([], [], "get_remote_file_content", {"file_path": "test.py"}, 100, 50, True, 10),
            # Second call (commit)
            ([], [], "apply_diff_to_file", {"file_path": "test.py"}, 100, 50, True, 15),
            # Third call (exploration - no more files)
            ([], [], None, None, 100, 50, False, 20),
            # Fourth call (commit - no more changes)
            ([], [], None, None, 100, 50, False, 25)
        ]
        
        mock_create_pull_request.return_value = "https://github.com/owner/repo/pull/42"
        
        # Act
        await create_pr_from_issue(
            payload=mock_github_payload,
            trigger_type="label",
            input_from="github"
        )
        
        # Assert
        mock_deconstruct_github_payload.assert_called_once_with(payload=mock_github_payload)
        mock_delete_my_comments.assert_called_once()
        mock_create_comment.assert_called()
        mock_get_requests_left.assert_called_once()
        mock_create_user_request.assert_called_once()
        mock_get_remote_file_tree.assert_called_once()
        mock_find_config_files.assert_called_once()
        mock_get_comments.assert_called_once()
        mock_get_latest_commit_sha.assert_called_once()
        mock_create_remote_branch.assert_called_once()
        mock_chat_with_agent.assert_called()
        mock_create_pull_request.assert_called_once()
        mock_update_usage.assert_called_once()

    @pytest.mark.asyncio
    @patch('services.webhook.issue_handler.deconstruct_jira_payload')
    @patch('services.webhook.issue_handler.create_comment')
    @patch('services.webhook.issue_handler.get_how_many_requests_left_and_cycle')
    @patch('services.webhook.issue_handler.create_user_request')
    @patch('services.webhook.issue_handler.get_remote_file_tree')
    @patch('services.webhook.issue_handler.find_config_files')
    @patch('services.webhook.issue_handler.get_remote_file_content')
    @patch('services.webhook.issue_handler.extract_image_urls')
    @patch('services.webhook.issue_handler.get_remote_file_content_by_url')
    @patch('services.webhook.issue_handler.create_remote_branch')
    @patch('services.webhook.issue_handler.chat_with_agent')
    @patch('services.webhook.issue_handler.create_pull_request')
    @patch('services.webhook.issue_handler.update_comment')
    @patch('services.webhook.issue_handler.update_usage')
    async def test_create_pr_from_issue_jira_success_flow(
        self,
        mock_update_usage,
        mock_update_comment,
        mock_create_pull_request,
        mock_chat_with_agent,
        mock_create_remote_branch,
        mock_get_remote_file_content_by_url,
        mock_extract_image_urls,
        mock_get_remote_file_content,
        mock_find_config_files,
        mock_get_remote_file_tree,
        mock_create_user_request,
        mock_get_requests_left,
        mock_create_comment,
        mock_deconstruct_jira_payload,
        mock_jira_payload,
        mock_base_args,
        mock_repo_settings
    ):
        """Test successful JIRA issue to PR creation flow."""
        # Arrange
        jira_base_args = mock_base_args.copy()
        jira_base_args["latest_commit_sha"] = "def456"
        jira_base_args["issue_comments"] = ["jira comment"]
        
        mock_deconstruct_jira_payload.return_value = (jira_base_args, mock_repo_settings)
        mock_create_comment.return_value = "https://api.github.com/repos/owner/repo/issues/comments/123"
        mock_get_requests_left.return_value = (5, 0, "2024-01-01", False)
        mock_create_user_request.return_value = "usage_record_123"
        mock_get_remote_file_tree.return_value = (["file1.py"], "Found 1 file")
        mock_find_config_files.return_value = []
        mock_get_remote_file_content.return_value = "file content"
        mock_extract_image_urls.return_value = []
        mock_get_remote_file_content_by_url.return_value = "url content"
        
        mock_chat_with_agent.side_effect = [
            ([], [], None, None, 100, 50, False, 10),
            ([], [], None, None, 100, 50, False, 15)
        ]
        
        mock_create_pull_request.return_value = "https://github.com/owner/repo/pull/42"
        
        # Act
        await create_pr_from_issue(
            payload=mock_jira_payload,
            trigger_type="comment",
            input_from="jira"
        )
        
        # Assert
        mock_deconstruct_jira_payload.assert_called_once_with(payload=mock_jira_payload)
        # Should not call delete_my_comments for JIRA
        mock_create_comment.assert_called()
        mock_create_remote_branch.assert_called_once()
        # Should use latest_commit_sha from base_args for JIRA
        mock_create_pull_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_pr_from_issue_wrong_label(self, mock_github_payload):
        """Test that function returns early when label doesn't match PRODUCT_ID."""
        # Arrange
        mock_github_payload["label"]["name"] = "wrong-label"
        
        # Act
        result = await create_pr_from_issue(
            payload=mock_github_payload,
            trigger_type="label",
            input_from="github"
        )
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    @patch('services.webhook.issue_handler.deconstruct_github_payload')
    @patch('services.webhook.issue_handler.delete_my_comments')
    @patch('services.webhook.issue_handler.create_comment')
    @patch('services.webhook.issue_handler.get_how_many_requests_left_and_cycle')
    @patch('services.webhook.issue_handler.update_comment')
    async def test_create_pr_from_issue_request_limit_reached(
        self,
        mock_update_comment,
        mock_get_requests_left,
        mock_create_comment,
        mock_delete_my_comments,
        mock_deconstruct_github_payload,
        mock_github_payload,
        mock_base_args,
        mock_repo_settings
    ):
        """Test that function handles request limit reached."""
        # Arrange
        mock_deconstruct_github_payload.return_value = (mock_base_args, mock_repo_settings)
        mock_create_comment.return_value = "https://api.github.com/repos/owner/repo/issues/comments/123"
        mock_get_requests_left.return_value = (0, 5, "2024-01-01", False)  # No requests left
        
        # Act
        await create_pr_from_issue(
            payload=mock_github_payload,
            trigger_type="label",
            input_from="github"
        )
        
        # Assert
        mock_update_comment.assert_called()
        call_args = mock_update_comment.call_args[1]
        assert "request limit" in call_args['body'].lower()

    @pytest.mark.asyncio
    @patch('services.webhook.issue_handler.deconstruct_github_payload')
    @patch('services.webhook.issue_handler.delete_my_comments')
    @patch('services.webhook.issue_handler.create_comment')
    @patch('services.webhook.issue_handler.get_how_many_requests_left_and_cycle')
    @patch('services.webhook.issue_handler.create_user_request')
    @patch('services.webhook.issue_handler.get_remote_file_tree')
    @patch('services.webhook.issue_handler.find_config_files')
    @patch('services.webhook.issue_handler.get_remote_file_content')
    @patch('services.webhook.issue_handler.get_comments')
    @patch('services.webhook.issue_handler.extract_image_urls')
    @patch('services.webhook.issue_handler.get_base64')
    @patch('services.webhook.issue_handler.describe_image')
    @patch('services.webhook.issue_handler.render_text')
    async def test_create_pr_from_issue_with_images(
        self,
        mock_render_text,
        mock_describe_image,
        mock_get_base64,
        mock_extract_image_urls,
        mock_get_comments,
        mock_get_remote_file_content,
        mock_find_config_files,
        mock_get_remote_file_tree,
        mock_create_user_request,
        mock_get_requests_left,
        mock_create_comment,
        mock_delete_my_comments,
        mock_deconstruct_github_payload,
        mock_github_payload,
        mock_base_args,
        mock_repo_settings
    ):
        """Test handling of images in issue body and comments."""
        # Arrange
        mock_deconstruct_github_payload.return_value = (mock_base_args, mock_repo_settings)
        mock_create_comment.return_value = "https://api.github.com/repos/owner/repo/issues/comments/123"
        mock_get_requests_left.return_value = (5, 0, "2024-01-01", False)
        mock_create_user_request.return_value = "usage_record_123"
        mock_get_remote_file_tree.return_value = (["file1.py"], "Found 1 file")
        mock_find_config_files.return_value = []
        mock_get_remote_file_content.return_value = "file content"
        mock_get_comments.return_value = ["comment with image"]
        mock_render_text.side_effect = lambda base_args, text: text
        mock_extract_image_urls.side_effect = [
            [{"url": "https://example.com/image1.png", "alt": "Image 1"}],  # From issue body
            [{"url": "https://example.com/image2.png", "alt": "Image 2"}]   # From comment
        ]
        mock_get_base64.return_value = "base64_image_data"
        mock_describe_image.return_value = "Image description"
        
        with patch('services.webhook.issue_handler.get_remote_file_content_by_url') as mock_get_url_content, \
             patch('services.webhook.issue_handler.get_latest_remote_commit_sha') as mock_get_commit_sha, \
             patch('services.webhook.issue_handler.create_remote_branch') as mock_create_branch, \
             patch('services.webhook.issue_handler.chat_with_agent') as mock_chat_agent, \
             patch('services.webhook.issue_handler.create_pull_request') as mock_create_pr, \
             patch('services.webhook.issue_handler.update_usage') as mock_update_usage:
            
            mock_get_url_content.return_value = "url content"
            mock_get_commit_sha.return_value = "abc123"
            mock_chat_agent.side_effect = [
                ([], [], None, None, 100, 50, False, 10),
                ([], [], None, None, 100, 50, False, 15)
            ]
            mock_create_pr.return_value = "https://github.com/owner/repo/pull/42"
            
            # Act
            await create_pr_from_issue(
                payload=mock_github_payload,
                trigger_type="label",
                input_from="github"
            )
            
            # Assert
            mock_extract_image_urls.assert_called()
            mock_get_base64.assert_called()
            mock_describe_image.assert_called()
            # Should create comments for image descriptions
            assert mock_create_comment.call_count >= 3  # Initial + 2 image descriptions

    @pytest.mark.asyncio
    @patch('services.webhook.issue_handler.deconstruct_github_payload')
    @patch('services.webhook.issue_handler.delete_my_comments')
    @patch('services.webhook.issue_handler.create_comment')
    @patch('services.webhook.issue_handler.get_how_many_requests_left_and_cycle')
    @patch('services.webhook.issue_handler.create_user_request')
    @patch('services.webhook.issue_handler.get_remote_file_tree')
    @patch('services.webhook.issue_handler.find_config_files')
    @patch('services.webhook.issue_handler.get_remote_file_content')
    @patch('services.webhook.issue_handler.get_comments')
    @patch('services.webhook.issue_handler.extract_image_urls')
    @patch('services.webhook.issue_handler.get_remote_file_content_by_url')
    @patch('services.webhook.issue_handler.get_latest_remote_commit_sha')
    @patch('services.webhook.issue_handler.create_remote_branch')
    @patch('services.webhook.issue_handler.chat_with_agent')
    @patch('services.webhook.issue_handler.create_pull_request')
    @patch('services.webhook.issue_handler.update_comment')
    @patch('services.webhook.issue_handler.update_usage')
    async def test_create_pr_from_issue_pr_creation_fails(
        self,
        mock_update_usage,
        mock_update_comment,
        mock_create_pull_request,
        mock_chat_with_agent,
        mock_create_remote_branch,
        mock_get_latest_commit_sha,
        mock_get_remote_file_content_by_url,
        mock_extract_image_urls,
        mock_get_comments,
        mock_get_remote_file_content,
        mock_find_config_files,
        mock_get_remote_file_tree,
        mock_create_user_request,
        mock_get_requests_left,
        mock_create_comment,
        mock_delete_my_comments,
        mock_deconstruct_github_payload,
        mock_github_payload,
        mock_base_args,
        mock_repo_settings
    ):
        """Test handling when PR creation fails."""
        # Arrange
        mock_deconstruct_github_payload.return_value = (mock_base_args, mock_repo_settings)
        mock_create_comment.return_value = "https://api.github.com/repos/owner/repo/issues/comments/123"
        mock_get_requests_left.return_value = (5, 0, "2024-01-01", False)
        mock_create_user_request.return_value = "usage_record_123"
        mock_get_remote_file_tree.return_value = (["file1.py"], "Found 1 file")
        mock_find_config_files.return_value = []
        mock_get_remote_file_content.return_value = "file content"
        mock_get_comments.return_value = []
        mock_extract_image_urls.return_value = []
        mock_get_remote_file_content_by_url.return_value = "url content"
        mock_get_latest_commit_sha.return_value = "abc123"
        
        mock_chat_with_agent.side_effect = [
            ([], [], None, None, 100, 50, False, 10),
            ([], [], None, None, 100, 50, False, 15)
        ]
        
        mock_create_pull_request.return_value = None  # PR creation fails
        
        # Act
        await create_pr_from_issue(
            payload=mock_github_payload,
            trigger_type="label",
            input_from="github"
        )
        
        # Assert
        mock_update_usage.assert_called_once()
        usage_call_args = mock_update_usage.call_args[1]
        assert usage_call_args['is_completed'] is False
        assert usage_call_args['pr_number'] is None

    @pytest.mark.asyncio
    async def test_create_pr_from_issue_exception_owner_bypass(self, mock_github_payload):
        """Test that exception owners bypass request limits."""
        # Modify payload to use exception owner
        mock_github_payload["repository"]["owner"]["login"] = EXCEPTION_OWNERS[0]
        
        with patch('services.webhook.issue_handler.deconstruct_github_payload') as mock_deconstruct, \
             patch('services.webhook.issue_handler.delete_my_comments') as mock_delete_comments, \
             patch('services.webhook.issue_handler.create_comment') as mock_create_comment, \
             patch('services.webhook.issue_handler.get_how_many_requests_left_and_cycle') as mock_get_requests, \
             patch('services.webhook.issue_handler.create_user_request') as mock_create_user_request:
            
            # Arrange
            base_args = {
                "owner": EXCEPTION_OWNERS[0],
                "repo": "test-repo",
                "sender_name": "test-sender"
            }
            mock_deconstruct.return_value = (base_args, {})
            mock_create_comment.return_value = "https://api.github.com/repos/owner/repo/issues/comments/123"
            mock_get_requests.return_value = (0, 5, "2024-01-01", False)  # No requests left
            mock_create_user_request.return_value = "usage_record_123"
            
            # Act
            await create_pr_from_issue(
                payload=mock_github_payload,
                trigger_type="label",
                input_from="github"
            )
            
            # Assert - should proceed despite no requests left because owner is in exceptions
            mock_create_user_request.assert_called_once()  # Should reach this point
