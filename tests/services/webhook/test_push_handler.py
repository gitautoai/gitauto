import pytest
from unittest.mock import patch, MagicMock, call
from typing import Any, Dict

from services.webhook.push_handler import handle_push_event
from config import STRIPE_PRODUCT_ID_FREE, EXCEPTION_OWNERS


@pytest.fixture
def mock_push_payload():
    """Mock push event payload."""
    return {
        "ref": "refs/heads/feature-branch",
        "commits": [
            {
                "id": "abc123",
                "message": "Add new feature",
                "timestamp": "2024-01-01T12:00:00Z"
            },
            {
                "id": "def456",
                "message": "Fix bug",
                "timestamp": "2024-01-01T12:30:00Z"
            }
        ],
        "head_commit": {
            "id": "def456",
            "message": "Fix bug",
            "timestamp": "2024-01-01T12:30:00Z"
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
            "login": "test-sender"
        },
        "installation": {
            "id": 12345
        }
    }


@pytest.fixture
def mock_push_payload_no_commits():
    """Mock push payload with no commits."""
    return {
        "ref": "refs/heads/feature-branch",
        "commits": [],
        "head_commit": None,
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
            "login": "test-sender"
        },
        "installation": {
            "id": 12345
        }
    }


@pytest.fixture
def mock_commit_diff():
    """Mock commit diff data."""
    return {
        "message": "Add new feature",
        "author": {"name": "Test Author", "email": "test@example.com"},
        "files": [
            {
                "filename": "src/main.py",
                "status": "modified",
                "patch": "@@ -1,3 +1,4 @@\n def main():\n+    print('hello')\n     pass"
            },
            {
                "filename": "tests/test_main.py",
                "status": "added",
                "patch": "@@ -0,0 +1,5 @@\n+def test_main():\n+    assert True"
            }
        ]
    }


