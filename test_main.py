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
def mock_github_request_no_event_header():
    """Create a mock request object without X-GitHub-Event header."""
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {}
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
def mock_github_request_with_malformed_url_encoded_body():
    """Create a mock request with malformed URL-encoded body."""
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {"X-GitHub-Event": "push"}
    encoded_body = "other_key=some_value"
    mock_req.body = AsyncMock(return_value=encoded_body.encode())
    return mock_req


@pytest.fixture
def mock_github_request_with_invalid_json_in_url_encoded():
    """Create a mock request with invalid JSON in URL-encoded payload."""
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {"X-GitHub-Event": "push"}
    encoded_body = "payload=invalid_json"
    mock_req.body = AsyncMock(return_value=encoded_body.encode())
    return mock_req


@pytest.fixture
def mock_github_request_with_exception_on_body():
    """Create a mock request that raises exception when body() is called."""
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {"X-GitHub-Event": "push"}
    mock_req.body = AsyncMock(side_effect=Exception("Body read error"))
    return mock_req


@pytest.fixture
def mock_github_request_with_json_decode_error():
    """Create a mock request with invalid JSON body."""
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {"X-GitHub-Event": "push"}
    mock_req.body = AsyncMock(return_value=b'invalid json')
    return mock_req


@pytest.fixture
def mock_scheduled_event():
    """Create a mock scheduled event from EventBridge."""
    return {
        "triggerType": "schedule",
        "ownerName": "test-owner",
        "repoName": "test-repo",
    }


@pytest.fixture
def mock_api_gateway_event():
    """Create a mock API Gateway event."""
    return {
        "httpMethod": "POST",
        "path": "/webhook",
        "headers": {"X-GitHub-Event": "push"},
        "body": '{"key": "value"}',
    }


class TestSentryInitialization:
    """Tests for Sentry initialization in main.py."""

    @patch("main.ENV", "prod")
    @patch("main.sentry_sdk.init")
    def test_sentry_initialized_in_prod(self, mock_sentry_init):
        """Test that Sentry is initialized when ENV is prod. This test is unreliable.

        Note: This test may be unreliable as it depends on module import behavior.
        See test_sentry_initialized_in_prod_with_config_patch for a more reliable test.
        """
        import importlib

        import main
        # Skip assertion as this test is unreliable
        # The test_sentry_initialized_in_prod_with_config_patch test is more reliable
        mock_sentry_init.assert_called_once()

    @patch("config.ENV", "prod")
    @patch("sentry_sdk.init")
    def test_sentry_initialized_in_prod_with_config_patch(self, mock_sentry_init):
        """Test that Sentry is initialized when ENV is prod by patching config.ENV."""
        # Clear any existing modules to ensure clean import
        import sys
        if "main" in sys.modules:
            del sys.modules["main"]

        # Now import main, which should trigger Sentry initialization
        import main  # noqa

        # Verify Sentry was initialized
        mock_sentry_init.assert_called_once()


class TestHandler:
    @patch("main.slack_notify")
    @patch("main.schedule_handler")
    def test_handler_with_scheduled_event_success(
        self, mock_schedule_handler, mock_slack_notify, mock_scheduled_event
    ):
        """Test handler with scheduled event that succeeds."""
        from main import handler

        mock_slack_notify.return_value = "thread_123"
        mock_schedule_handler.return_value = {"status": "success"}

        result = handler(mock_scheduled_event, None)

        assert result is None
        assert mock_slack_notify.call_count == 2
        mock_schedule_handler.assert_called_once_with(event=mock_scheduled_event)

    @patch("main.slack_notify")
    @patch("main.schedule_handler")
    def test_handler_with_scheduled_event_failure(
        self, mock_schedule_handler, mock_slack_notify, mock_scheduled_event
    ):
        """Test handler with scheduled event that fails."""
        from main import handler

        mock_slack_notify.return_value = "thread_123"
        mock_schedule_handler.return_value = {
            "status": "failure",
            "message": "Test error",
        }

        result = handler(mock_scheduled_event, None)

        assert result is None
        assert mock_slack_notify.call_count == 2

    @patch("main.mangum_handler")
    def test_handler_with_api_gateway_event(
        self, mock_mangum_handler, mock_api_gateway_event
    ):
        """Test handler with API Gateway event."""
        from main import handler

        mock_mangum_handler.return_value = {"statusCode": 200}

        result = handler(mock_api_gateway_event, None)

        assert result == {"statusCode": 200}
        mock_mangum_handler.assert_called_once_with(
            event=mock_api_gateway_event, context=None
        )


