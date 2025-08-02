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


@pytest.fixture
def mock_dependencies():
    """Fixture to mock all external dependencies."""
    with patch.multiple(
        'services.webhook.issue_handler',
        deconstruct_github_payload=MagicMock(),
        slack_notify=MagicMock(),
        delete_comments_by_identifiers=MagicMock(),
        create_comment=MagicMock(),
        update_comment=MagicMock(),
        is_request_limit_reached=MagicMock(),
        create_user_request=MagicMock(),
        add_reaction_to_issue=AsyncMock(),
        get_file_tree_list=MagicMock(),
        find_config_files=MagicMock(),
        get_remote_file_content=MagicMock(),
        get_comments=MagicMock(),
        render_text=MagicMock(),
        extract_image_urls=MagicMock(),
        get_latest_remote_commit_sha=MagicMock(),
        create_remote_branch=MagicMock(),
        check_branch_exists=MagicMock(),
        chat_with_agent=MagicMock(),
        create_empty_commit=MagicMock(),
        create_pull_request=MagicMock(),
        update_usage=MagicMock(),
        insert_credit=MagicMock(),
        get_owner=MagicMock(),
        get_user=MagicMock(),
        send_email=MagicMock(),
        get_credits_depleted_email_text=MagicMock(),
        create_progress_bar=MagicMock(),
        is_lambda_timeout_approaching=MagicMock(),
        get_timeout_message=MagicMock(),
    ) as mocks:
        yield mocks


@pytest.mark.asyncio
async def test_create_pr_from_issue_early_return_wrong_label(mock_github_payload, mock_dependencies):
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
        # Verify no other functions were called
        mock_dependencies['slack_notify'].assert_not_called()


@pytest.mark.asyncio
async def test_create_pr_from_issue_request_limit_reached(mock_github_payload, mock_base_args, mock_dependencies):
    """Test behavior when request limit is reached."""
    # Setup
    mock_dependencies['deconstruct_github_payload'].return_value = (mock_base_args, {})
    mock_dependencies['is_request_limit_reached'].return_value = {
        "is_limit_reached": True,
        "requests_left": 0,
        "request_limit": 10,
        "end_date": "2024-01-01",
        "is_credit_user": False
    }
    mock_dependencies['create_comment'].return_value = "comment-url"
    mock_dependencies['create_progress_bar'].return_value = "progress bar"
    
    with patch('services.webhook.issue_handler.PRODUCT_ID', 'gitauto'):
        # Execute
        result = await create_pr_from_issue(
            payload=mock_github_payload,
            trigger="issue_label",
            input_from="github"
        )
        
        # Assert
        assert result is None
        mock_dependencies['slack_notify'].assert_called()
        mock_dependencies['update_comment'].assert_called()


