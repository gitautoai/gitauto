# Standard imports
import json
from unittest.mock import patch, MagicMock, AsyncMock

# Third-party imports
import pytest
from fastapi import Request
from fastapi.responses import JSONResponse

# Local imports
from main import app, handler, handle_webhook, handle_jira_webhook, root
from payloads.aws.event_bridge_scheduler.event_types import EventBridgeSchedulerEvent


@pytest.fixture
def mock_request():
    """Create a mock request object for testing."""
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {"X-GitHub-Event": "push"}
    mock_req.body = AsyncMock(return_value=b'{"key": "value"}')
    return mock_req


@pytest.fixture
def mock_jira_request():
    """Create a mock Jira request object for testing."""
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {"X-Atlassian-Token": "no-check"}
    mock_req.body = AsyncMock(return_value=b'{"key": "value"}')
    return mock_req


class TestHandler:
    @patch("main.schedule_handler")
    @patch("main.slack_notify")
    def test_handler_schedule_event_success(self, mock_slack_notify, mock_schedule_handler):
        """Test handler function with a successful schedule event."""
        # Setup
        mock_slack_notify.return_value = "thread-123"
        mock_schedule_handler.return_value = {"status": "success"}
        
        event = EventBridgeSchedulerEvent(
            triggerType="schedule",
            ownerName="test-owner",
            repoName="test-repo"
        )
        
        # Execute
        handler(event=event, context={})
        
        # Verify
        mock_slack_notify.assert_called_with("Event Scheduler started for test-owner/test-repo")
        mock_schedule_handler.assert_called_with(event=event)
        mock_slack_notify.assert_called_with("Completed", "thread-123")

    @patch("main.schedule_handler")
    @patch("main.slack_notify")
    def test_handler_schedule_event_failure(self, mock_slack_notify, mock_schedule_handler):
        """Test handler function with a failed schedule event."""
        # Setup
        mock_slack_notify.return_value = "thread-123"
        mock_schedule_handler.return_value = {"status": "error", "message": "Something went wrong"}
        
        event = EventBridgeSchedulerEvent(
            triggerType="schedule",
            ownerName="test-owner",
            repoName="test-repo"
        )
        
        # Execute
        handler(event=event, context={})
        
        # Verify
        mock_slack_notify.assert_called_with("Event Scheduler started for test-owner/test-repo")
        mock_schedule_handler.assert_called_with(event=event)
        mock_slack_notify.assert_called_with("@channel Failed: Something went wrong", "thread-123")

    @patch("main.mangum_handler")
    def test_handler_non_schedule_event(self, mock_mangum_handler):
        """Test handler function with a non-schedule event."""
        # Setup
        event = {"key": "value"}  # Not a schedule event
        context = {"context": "data"}
        mock_mangum_handler.return_value = {"status": "success"}
        
        # Execute
        result = handler(event=event, context=context)
        
        # Verify
        mock_mangum_handler.assert_called_with(event=event, context=context)
        assert result == {"status": "success"}


class TestHandleWebhook:
    @patch("main.verify_webhook_signature")
    @patch("main.handle_webhook_event")
    async def test_handle_webhook_success(self, mock_handle_webhook_event, mock_verify_signature, mock_request):
        """Test handle_webhook function with successful execution."""
        # Setup
        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        
        # Execute
        response = await handle_webhook(request=mock_request)
        
        # Verify
        mock_verify_signature.assert_called_once()
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push", 
            payload={"key": "value"}
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.verify_webhook_signature")
    @patch("main.handle_webhook_event")
    async def test_handle_webhook_body_error(self, mock_handle_webhook_event, mock_verify_signature, mock_request):
        """Test handle_webhook function when request.body() raises an exception."""
        # Setup
        mock_verify_signature.return_value = None
        mock_request.body.side_effect = Exception("Body error")
        
        # Execute
        response = await handle_webhook(request=mock_request)
        
        # Verify
        mock_verify_signature.assert_called_once()
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push", 
            payload={}
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.verify_webhook_signature")
    @patch("main.handle_webhook_event")
    async def test_handle_webhook_json_decode_error(self, mock_handle_webhook_event, mock_verify_signature, mock_request):
        """Test handle_webhook function when JSON decoding fails."""
        # Setup
        mock_verify_signature.return_value = None
        mock_request.body.return_value = b'invalid json'
        
        # Execute
        response = await handle_webhook(request=mock_request)
        
        # Verify
        mock_verify_signature.assert_called_once()
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push", 
            payload={}
        )
        assert response == {"message": "Webhook processed successfully"}


class TestHandleJiraWebhook:
    @patch("main.verify_jira_webhook")
    @patch("main.create_pr_from_issue")
    async def test_handle_jira_webhook_success(self, mock_create_pr, mock_verify_jira, mock_jira_request):
        """Test handle_jira_webhook function with successful execution."""
        # Setup
        mock_verify_jira.return_value = {"key": "value"}
        mock_create_pr.return_value = None
        
        # Execute
        response = await handle_jira_webhook(request=mock_jira_request)
        
        # Verify
        mock_verify_jira.assert_called_once_with(mock_jira_request)
        mock_create_pr.assert_called_once_with(
            payload={"key": "value"}, 
            trigger="issue_checkbox", 
            input_from="jira"
        )
        assert response == {"message": "Jira webhook processed successfully"}


class TestRoot:
    @patch("main.PRODUCT_NAME", "TestProduct")
    async def test_root_endpoint(self):
        """Test root endpoint returns correct product name."""
        response = await root()
        assert response == {"message": "TestProduct"}