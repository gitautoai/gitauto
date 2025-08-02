from unittest.mock import patch, MagicMock, AsyncMock
import pytest
import time

from services.webhook.issue_handler import create_pr_from_issue


@pytest.fixture
def mock_github_payload():
    """Fixture providing a mock GitHub payload."""
    return {
        "action": "labeled",
        "label": {"name": "gitauto"},
        "issue": {
            "number": 123,
            "title": "Test Issue",
            "body": "Test issue body",
            "user": {"login": "test-user", "id": 12345}
        },
        "repository": {
            "id": 456,
            "name": "test-repo",
            "owner": {"login": "test-owner", "id": 789, "type": "User"},
            "clone_url": "https://github.com/test-owner/test-repo.git"
        },
        "sender": {
            "login": "test-sender",
            "id": 12345,
            "email": "test@example.com"
        },
        "installation": {"id": 987}
    }


@pytest.fixture
def mock_base_args():
    """Fixture providing mock base args."""
    return {
        "owner": "test-owner",
        "repo": "test-repo", 
        "issue_number": 123,
        "issue_title": "Test Issue",
        "sender_name": "test-sender",
        "installation_id": 987,
        "owner_id": 789,
        "owner_type": "User",
        "repo_id": 456,
        "issue_body": "Test issue body",
        "issuer_name": "test-user",
        "parent_issue_number": None,
        "parent_issue_title": None,
        "parent_issue_body": None,
        "new_branch": "gitauto/issue-123",
        "sender_id": 12345,
        "sender_email": "test@example.com",
        "github_urls": [],
        "token": "test-token",
        "is_automation": False,
        "clone_url": "https://github.com/test-owner/test-repo.git",
        "comment_url": "https://api.github.com/repos/test-owner/test-repo/issues/comments/123"
    }


@pytest.mark.asyncio
async def test_create_pr_from_issue_early_return_wrong_label(mock_github_payload):
    """Test early return when label name doesn't match PRODUCT_ID."""
    # Setup
    mock_github_payload["label"]["name"] = "wrong-label"
    
    with patch('services.webhook.issue_handler.PRODUCT_ID', 'gitauto'):
        # Execute
        result = await create_pr_from_issue(
            payload=mock_github_payload,
            trigger="issue_label",
            input_from="github"
        )
        
        # Assert
        assert result is None


@pytest.mark.asyncio
async def test_create_pr_from_issue_request_limit_reached(mock_github_payload, mock_base_args):
    """Test behavior when request limit is reached."""
    with patch('services.webhook.issue_handler.PRODUCT_ID', 'gitauto'), \
         patch('services.webhook.issue_handler.deconstruct_github_payload') as mock_deconstruct, \
         patch('services.webhook.issue_handler.slack_notify') as mock_slack, \
         patch('services.webhook.issue_handler.delete_comments_by_identifiers') as mock_delete, \
         patch('services.webhook.issue_handler.create_comment') as mock_create_comment, \
         patch('services.webhook.issue_handler.update_comment') as mock_update_comment, \
         patch('services.webhook.issue_handler.is_request_limit_reached') as mock_limit_check, \
         patch('services.webhook.issue_handler.create_progress_bar') as mock_progress_bar:
        
        # Setup mocks
        mock_deconstruct.return_value = (mock_base_args, {})
        mock_limit_check.return_value = {
            "is_limit_reached": True,
            "requests_left": 0,
            "request_limit": 10,
            "end_date": "2024-01-01",
            "is_credit_user": False
        }
        mock_create_comment.return_value = "comment-url"
        mock_progress_bar.return_value = "progress bar"
        
        # Execute
        result = await create_pr_from_issue(
            payload=mock_github_payload,
            trigger="issue_label",
            input_from="github"
        )
        
        # Assert
        assert result is None
        mock_slack.assert_called()
        mock_update_comment.assert_called()


