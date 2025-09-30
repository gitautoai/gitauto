import json
import urllib.parse
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from payloads.aws.event_bridge_scheduler.event_types import \
    EventBridgeSchedulerEvent


@pytest.fixture
def mock_github_request():
    """Create a mock request object for testing."""
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {"X-GitHub-Event": "push"}
    mock_req.body = AsyncMock(return_value=b'{"key": "value"}')
    return mock_req


@pytest.fixture
def mock_jira_request():
    """Create a mock request object for testing."""
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {"X-Atlassian-Token": "no-check"}
    mock_req.body = AsyncMock(return_value=b'{"key": "value"}')
    return mock_req


class TestHandleWebhook:
    """Test handle_webhook function in main.py."""

    @patch("main.verify_webhook_signature")
    @patch("main.handle_webhook_event")
    async def test_handle_webhook(
        self, mock_handle_webhook_event, mock_verify_webhook_signature, mock_github_request
    ):
        """Test handle_webhook function."""
        from main import handle_webhook

        result = await handle_webhook(request=mock_github_request)
        mock_verify_webhook_signature.assert_called_once()
        mock_handle_webhook_event.assert_called_once()
        assert result == {"message": "Webhook processed successfully"}

    @patch("main.verify_webhook_signature")
    @patch("main.handle_webhook_event")
    async def test_handle_webhook_with_json_decode_error(
        self, mock_handle_webhook_event, mock_verify_webhook_signature
    ):
        """Test handle_webhook function with JSON decode error."""
        from main import handle_webhook

        mock_req = MagicMock(spec=Request)
        mock_req.headers = {"X-GitHub-Event": "push"}
        mock_req.body = AsyncMock(return_value=b"invalid json")

        result = await handle_webhook(request=mock_req)
        mock_verify_webhook_signature.assert_called_once()
        mock_handle_webhook_event.assert_called_once()
        assert result == {"message": "Webhook processed successfully"}

    @patch("main.verify_webhook_signature")
    @patch("main.handle_webhook_event")
    async def test_handle_webhook_with_url_encoded_payload(
        self, mock_handle_webhook_event, mock_verify_webhook_signature
    ):
        """Test handle_webhook function with URL-encoded payload."""
        from main import handle_webhook

        mock_req = MagicMock(spec=Request)
        mock_req.headers = {"X-GitHub-Event": "push"}
        payload = {"key": "value"}
        encoded_payload = f"payload={urllib.parse.quote(json.dumps(payload))}"
        mock_req.body = AsyncMock(return_value=encoded_payload.encode("utf-8"))

        result = await handle_webhook(request=mock_req)
        mock_verify_webhook_signature.assert_called_once()
        mock_handle_webhook_event.assert_called_once()
        assert result == {"message": "Webhook processed successfully"}

    @patch("main.verify_webhook_signature")
    @patch("main.handle_webhook_event")
    async def test_handle_webhook_with_invalid_url_encoded_payload(
        self, mock_handle_webhook_event, mock_verify_webhook_signature
    ):
        """Test handle_webhook function with invalid URL-encoded payload."""
        from main import handle_webhook

        mock_req = MagicMock(spec=Request)
        mock_req.headers = {"X-GitHub-Event": "push"}
        encoded_payload = "payload=invalid json"
        mock_req.body = AsyncMock(return_value=encoded_payload.encode("utf-8"))

        result = await handle_webhook(request=mock_req)
        mock_verify_webhook_signature.assert_called_once()
        mock_handle_webhook_event.assert_called_once()
        assert result == {"message": "Webhook processed successfully"}

    @patch("main.verify_webhook_signature")
    @patch("main.handle_webhook_event")
    async def test_handle_webhook_with_body_read_error(
        self, mock_handle_webhook_event, mock_verify_webhook_signature
    ):
        """Test handle_webhook function with body read error."""
        from main import handle_webhook

        mock_req = MagicMock(spec=Request)
        mock_req.headers = {"X-GitHub-Event": "push"}
        mock_req.body = AsyncMock(side_effect=Exception("Error reading body"))

        result = await handle_webhook(request=mock_req)
        mock_verify_webhook_signature.assert_called_once()
        mock_handle_webhook_event.assert_called_once()
        assert result == {"message": "Webhook processed successfully"}


