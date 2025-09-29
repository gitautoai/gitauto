# pylint: disable=unused-argument

# Standard imports
import asyncio
import json
import urllib.parse
from unittest.mock import AsyncMock, MagicMock, call, patch

# Third-party imports
from fastapi import FastAPI, Request
from mangum import Mangum
import pytest

# Local imports
import main
from config import GITHUB_WEBHOOK_SECRET, PRODUCT_NAME
from main import app, mangum_handler, handle_jira_webhook, handle_webhook, handler, root
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
    # URL-encoded body without payload key
    encoded_body = "other_key=some_value"
    mock_req.body = AsyncMock(return_value=encoded_body.encode())
    return mock_req


@pytest.fixture
def mock_github_request_with_invalid_json_in_url_encoded():
    """Create a mock request with invalid JSON in URL-encoded payload."""
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {"X-GitHub-Event": "push"}
    # URL-encoded body with invalid JSON in payload
    encoded_body = "payload=invalid_json_content"
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


@pytest.fixture
def mock_event_bridge_event_missing_names():
    """Create a mock EventBridge Scheduler event with missing owner/repo names."""
    return {
        "triggerType": "schedule",
        # Missing ownerName and repoName to test default empty strings
        "ownerId": 123456,
        "ownerType": "Organization",
        "repoId": 789012,
        "userId": 345678,
        "userName": "test-user",
        "installationId": 901234,
    }


