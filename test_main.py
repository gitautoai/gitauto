# Standard imports
import json
import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

# Local imports
import main
# Third-party imports
import pytest
from fastapi import Request


class TestHandleWebhook:
    """Test the handle_webhook function."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        request = MagicMock(spec=Request)
        request.headers = {"X-GitHub-Event": "push"}
        request.body = AsyncMock(return_value=b'{"test": "data"}')
        return request

    @pytest.fixture
    def mock_verify_webhook_signature(self):
        """Mock the verify_webhook_signature function."""
        with patch("main.verify_webhook_signature") as mock:
            async_mock = AsyncMock(return_value=None)
            mock.side_effect = async_mock
            yield mock

    @pytest.fixture
    def mock_handle_webhook_event(self):
        """Mock the handle_webhook_event function."""
        with patch("main.handle_webhook_event", new_callable=AsyncMock) as mock:
            mock.return_value = None
            yield mock

    @pytest.fixture
    def mock_extract_lambda_info(self):
        """Mock the extract_lambda_info function."""
        with patch("main.extract_lambda_info") as mock:
            mock.return_value = {"function_name": "test-function"}
            yield mock

    @pytest.mark.asyncio
    async def test_handle_webhook_success(
        self,
        mock_request,
        mock_verify_webhook_signature,
        mock_handle_webhook_event,
        mock_extract_lambda_info,
    ):
        """Test successful webhook handling."""
        result = await main.handle_webhook(mock_request)

        assert result == {"message": "Webhook processed successfully"}
        mock_verify_webhook_signature.assert_called_once()
        mock_handle_webhook_event.assert_called_once()
        mock_extract_lambda_info.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_handle_webhook_with_url_encoded_payload(
        self,
        mock_verify_webhook_signature,
        mock_handle_webhook_event,
        mock_extract_lambda_info,
    ):
        """Test webhook handling with URL-encoded payload."""
        request = MagicMock(spec=Request)
        request.headers = {"X-GitHub-Event": "push"}
        # Simulate URL-encoded payload
        url_encoded_data = 'payload={"test": "data"}'
        request.body = AsyncMock(return_value=url_encoded_data.encode())

        result = await main.handle_webhook(request)

        assert result == {"message": "Webhook processed successfully"}
        mock_verify_webhook_signature.assert_called_once()
        mock_handle_webhook_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_webhook_with_invalid_json(
        self,
        mock_verify_webhook_signature,
        mock_handle_webhook_event,
        mock_extract_lambda_info,
    ):
        """Test webhook handling with invalid JSON payload."""
        request = MagicMock(spec=Request)
        request.headers = {"X-GitHub-Event": "push"}
        request.body = AsyncMock(return_value=b"invalid json")

        result = await main.handle_webhook(request)

        assert result == {"message": "Webhook processed successfully"}
        mock_verify_webhook_signature.assert_called_once()
        mock_handle_webhook_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_webhook_body_read_error(
        self,
        mock_verify_webhook_signature,
        mock_handle_webhook_event,
        mock_extract_lambda_info,
    ):
        """Test webhook handling when request body read fails."""
        request = MagicMock(spec=Request)
        request.headers = {"X-GitHub-Event": "push"}
        request.body = AsyncMock(side_effect=Exception("Body read error"))

        result = await main.handle_webhook(request)

        assert result == {"message": "Webhook processed successfully"}
        mock_verify_webhook_signature.assert_called_once()
        mock_handle_webhook_event.assert_called_once()


class TestHandleJiraWebhook:
    """Test the handle_jira_webhook function."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        return MagicMock(spec=Request)

    @pytest.fixture
    def mock_verify_jira_webhook(self):
        """Mock the verify_jira_webhook function."""
        with patch("main.verify_jira_webhook", new_callable=AsyncMock) as mock:
            mock.return_value = {"test": "payload"}
            yield mock

    @pytest.fixture
    def mock_create_pr_from_issue(self):
        """Mock the create_pr_from_issue function."""
        with patch("main.create_pr_from_issue") as mock:
            yield mock

    @pytest.fixture
    def mock_extract_lambda_info(self):
        """Mock the extract_lambda_info function."""
        with patch("main.extract_lambda_info") as mock:
            mock.return_value = {"function_name": "test-function"}
            yield mock

    @pytest.mark.asyncio
    async def test_handle_jira_webhook_success(
        self,
        mock_request,
        mock_verify_jira_webhook,
        mock_create_pr_from_issue,
        mock_extract_lambda_info,
    ):
        """Test successful Jira webhook handling."""
        result = await main.handle_jira_webhook(mock_request)

        assert result == {"message": "Jira webhook processed successfully"}
        mock_verify_jira_webhook.assert_called_once_with(mock_request)
        mock_create_pr_from_issue.assert_called_once_with(
            payload={"test": "payload"},
            trigger="issue_comment",
            input_from="jira",
            lambda_info={"function_name": "test-function"},
        )