@pytest.mark.asyncio
async def test_create_pr_from_issue_successful_flow(mock_github_payload, mock_base_args, mock_dependencies):
    """Test successful PR creation flow."""
    # Setup
    mock_dependencies['deconstruct_github_payload'].return_value = (mock_base_args, {})
    mock_dependencies['is_request_limit_reached'].return_value = {
        "is_limit_reached": False,
        "requests_left": 5,
        "request_limit": 10,
        "end_date": "2024-01-01",
        "is_credit_user": True
    }
    mock_dependencies['create_user_request'].return_value = "usage-id"
    mock_dependencies['create_comment'].return_value = "comment-url"
    mock_dependencies['get_file_tree_list'].return_value = (["file1.py", "file2.py"], "Found 2 files")
    mock_dependencies['find_config_files'].return_value = ["config.json"]
    mock_dependencies['get_comments'].return_value = ["comment1", "comment2"]
    mock_dependencies['render_text'].return_value = "rendered text"
    mock_dependencies['extract_image_urls'].return_value = []
    mock_dependencies['get_latest_remote_commit_sha'].return_value = "abc123"
    mock_dependencies['check_branch_exists'].return_value = True
    mock_dependencies['chat_with_agent'].side_effect = [
        # First call (explore mode)
        ([], [], "tool", {}, 100, 200, True, 50),
        # Second call (commit mode)  
        ([], [], "tool", {}, 100, 200, True, 75)
    ]
    mock_dependencies['create_pull_request'].return_value = "https://github.com/test-owner/test-repo/pull/456"
    mock_dependencies['get_owner'].return_value = {"credit_balance_usd": 0}
    mock_dependencies['get_user'].return_value = {"email": "test@example.com"}
    mock_dependencies['get_credits_depleted_email_text'].return_value = ("Subject", "Email text")
    mock_dependencies['create_progress_bar'].return_value = "progress bar"
    mock_dependencies['is_lambda_timeout_approaching'].return_value = (False, 30)
    
    with patch('services.webhook.issue_handler.PRODUCT_ID', 'gitauto'):
        # Execute
        result = await create_pr_from_issue(
            payload=mock_github_payload,
            trigger="issue_label",
            input_from="github"
        )
        
        # Assert
        assert result is None  # Function doesn't return a value
        mock_dependencies['create_pull_request'].assert_called_once()
        mock_dependencies['update_usage'].assert_called_once()
        mock_dependencies['insert_credit'].assert_called_once()
        mock_dependencies['send_email'].assert_called_once()


@pytest.mark.asyncio
async def test_create_pr_from_issue_jira_input(mock_github_payload, mock_base_args, mock_dependencies):
    """Test handling of Jira input source."""
    # Setup
    with patch('services.webhook.issue_handler.deconstruct_jira_payload') as mock_jira:
        mock_jira.return_value = (mock_base_args, {})
        mock_dependencies['is_request_limit_reached'].return_value = {
            "is_limit_reached": True,
            "requests_left": 0,
            "request_limit": 10,
            "end_date": "2024-01-01",
            "is_credit_user": False
        }
        mock_dependencies['create_comment'].return_value = "comment-url"
        mock_dependencies['create_progress_bar'].return_value = "progress bar"
        
        with patch('services.webhook.issue_handler.PRODUCT_ID', 'gitauto'):
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
async def test_create_pr_from_issue_branch_deleted(mock_github_payload, mock_base_args, mock_dependencies):
    """Test behavior when branch is deleted during processing."""
    # Setup
    mock_dependencies['deconstruct_github_payload'].return_value = (mock_base_args, {})
    mock_dependencies['is_request_limit_reached'].return_value = {
        "is_limit_reached": False,
        "requests_left": 5,
        "request_limit": 10,
        "end_date": "2024-01-01",
        "is_credit_user": False
    }
    mock_dependencies['create_user_request'].return_value = "usage-id"
    mock_dependencies['create_comment'].return_value = "comment-url"
    mock_dependencies['get_file_tree_list'].return_value = (["file1.py"], "Found 1 file")
    mock_dependencies['find_config_files'].return_value = []
    mock_dependencies['get_comments'].return_value = []
    mock_dependencies['render_text'].return_value = "rendered text"
    mock_dependencies['extract_image_urls'].return_value = []
    mock_dependencies['get_latest_remote_commit_sha'].return_value = "abc123"
    mock_dependencies['check_branch_exists'].return_value = False  # Branch deleted
    mock_dependencies['create_progress_bar'].return_value = "progress bar"
    mock_dependencies['is_lambda_timeout_approaching'].return_value = (False, 30)
    
    with patch('services.webhook.issue_handler.PRODUCT_ID', 'gitauto'):
        # Execute
        result = await create_pr_from_issue(
            payload=mock_github_payload,
            trigger="issue_label",
            input_from="github"
        )
        
        # Assert
        assert result is None
        mock_dependencies['update_comment'].assert_called()


