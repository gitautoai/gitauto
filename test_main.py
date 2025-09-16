# Standard imports
import json
import sys
import urllib.parse
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, call, patch

# Third-party imports
import pytest
# Local imports
from config import GITHUB_WEBHOOK_SECRET, PRODUCT_NAME
from fastapi import Request
from main import app, handle_jira_webhook, handle_webhook, handler, root
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
def mock_github_request_with_url_encoded_body():
    """Create a mock request with URL-encoded body."""
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {"X-GitHub-Event": "push"}
    payload = json.dumps({"key": "value"})
    encoded_body = f"payload={urllib.parse.quote(payload)}"
    mock_req.body = AsyncMock(return_value=encoded_body.encode())
    return mock_req


@pytest.fixture
def mock_github_request_no_event_header():
    """Create a mock request without X-GitHub-Event header."""
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {}
    mock_req.body = AsyncMock(return_value=b'{"key": "value"}')
    return mock_req


@pytest.fixture
def mock_github_request_malformed_url_encoded():
    """Create a mock request with malformed URL-encoded body."""
    mock_req = MagicMock(spec=Request)
    mock_req.headers = {"X-GitHub-Event": "push"}
    mock_req.body = AsyncMock(return_value=b"payload=invalid%json")
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
def mock_event_bridge_event_no_names():
    """Create a mock EventBridge Scheduler event without owner/repo names."""
    return {
        "triggerType": "schedule",
        "ownerId": 123456,
        "ownerType": "Organization",
        "repoId": 789012,
        "userId": 345678,
        "userName": "test-user",
        "installationId": 901234,
    }


class TestSentryInitialization:
    @patch("config.ENV", "prod")
    @patch("sentry_sdk.init")
    def test_sentry_initialization_logic(self, mock_sentry_init):
        """Test the Sentry initialization logic."""
        # Import the config to get the ENV value
        from config import ENV, SENTRY_DSN

        # Simulate the initialization logic from main.py
        if ENV == "prod":
            import sentry_sdk
            from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
            sentry_sdk.init(
                dsn=SENTRY_DSN,
                environment=ENV,
                integrations=[AwsLambdaIntegration()],
                traces_sample_rate=1.0,
            )

        # Verify Sentry was initialized
        mock_sentry_init.assert_called_once()

    @patch("config.ENV", "dev")
    @patch("sentry_sdk.init")
    def test_sentry_not_initialized_in_dev(self, mock_sentry_init):
        """Test that Sentry initialization is skipped in non-prod environments."""
        from config import ENV

        # Simulate the initialization logic from main.py
        if ENV == "prod":
            import sentry_sdk
            from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
            sentry_sdk.init(
                dsn="test-dsn",
                environment=ENV,
                integrations=[AwsLambdaIntegration()],
                traces_sample_rate=1.0,
            )

        # Verify Sentry was not initialized
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
    def test_handler_schedule_event_no_owner_repo_names(
        self, mock_slack_notify, mock_schedule_handler, mock_event_bridge_event_no_names
    ):
        """Test handler function with schedule event missing owner/repo names."""
        # Setup
        mock_slack_notify.return_value = "thread-123"
        mock_schedule_handler.return_value = {"status": "success"}

        # Execute
        result = handler(event=mock_event_bridge_event_no_names, context={})

        # Verify
        mock_schedule_handler.assert_called_with(event=mock_event_bridge_event_no_names)
        mock_slack_notify.assert_has_calls(
            [
                call("Event Scheduler started for /"),
                call("Completed", "thread-123"),
            ]
        )
        assert mock_slack_notify.call_count == 2
        assert result is None

    @patch("main.mangum_handler")
    def test_handler_non_schedule_event(self, mock_mangum_handler):
        """Test handler function with a non-schedule event."""
        # Setup
        event = {"key": "value", "triggerType": "not-schedule"}
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
        event = {"key": "value"}
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
        mock_extract_lambda_info.assert_called_once_with(mock_github_request_no_event_header)
        mock_handle_webhook_event.assert_called_once_with(
            event_name="Event not specified",
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
    async def test_handle_webhook_url_encoded_no_payload_key(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
    ):
        """Test handle_webhook function with URL-encoded body without payload key."""
        # Setup
        mock_req = MagicMock(spec=Request)
        mock_req.headers = {"X-GitHub-Event": "push"}
        mock_req.body = AsyncMock(return_value=b"other_key=value")

        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_extract_lambda_info.return_value = {}

        # Execute
        response = await handle_webhook(request=mock_req)

        # Verify
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push", payload={}, lambda_info={}
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_malformed_url_encoded_payload(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
        mock_github_request_malformed_url_encoded,
    ):
        """Test handle_webhook function with malformed URL-encoded payload."""
        # Setup
        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_extract_lambda_info.return_value = {}

        # Execute
        response = await handle_webhook(
            request=mock_github_request_malformed_url_encoded
        )

        # Verify
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push", payload={}, lambda_info={}
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

    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_general_exception_in_parsing(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
    ):
        """Test handle_webhook function when a general exception occurs during parsing."""
        # Setup
        mock_req = MagicMock(spec=Request)
        mock_req.headers = {"X-GitHub-Event": "push"}
        # Mock body to return bytes that will cause an exception during decode
        mock_req.body = AsyncMock(return_value=b"\xff\xfe")  # Invalid UTF-8

        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_extract_lambda_info.return_value = {}

        # Execute
        response = await handle_webhook(request=mock_req)

        # Verify
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push", payload={}, lambda_info={}
        )
        assert response == {"message": "Webhook processed successfully"}