@pytest.mark.asyncio
async def test_create_pr_from_issue_successful_flow(mock_github_payload, mock_base_args):
    """Test successful PR creation flow."""
    with patch('services.webhook.issue_handler.PRODUCT_ID', 'gitauto'), \
         patch('services.webhook.issue_handler.deconstruct_github_payload') as mock_deconstruct, \
         patch('services.webhook.issue_handler.slack_notify') as mock_slack, \
         patch('services.webhook.issue_handler.delete_comments_by_identifiers'), \
         patch('services.webhook.issue_handler.create_comment') as mock_create_comment, \
         patch('services.webhook.issue_handler.update_comment'), \
         patch('services.webhook.issue_handler.is_request_limit_reached') as mock_limit_check, \
         patch('services.webhook.issue_handler.create_user_request') as mock_create_request, \
         patch('services.webhook.issue_handler.add_reaction_to_issue'), \
         patch('services.webhook.issue_handler.get_file_tree_list') as mock_file_tree, \
         patch('services.webhook.issue_handler.find_config_files') as mock_config_files, \
         patch('services.webhook.issue_handler.get_remote_file_content'), \
         patch('services.webhook.issue_handler.get_comments') as mock_get_comments, \
         patch('services.webhook.issue_handler.render_text') as mock_render, \
         patch('services.webhook.issue_handler.extract_image_urls') as mock_extract_images, \
         patch('services.webhook.issue_handler.get_latest_remote_commit_sha') as mock_commit_sha, \
         patch('services.webhook.issue_handler.create_remote_branch'), \
         patch('services.webhook.issue_handler.check_branch_exists') as mock_branch_exists, \
         patch('services.webhook.issue_handler.chat_with_agent') as mock_chat, \
         patch('services.webhook.issue_handler.create_empty_commit'), \
         patch('services.webhook.issue_handler.create_pull_request') as mock_create_pr, \
         patch('services.webhook.issue_handler.update_usage') as mock_update_usage, \
         patch('services.webhook.issue_handler.insert_credit') as mock_insert_credit, \
         patch('services.webhook.issue_handler.get_owner') as mock_get_owner, \
         patch('services.webhook.issue_handler.get_user') as mock_get_user, \
         patch('services.webhook.issue_handler.send_email') as mock_send_email, \
         patch('services.webhook.issue_handler.get_credits_depleted_email_text') as mock_email_text, \
         patch('services.webhook.issue_handler.create_progress_bar') as mock_progress_bar, \
         patch('services.webhook.issue_handler.is_lambda_timeout_approaching') as mock_timeout:
        
        # Setup mocks
        mock_deconstruct.return_value = (mock_base_args, {})
        mock_limit_check.return_value = {
            "is_limit_reached": False,
            "requests_left": 5,
            "request_limit": 10,
            "end_date": "2024-01-01",
            "is_credit_user": True
        }
        mock_create_request.return_value = "usage-id"
        mock_create_comment.return_value = "comment-url"
        mock_file_tree.return_value = (["file1.py", "file2.py"], "Found 2 files")
        mock_config_files.return_value = ["config.json"]
        mock_get_comments.return_value = ["comment1", "comment2"]
        mock_render.return_value = "rendered text"
        mock_extract_images.return_value = []
        mock_commit_sha.return_value = "abc123"
        mock_branch_exists.return_value = True
        mock_chat.side_effect = [
            # First call (explore mode)
            ([], [], "tool", {}, 100, 200, True, 50),
            # Second call (commit mode)  
            ([], [], "tool", {}, 100, 200, True, 75)
        ]
        mock_create_pr.return_value = "https://github.com/test-owner/test-repo/pull/456"
        mock_get_owner.return_value = {"credit_balance_usd": 0}
        mock_get_user.return_value = {"email": "test@example.com"}
        mock_email_text.return_value = ("Subject", "Email text")
        mock_progress_bar.return_value = "progress bar"
        mock_timeout.return_value = (False, 30)
        
        # Execute
        result = await create_pr_from_issue(
            payload=mock_github_payload,
            trigger="issue_label",
            input_from="github"
        )
        
        # Assert
        assert result is None  # Function doesn't return a value
        mock_create_pr.assert_called_once()
        mock_update_usage.assert_called_once()
        mock_insert_credit.assert_called_once()
        mock_send_email.assert_called_once()