class TestSentryInitialization:
    """Test Sentry initialization based on environment."""

    def test_sentry_init_called_in_prod_environment(self):
        """Test that Sentry is initialized when ENV is 'prod'."""
        # Remove main module from cache if it exists
        if 'main' in sys.modules:
            del sys.modules['main']

        with patch("config.ENV", "prod"), patch("sentry_sdk.init") as mock_sentry_init:
            # Import main module which will trigger the initialization code
            import main

            # Verify Sentry initialization was called
            mock_sentry_init.assert_called_once()
            call_args = mock_sentry_init.call_args

            # Verify the arguments passed to sentry_sdk.init
            assert call_args[1]["environment"] == "prod"
            assert call_args[1]["traces_sample_rate"] == 1.0
            assert "dsn" in call_args[1]
            assert "integrations" in call_args[1]

    def test_sentry_init_not_called_in_dev_environment(self):
        """Test that Sentry is not initialized when ENV is 'dev'."""
        # Remove main module from cache if it exists
        if 'main' in sys.modules:
            del sys.modules['main']

        with patch("config.ENV", "dev"), patch("sentry_sdk.init") as mock_sentry_init:
            # Import main module which will trigger the initialization code
            import main

            # Verify Sentry initialization was not called
            mock_sentry_init.assert_not_called()

    def test_sentry_init_not_called_in_staging_environment(self):
        """Test that Sentry is not initialized when ENV is 'staging'."""
        # Remove main module from cache if it exists
        if 'main' in sys.modules:
            del sys.modules['main']

        with patch("config.ENV", "staging"), patch("sentry_sdk.init") as mock_sentry_init:
            # Import main module which will trigger the initialization code
            import main

            # Verify Sentry initialization was not called
            mock_sentry_init.assert_not_called()

    def test_sentry_init_not_called_in_test_environment(self):
        """Test that Sentry is not initialized when ENV is 'test'."""
        # Remove main module from cache if it exists
        if 'main' in sys.modules:
            del sys.modules['main']

        with patch("config.ENV", "test"), patch("sentry_sdk.init") as mock_sentry_init:
            # Import main module which will trigger the initialization code
            import main

            # Verify Sentry initialization was not called
            mock_sentry_init.assert_not_called()


class TestHandler:
    """Test the main handler function."""

    @pytest.fixture
    def mock_schedule_handler(self):
        """Mock the schedule_handler function."""
        with patch("main.schedule_handler") as mock:
            mock.return_value = {"status": "success"}
            yield mock

    @pytest.fixture
    def mock_slack_notify(self):
        """Mock the slack_notify function."""
        with patch("main.slack_notify") as mock:
            mock.return_value = "thread_ts_123"
            yield mock

    @pytest.fixture
    def mock_mangum_handler(self):
        """Mock the mangum_handler."""
        with patch("main.mangum_handler") as mock:
            mock.return_value = {"statusCode": 200}
            yield mock

    def test_handler_with_schedule_event_success(
        self, mock_schedule_handler, mock_slack_notify
    ):
        """Test handler with successful schedule event."""
        # Ensure mocks are configured correctly
        mock_schedule_handler.return_value = {"status": "success"}
        mock_slack_notify.return_value = "thread_ts_123"

        event = {
            "triggerType": "schedule",
            "ownerName": "test-owner",
            "repoName": "test-repo",
            "ownerId": 12345,
            "ownerType": "User",
            "repoId": 67890,
            "userId": 11111,
            "userName": "test-user",
            "installationId": 22222,
        }
        context = {}

        result = main.handler(event, context)

        assert result is None
        mock_slack_notify.assert_any_call("Event Scheduler started for test-owner/test-repo")
        mock_slack_notify.assert_any_call("Completed", "thread_ts_123")
        mock_schedule_handler.assert_called_once_with(event=event)

    def test_handler_with_schedule_event_failure(
        self, mock_schedule_handler, mock_slack_notify
    ):
        """Test handler with failed schedule event."""
        event = {
            "triggerType": "schedule",
            "ownerName": "test-owner",
            "repoName": "test-repo",
        }
        context = {}
        mock_schedule_handler.return_value = {
            "status": "error",
            "message": "Test error message",
        }

        result = main.handler(event, context)

        assert result is None
        mock_slack_notify.assert_any_call("Event Scheduler started for test-owner/test-repo")
        mock_slack_notify.assert_any_call(
            "@channel Failed: Test error message", "thread_ts_123"
        )
        mock_schedule_handler.assert_called_once_with(event=event)

    def test_handler_with_non_schedule_event(self, mock_mangum_handler):
        """Test handler with non-schedule event."""
        event = {"some": "data"}
        context = {"context": "data"}

        result = main.handler(event, context)

        assert result == {"statusCode": 200}
        mock_mangum_handler.assert_called_once_with(event=event, context=context)


    def test_handler_with_schedule_event_exception(
        self, mock_schedule_handler, mock_slack_notify
    ):
        """Test handler with schedule event that raises an exception."""
        event = {
            "triggerType": "schedule",
            "ownerName": "test-owner",
            "repoName": "test-repo",
        }
        context = {}
        mock_schedule_handler.side_effect = Exception("Test exception")

        result = main.handler(event, context)

        assert result is None
        mock_slack_notify.assert_any_call("Event Scheduler started for test-owner/test-repo")
        mock_slack_notify.assert_any_call("@channel Failed: Test exception", "thread_ts_123")
        mock_schedule_handler.assert_called_once_with(event=event)

class TestRoot:
    """Test the root endpoint."""

    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Test the root endpoint returns the product name."""
        with patch("main.PRODUCT_NAME", "Test Product"):
            result = await main.root()
            assert result == {"message": "Test Product"}
