# Standard imports
import json
import urllib.parse
from unittest.mock import patch, MagicMock, AsyncMock, call

# Third-party imports
import pytest
from fastapi import Request

# Local imports
from main import app, handler, handle_webhook, handle_jira_webhook, root
from payloads.aws.event_bridge_scheduler.event_types import EventBridgeSchedulerEvent
from config import PRODUCT_NAME, GITHUB_WEBHOOK_SECRET


@pytest.fixture
def mock_github_request():
    """Create a mock request object for testing."""
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {"X-GitHub-Event": "push"}
    mock_req.body = AsyncMock(return_value=b'{"key": "value"}')
    return mock_req


@pytest.fixture
def mock_github_request_with_url_encoded_body():
    """Create a mock request with URL-encoded body."""
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {"X-GitHub-Event": "push"}
    payload = json.dumps({"key": "value"})
    encoded_body = f"payload={urllib.parse.quote(payload)}"
    mock_req.body = AsyncMock(return_value=encoded_body.encode())
    return mock_req


@pytest.fixture
def mock_jira_request():
    """Create a mock Jira request object for testing."""
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {"X-Atlassian-Token": "no-check"}
    mock_req.body = AsyncMock(return_value=b'{"issue": {"key": "JIRA-123"}}')
    return mock_req


@pytest.fixture
def mock_event_bridge_event():
    """Create a mock EventBridge Scheduler event."""
    return EventBridgeSchedulerEvent(
        triggerType="schedule",
        ownerName="test-owner",
        repoName="test-repo",
        ownerId=123456,
        ownerType="Organization",
        repoId=789012,
        userId=345678,
        userName="test-user",
        installationId=901234,
    )