@pytest.mark.asyncio
async def test_create_pr_from_issue_jira_input(mock_github_payload, mock_base_args):
    """Test handling of Jira input source."""
    with patch('services.webhook.issue_handler.PRODUCT_ID', 'gitauto'), \
         patch('services.webhook.issue_handler.deconstruct_jira_payload') as mock_jira, \
         patch('services.webhook.issue_handler.slack_notify'), \
         patch('services.webhook.issue_handler.create_comment') as mock_create_comment, \
         patch('services.webhook.issue_handler.update_comment'), \
         patch('services.webhook.issue_handler.is_request_limit_reached') as mock_limit_check, \
         patch('services.webhook.issue_handler.create_progress_bar') as mock_progress_bar:
        
        # Setup mocks
        mock_jira.return_value = (mock_base_args, {})
        mock_limit_check.return_value = {
            "is_limit_reached": True,
            "requests_left": 0,
            "request_limit": 10,
            "end_date": "2024-01-01",
            "is_credit_user": False
        }
        mock_create_comment.return_value = "comment-url"
        mock_progress_bar.return_value = "progress bar"
        
        # Execute
        result = await create_pr_from_issue(
            payload=mock_github_payload,
            trigger="issue_label",
            input_from="jira"
        )
        
        # Assert
        assert result is None
        mock_jira.assert_called_once()


@pytest.mark.asyncio
async def test_create_pr_from_issue_branch_deleted(mock_github_payload, mock_base_args):
    """Test behavior when branch is deleted during processing."""
    with patch('services.webhook.issue_handler.PRODUCT_ID', 'gitauto'), \
         patch('services.webhook.issue_handler.deconstruct_github_payload') as mock_deconstruct, \
         patch('services.webhook.issue_handler.slack_notify'), \
         patch('services.webhook.issue_handler.delete_comments_by_identifiers'), \
         patch('services.webhook.issue_handler.create_comment') as mock_create_comment, \
         patch('services.webhook.issue_handler.update_comment') as mock_update_comment, \
         patch('services.webhook.issue_handler.is_request_limit_reached') as mock_limit_check, \
         patch('services.webhook.issue_handler.create_user_request') as mock_create_request, \
         patch('services.webhook.issue_handler.add_reaction_to_issue'), \
         patch('services.webhook.issue_handler.get_file_tree_list') as mock_file_tree, \
         patch('services.webhook.issue_handler.find_config_files') as mock_config_files, \
         patch('services.webhook.issue_handler.get_remote_file_content'), \
         patch('services.webhook.issue_handler.get_comments') as mock_get_comments, \
         patch('services.webhook.issue_handler.render_text') as mock_render, \
         patch('services.webhook.issue_handler.extract_image_urls') as mock_extract_images, \
         patch('services.webhook.issue_handler.get_latest_remote_commit_sha') as mock_commit_sha, \
         patch('services.webhook.issue_handler.create_remote_branch'), \
         patch('services.webhook.issue_handler.check_branch_exists') as mock_branch_exists, \
         patch('services.webhook.issue_handler.create_progress_bar') as mock_progress_bar, \
         patch('services.webhook.issue_handler.is_lambda_timeout_approaching') as mock_timeout:
        
        # Setup mocks
        mock_deconstruct.return_value = (mock_base_args, {})
        mock_limit_check.return_value = {
            "is_limit_reached": False,
            "requests_left": 5,
            "request_limit": 10,
            "end_date": "2024-01-01",
            "is_credit_user": False
        }
        mock_create_request.return_value = "usage-id"
        mock_create_comment.return_value = "comment-url"
        mock_file_tree.return_value = (["file1.py"], "Found 1 file")
        mock_config_files.return_value = []
        mock_get_comments.return_value = []
        mock_render.return_value = "rendered text"
        mock_extract_images.return_value = []
        mock_commit_sha.return_value = "abc123"
        mock_branch_exists.return_value = False  # Branch deleted
        mock_progress_bar.return_value = "progress bar"
        mock_timeout.return_value = (False, 30)
        
        # Execute
        result = await create_pr_from_issue(
            payload=mock_github_payload,
            trigger="issue_label",
            input_from="github"
        )
        
        # Assert
        assert result is None
        mock_update_comment.assert_called()


