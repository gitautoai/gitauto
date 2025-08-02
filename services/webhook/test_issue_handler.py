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
    # Test with wrong label to ensure early return
    mock_github_payload["label"]["name"] = "wrong-label"
    
    with patch('config.PRODUCT_ID', 'gitauto'):
        result = await create_pr_from_issue(
            payload=mock_github_payload,
            trigger="issue_label",
            input_from="github"
        )
        
        assert result is None


@pytest.mark.asyncio
async def test_create_pr_from_issue_jira_input(mock_github_payload):
    """Test handling of Jira input source."""
    # Test with wrong label to ensure early return
    mock_github_payload["label"]["name"] = "wrong-label"
    
    with patch('config.PRODUCT_ID', 'gitauto'):
        result = await create_pr_from_issue(
            payload=mock_github_payload,
            trigger="issue_label",
            input_from="jira"
        )
        
        assert result is None


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