class TestHandler:
    @patch("main.schedule_handler")
    @patch("main.slack_notify")
    def test_handler_schedule_event_success(
        self, mock_slack_notify, mock_schedule_handler, mock_event_bridge_event
    ):
        """Test handler function with a successful schedule event."""
        # Setup
        mock_slack_notify.return_value = "thread-123"
        mock_schedule_handler.return_value = {"status": "success"}

        # Execute
        handler(event=mock_event_bridge_event, context={})

        # Verify
        mock_schedule_handler.assert_called_with(event=mock_event_bridge_event)
        mock_slack_notify.assert_has_calls(
            [
                call("Event Scheduler started for test-owner/test-repo"),
                call("Completed", "thread-123"),
            ]
        )
        assert mock_slack_notify.call_count == 2

    @patch("main.schedule_handler")
    @patch("main.slack_notify")
    def test_handler_schedule_event_failure(
        self, mock_slack_notify, mock_schedule_handler, mock_event_bridge_event
    ):
        """Test handler function with a failed schedule event."""
        # Setup
        mock_slack_notify.return_value = "thread-123"
        mock_schedule_handler.return_value = {
            "status": "error",
            "message": "Something went wrong",
        }

        # Execute
        handler(event=mock_event_bridge_event, context={})

        # Verify
        mock_schedule_handler.assert_called_with(event=mock_event_bridge_event)
        mock_slack_notify.assert_has_calls(
            [
                call("Event Scheduler started for test-owner/test-repo"),
                call("@channel Failed: Something went wrong", "thread-123"),
            ]
        )
        assert mock_slack_notify.call_count == 2

    @patch("main.mangum_handler")
    def test_handler_non_schedule_event(self, mock_mangum_handler):
        """Test handler function with a non-schedule event."""
        # Setup
        event = {"key": "value", "triggerType": "not-schedule"}  # Not a schedule event
        context = {"context": "data"}
        mock_mangum_handler.return_value = {"status": "success"}

        # Execute
        result = handler(event=event, context=context)

        # Verify
        mock_mangum_handler.assert_called_with(event=event, context=context)
        assert result == {"status": "success"}

    @patch("main.mangum_handler")
    def test_handler_without_trigger_type(self, mock_mangum_handler):
        """Test handler function with an event that doesn't have triggerType."""
        # Setup
        event = {"key": "value"}  # No triggerType
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
    async def test_handle_webhook_success(
        self, mock_handle_webhook_event, mock_verify_signature, mock_github_request
    ):
        """Test handle_webhook function with successful execution."""
        # Setup
        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None

        # Execute
        response = await handle_webhook(request=mock_github_request)

        # Verify
        mock_verify_signature.assert_called_once_with(
            request=mock_github_request, secret=GITHUB_WEBHOOK_SECRET
        )
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push", payload={"key": "value"}
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.verify_webhook_signature")
    @patch("main.handle_webhook_event")
    async def test_handle_webhook_body_error(
        self, mock_handle_webhook_event, mock_verify_signature, mock_github_request
    ):
        """Test handle_webhook function when request.body() raises an exception."""
        # Setup
        mock_verify_signature.return_value = None
        mock_github_request.body.side_effect = Exception("Body error")

        # Execute
        response = await handle_webhook(request=mock_github_request)

        # Verify
        mock_verify_signature.assert_called_once_with(
            request=mock_github_request, secret=GITHUB_WEBHOOK_SECRET
        )
        mock_handle_webhook_event.assert_called_once_with(event_name="push", payload={})
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.verify_webhook_signature")
    @patch("main.handle_webhook_event")
    async def test_handle_webhook_json_decode_error(
        self, mock_handle_webhook_event, mock_verify_signature, mock_github_request
    ):
        """Test handle_webhook function when JSON decoding fails."""
        # Setup
        mock_verify_signature.return_value = None
        mock_github_request.body.return_value = b"invalid json"

        # Execute
        response = await handle_webhook(request=mock_github_request)

        # Verify
        mock_verify_signature.assert_called_once_with(
            request=mock_github_request, secret=GITHUB_WEBHOOK_SECRET
        )
        mock_handle_webhook_event.assert_called_once_with(event_name="push", payload={})
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.verify_webhook_signature")
    @patch("main.handle_webhook_event")
    async def test_handle_webhook_url_encoded_payload(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_github_request_with_url_encoded_body,
    ):
        """Test handle_webhook function with URL-encoded payload."""
        # Setup
        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None

        # Execute
        response = await handle_webhook(
            request=mock_github_request_with_url_encoded_body
        )

        # Verify
        mock_verify_signature.assert_called_once_with(
            request=mock_github_request_with_url_encoded_body,
            secret=GITHUB_WEBHOOK_SECRET,
        )
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push", payload={"key": "value"}
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.verify_webhook_signature")
    @patch("main.handle_webhook_event")
    async def test_handle_webhook_with_custom_event_name(
        self, mock_handle_webhook_event, mock_verify_signature, mock_github_request
    ):
        """Test handle_webhook function with a custom event name."""
        # Setup
        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_github_request.headers = {"X-GitHub-Event": "issue_comment"}

        # Execute
        response = await handle_webhook(request=mock_github_request)

        # Verify
        mock_verify_signature.assert_called_once_with(
            request=mock_github_request, secret=GITHUB_WEBHOOK_SECRET
        )
        mock_handle_webhook_event.assert_called_once_with(
            event_name="issue_comment", payload={"key": "value"}
        )
        assert response == {"message": "Webhook processed successfully"}


@patch("main.verify_jira_webhook")
@patch("main.create_pr_from_issue")
async def test_handle_jira_webhook_success(
    mock_create_pr, mock_verify_jira, mock_jira_request
):
    """Test handle_jira_webhook function with successful execution."""
    # Setup
    mock_verify_jira.return_value = {"issue": {"key": "JIRA-123"}}
    mock_create_pr.return_value = None

    # Execute
    response = await handle_jira_webhook(request=mock_jira_request)

    # Verify
    mock_verify_jira.assert_called_once_with(mock_jira_request)
    mock_create_pr.assert_called_once_with(
        payload={"issue": {"key": "JIRA-123"}},
        trigger="issue_comment",
        input_from="jira",
    )
    assert response == {"message": "Jira webhook processed successfully"}


async def test_root_endpoint():
    """Test root endpoint returns correct product name."""
    response = await root()
    assert response == {"message": PRODUCT_NAME}


def test_app_routes():
    """Test that the FastAPI app has the expected routes."""
    routes = {route.path: route.methods for route in app.routes}

    assert "/" in routes
    assert "GET" in routes["/"]

    assert "/webhook" in routes
    assert "POST" in routes["/webhook"]

    assert "/jira-webhook" in routes
    assert "POST" in routes["/jira-webhook"]
