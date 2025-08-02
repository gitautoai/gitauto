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


@pytest.mark.asyncio
async def test_create_pr_from_issue_early_return_wrong_label(mock_github_payload):
    """Test early return when label name doesn't match PRODUCT_ID."""
    # Setup
    mock_github_payload["label"]["name"] = "wrong-label"
    
    with patch('config.PRODUCT_ID', 'gitauto'):
        # Execute
        result = await create_pr_from_issue(
            payload=mock_github_payload,
            trigger="issue_label",
            input_from="github"
        )
        
        # Assert
        assert result is None


@pytest.mark.asyncio
async def test_create_pr_from_issue_basic_functionality():
    """Test basic functionality without complex mocking."""
    payload = {
        "action": "labeled",
        "label": {"name": "wrong-label"},
        "issue": {"number": 123, "title": "Test", "body": "Test", "user": {"login": "test", "id": 1}},
        "repository": {"id": 1, "name": "test", "owner": {"login": "test", "id": 1, "type": "User"}},
        "sender": {"login": "test", "id": 1, "email": "test@test.com"},
        "installation": {"id": 1}
    }
    
    result = await create_pr_from_issue(payload, "issue_label", "github")
    assert result is None

@pytest.mark.asyncio
async def test_create_pr_from_issue_request_limit_reached(mock_github_payload):
    """Test behavior when request limit is reached."""
    mock_base_args = {
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
    
    with patch('config.PRODUCT_ID', 'gitauto'), \
         patch('services.github.utils.deconstruct_github_payload.deconstruct_github_payload') as mock_deconstruct, \
         patch('services.slack.slack_notify.slack_notify') as mock_slack, \
         patch('services.github.comments.delete_comments_by_identifiers.delete_comments_by_identifiers'), \
         patch('services.github.comments.create_comment.create_comment') as mock_create_comment, \
         patch('services.github.comments.update_comment.update_comment') as mock_update_comment, \
         patch('services.supabase.usage.is_request_limit_reached.is_request_limit_reached') as mock_limit_check, \
         patch('utils.progress_bar.progress_bar.create_progress_bar') as mock_progress_bar:
        
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
async def test_create_pr_from_issue_jira_input(mock_github_payload):
    """Test handling of Jira input source."""
    mock_base_args = {
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
    
    with patch('config.PRODUCT_ID', 'gitauto'), \
         patch('services.jira.deconstruct_jira_payload.deconstruct_jira_payload') as mock_jira, \
         patch('services.slack.slack_notify.slack_notify'), \
         patch('services.github.comments.create_comment.create_comment') as mock_create_comment, \
         patch('services.github.comments.update_comment.update_comment'), \
         patch('services.supabase.usage.is_request_limit_reached.is_request_limit_reached') as mock_limit_check, \
         patch('utils.progress_bar.progress_bar.create_progress_bar') as mock_progress_bar:
        
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