class TestHandleJiraWebhook:
    """Test handle_jira_webhook function in main.py."""

    @patch("main.verify_jira_webhook")
    @patch("main.create_pr_from_issue")
    async def test_handle_jira_webhook(
        self, mock_create_pr_from_issue, mock_verify_jira_webhook, mock_jira_request
    ):
        """Test handle_jira_webhook function."""
        from main import handle_jira_webhook

        mock_verify_jira_webhook.return_value = {"key": "value"}
        result = await handle_jira_webhook(request=mock_jira_request)
        mock_verify_jira_webhook.assert_called_once_with(mock_jira_request)
        mock_create_pr_from_issue.assert_called_once()
        assert result == {"message": "Jira webhook processed successfully"}


class TestSentryInitialization:
    """Test Sentry initialization in main.py."""

    @patch("config.ENV", "prod")
    @patch("main.sentry_sdk.init")
    def test_sentry_initialized_in_prod(self, mock_sentry_init):
        """Test that Sentry is initialized when ENV is prod."""
        import importlib

        import main

        # Reload main module to apply the patched ENV value
        importlib.reload(main)
        mock_sentry_init.assert_called_once()

    @patch("config.ENV", "dev")
    @patch("main.sentry_sdk.init")
    def test_sentry_not_initialized_in_dev(self, mock_sentry_init):
        """Test that Sentry is not initialized when ENV is not prod."""
        import importlib

        import main

        # Reload main module to apply the patched ENV value
        importlib.reload(main)
        mock_sentry_init.assert_not_called()


class TestHandler:
    """Test handler function in main.py."""

    @patch("main.schedule_handler")
    @patch("main.slack_notify")
    def test_handler_with_schedule_event(self, mock_slack_notify, mock_schedule_handler):
        """Test handler function with schedule event."""
        from main import handler

        mock_slack_notify.return_value = "thread_ts"
        mock_schedule_handler.return_value = {"status": "success"}

        event = EventBridgeSchedulerEvent(
            triggerType="schedule",
            ownerName="owner",
            repoName="repo",
        )
        result = handler(event=event, context={})

        assert mock_slack_notify.call_count == 2
        mock_schedule_handler.assert_called_once_with(event=event)
        assert result is None

    @patch("main.schedule_handler")
    @patch("main.slack_notify")
    def test_handler_with_schedule_event_failure(
        self, mock_slack_notify, mock_schedule_handler
    ):
        """Test handler function with schedule event failure."""
        from main import handler

        mock_slack_notify.return_value = "thread_ts"
        mock_schedule_handler.return_value = {
            "status": "error",
            "message": "Error message",
        }

        event = EventBridgeSchedulerEvent(
            triggerType="schedule",
            ownerName="owner",
            repoName="repo",
        )
        result = handler(event=event, context={})

        assert mock_slack_notify.call_count == 2
        mock_schedule_handler.assert_called_once_with(event=event)
        assert result is None

    @patch("main.mangum_handler")
    def test_handler_with_non_schedule_event(self, mock_mangum_handler):
        """Test handler function with non-schedule event."""
        from main import handler

        event = {"key": "value"}
        context = {"key": "value"}
        result = handler(event=event, context=context)

        mock_mangum_handler.assert_called_once_with(event=event, context=context)
        assert result == mock_mangum_handler.return_value


class TestRoot:
    """Test root function in main.py."""

    async def test_root(self):
        """Test root function."""
        from main import root

        result = await root()
        assert result == {"message": "GitAuto"}