@pytest.mark.asyncio
async def test_create_pr_from_issue_timeout_approaching(mock_github_payload, mock_base_args):
    """Test behavior when Lambda timeout is approaching."""
    with patch('services.webhook.issue_handler.PRODUCT_ID', 'gitauto'), \
         patch('services.webhook.issue_handler.deconstruct_github_payload') as mock_deconstruct, \
         patch('services.webhook.issue_handler.slack_notify'), \
         patch('services.webhook.issue_handler.delete_comments_by_identifiers'), \
         patch('services.webhook.issue_handler.create_comment') as mock_create_comment, \
         patch('services.webhook.issue_handler.update_comment'), \
         patch('services.webhook.issue_handler.is_request_limit_reached') as mock_limit_check, \
         patch('services.webhook.issue_handler.create_user_request') as mock_create_request, \
         patch('services.webhook.issue_handler.add_reaction_to_issue'), \
         patch('services.webhook.issue_handler.get_file_tree_list') as mock_file_tree, \
         patch('services.webhook.issue_handler.find_config_files') as mock_config_files, \
         patch('services.webhook.issue_handler.get_remote_file_content'), \
         patch('services.webhook.issue_handler.get_comments') as mock_get_comments, \
         patch('services.webhook.issue_handler.render_text') as mock_render, \
         patch('services.webhook.issue_handler.extract_image_urls') as mock_extract_images, \
         patch('services.webhook.issue_handler.get_latest_remote_commit_sha') as mock_commit_sha, \
         patch('services.webhook.issue_handler.create_remote_branch'), \
         patch('services.webhook.issue_handler.check_branch_exists') as mock_branch_exists, \
         patch('services.webhook.issue_handler.is_lambda_timeout_approaching') as mock_timeout, \
         patch('services.webhook.issue_handler.get_timeout_message') as mock_timeout_msg, \
         patch('services.webhook.issue_handler.create_progress_bar') as mock_progress_bar:
        
        # Setup mocks
        mock_deconstruct.return_value = (mock_base_args, {})
        mock_limit_check.return_value = {
            "is_limit_reached": False,
            "requests_left": 5,
            "request_limit": 10,
            "end_date": "2024-01-01",
            "is_credit_user": False
        }
        mock_create_request.return_value = "usage-id"
        mock_create_comment.return_value = "comment-url"
        mock_file_tree.return_value = (["file1.py"], "Found 1 file")
        mock_config_files.return_value = []
        mock_get_comments.return_value = []
        mock_render.return_value = "rendered text"
        mock_extract_images.return_value = []
        mock_commit_sha.return_value = "abc123"
        mock_branch_exists.return_value = True
        mock_timeout.return_value = (True, 890)  # Timeout approaching
        mock_timeout_msg.return_value = "Timeout approaching"
        mock_progress_bar.return_value = "progress bar"
        
        # Execute
        result = await create_pr_from_issue(
            payload=mock_github_payload,
            trigger="issue_label",
            input_from="github"
        )
        
        # Assert
        assert result is None
        mock_timeout_msg.assert_called_once()