class TestSentryInitialization:
    """Test Sentry initialization based on environment."""

    @patch("main.sentry_sdk.init")
    @patch("main.ENV", "prod")
    def test_sentry_init_called_in_prod_environment(self, mock_env, mock_sentry_init):
        """Test that Sentry is initialized when ENV is 'prod'."""
        # Force reimport of main module to trigger the initialization code
        import importlib
        importlib.reload(main)

        # Verify Sentry initialization was called
        mock_sentry_init.assert_called_once()
        call_args = mock_sentry_init.call_args

        # Verify the arguments passed to sentry_sdk.init
        assert call_args[1]["environment"] == "prod"
        assert call_args[1]["traces_sample_rate"] == 1.0
        assert "dsn" in call_args[1]
        assert "integrations" in call_args[1]

    @patch("main.sentry_sdk.init")
    @patch("main.ENV", "dev")
    def test_sentry_init_not_called_in_non_prod_environment(self, mock_sentry_init):
        """Test that Sentry is not initialized when ENV is not 'prod'."""
        # Force reimport of main module to trigger the initialization code
        import importlib
        importlib.reload(main)

        # Verify Sentry initialization was not called
        mock_sentry_init.assert_not_called()

    @patch("main.sentry_sdk.init")
    @patch("main.ENV", "staging")
    def test_sentry_init_not_called_in_staging_environment(self, mock_sentry_init):
        """Test that Sentry is not initialized when ENV is 'staging'."""
        # Force reimport of main module to trigger the initialization code
        import importlib
        importlib.reload(main)

        # Verify Sentry initialization was not called
        mock_sentry_init.assert_not_called()

    @patch("main.sentry_sdk.init")
    @patch("main.ENV", "test")
    def test_sentry_init_not_called_in_test_environment(self, mock_sentry_init):
        """Test that Sentry is not initialized when ENV is 'test'."""
        # Force reimport of main module to trigger the initialization code
        import importlib
        importlib.reload(main)

        # Verify Sentry initialization was not called
        mock_sentry_init.assert_not_called()


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
        result = handler(event=mock_event_bridge_event, context={})

        # Verify
        mock_schedule_handler.assert_called_with(event=mock_event_bridge_event)
        mock_slack_notify.assert_has_calls(
            [
                call("Event Scheduler started for test-owner/test-repo"),
                call("Completed", "thread-123"),
            ]
        )
        assert mock_slack_notify.call_count == 2
        assert result is None

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
        result = handler(event=mock_event_bridge_event, context={})

        # Verify
        mock_schedule_handler.assert_called_with(event=mock_event_bridge_event)
        mock_slack_notify.assert_has_calls(
            [
                call("Event Scheduler started for test-owner/test-repo"),
                call("@channel Failed: Something went wrong", "thread-123"),
            ]
        )
        assert mock_slack_notify.call_count == 2
        assert result is None

    @patch("main.schedule_handler")
    @patch("main.slack_notify")
    def test_handler_schedule_event_missing_owner_repo_names(
        self,
        mock_slack_notify,
        mock_schedule_handler,
        mock_event_bridge_event_missing_names,
    ):
        """Test handler function with schedule event missing owner/repo names."""
        # Setup
        mock_slack_notify.return_value = "thread-456"
        mock_schedule_handler.return_value = {"status": "success"}

        # Execute
        result = handler(event=mock_event_bridge_event_missing_names, context={})

        # Verify
        mock_schedule_handler.assert_called_with(
            event=mock_event_bridge_event_missing_names
        )
        mock_slack_notify.assert_has_calls(
            [
                call("Event Scheduler started for /"),  # Empty owner/repo names
                call("Completed", "thread-456"),
            ]
        )
        assert mock_slack_notify.call_count == 2
        assert result is None

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
    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_success(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
        mock_github_request,
    ):
        """Test handle_webhook function with successful execution."""
        # Setup
        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_extract_lambda_info.return_value = {
            "log_group": "/aws/lambda/pr-agent-prod",
            "log_stream": "2025/09/04/pr-agent-prod[$LATEST]841315c5",
            "request_id": "17921070-5cb6-43ee-8d2e-b5161ae89729",
        }

        # Execute
        response = await handle_webhook(request=mock_github_request)

        # Verify
        mock_verify_signature.assert_called_once_with(
            request=mock_github_request, secret=GITHUB_WEBHOOK_SECRET
        )
        mock_extract_lambda_info.assert_called_once_with(mock_github_request)
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push",
            payload={"key": "value"},
            lambda_info={
                "log_group": "/aws/lambda/pr-agent-prod",
                "log_stream": "2025/09/04/pr-agent-prod[$LATEST]841315c5",
                "request_id": "17921070-5cb6-43ee-8d2e-b5161ae89729",
            },
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_no_event_header(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
        mock_github_request_no_event_header,
    ):
        """Test handle_webhook function when X-GitHub-Event header is missing."""
        # Setup
        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_extract_lambda_info.return_value = {}

        # Execute
        response = await handle_webhook(request=mock_github_request_no_event_header)

        # Verify
        mock_verify_signature.assert_called_once_with(
            request=mock_github_request_no_event_header, secret=GITHUB_WEBHOOK_SECRET
        )
        mock_extract_lambda_info.assert_called_once_with(
            mock_github_request_no_event_header
        )
        mock_handle_webhook_event.assert_called_once_with(
            event_name="Event not specified",  # Default value when header is missing
            payload={"key": "value"},
            lambda_info={},
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_body_error(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
        mock_github_request,
    ):
        """Test handle_webhook function when request.body() raises an exception."""
        # Setup
        mock_verify_signature.return_value = None
        mock_github_request.body.side_effect = Exception("Body error")
        mock_extract_lambda_info.return_value = {}

        # Execute
        response = await handle_webhook(request=mock_github_request)

        # Verify
        mock_verify_signature.assert_called_once_with(
            request=mock_github_request, secret=GITHUB_WEBHOOK_SECRET
        )
        mock_extract_lambda_info.assert_called_once_with(mock_github_request)
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push", payload={}, lambda_info={}
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_json_decode_error(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
        mock_github_request,
    ):
        """Test handle_webhook function when JSON decoding fails."""
        # Setup
        mock_verify_signature.return_value = None
        mock_github_request.body.return_value = b"invalid json"
        mock_extract_lambda_info.return_value = {}

        # Execute
        response = await handle_webhook(request=mock_github_request)

        # Verify
        mock_verify_signature.assert_called_once_with(
            request=mock_github_request, secret=GITHUB_WEBHOOK_SECRET
        )
        mock_extract_lambda_info.assert_called_once_with(mock_github_request)
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push", payload={}, lambda_info={}
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_url_encoded_payload(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
        mock_github_request_with_url_encoded_body,
    ):
        """Test handle_webhook function with URL-encoded payload."""
        # Setup
        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_extract_lambda_info.return_value = {"log_group": "test-group"}

        # Execute
        response = await handle_webhook(
            request=mock_github_request_with_url_encoded_body
        )

        # Verify
        mock_verify_signature.assert_called_once_with(
            request=mock_github_request_with_url_encoded_body,
            secret=GITHUB_WEBHOOK_SECRET,
        )
        mock_extract_lambda_info.assert_called_once_with(
            mock_github_request_with_url_encoded_body
        )
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push",
            payload={"key": "value"},
            lambda_info={"log_group": "test-group"},
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_url_encoded_without_payload_key(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
        mock_github_request_with_malformed_url_encoded_body,
    ):
        """Test handle_webhook function with URL-encoded body without payload key."""
        # Setup
        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_extract_lambda_info.return_value = {}

        # Execute
        response = await handle_webhook(
            request=mock_github_request_with_malformed_url_encoded_body
        )

        # Verify
        mock_verify_signature.assert_called_once_with(
            request=mock_github_request_with_malformed_url_encoded_body,
            secret=GITHUB_WEBHOOK_SECRET,
        )
        mock_extract_lambda_info.assert_called_once_with(
            mock_github_request_with_malformed_url_encoded_body
        )
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push",
            payload={},  # Empty payload when no payload key in URL-encoded data
            lambda_info={},
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_url_encoded_invalid_json_payload(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
        mock_github_request_with_invalid_json_in_url_encoded,
    ):
        """Test handle_webhook function with invalid JSON in URL-encoded payload."""
        # Setup
        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_extract_lambda_info.return_value = {}

        # Execute
        response = await handle_webhook(
            request=mock_github_request_with_invalid_json_in_url_encoded
        )

        # Verify
        mock_verify_signature.assert_called_once_with(
            request=mock_github_request_with_invalid_json_in_url_encoded,
            secret=GITHUB_WEBHOOK_SECRET,
        )
        mock_extract_lambda_info.assert_called_once_with(
            mock_github_request_with_invalid_json_in_url_encoded
        )
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push",
            payload={},  # Empty payload when JSON parsing fails
            lambda_info={},
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_general_exception_in_json_parsing(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
        mock_github_request,
    ):
        """Test handle_webhook function when a general exception occurs during JSON parsing."""
        # Setup
        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_extract_lambda_info.return_value = {}

        # Mock json.loads to raise a general exception (not JSONDecodeError)
        with patch("main.json.loads", side_effect=Exception("General parsing error")):
            # Execute
            response = await handle_webhook(request=mock_github_request)

        # Verify
        mock_verify_signature.assert_called_once_with(
            request=mock_github_request, secret=GITHUB_WEBHOOK_SECRET
        )
        mock_extract_lambda_info.assert_called_once_with(mock_github_request)
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push",
            payload={},  # Empty payload when exception occurs
            lambda_info={},
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_with_custom_event_name(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
        mock_github_request,
    ):
        """Test handle_webhook function with a custom event name."""
        # Setup
        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_github_request.headers = {"X-GitHub-Event": "issue_comment"}
        mock_extract_lambda_info.return_value = {"request_id": "test-request-123"}

        # Execute
        response = await handle_webhook(request=mock_github_request)

        # Verify
        mock_verify_signature.assert_called_once_with(
            request=mock_github_request, secret=GITHUB_WEBHOOK_SECRET
        )
        mock_extract_lambda_info.assert_called_once_with(mock_github_request)
        mock_handle_webhook_event.assert_called_once_with(
            event_name="issue_comment",
            payload={"key": "value"},
            lambda_info={"request_id": "test-request-123"},
        )
        assert response == {"message": "Webhook processed successfully"}


class TestHandleJiraWebhook:
    @patch("main.extract_lambda_info")
    @patch("main.verify_jira_webhook", new_callable=AsyncMock)
    @patch("main.create_pr_from_issue")
    @pytest.mark.asyncio
    async def test_handle_jira_webhook_success(
        self,
        mock_create_pr,
        mock_verify_jira,
        mock_extract_lambda_info,
        mock_jira_request,
    ):
        """Test handle_jira_webhook function with successful execution."""
        # Setup
        mock_verify_jira.return_value = {"issue": {"key": "JIRA-123"}}
        mock_create_pr.return_value = None
        mock_extract_lambda_info.return_value = {
            "log_group": "/aws/lambda/pr-agent-prod",
            "log_stream": "2025/09/04/jira-stream",
            "request_id": "jira-request-456",
        }

        # Execute
        response = await handle_jira_webhook(request=mock_jira_request)

        # Verify
        mock_verify_jira.assert_called_once_with(mock_jira_request)
        mock_extract_lambda_info.assert_called_once_with(mock_jira_request)
        mock_create_pr.assert_called_once_with(
            payload={"issue": {"key": "JIRA-123"}},
            trigger="issue_comment",
            input_from="jira",
            lambda_info={
                "log_group": "/aws/lambda/pr-agent-prod",
                "log_stream": "2025/09/04/jira-stream",
                "request_id": "jira-request-456",
            },
        )
        assert response == {"message": "Jira webhook processed successfully"}


class TestRootEndpoint:
    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Test root endpoint returns correct product name."""
        response = await root()
        assert response == {"message": PRODUCT_NAME}


class TestAppConfiguration:
    def test_app_routes(self):
        """Test that the FastAPI app has the expected routes."""
        # Simple test to verify app has routes
        assert len(app.routes) > 0

        # Test that we can access the root endpoint

        result = asyncio.run(root())
        assert result == {"message": PRODUCT_NAME}

    def test_app_instance(self):
        """Test that the FastAPI app instance is properly configured."""
        assert isinstance(app, FastAPI)
        assert app is not None

    def test_mangum_handler_instance(self):
        """Test that the Mangum handler is properly configured."""
        assert isinstance(mangum_handler, Mangum)
        assert mangum_handler is not None

    def test_app_routes_configuration(self):
        """Test that the FastAPI app has the expected route paths."""
        route_paths = [route.path for route in app.routes if hasattr(route, "path")]

        # Check that expected routes exist
        assert "/" in route_paths
        assert "/webhook" in route_paths
        assert "/jira-webhook" in route_paths


class TestEdgeCases:
    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_empty_body(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
    ):
        """Test handle_webhook function with empty request body."""
        # Setup
        mock_req = MagicMock(spec=Request)
        mock_req.headers = {"X-GitHub-Event": "ping"}
        mock_req.body = AsyncMock(return_value=b"")

        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_extract_lambda_info.return_value = {}

        # Execute
        response = await handle_webhook(request=mock_req)

        # Verify
        mock_verify_signature.assert_called_once_with(
            request=mock_req, secret=GITHUB_WEBHOOK_SECRET
        )
        mock_extract_lambda_info.assert_called_once_with(mock_req)
        mock_handle_webhook_event.assert_called_once_with(
            event_name="ping",
            payload={},  # Empty payload for empty body
            lambda_info={},
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.schedule_handler")
    @patch("main.slack_notify")
    def test_handler_schedule_event_with_none_result_status(
        self, mock_slack_notify, mock_schedule_handler, mock_event_bridge_event
    ):
        """Test handler function when schedule_handler returns None status."""
        # Setup
        mock_slack_notify.return_value = "thread-789"
        mock_schedule_handler.return_value = {
            "status": None,
            "message": "Unknown status",
        }

        # Execute
        result = handler(event=mock_event_bridge_event, context={})

        # Verify
        mock_schedule_handler.assert_called_with(event=mock_event_bridge_event)
        mock_slack_notify.assert_has_calls(
            [
                call("Event Scheduler started for test-owner/test-repo"),
                call("@channel Failed: Unknown status", "thread-789"),
            ]
        )
        assert mock_slack_notify.call_count == 2
        assert result is None

    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_with_unicode_content(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
    ):
        """Test handle_webhook function with Unicode content in request body."""
        # Setup
        mock_req = MagicMock(spec=Request)
        mock_req.headers = {"X-GitHub-Event": "issues"}
        unicode_content = '{"title": "测试 Unicode 内容", "body": "🚀 Emoji test"}'
        mock_req.body = AsyncMock(return_value=unicode_content.encode("utf-8"))

        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_extract_lambda_info.return_value = {}

        # Execute
        response = await handle_webhook(request=mock_req)

        # Verify
        mock_verify_signature.assert_called_once_with(
            request=mock_req, secret=GITHUB_WEBHOOK_SECRET
        )
        mock_extract_lambda_info.assert_called_once_with(mock_req)
        mock_handle_webhook_event.assert_called_once_with(
            event_name="issues",
            payload={"title": "测试 Unicode 内容", "body": "🚀 Emoji test"},
            lambda_info={},
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.schedule_handler")
    @patch("main.slack_notify")
    def test_handler_schedule_event_with_missing_message_in_result(
        self, mock_slack_notify, mock_schedule_handler, mock_event_bridge_event
    ):
        """Test handler function when schedule_handler returns error status without message."""
        # Setup
        mock_slack_notify.return_value = "thread-999"
        mock_schedule_handler.return_value = {
            "status": "error"
        }  # Missing 'message' key

        # Execute
        result = handler(event=mock_event_bridge_event, context={})

        # Verify
        mock_schedule_handler.assert_called_with(event=mock_event_bridge_event)
        mock_slack_notify.assert_has_calls(
            [
                call("Event Scheduler started for test-owner/test-repo"),
                call("@channel Failed: Unknown error", "thread-999"),
            ]
        )
        assert mock_slack_notify.call_count == 2
        assert result is None


class TestPrintStatements:
    @patch("builtins.print")
    @patch("main.schedule_handler")
    @patch("main.slack_notify")
    def test_handler_schedule_event_prints_message(
        self,
        mock_slack_notify,
        mock_schedule_handler,
        mock_print,
        mock_event_bridge_event,
    ):
        """Test that handler function prints the correct message for schedule events."""
        # Setup
        mock_slack_notify.return_value = "thread-123"
        mock_schedule_handler.return_value = {"status": "success"}

        # Execute
        handler(event=mock_event_bridge_event, context={})

        # Verify
        mock_print.assert_called_once_with("AWS EventBridge Scheduler invoked")

    @patch("builtins.print")
    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_prints_body_error(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
        mock_print,
        mock_github_request,
    ):
        """Test that handle_webhook prints error message when body reading fails."""
        # Setup
        mock_verify_signature.return_value = None
        mock_github_request.body.side_effect = Exception("Body read error")
        mock_extract_lambda_info.return_value = {}

        # Execute
        await handle_webhook(request=mock_github_request)

        # Verify
        mock_print.assert_called_once_with(
            "Error in reading request body: Body read error"
        )

    @patch("builtins.print")
    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_prints_json_parsing_error(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
        mock_print,
        mock_github_request,
    ):
        """Test that handle_webhook prints error message when JSON parsing fails."""
        # Setup
        mock_verify_signature.return_value = None
        mock_extract_lambda_info.return_value = {}

        # Mock json.loads to raise a general exception
        with patch("main.json.loads", side_effect=Exception("JSON parsing error")):
            # Execute
            await handle_webhook(request=mock_github_request)

        # Verify
        mock_print.assert_called_once_with(
            "Error in parsing JSON payload: JSON parsing error"
        )


class TestModuleImports:
    def test_required_imports_available(self):
        """Test that all required modules and functions are properly imported."""
        # Test FastAPI app
        assert hasattr(main, "app")
        assert hasattr(main, "mangum_handler")

        # Test handler functions
        assert hasattr(main, "handler")
        assert hasattr(main, "handle_webhook")
        assert hasattr(main, "handle_jira_webhook")
        assert hasattr(main, "root")

        # Test that functions are callable
        assert callable(main.handler)
        assert callable(main.handle_webhook)
        assert callable(main.handle_jira_webhook)
        assert callable(main.root)


class TestTypeAnnotations:
    @pytest.mark.asyncio
    async def test_handle_webhook_return_type(self, mock_github_request):
        """Test that handle_webhook returns the correct type."""
        with patch("main.extract_lambda_info"), patch(
            "main.verify_webhook_signature", new_callable=AsyncMock
        ), patch("main.handle_webhook_event", new_callable=AsyncMock):

            result = await handle_webhook(request=mock_github_request)

            # Should return a dictionary with string keys and values
            assert isinstance(result, dict)
            assert all(isinstance(k, str) for k in result.keys())
            assert all(isinstance(v, str) for v in result.values())

    @pytest.mark.asyncio
    async def test_root_return_type(self):
        """Test that root endpoint returns the correct type."""
        result = await root()

        assert isinstance(result, dict)
        assert all(isinstance(k, str) for k in result.keys())


class TestCornerCases:
    """Additional corner cases and edge scenarios."""

    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_with_binary_content(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
    ):
        """Test handle_webhook function with binary content that can't be decoded."""
        # Setup
        mock_req = MagicMock(spec=Request)
        mock_req.headers = {"X-GitHub-Event": "push"}
        # Binary content that will cause decode error
        mock_req.body = AsyncMock(return_value=b'\x80\x81\x82\x83')

        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_extract_lambda_info.return_value = {}

        # Execute
        response = await handle_webhook(request=mock_req)

        # Verify - should handle decode error gracefully
        mock_verify_signature.assert_called_once_with(
            request=mock_req, secret=GITHUB_WEBHOOK_SECRET
        )
        mock_extract_lambda_info.assert_called_once_with(mock_req)
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push",
            payload={},  # Empty payload when decoding fails
            lambda_info={},
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_with_very_large_payload(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
    ):
        """Test handle_webhook function with a very large JSON payload."""
        # Setup
        mock_req = MagicMock(spec=Request)
        mock_req.headers = {"X-GitHub-Event": "push"}
        # Create a large payload
        large_payload = {"data": "x" * 10000, "items": list(range(1000))}
        mock_req.body = AsyncMock(return_value=json.dumps(large_payload).encode())

        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_extract_lambda_info.return_value = {}

        # Execute
        response = await handle_webhook(request=mock_req)

        # Verify
        mock_verify_signature.assert_called_once_with(
            request=mock_req, secret=GITHUB_WEBHOOK_SECRET
        )
        mock_extract_lambda_info.assert_called_once_with(mock_req)
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push",
            payload=large_payload,
            lambda_info={},
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_with_nested_json_payload(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
    ):
        """Test handle_webhook function with deeply nested JSON payload."""
        # Setup
        mock_req = MagicMock(spec=Request)
        mock_req.headers = {"X-GitHub-Event": "issues"}
        nested_payload = {
            "action": "opened",
            "issue": {
                "id": 123,
                "title": "Test Issue",
                "user": {
                    "login": "testuser",
                    "id": 456,
                    "avatar_url": "https://example.com/avatar.png"
                },
                "labels": [
                    {"id": 1, "name": "bug", "color": "red"},
                    {"id": 2, "name": "priority:high", "color": "orange"}
                ]
            },
            "repository": {
                "id": 789,
                "name": "test-repo",
                "owner": {
                    "login": "testorg",
                    "id": 101112
                }
            }
        }
        mock_req.body = AsyncMock(return_value=json.dumps(nested_payload).encode())

        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_extract_lambda_info.return_value = {}

        # Execute
        response = await handle_webhook(request=mock_req)

        # Verify
        mock_verify_signature.assert_called_once_with(
            request=mock_req, secret=GITHUB_WEBHOOK_SECRET
        )
        mock_extract_lambda_info.assert_called_once_with(mock_req)
        mock_handle_webhook_event.assert_called_once_with(
            event_name="issues",
            payload=nested_payload,
            lambda_info={},
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.schedule_handler")
    @patch("main.slack_notify")
    def test_handler_schedule_event_with_empty_result(
        self, mock_slack_notify, mock_schedule_handler, mock_event_bridge_event
    ):
        """Test handler function when schedule_handler returns empty result."""
        # Setup
        mock_slack_notify.return_value = "thread-empty"
        mock_schedule_handler.return_value = {}  # Empty result

        # Execute
        result = handler(event=mock_event_bridge_event, context={})

        # Verify
        mock_schedule_handler.assert_called_with(event=mock_event_bridge_event)
        mock_slack_notify.assert_has_calls(
            [
                call("Event Scheduler started for test-owner/test-repo"),
                call("@channel Failed: Unknown error", "thread-empty"),
            ]
        )
        assert mock_slack_notify.call_count == 2
        assert result is None

    @patch("main.schedule_handler")
    @patch("main.slack_notify")
    def test_handler_schedule_event_with_different_status_values(
        self, mock_slack_notify, mock_schedule_handler, mock_event_bridge_event
    ):
        """Test handler function with various non-success status values."""
        test_cases = [
            {"status": "failed", "message": "Process failed"},
            {"status": "timeout", "message": "Operation timed out"},
            {"status": "cancelled", "message": "User cancelled"},
            {"status": "pending", "message": "Still processing"},
        ]

        for i, test_case in enumerate(test_cases):
            with patch.object(mock_slack_notify, 'reset_mock'):
                mock_slack_notify.reset_mock()
                mock_schedule_handler.reset_mock()

                # Setup
                thread_id = f"thread-{i}"
                mock_slack_notify.return_value = thread_id
                mock_schedule_handler.return_value = test_case

                # Execute
                result = handler(event=mock_event_bridge_event, context={})

                # Verify
                mock_schedule_handler.assert_called_with(event=mock_event_bridge_event)
                mock_slack_notify.assert_has_calls(
                    [
                        call("Event Scheduler started for test-owner/test-repo"),
                        call(f"@channel Failed: {test_case['message']}", thread_id),
                    ]
                )
                assert mock_slack_notify.call_count == 2
                assert result is None

    @patch("main.extract_lambda_info")
    @patch("main.verify_jira_webhook", new_callable=AsyncMock)
    @patch("main.create_pr_from_issue")
    @pytest.mark.asyncio
    async def test_handle_jira_webhook_with_empty_lambda_info(
        self,
        mock_create_pr,
        mock_verify_jira,
        mock_extract_lambda_info,
        mock_jira_request,
    ):
        """Test handle_jira_webhook function with empty lambda info."""
        # Setup
        mock_verify_jira.return_value = {"issue": {"key": "JIRA-456", "summary": "Test Issue"}}
        mock_create_pr.return_value = None
        mock_extract_lambda_info.return_value = {}  # Empty lambda info

        # Execute
        response = await handle_jira_webhook(request=mock_jira_request)

        # Verify
        mock_verify_jira.assert_called_once_with(mock_jira_request)
        mock_extract_lambda_info.assert_called_once_with(mock_jira_request)
        mock_create_pr.assert_called_once_with(
            payload={"issue": {"key": "JIRA-456", "summary": "Test Issue"}},
            trigger="issue_comment",
            input_from="jira",
            lambda_info={},
        )
        assert response == {"message": "Jira webhook processed successfully"}

    @patch("main.extract_lambda_info")
    @patch("main.verify_jira_webhook", new_callable=AsyncMock)
    @patch("main.create_pr_from_issue")
    @pytest.mark.asyncio
    async def test_handle_jira_webhook_with_complex_payload(
        self,
        mock_create_pr,
        mock_verify_jira,
        mock_extract_lambda_info,
        mock_jira_request,
    ):
        """Test handle_jira_webhook function with complex Jira payload."""
        # Setup
        complex_payload = {
            "issue": {
                "key": "PROJ-789",
                "summary": "Complex Issue",
                "description": "This is a complex issue with multiple fields",
                "status": {"name": "In Progress"},
                "assignee": {"displayName": "John Doe", "emailAddress": "john@example.com"},
                "components": [{"name": "Backend"}, {"name": "API"}],
                "labels": ["bug", "critical"],
                "customfield_10001": "Custom value"
            },
            "user": {
                "displayName": "Jane Smith",
                "emailAddress": "jane@example.com"
            },
            "changelog": {
                "items": [
                    {
                        "field": "status",
                        "fromString": "To Do",
                        "toString": "In Progress"
                    }
                ]
            }
        }

        mock_verify_jira.return_value = complex_payload
        mock_create_pr.return_value = None
        mock_extract_lambda_info.return_value = {
            "log_group": "/aws/lambda/jira-handler",
            "request_id": "complex-request-789"
        }

        # Execute
        response = await handle_jira_webhook(request=mock_jira_request)

        # Verify
        mock_verify_jira.assert_called_once_with(mock_jira_request)
        mock_extract_lambda_info.assert_called_once_with(mock_jira_request)
        mock_create_pr.assert_called_once_with(
            payload=complex_payload,
            trigger="issue_comment",
            input_from="jira",
            lambda_info={
                "log_group": "/aws/lambda/jira-handler",
                "request_id": "complex-request-789"
            },
        )
        assert response == {"message": "Jira webhook processed successfully"}


class TestErrorHandling:
    """Test error handling scenarios."""

    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_with_decode_error_in_url_parsing(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
    ):
        """Test handle_webhook when URL decoding fails."""
        # Setup
        mock_req = MagicMock(spec=Request)
        mock_req.headers = {"X-GitHub-Event": "push"}
        # Invalid UTF-8 sequence that will cause decode error
        mock_req.body = AsyncMock(return_value=b'\xff\xfe\xfd')

        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_extract_lambda_info.return_value = {}

        # Execute
        response = await handle_webhook(request=mock_req)

        # Verify - should handle decode error gracefully
        mock_verify_signature.assert_called_once_with(
            request=mock_req, secret=GITHUB_WEBHOOK_SECRET
        )
        mock_extract_lambda_info.assert_called_once_with(mock_req)
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push",
            payload={},  # Empty payload when decoding fails
            lambda_info={},
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_with_url_encoded_decode_error(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
    ):
        """Test handle_webhook when URL-encoded content has decode issues."""
        # Setup
        mock_req = MagicMock(spec=Request)
        mock_req.headers = {"X-GitHub-Event": "push"}
        # Content that looks like JSON but will fail JSON parsing, then fail URL parsing
        mock_req.body = AsyncMock(return_value=b'not_json_and_not_url_encoded')

        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_extract_lambda_info.return_value = {}

        # Execute
        response = await handle_webhook(request=mock_req)

        # Verify
        mock_verify_signature.assert_called_once_with(
            request=mock_req, secret=GITHUB_WEBHOOK_SECRET
        )
        mock_extract_lambda_info.assert_called_once_with(mock_req)
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push",
            payload={},  # Empty payload when all parsing fails
            lambda_info={},
        )
        assert response == {"message": "Webhook processed successfully"}


class TestIntegrationScenarios:
    """Test integration-like scenarios that combine multiple components."""

    @patch("main.schedule_handler")
    @patch("main.slack_notify")
    def test_handler_complete_schedule_workflow_success(
        self, mock_slack_notify, mock_schedule_handler
    ):
        """Test complete successful schedule workflow from start to finish."""
        # Setup
        event = {
            "triggerType": "schedule",
            "ownerName": "integration-owner",
            "repoName": "integration-repo",
            "ownerId": 999888,
            "ownerType": "Organization",
            "repoId": 777666,
            "userId": 555444,
            "userName": "integration-user",
            "installationId": 333222,
        }
        context = {"aws_request_id": "integration-request-123"}

        mock_slack_notify.return_value = "integration-thread-456"
        mock_schedule_handler.return_value = {
            "status": "success",
            "message": "All tasks completed successfully",
            "processed_items": 5
        }

        # Execute
        result = handler(event=event, context=context)

        # Verify complete workflow
        mock_schedule_handler.assert_called_once_with(event=event)
        mock_slack_notify.assert_has_calls(
            [
                call("Event Scheduler started for integration-owner/integration-repo"),
                call("Completed", "integration-thread-456"),
            ]
        )
        assert mock_slack_notify.call_count == 2
        assert result is None

    @patch("main.schedule_handler")
    @patch("main.slack_notify")
    def test_handler_complete_schedule_workflow_failure(
        self, mock_slack_notify, mock_schedule_handler
    ):
        """Test complete failed schedule workflow from start to finish."""
        # Setup
        event = {
            "triggerType": "schedule",
            "ownerName": "failing-owner",
            "repoName": "failing-repo",
            "ownerId": 111222,
            "ownerType": "User",
            "repoId": 333444,
            "userId": 555666,
            "userName": "failing-user",
            "installationId": 777888,
        }
        context = {"aws_request_id": "failing-request-789"}

        mock_slack_notify.return_value = "failing-thread-101"
        mock_schedule_handler.return_value = {
            "status": "error",
            "message": "Database connection failed",
            "error_code": "DB_CONNECTION_ERROR"
        }

        # Execute
        result = handler(event=event, context=context)

        # Verify complete workflow
        mock_schedule_handler.assert_called_once_with(event=event)
        mock_slack_notify.assert_has_calls(
            [
                call("Event Scheduler started for failing-owner/failing-repo"),
                call("@channel Failed: Database connection failed", "failing-thread-101"),
            ]
        )
        assert mock_slack_notify.call_count == 2
        assert result is None