class TestHandleWebhook:
    @patch("main.handle_webhook_event")
    @patch("main.verify_webhook_signature")
    @patch("main.extract_lambda_info")
    async def test_handle_webhook_with_json_body(
        self,
        mock_extract_lambda_info,
        mock_verify_webhook_signature,
        mock_handle_webhook_event,
        mock_github_request,
    ):
        """Test handle_webhook with JSON body."""
        from main import handle_webhook

        mock_extract_lambda_info.return_value = {"request_id": "test-id"}

        result = await handle_webhook(mock_github_request)

        assert result == {"message": "Webhook processed successfully"}
        mock_verify_webhook_signature.assert_called_once()
        mock_handle_webhook_event.assert_called_once()

    @patch("main.handle_webhook_event")
    @patch("main.verify_webhook_signature")
    @patch("main.extract_lambda_info")
    async def test_handle_webhook_without_event_header(
        self,
        mock_extract_lambda_info,
        mock_verify_webhook_signature,
        mock_handle_webhook_event,
        mock_github_request_no_event_header,
    ):
        """Test handle_webhook without X-GitHub-Event header."""
        from main import handle_webhook

        mock_extract_lambda_info.return_value = {"request_id": "test-id"}

        result = await handle_webhook(mock_github_request_no_event_header)

        assert result == {"message": "Webhook processed successfully"}
        mock_handle_webhook_event.assert_called_once()

    @patch("main.handle_webhook_event")
    @patch("main.verify_webhook_signature")
    @patch("main.extract_lambda_info")
    async def test_handle_webhook_with_url_encoded_body(
        self,
        mock_extract_lambda_info,
        mock_verify_webhook_signature,
        mock_handle_webhook_event,
        mock_github_request_with_url_encoded_body,
    ):
        """Test handle_webhook with URL-encoded body."""
        from main import handle_webhook

        mock_extract_lambda_info.return_value = {"request_id": "test-id"}

        result = await handle_webhook(mock_github_request_with_url_encoded_body)

        assert result == {"message": "Webhook processed successfully"}
        mock_handle_webhook_event.assert_called_once()

    @patch("main.handle_webhook_event")
    @patch("main.verify_webhook_signature")
    @patch("main.extract_lambda_info")
    async def test_handle_webhook_with_malformed_url_encoded_body(
        self,
        mock_extract_lambda_info,
        mock_verify_webhook_signature,
        mock_handle_webhook_event,
        mock_github_request_with_malformed_url_encoded_body,
    ):
        """Test handle_webhook with malformed URL-encoded body."""
        from main import handle_webhook

        mock_extract_lambda_info.return_value = {"request_id": "test-id"}

        result = await handle_webhook(
            mock_github_request_with_malformed_url_encoded_body
        )

        assert result == {"message": "Webhook processed successfully"}
        mock_handle_webhook_event.assert_called_once()

    @patch("main.handle_webhook_event")
    @patch("main.verify_webhook_signature")
    @patch("main.extract_lambda_info")
    async def test_handle_webhook_with_invalid_json_in_url_encoded(
        self,
        mock_extract_lambda_info,
        mock_verify_webhook_signature,
        mock_handle_webhook_event,
        mock_github_request_with_invalid_json_in_url_encoded,
    ):
        """Test handle_webhook with invalid JSON in URL-encoded payload."""
        from main import handle_webhook

        mock_extract_lambda_info.return_value = {"request_id": "test-id"}

        result = await handle_webhook(
            mock_github_request_with_invalid_json_in_url_encoded
        )

        assert result == {"message": "Webhook processed successfully"}
        mock_handle_webhook_event.assert_called_once()

    @patch("main.handle_webhook_event")
    @patch("main.verify_webhook_signature")
    @patch("main.extract_lambda_info")
    async def test_handle_webhook_with_exception_on_body(
        self,
        mock_extract_lambda_info,
        mock_verify_webhook_signature,
        mock_handle_webhook_event,
        mock_github_request_with_exception_on_body,
    ):
        """Test handle_webhook when body() raises exception."""
        from main import handle_webhook

        mock_extract_lambda_info.return_value = {"request_id": "test-id"}

        result = await handle_webhook(mock_github_request_with_exception_on_body)

        assert result == {"message": "Webhook processed successfully"}
        mock_handle_webhook_event.assert_called_once()

    @patch("main.handle_webhook_event")
    @patch("main.verify_webhook_signature")
    @patch("main.extract_lambda_info")
    async def test_handle_webhook_with_json_decode_error(
        self,
        mock_extract_lambda_info,
        mock_verify_webhook_signature,
        mock_handle_webhook_event,
        mock_github_request_with_json_decode_error,
    ):
        """Test handle_webhook with invalid JSON body."""
        from main import handle_webhook

        mock_extract_lambda_info.return_value = {"request_id": "test-id"}

        result = await handle_webhook(mock_github_request_with_json_decode_error)

        assert result == {"message": "Webhook processed successfully"}
        mock_handle_webhook_event.assert_called_once()


class TestHandleJiraWebhook:
    @patch("main.create_pr_from_issue")
    @patch("main.verify_jira_webhook")
    @patch("main.extract_lambda_info")
    async def test_handle_jira_webhook(
        self,
        mock_extract_lambda_info,
        mock_verify_jira_webhook,
        mock_create_pr_from_issue,
    ):
        """Test handle_jira_webhook."""
        from main import handle_jira_webhook

        mock_request = MagicMock(spec=Request)
        mock_extract_lambda_info.return_value = {"request_id": "test-id"}
        mock_verify_jira_webhook.return_value = {"issue": "TEST-123"}

        result = await handle_jira_webhook(mock_request)

        assert result == {"message": "Jira webhook processed successfully"}
        mock_verify_jira_webhook.assert_called_once_with(mock_request)
        mock_create_pr_from_issue.assert_called_once()


class TestRoot:
    @patch("main.PRODUCT_NAME", "TestProduct")
    async def test_root(self):
        """Test root endpoint."""
        from main import root

        result = await root()

        assert result == {"message": "TestProduct"}
