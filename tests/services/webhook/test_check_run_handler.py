import pytest
from unittest.mock import patch, MagicMock, call
from typing import Any, Dict

from services.webhook.check_run_handler import handle_check_run
from config import GITHUB_APP_USER_NAME, STRIPE_PRODUCT_ID_FREE, EXCEPTION_OWNERS


@pytest.fixture
def mock_check_run_payload():
    """Mock check run completed payload."""
    return {
        "check_run": {
            "id": 123456,
            "name": "test-check",
            "details_url": "https://github.com/owner/repo/actions/runs/987654321/job/123456789",
            "check_suite": {
                "head_branch": "feature-branch"
            },
            "pull_requests": [
                {
                    "number": 42,
                    "url": "https://api.github.com/repos/owner/repo/pulls/42"
                }
            ]
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
        "sender": {
            "id": 999,
            "login": GITHUB_APP_USER_NAME
        },
        "installation": {
            "id": 12345
        }
    }


@pytest.fixture
def mock_check_run_payload_no_pr():
    """Mock check run payload without pull requests."""
    return {
        "check_run": {
            "id": 123456,
            "name": "test-check",
            "details_url": "https://github.com/owner/repo/actions/runs/987654321/job/123456789",
            "check_suite": {
                "head_branch": "feature-branch"
            },
            "pull_requests": []
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
        "sender": {
            "id": 999,
            "login": GITHUB_APP_USER_NAME
        },
        "installation": {
            "id": 12345
        }
    }


@pytest.fixture
def mock_check_run_payload_wrong_sender():
    """Mock check run payload with wrong sender."""
    return {
        "check_run": {
            "id": 123456,
            "name": "test-check",
            "details_url": "https://github.com/owner/repo/actions/runs/987654321/job/123456789",
            "check_suite": {
                "head_branch": "feature-branch"
            },
            "pull_requests": [
                {
                    "number": 42,
                    "url": "https://api.github.com/repos/owner/repo/pulls/42"
                }
            ]
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
        "sender": {
            "id": 999,
            "login": "other-user"
        },
        "installation": {
            "id": 12345
        }
    }


class TestHandleCheckRun:
    """Test cases for handle_check_run function."""

    @patch('services.webhook.check_run_handler.get_installation_access_token')
    @patch('services.webhook.check_run_handler.create_comment')
    @patch('services.webhook.check_run_handler.get_stripe_customer_id')
    @patch('services.webhook.check_run_handler.get_stripe_product_id')
    @patch('services.webhook.check_run_handler.get_pull_request')
    @patch('services.webhook.check_run_handler.get_pull_request_file_changes')
    @patch('services.webhook.check_run_handler.get_workflow_run_path')
    @patch('services.webhook.check_run_handler.get_remote_file_content')
    @patch('services.webhook.check_run_handler.get_remote_file_tree')
    @patch('services.webhook.check_run_handler.get_workflow_run_logs')
    @patch('services.webhook.check_run_handler.get_retry_workflow_id_hash_pairs')
    @patch('services.webhook.check_run_handler.update_retry_workflow_id_hash_pairs')
    @patch('services.webhook.check_run_handler.get_repository_settings')
    @patch('services.webhook.check_run_handler.create_system_messages')
    @patch('services.webhook.check_run_handler.chat_with_agent')
    @patch('services.webhook.check_run_handler.update_comment')
    def test_handle_check_run_success_flow(
        self,
        mock_update_comment,
        mock_chat_with_agent,
        mock_create_system_messages,
        mock_get_repository_settings,
        mock_update_retry_pairs,
        mock_get_retry_pairs,
        mock_get_workflow_logs,
        mock_get_remote_file_tree,
        mock_get_remote_file_content,
        mock_get_workflow_path,
        mock_get_pr_file_changes,
        mock_get_pull_request,
        mock_get_stripe_product_id,
        mock_get_stripe_customer_id,
        mock_create_comment,
        mock_get_installation_token,
        mock_check_run_payload
    ):
        """Test successful check run handling flow."""
        # Arrange
        mock_get_installation_token.return_value = "test_token"
        mock_create_comment.return_value = "https://api.github.com/repos/owner/repo/issues/comments/123"
        mock_get_stripe_customer_id.return_value = "cus_123"
        mock_get_stripe_product_id.return_value = "prod_standard"
        mock_get_pull_request.return_value = ("Test PR", "Test PR body")
        mock_get_pr_file_changes.return_value = [{"filename": "test.py", "patch": "diff"}]
        mock_get_workflow_path.return_value = ".github/workflows/test.yml"
        mock_get_remote_file_content.return_value = "workflow content"
        mock_get_remote_file_tree.return_value = "file tree"
        mock_get_workflow_logs.return_value = "error log content"
        mock_get_retry_pairs.return_value = []
        mock_get_repository_settings.return_value = {"repo_rules": "test rules"}
        mock_create_system_messages.return_value = [{"role": "system", "content": "system message"}]
        
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
        
        # Act
        handle_check_run(mock_check_run_payload)
        
        # Assert
        mock_get_installation_token.assert_called_once_with(installation_id=12345)
        mock_create_comment.assert_called_once()
        mock_get_stripe_customer_id.assert_called_once_with(owner_id=456)
        mock_get_stripe_product_id.assert_called_once_with(customer_id="cus_123")
        mock_get_pull_request.assert_called_once()
        mock_get_pr_file_changes.assert_called_once()
        mock_get_workflow_path.assert_called_once()
        mock_get_remote_file_content.assert_called_once()
        mock_get_remote_file_tree.assert_called_once()
        mock_get_workflow_logs.assert_called_once()
        mock_update_retry_pairs.assert_called_once()
        mock_chat_with_agent.assert_called()
        mock_update_comment.assert_called()
        
        # Check final message
        final_call = mock_update_comment.call_args_list[-1]
        assert "Committed the Check Run" in final_call[0][0]

    @patch('services.webhook.check_run_handler.colorize')
    def test_handle_check_run_skips_wrong_sender(self, mock_colorize, mock_check_run_payload_wrong_sender):
        """Test that handle_check_run skips when sender is not GitAuto."""
        # Act
        handle_check_run(mock_check_run_payload_wrong_sender)
        
        # Assert
        mock_colorize.assert_called_once()
        assert "sender is not GitAuto" in mock_colorize.call_args[1]['text']

    @patch('services.webhook.check_run_handler.get_installation_access_token')
    @patch('services.webhook.check_run_handler.colorize')
    def test_handle_check_run_skips_no_pull_requests(self, mock_colorize, mock_get_installation_token, mock_check_run_payload_no_pr):
        """Test that handle_check_run skips when no pull requests are associated."""
        # Arrange
        mock_get_installation_token.return_value = "test_token"
        
        # Act
        handle_check_run(mock_check_run_payload_no_pr)
        
        # Assert
        mock_colorize.assert_called_once()
        assert "no pull request is associated" in mock_colorize.call_args[1]['text']

    @patch('services.webhook.check_run_handler.get_installation_access_token')
    @patch('services.webhook.check_run_handler.create_comment')
    @patch('services.webhook.check_run_handler.get_stripe_customer_id')
    @patch('services.webhook.check_run_handler.update_comment')
    def test_handle_check_run_no_stripe_customer(self, mock_update_comment, mock_get_stripe_customer_id, mock_create_comment, mock_get_installation_token, mock_check_run_payload):
        """Test handle_check_run when no Stripe customer ID is found."""
        # Arrange
        mock_get_installation_token.return_value = "test_token"
        mock_create_comment.return_value = "https://api.github.com/repos/owner/repo/issues/comments/123"
        mock_get_stripe_customer_id.return_value = None
        
        # Act
        handle_check_run(mock_check_run_payload)
        
        # Assert
        mock_update_comment.assert_called_once()
        call_args = mock_update_comment.call_args[1]
        assert "Subscribe" in call_args['body']
        assert "pricing" in call_args['body']

    @patch('services.webhook.check_run_handler.get_installation_access_token')
    @patch('services.webhook.check_run_handler.create_comment')
    @patch('services.webhook.check_run_handler.get_stripe_customer_id')
    @patch('services.webhook.check_run_handler.get_stripe_product_id')
    @patch('services.webhook.check_run_handler.update_comment')
    def test_handle_check_run_free_tier_user(self, mock_update_comment, mock_get_stripe_product_id, mock_get_stripe_customer_id, mock_create_comment, mock_get_installation_token, mock_check_run_payload):
        """Test handle_check_run for free tier users."""
        # Arrange
        mock_get_installation_token.return_value = "test_token"
        mock_create_comment.return_value = "https://api.github.com/repos/owner/repo/issues/comments/123"
        mock_get_stripe_customer_id.return_value = "cus_123"
        mock_get_stripe_product_id.return_value = STRIPE_PRODUCT_ID_FREE
        
        # Act
        handle_check_run(mock_check_run_payload)
        
        # Assert
        mock_update_comment.assert_called_once()
        call_args = mock_update_comment.call_args[1]
        assert "Subscribe" in call_args['body']

    @patch('services.webhook.check_run_handler.get_installation_access_token')
    @patch('services.webhook.check_run_handler.create_comment')
    @patch('services.webhook.check_run_handler.get_stripe_customer_id')
    @patch('services.webhook.check_run_handler.get_stripe_product_id')
    @patch('services.webhook.check_run_handler.get_pull_request')
    @patch('services.webhook.check_run_handler.get_pull_request_file_changes')
    @patch('services.webhook.check_run_handler.get_workflow_run_path')
    @patch('services.webhook.check_run_handler.create_permission_url')
    @patch('services.webhook.check_run_handler.update_comment')
    def test_handle_check_run_workflow_path_404(
        self,
        mock_update_comment,
        mock_create_permission_url,
        mock_get_workflow_path,
        mock_get_pr_file_changes,
        mock_get_pull_request,
        mock_get_stripe_product_id,
        mock_get_stripe_customer_id,
        mock_create_comment,
        mock_get_installation_token,
        mock_check_run_payload
    ):
        """Test handle_check_run when workflow path returns 404."""
        # Arrange
        mock_get_installation_token.return_value = "test_token"
        mock_create_comment.return_value = "https://api.github.com/repos/owner/repo/issues/comments/123"
        mock_get_stripe_customer_id.return_value = "cus_123"
        mock_get_stripe_product_id.return_value = "prod_standard"
        mock_get_pull_request.return_value = ("Test PR", "Test PR body")
        mock_get_pr_file_changes.return_value = [{"filename": "test.py"}]
        mock_get_workflow_path.return_value = 404
        mock_create_permission_url.return_value = "https://github.com/apps/gitauto/installations/new"
        
        # Act
        handle_check_run(mock_check_run_payload)
        
        # Assert
        mock_update_comment.assert_called()
        call_args = mock_update_comment.call_args[1]
        assert "Approve permission" in call_args['body']
        assert "https://github.com/apps/gitauto/installations/new" in call_args['body']

    @patch('services.webhook.check_run_handler.get_installation_access_token')
    @patch('services.webhook.check_run_handler.create_comment')
    @patch('services.webhook.check_run_handler.get_stripe_customer_id')
    @patch('services.webhook.check_run_handler.get_stripe_product_id')
    @patch('services.webhook.check_run_handler.get_pull_request')
    @patch('services.webhook.check_run_handler.get_pull_request_file_changes')
    @patch('services.webhook.check_run_handler.get_workflow_run_path')
    @patch('services.webhook.check_run_handler.get_remote_file_content')
    @patch('services.webhook.check_run_handler.get_remote_file_tree')
    @patch('services.webhook.check_run_handler.get_workflow_run_logs')
    @patch('services.webhook.check_run_handler.update_comment')
    def test_handle_check_run_workflow_logs_404(
        self,
        mock_update_comment,
        mock_get_workflow_logs,
        mock_get_remote_file_tree,
        mock_get_remote_file_content,
        mock_get_workflow_path,
        mock_get_pr_file_changes,
        mock_get_pull_request,
        mock_get_stripe_product_id,
        mock_get_stripe_customer_id,
        mock_create_comment,
        mock_get_installation_token,
        mock_check_run_payload
    ):
        """Test handle_check_run when workflow logs return 404."""
        # Arrange
        mock_get_installation_token.return_value = "test_token"
        mock_create_comment.return_value = "https://api.github.com/repos/owner/repo/issues/comments/123"
        mock_get_stripe_customer_id.return_value = "cus_123"
        mock_get_stripe_product_id.return_value = "prod_standard"
        mock_get_pull_request.return_value = ("Test PR", "Test PR body")
        mock_get_pr_file_changes.return_value = [{"filename": "test.py"}]
        mock_get_workflow_path.return_value = ".github/workflows/test.yml"
        mock_get_remote_file_content.return_value = "workflow content"
        mock_get_remote_file_tree.return_value = "file tree"
        mock_get_workflow_logs.return_value = 404
        
        # Act
        handle_check_run(mock_check_run_payload)
        
        # Assert
        mock_update_comment.assert_called()
        call_args = mock_update_comment.call_args[1]
        assert "Approve permission" in call_args['body']

    @patch('services.webhook.check_run_handler.get_installation_access_token')
    @patch('services.webhook.check_run_handler.create_comment')
    @patch('services.webhook.check_run_handler.get_stripe_customer_id')
    @patch('services.webhook.check_run_handler.get_stripe_product_id')
    @patch('services.webhook.check_run_handler.get_pull_request')
    @patch('services.webhook.check_run_handler.get_pull_request_file_changes')
    @patch('services.webhook.check_run_handler.get_workflow_run_path')
    @patch('services.webhook.check_run_handler.get_remote_file_content')
    @patch('services.webhook.check_run_handler.get_remote_file_tree')
    @patch('services.webhook.check_run_handler.get_workflow_run_logs')
    @patch('services.webhook.check_run_handler.get_retry_workflow_id_hash_pairs')
    @patch('services.webhook.check_run_handler.update_comment')
    def test_handle_check_run_duplicate_error_hash(
        self,
        mock_update_comment,
        mock_get_retry_pairs,
        mock_get_workflow_logs,
        mock_get_remote_file_tree,
        mock_get_remote_file_content,
        mock_get_workflow_path,
        mock_get_pr_file_changes,
        mock_get_pull_request,
        mock_get_stripe_product_id,
        mock_get_stripe_customer_id,
        mock_create_comment,
        mock_get_installation_token,
        mock_check_run_payload
    ):
        """Test handle_check_run when error hash already exists (duplicate error)."""
        # Arrange
        mock_get_installation_token.return_value = "test_token"
        mock_create_comment.return_value = "https://api.github.com/repos/owner/repo/issues/comments/123"
        mock_get_stripe_customer_id.return_value = "cus_123"
        mock_get_stripe_product_id.return_value = "prod_standard"
        mock_get_pull_request.return_value = ("Test PR", "Test PR body")
        mock_get_pr_file_changes.return_value = [{"filename": "test.py"}]
        mock_get_workflow_path.return_value = ".github/workflows/test.yml"
        mock_get_remote_file_content.return_value = "workflow content"
        mock_get_remote_file_tree.return_value = "file tree"
        mock_get_workflow_logs.return_value = "error log content"
        
        # Mock existing error hash
        with patch('services.webhook.check_run_handler.hashlib') as mock_hashlib:
            mock_hash = MagicMock()
            mock_hash.hexdigest.return_value = "abc123"
            mock_hashlib.sha256.return_value = mock_hash
            mock_get_retry_pairs.return_value = ["987654321:abc123"]  # Same hash exists
            
            # Act
            handle_check_run(mock_check_run_payload)
            
            # Assert
            mock_update_comment.assert_called()
            call_args = mock_update_comment.call_args[1]
            assert "already tried to fix this exact error" in call_args['body']

    def test_handle_check_run_exception_owner_bypass(self, mock_check_run_payload):
        """Test that exception owners bypass payment checks."""
        # Modify payload to use exception owner
        mock_check_run_payload["repository"]["owner"]["login"] = EXCEPTION_OWNERS[0]
        
        with patch('services.webhook.check_run_handler.get_installation_access_token') as mock_get_token, \
             patch('services.webhook.check_run_handler.create_comment') as mock_create_comment, \
             patch('services.webhook.check_run_handler.get_stripe_customer_id') as mock_get_customer_id, \
             patch('services.webhook.check_run_handler.get_stripe_product_id') as mock_get_product_id, \
             patch('services.webhook.check_run_handler.get_pull_request') as mock_get_pr:
            
            # Arrange
            mock_get_token.return_value = "test_token"
            mock_create_comment.return_value = "https://api.github.com/repos/owner/repo/issues/comments/123"
            mock_get_customer_id.return_value = "cus_123"
            mock_get_product_id.return_value = STRIPE_PRODUCT_ID_FREE  # Free tier
            mock_get_pr.return_value = ("Test PR", "Test PR body")
            
            # Act
            handle_check_run(mock_check_run_payload)
            
            # Assert - should proceed despite free tier because owner is in exceptions
            mock_get_pr.assert_called_once()  # Should reach this point