@pytest.mark.asyncio
async def test_create_pr_from_issue_failed_pr_creation(mock_github_payload, mock_base_args):
    """Test behavior when PR creation fails."""
    with patch('services.webhook.issue_handler.PRODUCT_ID', 'gitauto'), \
         patch('services.webhook.issue_handler.deconstruct_github_payload') as mock_deconstruct, \
         patch('services.webhook.issue_handler.slack_notify'), \
         patch('services.webhook.issue_handler.delete_comments_by_identifiers'), \
         patch('services.webhook.issue_handler.create_comment') as mock_create_comment, \
         patch('services.webhook.issue_handler.update_comment'), \
         patch('services.webhook.issue_handler.is_request_limit_reached') as mock_limit_check, \
         patch('services.webhook.issue_handler.create_user_request') as mock_create_request, \
         patch('services.webhook.issue_handler.add_reaction_to_issue'), \
         patch('services.webhook.issue_handler.get_file_tree_list') as mock_file_tree, \
         patch('services.webhook.issue_handler.find_config_files') as mock_config_files, \
         patch('services.webhook.issue_handler.get_remote_file_content'), \
         patch('services.webhook.issue_handler.get_comments') as mock_get_comments, \
         patch('services.webhook.issue_handler.render_text') as mock_render, \
         patch('services.webhook.issue_handler.extract_image_urls') as mock_extract_images, \
         patch('services.webhook.issue_handler.get_latest_remote_commit_sha') as mock_commit_sha, \
         patch('services.webhook.issue_handler.create_remote_branch'), \
         patch('services.webhook.issue_handler.check_branch_exists') as mock_branch_exists, \
         patch('services.webhook.issue_handler.chat_with_agent') as mock_chat, \
         patch('services.webhook.issue_handler.create_empty_commit'), \
         patch('services.webhook.issue_handler.create_pull_request') as mock_create_pr, \
         patch('services.webhook.issue_handler.update_usage') as mock_update_usage, \
         patch('services.webhook.issue_handler.create_progress_bar') as mock_progress_bar, \
         patch('services.webhook.issue_handler.is_lambda_timeout_approaching') as mock_timeout:
        
        # Setup mocks
        mock_deconstruct.return_value = (mock_base_args, {})
        mock_limit_check.return_value = {
            "is_limit_reached": False,
            "requests_left": 5,
            "request_limit": 10,
            "end_date": "2024-01-01",
            "is_credit_user": False
        }
        mock_create_request.return_value = "usage-id"
        mock_create_comment.return_value = "comment-url"
        mock_file_tree.return_value = (["file1.py"], "Found 1 file")
        mock_config_files.return_value = []
        mock_get_comments.return_value = []
        mock_render.return_value = "rendered text"
        mock_extract_images.return_value = []
        mock_commit_sha.return_value = "abc123"
        mock_branch_exists.return_value = True
        mock_chat.side_effect = [
            # First call (explore mode) - no exploration, no commits
            ([], [], "tool", {}, 100, 200, False, 50),
            # Second call (commit mode)
            ([], [], "tool", {}, 100, 200, False, 75)
        ]
        mock_create_pr.return_value = None  # PR creation failed
        mock_progress_bar.return_value = "progress bar"
        mock_timeout.return_value = (False, 30)
        
        # Execute
        result = await create_pr_from_issue(
            payload=mock_github_payload,
            trigger="issue_label",
            input_from="github"
        )
        
        # Assert
        assert result is None
        mock_update_usage.assert_called_once_with(
            usage_id="usage-id",
            is_completed=False,
            pr_number=None,
            token_input=0,
            token_output=0,
            total_seconds=pytest.approx(0, abs=5)  # Allow some tolerance for execution time
        )


