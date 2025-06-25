import pytest
from unittest.mock import patch, MagicMock, call
from typing import Any, Dict

from services.webhook.review_run_handler import handle_review_run
from config import GITHUB_APP_USER_NAME, STRIPE_PRODUCT_ID_FREE, EXCEPTION_OWNERS


@pytest.fixture
def mock_review_payload():
    """Mock review comment payload."""
    return {
        "comment": {
            "id": 123456,
            "node_id": "MDI6UHVsbFJlcXVlc3RSZXZpZXdDb21tZW50MTIzNDU2",
            "path": "src/main.py",
            "subject_type": "line",
            "line": 42,
            "side": "RIGHT",
            "position": 10,
            "body": "This needs to be fixed"
        },
        "repository": {
            "id": 789,
            "name": "test-repo",
            "fork": False,
            "owner": {
                "id": 456,
                "login": "test-owner",
                "type": "Organization"
            }
        },
        "pull_request": {
            "number": 42,
            "title": "Test PR",
            "body": "Test PR body",
            "url": "https://api.github.com/repos/test-owner/test-repo/pulls/42",
            "head": {
                "ref": "feature-branch"
            },
            "user": {
                "login": GITHUB_APP_USER_NAME
            }
        },
        "sender": {
            "id": 999,
            "login": "test-reviewer"
        },
        "installation": {
            "id": 12345
        }
    }


@pytest.fixture
def mock_review_payload_wrong_pr_user():
    """Mock review payload with wrong PR user."""
    return {
        "comment": {
            "id": 123456,
            "node_id": "MDI6UHVsbFJlcXVlc3RSZXZpZXdDb21tZW50MTIzNDU2",
            "path": "src/main.py",
            "subject_type": "line",
            "line": 42,
            "side": "RIGHT",
            "position": 10,
            "body": "This needs to be fixed"
        },
        "repository": {
            "id": 789,
            "name": "test-repo",
            "fork": False,
            "owner": {
                "id": 456,
                "login": "test-owner",
                "type": "Organization"
            }
        },
        "pull_request": {
            "number": 42,
            "title": "Test PR",
            "body": "Test PR body",
            "url": "https://api.github.com/repos/test-owner/test-repo/pulls/42",
            "head": {
                "ref": "feature-branch"
            },
            "user": {
                "login": "other-user"  # Not GitAuto
            }
        },
        "sender": {
            "id": 999,
            "login": "test-reviewer"
        },
        "installation": {
            "id": 12345
        }
    }


@pytest.fixture
def mock_review_payload_gitauto_sender():
    """Mock review payload with GitAuto as sender."""
    return {
        "comment": {
            "id": 123456,
            "node_id": "MDI6UHVsbFJlcXVlc3RSZXZpZXdDb21tZW50MTIzNDU2",
            "path": "src/main.py",
            "subject_type": "line",
            "line": 42,
            "side": "RIGHT",
            "position": 10,
            "body": "This needs to be fixed"
        },
        "repository": {
            "id": 789,
            "name": "test-repo",
            "fork": False,
            "owner": {
                "id": 456,
                "login": "test-owner",
                "type": "Organization"
            }
        },
        "pull_request": {
            "number": 42,
            "title": "Test PR",
            "body": "Test PR body",
            "url": "https://api.github.com/repos/test-owner/test-repo/pulls/42",
            "head": {
                "ref": "feature-branch"
            },
            "user": {
                "login": GITHUB_APP_USER_NAME
            }
        },
        "sender": {
            "id": 999,
            "login": GITHUB_APP_USER_NAME  # GitAuto as sender
        },
        "installation": {
            "id": 12345
        }
    }