class TestHandlePushEvent:
    """Test cases for handle_push_event function."""

    @patch('services.webhook.push_handler.get_repository_settings')
    def test_handle_push_event_trigger_disabled(self, mock_get_repo_settings, mock_push_payload):
        """Test that function returns early when trigger_on_commit is disabled."""
        # Arrange
        mock_get_repo_settings.return_value = {"trigger_on_commit": False}
        
        # Act
        handle_push_event(mock_push_payload)
        
        # Assert
        mock_get_repo_settings.assert_called_once_with(repo_id=789)

    @patch('services.webhook.push_handler.get_repository_settings')
    def test_handle_push_event_no_repo_settings(self, mock_get_repo_settings, mock_push_payload):
        """Test that function returns early when no repository settings found."""
        # Arrange
        mock_get_repo_settings.return_value = None
        
        # Act
        handle_push_event(mock_push_payload)
        
        # Assert
        mock_get_repo_settings.assert_called_once_with(repo_id=789)

    @patch('services.webhook.push_handler.get_repository_settings')
    def test_handle_push_event_no_commits(self, mock_get_repo_settings, mock_push_payload_no_commits):
        """Test that function returns early when no commits are found."""
        # Arrange
        mock_get_repo_settings.return_value = {"trigger_on_commit": True}
        
        # Act
        handle_push_event(mock_push_payload_no_commits)
        
        # Assert
        mock_get_repo_settings.assert_called_once()

    @patch('services.webhook.push_handler.get_repository_settings')
    @patch('services.webhook.push_handler.get_installation_access_token')
    @patch('services.webhook.push_handler.get_commit_diff')
    @patch('services.webhook.push_handler.get_coverages')
    @patch('services.webhook.push_handler.is_code_file')
    @patch('services.webhook.push_handler.is_test_file')
    @patch('services.webhook.push_handler.is_excluded_from_testing')
    def test_handle_push_event_no_code_files(
        self,
        mock_is_excluded,
        mock_is_test_file,
        mock_is_code_file,
        mock_get_coverages,
        mock_get_commit_diff,
        mock_get_installation_token,
        mock_get_repo_settings,
        mock_push_payload,
        mock_commit_diff
    ):
        """Test that function returns early when no code files are found."""
        # Arrange
        mock_get_repo_settings.return_value = {"trigger_on_commit": True}
        mock_get_installation_token.return_value = "test_token"
        mock_get_commit_diff.return_value = mock_commit_diff
        mock_get_coverages.return_value = {}
        mock_is_code_file.return_value = False  # No code files
        mock_is_test_file.return_value = False
        mock_is_excluded.return_value = False
        
        # Act
        handle_push_event(mock_push_payload)
        
        # Assert
        mock_get_commit_diff.assert_called()
        mock_is_code_file.assert_called()

    @patch('services.webhook.push_handler.get_repository_settings')
    @patch('services.webhook.push_handler.get_installation_access_token')
    @patch('services.webhook.push_handler.get_commit_diff')
    @patch('services.webhook.push_handler.get_coverages')
    @patch('services.webhook.push_handler.is_code_file')
    @patch('services.webhook.push_handler.is_test_file')
    @patch('services.webhook.push_handler.is_excluded_from_testing')
    @patch('services.webhook.push_handler.find_pull_request_by_branch')
    @patch('services.webhook.push_handler.get_stripe_customer_id')
    @patch('services.webhook.push_handler.get_stripe_product_id')
    @patch('services.webhook.push_handler.create_comment')
    @patch('services.webhook.push_handler.get_remote_file_tree')
    @patch('services.webhook.push_handler.create_system_messages')
    @patch('services.webhook.push_handler.chat_with_agent')
    @patch('services.webhook.push_handler.update_comment')
    def test_handle_push_event_success_flow(
        self,
        mock_update_comment,
        mock_chat_with_agent,
        mock_create_system_messages,
        mock_get_remote_file_tree,
        mock_create_comment,
        mock_get_stripe_product_id,
        mock_get_stripe_customer_id,
        mock_find_pull_request,
        mock_is_excluded,
        mock_is_test_file,
        mock_is_code_file,
        mock_get_coverages,
        mock_get_commit_diff,
        mock_get_installation_token,
        mock_get_repo_settings,
        mock_push_payload,
        mock_commit_diff
    ):
        """Test successful push event handling flow."""
        # Arrange
        mock_get_repo_settings.return_value = {"trigger_on_commit": True}
        mock_get_installation_token.return_value = "test_token"
        mock_get_commit_diff.return_value = mock_commit_diff
        mock_get_coverages.return_value = {}
        mock_is_code_file.side_effect = lambda f: f.endswith('.py') and not f.startswith('tests/')
        mock_is_test_file.side_effect = lambda f: f.startswith('tests/')
        mock_is_excluded.return_value = False
        mock_find_pull_request.return_value = {"number": 42}
        mock_get_stripe_customer_id.return_value = "cus_123"
        mock_get_stripe_product_id.return_value = "prod_standard"
        mock_create_comment.return_value = "https://api.github.com/repos/owner/repo/issues/comments/123"
        mock_get_remote_file_tree.return_value = (["file1.py", "file2.py"], "Found 2 files")
        mock_create_system_messages.return_value = [{"role": "system", "content": "system message"}]
        
        # Mock chat_with_agent to simulate exploration and commit phases
        mock_chat_with_agent.side_effect = [
            # First call (exploration)
            ([], [], "get_remote_file_content", {"file_path": "src/main.py"}, 100, 50, True, 10),
            # Second call (commit)
            ([], [], "apply_diff_to_file", {"file_path": "tests/test_main.py"}, 100, 50, True, 15),
            # Third call (exploration - no more files)
            ([], [], None, None, 100, 50, False, 20),
            # Fourth call (commit - no more changes)
            ([], [], None, None, 100, 50, False, 25)
        ]
        
        # Act
        handle_push_event(mock_push_payload)
        
        # Assert
        mock_get_repo_settings.assert_called_once_with(repo_id=789)
        mock_get_installation_token.assert_called_once_with(installation_id=12345)
        mock_get_commit_diff.assert_called()
        mock_find_pull_request.assert_called_once()
        mock_get_stripe_customer_id.assert_called_once_with(owner_id=456)
        mock_get_stripe_product_id.assert_called_once_with(customer_id="cus_123")
        mock_create_comment.assert_called_once()
        mock_get_remote_file_tree.assert_called_once()
        mock_chat_with_agent.assert_called()
        mock_update_comment.assert_called()
        
        # Check final message
        final_call = mock_update_comment.call_args_list[-1]
        assert "Finished analyzing commits" in final_call[0][0]

    @patch('services.webhook.push_handler.get_repository_settings')
    @patch('services.webhook.push_handler.get_installation_access_token')
    @patch('services.webhook.push_handler.get_commit_diff')
    @patch('services.webhook.push_handler.get_coverages')
    @patch('services.webhook.push_handler.is_code_file')
    @patch('services.webhook.push_handler.is_test_file')
    @patch('services.webhook.push_handler.is_excluded_from_testing')
    @patch('services.webhook.push_handler.find_pull_request_by_branch')
    @patch('services.webhook.push_handler.get_stripe_customer_id')
    def test_handle_push_event_no_stripe_customer(
        self,
        mock_get_stripe_customer_id,
        mock_find_pull_request,
        mock_is_excluded,
        mock_is_test_file,
        mock_is_code_file,
        mock_get_coverages,
        mock_get_commit_diff,
        mock_get_installation_token,
        mock_get_repo_settings,
        mock_push_payload,
        mock_commit_diff
    ):
        """Test that function returns early when no Stripe customer ID is found."""
        # Arrange
        mock_get_repo_settings.return_value = {"trigger_on_commit": True}
        mock_get_installation_token.return_value = "test_token"
        mock_get_commit_diff.return_value = mock_commit_diff
        mock_get_coverages.return_value = {}
        mock_is_code_file.side_effect = lambda f: f.endswith('.py') and not f.startswith('tests/')
        mock_is_test_file.side_effect = lambda f: f.startswith('tests/')
        mock_is_excluded.return_value = False
        mock_find_pull_request.return_value = {"number": 42}
        mock_get_stripe_customer_id.return_value = None
        
        # Act
        handle_push_event(mock_push_payload)
        
        # Assert
        mock_get_stripe_customer_id.assert_called_once_with(owner_id=456)

    @patch('services.webhook.push_handler.get_repository_settings')
    @patch('services.webhook.push_handler.get_installation_access_token')
    @patch('services.webhook.push_handler.get_commit_diff')
    @patch('services.webhook.push_handler.get_coverages')
    @patch('services.webhook.push_handler.is_code_file')
    @patch('services.webhook.push_handler.is_test_file')
    @patch('services.webhook.push_handler.is_excluded_from_testing')
    @patch('services.webhook.push_handler.find_pull_request_by_branch')
    @patch('services.webhook.push_handler.get_stripe_customer_id')
    @patch('services.webhook.push_handler.get_stripe_product_id')
    @patch('services.webhook.push_handler.colorize')
    def test_handle_push_event_free_tier_user(
        self,
        mock_colorize,
        mock_get_stripe_product_id,
        mock_get_stripe_customer_id,
        mock_find_pull_request,
        mock_is_excluded,
        mock_is_test_file,
        mock_is_code_file,
        mock_get_coverages,
        mock_get_commit_diff,
        mock_get_installation_token,
        mock_get_repo_settings,
        mock_push_payload,
        mock_commit_diff
    ):
        """Test that function returns early for free tier users."""
        # Arrange
        mock_get_repo_settings.return_value = {"trigger_on_commit": True}
        mock_get_installation_token.return_value = "test_token"
        mock_get_commit_diff.return_value = mock_commit_diff
        mock_get_coverages.return_value = {}
        mock_is_code_file.side_effect = lambda f: f.endswith('.py') and not f.startswith('tests/')
        mock_is_test_file.side_effect = lambda f: f.startswith('tests/')
        mock_is_excluded.return_value = False
        mock_find_pull_request.return_value = {"number": 42}
        mock_get_stripe_customer_id.return_value = "cus_123"
        mock_get_stripe_product_id.return_value = STRIPE_PRODUCT_ID_FREE
        
        # Act
        handle_push_event(mock_push_payload)
        
        # Assert
        mock_colorize.assert_called_once()
        assert "free tier" in mock_colorize.call_args[1]['text']

    @patch('services.webhook.push_handler.get_repository_settings')
    @patch('services.webhook.push_handler.get_installation_access_token')
    @patch('services.webhook.push_handler.get_commit_diff')
    @patch('services.webhook.push_handler.get_coverages')
    @patch('services.webhook.push_handler.is_code_file')
    @patch('services.webhook.push_handler.is_test_file')
    @patch('services.webhook.push_handler.is_excluded_from_testing')
    @patch('services.webhook.push_handler.find_pull_request_by_branch')
    @patch('services.webhook.push_handler.get_stripe_customer_id')
    @patch('services.webhook.push_handler.get_stripe_product_id')
    @patch('services.webhook.push_handler.get_remote_file_tree')
    @patch('services.webhook.push_handler.create_system_messages')
    @patch('services.webhook.push_handler.chat_with_agent')
    def test_handle_push_event_no_pull_request(
        self,
        mock_chat_with_agent,
        mock_create_system_messages,
        mock_get_remote_file_tree,
        mock_get_stripe_product_id,
        mock_get_stripe_customer_id,
        mock_find_pull_request,
        mock_is_excluded,
        mock_is_test_file,
        mock_is_code_file,
        mock_get_coverages,
        mock_get_commit_diff,
        mock_get_installation_token,
        mock_get_repo_settings,
        mock_push_payload,
        mock_commit_diff
    ):
        """Test handling when no pull request is found for the branch."""
        # Arrange
        mock_get_repo_settings.return_value = {"trigger_on_commit": True}
        mock_get_installation_token.return_value = "test_token"
        mock_get_commit_diff.return_value = mock_commit_diff
        mock_get_coverages.return_value = {}
        mock_is_code_file.side_effect = lambda f: f.endswith('.py') and not f.startswith('tests/')
        mock_is_test_file.side_effect = lambda f: f.startswith('tests/')
        mock_is_excluded.return_value = False
        mock_find_pull_request.return_value = None  # No PR found
        mock_get_stripe_customer_id.return_value = "cus_123"
        mock_get_stripe_product_id.return_value = "prod_standard"
        mock_get_remote_file_tree.return_value = (["file1.py"], "Found 1 file")
        mock_create_system_messages.return_value = [{"role": "system", "content": "system message"}]
        
        mock_chat_with_agent.side_effect = [
            ([], [], None, None, 100, 50, False, 10),
            ([], [], None, None, 100, 50, False, 15)
        ]
        
        # Act
        handle_push_event(mock_push_payload)
        
        # Assert
        # Should still proceed but without creating comments (no PR)
        mock_chat_with_agent.assert_called()
        # Final message should be printed instead of updating comment
        assert mock_chat_with_agent.call_count == 2

    def test_handle_push_event_exception_owner_bypass(self, mock_push_payload):
        """Test that exception owners bypass payment checks."""
        # Modify payload to use exception owner
        mock_push_payload["repository"]["owner"]["login"] = EXCEPTION_OWNERS[0]
        
        with patch('services.webhook.push_handler.get_repository_settings') as mock_get_repo_settings, \
             patch('services.webhook.push_handler.get_installation_access_token') as mock_get_token, \
             patch('services.webhook.push_handler.get_commit_diff') as mock_get_commit_diff, \
             patch('services.webhook.push_handler.get_coverages') as mock_get_coverages, \
             patch('services.webhook.push_handler.is_code_file') as mock_is_code_file, \
             patch('services.webhook.push_handler.is_test_file') as mock_is_test_file, \
             patch('services.webhook.push_handler.is_excluded_from_testing') as mock_is_excluded, \
             patch('services.webhook.push_handler.find_pull_request_by_branch') as mock_find_pr, \
             patch('services.webhook.push_handler.get_stripe_customer_id') as mock_get_customer_id, \
             patch('services.webhook.push_handler.get_stripe_product_id') as mock_get_product_id, \
             patch('services.webhook.push_handler.get_remote_file_tree') as mock_get_file_tree:
            
            # Arrange
            mock_get_repo_settings.return_value = {"trigger_on_commit": True}
            mock_get_token.return_value = "test_token"
            mock_get_commit_diff.return_value = {
                "message": "Test commit",
                "author": {"name": "Test", "email": "test@example.com"},
                "files": [{"filename": "src/main.py", "patch": "diff"}]
            }
            mock_get_coverages.return_value = {}
            mock_is_code_file.return_value = True
            mock_is_test_file.return_value = False
            mock_is_excluded.return_value = False
            mock_find_pr.return_value = {"number": 42}
            mock_get_customer_id.return_value = "cus_123"
            mock_get_product_id.return_value = STRIPE_PRODUCT_ID_FREE  # Free tier
            mock_get_file_tree.return_value = (["file1.py"], "Found 1 file")
            
            # Act
            handle_push_event(mock_push_payload)
            
            # Assert - should proceed despite free tier because owner is in exceptions
            mock_get_file_tree.assert_called_once()  # Should reach this point