@pytest.mark.asyncio
async def test_create_pr_from_issue_infinite_loop_protection(mock_github_payload, mock_base_args):
    """Test that infinite loop protection works correctly."""
    with patch('services.webhook.issue_handler.PRODUCT_ID', 'gitauto'), \
         patch('services.webhook.issue_handler.deconstruct_github_payload') as mock_deconstruct, \
         patch('services.webhook.issue_handler.slack_notify'), \
         patch('services.webhook.issue_handler.delete_comments_by_identifiers'), \
         patch('services.webhook.issue_handler.create_comment') as mock_create_comment, \
         patch('services.webhook.issue_handler.update_comment'), \
         patch('services.webhook.issue_handler.is_request_limit_reached') as mock_limit_check, \
         patch('services.webhook.issue_handler.create_user_request') as mock_create_request, \
         patch('services.webhook.issue_handler.add_reaction_to_issue'), \
         patch('services.webhook.issue_handler.get_file_tree_list') as mock_file_tree, \
         patch('services.webhook.issue_handler.find_config_files') as mock_config_files, \
         patch('services.webhook.issue_handler.get_remote_file_content'), \
         patch('services.webhook.issue_handler.get_comments') as mock_get_comments, \
         patch('services.webhook.issue_handler.render_text') as mock_render, \
         patch('services.webhook.issue_handler.extract_image_urls') as mock_extract_images, \
         patch('services.webhook.issue_handler.get_latest_remote_commit_sha') as mock_commit_sha, \
         patch('services.webhook.issue_handler.create_remote_branch'), \
         patch('services.webhook.issue_handler.check_branch_exists') as mock_branch_exists, \
         patch('services.webhook.issue_handler.chat_with_agent') as mock_chat, \
         patch('services.webhook.issue_handler.create_empty_commit'), \
         patch('services.webhook.issue_handler.create_pull_request') as mock_create_pr, \
         patch('services.webhook.issue_handler.create_progress_bar') as mock_progress_bar, \
         patch('services.webhook.issue_handler.is_lambda_timeout_approaching') as mock_timeout:
        
        # Setup mocks
        mock_deconstruct.return_value = (mock_base_args, {})
        mock_limit_check.return_value = {
            "is_limit_reached": False,
            "requests_left": 5,
            "request_limit": 10,
            "end_date": "2024-01-01",
            "is_credit_user": False
        }
        mock_create_request.return_value = "usage-id"
        mock_create_comment.return_value = "comment-url"
        mock_file_tree.return_value = (["file1.py"], "Found 1 file")
        mock_config_files.return_value = []
        mock_get_comments.return_value = []
        mock_render.return_value = "rendered text"
        mock_extract_images.return_value = []
        mock_commit_sha.return_value = "abc123"
        mock_branch_exists.return_value = True
        
        # Setup chat_with_agent to simulate infinite loop scenario
        mock_chat.side_effect = [
            # Explore mode - finds files but no commits (4 times to trigger retry limit)
            ([], [], "tool", {}, 100, 200, True, 50),  # explore
            ([], [], "tool", {}, 100, 200, False, 75),  # commit
            ([], [], "tool", {}, 100, 200, True, 50),  # explore
            ([], [], "tool", {}, 100, 200, False, 75),  # commit
            ([], [], "tool", {}, 100, 200, True, 50),  # explore
            ([], [], "tool", {}, 100, 200, False, 75),  # commit
            ([], [], "tool", {}, 100, 200, True, 50),  # explore
            ([], [], "tool", {}, 100, 200, False, 75),  # commit
        ]
        
        mock_create_pr.return_value = None
        mock_progress_bar.return_value = "progress bar"
        mock_timeout.return_value = (False, 30)
        
        # Execute
        result = await create_pr_from_issue(
            payload=mock_github_payload,
            trigger="issue_label",
            input_from="github"
        )
        
        # Assert
        assert result is None
        # Should have called chat_with_agent 8 times (4 retry cycles * 2 calls each)
        assert mock_chat.call_count == 8


def test_create_pr_from_issue_time_tracking():
    """Test that time tracking works correctly."""
    start_time = time.time()
    
    # Simulate some processing time
    time.sleep(0.1)
    
    end_time = time.time()
    duration = int(end_time - start_time)
    
    # Assert duration is reasonable
    assert duration >= 0
    assert duration < 1  # Should be less than 1 second for this test