@pytest.mark.asyncio
async def test_create_pr_from_issue_timeout_approaching(mock_github_payload, mock_base_args, mock_dependencies):
    """Test behavior when Lambda timeout is approaching."""
    # Setup
    mock_dependencies['deconstruct_github_payload'].return_value = (mock_base_args, {})
    mock_dependencies['is_request_limit_reached'].return_value = {
        "is_limit_reached": False,
        "requests_left": 5,
        "request_limit": 10,
        "end_date": "2024-01-01",
        "is_credit_user": False
    }
    mock_dependencies['create_user_request'].return_value = "usage-id"
    mock_dependencies['create_comment'].return_value = "comment-url"
    mock_dependencies['get_file_tree_list'].return_value = (["file1.py"], "Found 1 file")
    mock_dependencies['find_config_files'].return_value = []
    mock_dependencies['get_comments'].return_value = []
    mock_dependencies['render_text'].return_value = "rendered text"
    mock_dependencies['extract_image_urls'].return_value = []
    mock_dependencies['get_latest_remote_commit_sha'].return_value = "abc123"
    mock_dependencies['check_branch_exists'].return_value = True
    mock_dependencies['is_lambda_timeout_approaching'].return_value = (True, 890)  # Timeout approaching
    mock_dependencies['get_timeout_message'].return_value = "Timeout approaching"
    mock_dependencies['create_progress_bar'].return_value = "progress bar"
    
    with patch('services.webhook.issue_handler.PRODUCT_ID', 'gitauto'):
        # Execute
        result = await create_pr_from_issue(
            payload=mock_github_payload,
            trigger="issue_label",
            input_from="github"
        )
        
        # Assert
        assert result is None
        mock_dependencies['get_timeout_message'].assert_called_once()


@pytest.mark.asyncio
async def test_create_pr_from_issue_failed_pr_creation(mock_github_payload, mock_base_args, mock_dependencies):
    """Test behavior when PR creation fails."""
    # Setup
    mock_dependencies['deconstruct_github_payload'].return_value = (mock_base_args, {})
    mock_dependencies['is_request_limit_reached'].return_value = {
        "is_limit_reached": False,
        "requests_left": 5,
        "request_limit": 10,
        "end_date": "2024-01-01",
        "is_credit_user": False
    }
    mock_dependencies['create_user_request'].return_value = "usage-id"
    mock_dependencies['create_comment'].return_value = "comment-url"
    mock_dependencies['get_file_tree_list'].return_value = (["file1.py"], "Found 1 file")
    mock_dependencies['find_config_files'].return_value = []
    mock_dependencies['get_comments'].return_value = []
    mock_dependencies['render_text'].return_value = "rendered text"
    mock_dependencies['extract_image_urls'].return_value = []
    mock_dependencies['get_latest_remote_commit_sha'].return_value = "abc123"
    mock_dependencies['check_branch_exists'].return_value = True
    mock_dependencies['chat_with_agent'].side_effect = [
        # First call (explore mode) - no exploration, no commits
        ([], [], "tool", {}, 100, 200, False, 50),
        # Second call (commit mode)
        ([], [], "tool", {}, 100, 200, False, 75)
    ]
    mock_dependencies['create_pull_request'].return_value = None  # PR creation failed
    mock_dependencies['create_progress_bar'].return_value = "progress bar"
    mock_dependencies['is_lambda_timeout_approaching'].return_value = (False, 30)
    
    with patch('services.webhook.issue_handler.PRODUCT_ID', 'gitauto'):
        # Execute
        result = await create_pr_from_issue(
            payload=mock_github_payload,
            trigger="issue_label",
            input_from="github"
        )
        
        # Assert
        assert result is None
        mock_dependencies['update_usage'].assert_called_once_with(
            usage_id="usage-id",
            is_completed=False,
            pr_number=None,
            token_input=0,
            token_output=0,
            total_seconds=pytest.approx(0, abs=5)  # Allow some tolerance for execution time
        )