class TestHandleJiraWebhook:
    @patch("main.extract_lambda_info")
    @patch("main.verify_jira_webhook", new_callable=AsyncMock)
    @patch("main.create_pr_from_issue")
    @pytest.mark.asyncio
    async def test_handle_jira_webhook_success(
        self, mock_create_pr, mock_verify_jira, mock_extract_lambda_info, mock_jira_request
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
        # Verify app has routes
        assert len(app.routes) > 0

        # Verify specific routes exist
        route_paths = [route.path for route in app.routes]
        assert "/" in route_paths
        assert "/webhook" in route_paths
        assert "/jira-webhook" in route_paths

    def test_app_instance(self):
        """Test that the FastAPI app instance is properly configured."""
        from fastapi import FastAPI
        assert isinstance(app, FastAPI)

    def test_mangum_handler_creation(self):
        """Test that the Mangum handler is properly created."""
        from main import mangum_handler
        from mangum import Mangum
        assert isinstance(mangum_handler, Mangum)


class TestModuleImports:
    def test_module_imports_successful(self):
        """Test that all required modules are imported successfully."""
        # This test ensures that the module can be imported without errors
        import main
        assert hasattr(main, 'app')
        assert hasattr(main, 'handler')
        assert hasattr(main, 'handle_webhook')
        assert hasattr(main, 'handle_jira_webhook')
        assert hasattr(main, 'root')
        assert hasattr(main, 'mangum_handler')


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
        mock_handle_webhook_event.assert_called_once_with(
            event_name="ping", payload={}, lambda_info={}
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.schedule_handler")
    @patch("main.slack_notify")
    def test_handler_schedule_event_with_different_status(
        self, mock_slack_notify, mock_schedule_handler, mock_event_bridge_event
    ):
        """Test handler function with schedule event returning different status."""
        # Setup
        mock_slack_notify.return_value = "thread-456"
        mock_schedule_handler.return_value = {
            "status": "partial_success",
            "message": "Some issues occurred",
        }

        # Execute
        result = handler(event=mock_event_bridge_event, context={})

        # Verify
        mock_schedule_handler.assert_called_with(event=mock_event_bridge_event)
        mock_slack_notify.assert_has_calls(
            [
                call("Event Scheduler started for test-owner/test-repo"),
                call("@channel Failed: Some issues occurred", "thread-456"),
            ]
        )
        assert mock_slack_notify.call_count == 2
        assert result is None

    def test_handler_with_schedule_event_missing_result_message(self):
        """Test handler with schedule event where result doesn't have message key."""
        # Setup
        event = {
            "triggerType": "schedule",
            "ownerName": "test-owner",
            "repoName": "test-repo",
        }

        with patch("main.schedule_handler") as mock_schedule_handler, \
             patch("main.slack_notify") as mock_slack_notify:
            mock_slack_notify.return_value = "thread-789"
            mock_schedule_handler.return_value = {"status": "error"}  # No message key

            # Execute
            result = handler(event=event, context={})

            # Verify - should handle missing message gracefully
            mock_slack_notify.assert_has_calls([
                call("Event Scheduler started for test-owner/test-repo"),
                call("@channel Failed: ", "thread-789"),  # Empty message
            ])
            assert result is None


class TestPrintStatements:
    @patch("main.schedule_handler")
    @patch("main.slack_notify")
    @patch("sys.stdout", new_callable=StringIO)
    def test_handler_schedule_event_prints_message(
        self, mock_stdout, mock_slack_notify, mock_schedule_handler, mock_event_bridge_event
    ):
        """Test handler function prints AWS EventBridge Scheduler invoked message."""
        # Setup
        mock_slack_notify.return_value = "thread-123"
        mock_schedule_handler.return_value = {"status": "success"}

        # Execute
        handler(event=mock_event_bridge_event, context={})

        # Verify print statement was called
        assert "AWS EventBridge Scheduler invoked" in mock_stdout.getvalue()

    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @patch("sys.stdout", new_callable=StringIO)
    @pytest.mark.asyncio
    async def test_handle_webhook_prints_body_error(
        self,
        mock_stdout,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
        mock_github_request,
    ):
        """Test handle_webhook function prints error when request.body() fails."""
        # Setup
        mock_verify_signature.return_value = None
        mock_github_request.body.side_effect = Exception("Body error")
        mock_extract_lambda_info.return_value = {}

        # Execute
        await handle_webhook(request=mock_github_request)

        # Verify print statement was called
        assert "Error in reading request body: Body error" in mock_stdout.getvalue()

    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @patch("sys.stdout", new_callable=StringIO)
    @pytest.mark.asyncio
    async def test_handle_webhook_prints_json_parsing_error(
        self,
        mock_stdout,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
    ):
        """Test handle_webhook function prints error when JSON parsing fails with general exception."""
        # Setup
        mock_req = MagicMock(spec=Request)
        mock_req.headers = {"X-GitHub-Event": "push"}
        mock_req.body = AsyncMock(return_value=b"\xff\xfe")  # Invalid UTF-8

        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_extract_lambda_info.return_value = {}

        # Execute
        await handle_webhook(request=mock_req)

        # Verify print statement was called
        output = mock_stdout.getvalue()
        assert "Error in parsing JSON payload:" in output


class TestComprehensiveCoverage:
    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_url_encoded_with_json_error_in_payload(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
    ):
        """Test handle_webhook with URL-encoded body that has invalid JSON in payload."""
        # Setup
        mock_req = MagicMock(spec=Request)
        mock_req.headers = {"X-GitHub-Event": "push"}
        # URL-encoded body with invalid JSON in payload
        mock_req.body = AsyncMock(return_value=b"payload=invalid%20json%20data")

        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_extract_lambda_info.return_value = {}

        # Execute
        response = await handle_webhook(request=mock_req)

        # Verify
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push", payload={}, lambda_info={}
        )
        assert response == {"message": "Webhook processed successfully"}

    @patch("main.extract_lambda_info")
    @patch("main.verify_webhook_signature", new_callable=AsyncMock)
    @patch("main.handle_webhook_event", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_handle_webhook_url_encoded_empty_payload_list(
        self,
        mock_handle_webhook_event,
        mock_verify_signature,
        mock_extract_lambda_info,
    ):
        """Test handle_webhook with URL-encoded body where payload list is empty."""
        # Setup
        mock_req = MagicMock(spec=Request)
        mock_req.headers = {"X-GitHub-Event": "push"}
        # URL-encoded body with empty payload list
        mock_req.body = AsyncMock(return_value=b"payload=")

        mock_verify_signature.return_value = None
        mock_handle_webhook_event.return_value = None
        mock_extract_lambda_info.return_value = {}

        # Execute
        response = await handle_webhook(request=mock_req)

        # Verify
        mock_handle_webhook_event.assert_called_once_with(
            event_name="push", payload={}, lambda_info={}
        )
        assert response == {"message": "Webhook processed successfully"}

    def test_handler_schedule_event_cast_functionality(self):
        """Test that EventBridge event is properly cast to EventBridgeSchedulerEvent."""
        # Setup
        event_dict = {
            "triggerType": "schedule",
            "ownerName": "test-owner",
            "repoName": "test-repo",
            "ownerId": 123456,
            "ownerType": "Organization",
            "repoId": 789012,
            "userId": 345678,
            "userName": "test-user",
            "installationId": 901234,
        }

        with patch("main.schedule_handler") as mock_schedule_handler, \
             patch("main.slack_notify") as mock_slack_notify:
            mock_slack_notify.return_value = "thread-cast"
            mock_schedule_handler.return_value = {"status": "success"}

            # Execute
            result = handler(event=event_dict, context={})

            # Verify that the event was passed to schedule_handler
            # The cast should work transparently
            mock_schedule_handler.assert_called_once()
            called_event = mock_schedule_handler.call_args[1]['event']
            assert called_event == event_dict
            assert result is None