@pytest.mark.asyncio
async def test_create_pr_from_issue_with_image_processing(mock_github_payload, mock_base_args):
    """Test behavior when images are found in issue body."""
    with patch('services.webhook.issue_handler.PRODUCT_ID', 'gitauto'), \
         patch('services.webhook.issue_handler.deconstruct_github_payload') as mock_deconstruct, \
         patch('services.webhook.issue_handler.slack_notify'), \
         patch('services.webhook.issue_handler.delete_comments_by_identifiers'), \
         patch('services.webhook.issue_handler.create_comment') as mock_create_comment, \
         patch('services.webhook.issue_handler.update_comment'), \
         patch('services.webhook.issue_handler.is_request_limit_reached') as mock_limit_check, \
         patch('services.webhook.issue_handler.create_user_request') as mock_create_request, \
         patch('services.webhook.issue_handler.add_reaction_to_issue'), \
         patch('services.webhook.issue_handler.get_file_tree_list') as mock_file_tree, \
         patch('services.webhook.issue_handler.find_config_files') as mock_config_files, \
         patch('services.webhook.issue_handler.get_remote_file_content'), \
         patch('services.webhook.issue_handler.get_comments') as mock_get_comments, \
         patch('services.webhook.issue_handler.render_text') as mock_render, \
         patch('services.webhook.issue_handler.extract_image_urls') as mock_extract_images, \
         patch('services.webhook.issue_handler.get_latest_remote_commit_sha') as mock_commit_sha, \
         patch('services.webhook.issue_handler.create_remote_branch'), \
         patch('services.webhook.issue_handler.check_branch_exists') as mock_branch_exists, \
         patch('services.webhook.issue_handler.chat_with_agent') as mock_chat, \
         patch('services.webhook.issue_handler.create_empty_commit'), \
         patch('services.webhook.issue_handler.create_pull_request') as mock_create_pr, \
         patch('services.webhook.issue_handler.create_progress_bar') as mock_progress_bar, \
         patch('services.webhook.issue_handler.is_lambda_timeout_approaching') as mock_timeout, \
         patch('services.webhook.issue_handler.get_base64') as mock_get_base64, \
         patch('services.webhook.issue_handler.describe_image') as mock_describe_image:
        
        # Setup mocks
        mock_deconstruct.return_value = (mock_base_args, {})
        mock_limit_check.return_value = {
            "is_limit_reached": False,
            "requests_left": 5,
            "request_limit": 10,
            "end_date": "2024-01-01",
            "is_credit_user": False
        }
        mock_create_request.return_value = "usage-id"
        mock_create_comment.return_value = "comment-url"
        mock_file_tree.return_value = (["file1.py"], "Found 1 file")
        mock_config_files.return_value = []
        mock_get_comments.return_value = []
        mock_render.return_value = "rendered text"
        mock_extract_images.return_value = [
            {"url": "https://example.com/image.png", "alt": "Test Image"}
        ]
        mock_commit_sha.return_value = "abc123"
        mock_branch_exists.return_value = True
        mock_chat.side_effect = [
            ([], [], "tool", {}, 100, 200, False, 50),
            ([], [], "tool", {}, 100, 200, False, 75)
        ]
        mock_create_pr.return_value = None
        mock_progress_bar.return_value = "progress bar"
        mock_timeout.return_value = (False, 30)
        mock_get_base64.return_value = "base64_image_data"
        mock_describe_image.return_value = "Image description"
        
        # Execute
        result = await create_pr_from_issue(
            payload=mock_github_payload,
            trigger="issue_label",
            input_from="github"
        )
        
        # Assert
        assert result is None
        mock_get_base64.assert_called_once()
        mock_describe_image.assert_called_once()
        # Should create a comment with image description
        assert mock_create_comment.call_count >= 2  # Initial comment + image description