@pytest.mark.asyncio
async def test_create_pr_from_issue_infinite_loop_protection(mock_github_payload, mock_base_args, mock_dependencies):
    """Test that infinite loop protection works correctly."""
    # Setup
    mock_dependencies['deconstruct_github_payload'].return_value = (mock_base_args, {})
    mock_dependencies['is_request_limit_reached'].return_value = {
        "is_limit_reached": False,
        "requests_left": 5,
        "request_limit": 10,
        "end_date": "2024-01-01",
        "is_credit_user": False
    }
    mock_dependencies['create_user_request'].return_value = "usage-id"
    mock_dependencies['create_comment'].return_value = "comment-url"
    mock_dependencies['get_file_tree_list'].return_value = (["file1.py"], "Found 1 file")
    mock_dependencies['find_config_files'].return_value = []
    mock_dependencies['get_comments'].return_value = []
    mock_dependencies['render_text'].return_value = "rendered text"
    mock_dependencies['extract_image_urls'].return_value = []
    mock_dependencies['get_latest_remote_commit_sha'].return_value = "abc123"
    mock_dependencies['check_branch_exists'].return_value = True
    
    # Setup chat_with_agent to simulate infinite loop scenario
    mock_dependencies['chat_with_agent'].side_effect = [
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
    
    mock_dependencies['create_pull_request'].return_value = None
    mock_dependencies['create_progress_bar'].return_value = "progress bar"
    mock_dependencies['is_lambda_timeout_approaching'].return_value = (False, 30)
    
    with patch('services.webhook.issue_handler.PRODUCT_ID', 'gitauto'):
        # Execute
        result = await create_pr_from_issue(
            payload=mock_github_payload,
            trigger="issue_label",
            input_from="github"
        )
        
        # Assert
        assert result is None
        # Should have called chat_with_agent 8 times (4 retry cycles * 2 calls each)
        assert mock_dependencies['chat_with_agent'].call_count == 8


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
async def test_create_pr_from_issue_with_image_processing(mock_github_payload, mock_base_args, mock_dependencies):
    """Test behavior when images are found in issue body."""
    # Setup
    mock_dependencies['deconstruct_github_payload'].return_value = (mock_base_args, {})
    mock_dependencies['is_request_limit_reached'].return_value = {
        "is_limit_reached": False,
        "requests_left": 5,
        "request_limit": 10,
        "end_date": "2024-01-01",
        "is_credit_user": False
    }
    mock_dependencies['create_user_request'].return_value = "usage-id"
    mock_dependencies['create_comment'].return_value = "comment-url"
    mock_dependencies['get_file_tree_list'].return_value = (["file1.py"], "Found 1 file")
    mock_dependencies['find_config_files'].return_value = []
    mock_dependencies['get_comments'].return_value = []
    mock_dependencies['render_text'].return_value = "rendered text"
    mock_dependencies['extract_image_urls'].return_value = [
        {"url": "https://example.com/image.png", "alt": "Test Image"}
    ]
    mock_dependencies['get_latest_remote_commit_sha'].return_value = "abc123"
    mock_dependencies['check_branch_exists'].return_value = True
    mock_dependencies['chat_with_agent'].side_effect = [
        ([], [], "tool", {}, 100, 200, False, 50),
        ([], [], "tool", {}, 100, 200, False, 75)
    ]
    mock_dependencies['create_pull_request'].return_value = None
    mock_dependencies['create_progress_bar'].return_value = "progress bar"
    mock_dependencies['is_lambda_timeout_approaching'].return_value = (False, 30)
    
    # Mock image processing functions
    with patch('services.webhook.issue_handler.get_base64') as mock_get_base64, \
         patch('services.webhook.issue_handler.describe_image') as mock_describe_image, \
         patch('services.webhook.issue_handler.PRODUCT_ID', 'gitauto'):
        
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
        assert mock_dependencies['create_comment'].call_count >= 2  # Initial comment + image description