class TestHandleReviewRun:
    """Test cases for handle_review_run function."""

    def test_handle_review_run_wrong_pr_user(self, mock_review_payload_wrong_pr_user):
        """Test that function returns early when PR user is not GitAuto."""
        # Act
        handle_review_run(mock_review_payload_wrong_pr_user)
        
        # Assert - function should return early, no further processing
        # This is verified by the fact that no exceptions are raised and function completes

    def test_handle_review_run_gitauto_sender(self, mock_review_payload_gitauto_sender):
        """Test that function returns early when sender is GitAuto itself."""
        # Act
        handle_review_run(mock_review_payload_gitauto_sender)
        
        # Assert - function should return early, no further processing
        # This is verified by the fact that no exceptions are raised and function completes

    @patch('services.webhook.review_run_handler.get_installation_access_token')
    @patch('services.webhook.review_run_handler.get_review_thread_comments')
    @patch('services.webhook.review_run_handler.get_stripe_customer_id')
    def test_handle_review_run_no_stripe_customer(
        self,
        mock_get_stripe_customer_id,
        mock_get_review_thread_comments,
        mock_get_installation_token,
        mock_review_payload
    ):
        """Test that function returns early when no Stripe customer ID is found."""
        # Arrange
        mock_get_installation_token.return_value = "test_token"
        mock_get_review_thread_comments.return_value = []
        mock_get_stripe_customer_id.return_value = None
        
        # Act
        handle_review_run(mock_review_payload)
        
        # Assert
        mock_get_stripe_customer_id.assert_called_once_with(owner_id=456)

    @patch('services.webhook.review_run_handler.get_installation_access_token')
    @patch('services.webhook.review_run_handler.get_review_thread_comments')
    @patch('services.webhook.review_run_handler.get_stripe_customer_id')
    @patch('services.webhook.review_run_handler.get_stripe_product_id')
    @patch('services.webhook.review_run_handler.colorize')
    def test_handle_review_run_free_tier_user(
        self,
        mock_colorize,
        mock_get_stripe_product_id,
        mock_get_stripe_customer_id,
        mock_get_review_thread_comments,
        mock_get_installation_token,
        mock_review_payload
    ):
        """Test that function returns early for free tier users."""
        # Arrange
        mock_get_installation_token.return_value = "test_token"
        mock_get_review_thread_comments.return_value = []
        mock_get_stripe_customer_id.return_value = "cus_123"
        mock_get_stripe_product_id.return_value = STRIPE_PRODUCT_ID_FREE
        
        # Act
        handle_review_run(mock_review_payload)
        
        # Assert
        mock_colorize.assert_called_once()
        assert "free tier" in mock_colorize.call_args[1]['text']

    @patch('services.webhook.review_run_handler.get_installation_access_token')
    @patch('services.webhook.review_run_handler.get_review_thread_comments')
    @patch('services.webhook.review_run_handler.get_stripe_customer_id')
    @patch('services.webhook.review_run_handler.get_stripe_product_id')
    @patch('services.webhook.review_run_handler.reply_to_comment')
    @patch('services.webhook.review_run_handler.get_remote_file_content')
    @patch('services.webhook.review_run_handler.get_pull_request_file_contents')
    @patch('services.webhook.review_run_handler.get_remote_file_tree')
    @patch('services.webhook.review_run_handler.get_repository_settings')
    @patch('services.webhook.review_run_handler.create_system_messages')
    @patch('services.webhook.review_run_handler.chat_with_agent')
    @patch('services.webhook.review_run_handler.update_comment')
    def test_handle_review_run_success_flow(
        self,
        mock_update_comment,
        mock_chat_with_agent,
        mock_create_system_messages,
        mock_get_repository_settings,
        mock_get_remote_file_tree,
        mock_get_pull_request_file_contents,
        mock_get_remote_file_content,
        mock_reply_to_comment,
        mock_get_stripe_product_id,
        mock_get_stripe_customer_id,
        mock_get_review_thread_comments,
        mock_get_installation_token,
        mock_review_payload
    ):
        """Test successful review run handling flow."""
        # Arrange
        mock_get_installation_token.return_value = "test_token"
        mock_get_review_thread_comments.return_value = [
            {
                "author": {"login": "reviewer1"},
                "body": "First comment",
                "createdAt": "2024-01-01T12:00:00Z"
            },
            {
                "author": {"login": "reviewer2"},
                "body": "Second comment",
                "createdAt": "2024-01-01T12:30:00Z"
            }
        ]
        mock_get_stripe_customer_id.return_value = "cus_123"
        mock_get_stripe_product_id.return_value = "prod_standard"
        mock_reply_to_comment.return_value = "https://api.github.com/repos/owner/repo/issues/comments/123"
        mock_get_remote_file_content.return_value = "file content"
        mock_get_pull_request_file_contents.return_value = [{"filename": "test.py", "patch": "diff"}]
        mock_get_remote_file_tree.return_value = (["file1.py", "file2.py"], "Found 2 files")
        mock_get_repository_settings.return_value = {"repo_rules": "test rules"}
        mock_create_system_messages.return_value = [{"role": "system", "content": "system message"}]
        
        # Mock chat_with_agent to simulate exploration and commit phases
        mock_chat_with_agent.side_effect = [
            # First call (exploration)
            ([], [], "get_remote_file_content", {"file_path": "src/main.py"}, 100, 50, True, 10),
            # Second call (commit)
            ([], [], "apply_diff_to_file", {"file_path": "src/main.py"}, 100, 50, True, 15),
            # Third call (exploration - no more files)
            ([], [], None, None, 100, 50, False, 20),
            # Fourth call (commit - no more changes)
            ([], [], None, None, 100, 50, False, 25)
        ]
        
        # Act
        handle_review_run(mock_review_payload)
        
        # Assert
        mock_get_installation_token.assert_called_once_with(installation_id=12345)
        mock_get_review_thread_comments.assert_called_once()
        mock_get_stripe_customer_id.assert_called_once_with(owner_id=456)
        mock_get_stripe_product_id.assert_called_once_with(customer_id="cus_123")
        mock_reply_to_comment.assert_called_once()
        mock_get_remote_file_content.assert_called_once()
        mock_get_pull_request_file_contents.assert_called_once()
        mock_get_remote_file_tree.assert_called_once()
        mock_get_repository_settings.assert_called_once()
        mock_chat_with_agent.assert_called()
        mock_update_comment.assert_called()
        
        # Check final message
        final_call = mock_update_comment.call_args_list[-1]
        assert "Resolved your feedback" in final_call[0][0]

    @patch('services.webhook.review_run_handler.get_installation_access_token')
    @patch('services.webhook.review_run_handler.get_review_thread_comments')
    @patch('services.webhook.review_run_handler.get_stripe_customer_id')
    @patch('services.webhook.review_run_handler.get_stripe_product_id')
    @patch('services.webhook.review_run_handler.reply_to_comment')
    @patch('services.webhook.review_run_handler.get_remote_file_content')
    @patch('services.webhook.review_run_handler.get_pull_request_file_contents')
    @patch('services.webhook.review_run_handler.get_remote_file_tree')
    @patch('services.webhook.review_run_handler.get_repository_settings')
    @patch('services.webhook.review_run_handler.create_system_messages')
    @patch('services.webhook.review_run_handler.chat_with_agent')
    @patch('services.webhook.review_run_handler.update_comment')
    def test_handle_review_run_no_thread_comments(
        self,
        mock_update_comment,
        mock_chat_with_agent,
        mock_create_system_messages,
        mock_get_repository_settings,
        mock_get_remote_file_tree,
        mock_get_pull_request_file_contents,
        mock_get_remote_file_content,
        mock_reply_to_comment,
        mock_get_stripe_product_id,
        mock_get_stripe_customer_id,
        mock_get_review_thread_comments,
        mock_get_installation_token,
        mock_review_payload
    ):
        """Test handling when no thread comments are found."""
        # Arrange
        mock_get_installation_token.return_value = "test_token"
        mock_get_review_thread_comments.return_value = []  # No thread comments
        mock_get_stripe_customer_id.return_value = "cus_123"
        mock_get_stripe_product_id.return_value = "prod_standard"
        mock_reply_to_comment.return_value = "https://api.github.com/repos/owner/repo/issues/comments/123"
        mock_get_remote_file_content.return_value = "file content"
        mock_get_pull_request_file_contents.return_value = [{"filename": "test.py"}]
        mock_get_remote_file_tree.return_value = (["file1.py"], "Found 1 file")
        mock_get_repository_settings.return_value = {"repo_rules": "test rules"}
        mock_create_system_messages.return_value = [{"role": "system", "content": "system message"}]
        
        mock_chat_with_agent.side_effect = [
            ([], [], None, None, 100, 50, False, 10),
            ([], [], None, None, 100, 50, False, 15)
        ]
        
        # Act
        handle_review_run(mock_review_payload)
        
        # Assert
        # Should use fallback to single comment body
        mock_chat_with_agent.assert_called()
        # Check that the input message contains the review body
        chat_call_args = mock_chat_with_agent.call_args_list[0]
        messages = chat_call_args[1]['messages']
        user_input = messages[0]['content']
        assert "This needs to be fixed" in user_input

    def test_handle_review_run_exception_owner_bypass(self, mock_review_payload):
        """Test that exception owners bypass payment checks."""
        # Modify payload to use exception owner
        mock_review_payload["repository"]["owner"]["login"] = EXCEPTION_OWNERS[0]
        
        with patch('services.webhook.review_run_handler.get_installation_access_token') as mock_get_token, \
             patch('services.webhook.review_run_handler.get_review_thread_comments') as mock_get_thread_comments, \
             patch('services.webhook.review_run_handler.get_stripe_customer_id') as mock_get_customer_id, \
             patch('services.webhook.review_run_handler.get_stripe_product_id') as mock_get_product_id, \
             patch('services.webhook.review_run_handler.reply_to_comment') as mock_reply_to_comment:
            
            # Arrange
            mock_get_token.return_value = "test_token"
            mock_get_thread_comments.return_value = []
            mock_get_customer_id.return_value = "cus_123"
            mock_get_product_id.return_value = STRIPE_PRODUCT_ID_FREE  # Free tier
            mock_reply_to_comment.return_value = "https://api.github.com/repos/owner/repo/issues/comments/123"
            
            # Act
            handle_review_run(mock_review_payload)
            
            # Assert - should proceed despite free tier because owner is in exceptions
            mock_reply_to_comment.assert_called_once()  # Should reach this point
