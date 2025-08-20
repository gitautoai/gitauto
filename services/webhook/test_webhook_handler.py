# Standard imports
from unittest.mock import patch, MagicMock, AsyncMock

# Third party imports
import pytest

# Local imports
from services.webhook.webhook_handler import handle_webhook_event


class TestHandleWebhookEvent:
    """Test cases for handle_webhook_event function."""

    @pytest.fixture
    def mock_dependencies(self):
        """Fixture to mock all dependencies for webhook handler."""
        with patch.multiple(
            "services.webhook.webhook_handler",
            create_log_group=MagicMock(),
            switch_lambda_log_group=MagicMock(),
            slack_notify=MagicMock(),
            handle_installation_created=AsyncMock(),
            delete_installation=MagicMock(),
            get_user=MagicMock(),
            send_email=MagicMock(),
            get_schedulers_by_owner_id=MagicMock(),
            delete_scheduler=MagicMock(),
            create_pr_from_issue=AsyncMock(),
            create_gitauto_button_comment=MagicMock(),
            handle_pr_checkbox_trigger=AsyncMock(),
            handle_check_run=MagicMock(),
            create_pr_checkbox_comment=MagicMock(),
            write_pr_description=MagicMock(),
            handle_screenshot_comparison=AsyncMock(),
            handle_coverage_report=AsyncMock(),
        ) as mocks:
            yield mocks

    @pytest.mark.asyncio
    async def test_handle_webhook_event_with_repository_log_group_creation(self, mock_dependencies):
        """Test that log group is created when repository info is available."""
        # Setup
        event_name = "issues"
        payload = {
            "action": "opened",
            "repository": {
                "owner": {"login": "testowner"},
                "name": "testrepo"
            }
        }

        # Execute
        await handle_webhook_event(event_name, payload)

        # Assert
        mock_dependencies["create_log_group"].assert_called_once_with("testowner", "testrepo")
        mock_dependencies["switch_lambda_log_group"].assert_called_once_with("testowner", "testrepo")

    @pytest.mark.asyncio
    async def test_handle_webhook_event_without_repository(self, mock_dependencies):
        """Test that log group creation is skipped when no repository info."""
        # Setup
        event_name = "ping"
        payload = {"action": "ping"}

        # Execute
        await handle_webhook_event(event_name, payload)

        # Assert
        mock_dependencies["create_log_group"].assert_not_called()
        mock_dependencies["switch_lambda_log_group"].assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_webhook_event_no_action(self, mock_dependencies):
        """Test that function returns early when no action is provided."""
        # Setup
        event_name = "issues"
        payload = {"repository": {"owner": {"login": "owner"}, "name": "repo"}}

        # Execute
        await handle_webhook_event(event_name, payload)

        # Assert - only log group functions should be called
        mock_dependencies["create_log_group"].assert_called_once()
        mock_dependencies["switch_lambda_log_group"].assert_called_once()
        # No other handlers should be called
        mock_dependencies["handle_installation_created"].assert_not_called()

    @pytest.mark.asyncio
    async def test_installation_created_event(self, mock_dependencies):
        """Test installation created event handling."""
        # Setup
        event_name = "installation"
        payload = {
            "action": "created",
            "installation": {"account": {"login": "testowner"}},
            "sender": {"login": "testuser"},
            "repository": {"owner": {"login": "testowner"}, "name": "testrepo"}
        }

        # Execute
        await handle_webhook_event(event_name, payload)

        # Assert
        mock_dependencies["slack_notify"].assert_called_once_with(
            "🎉 New installation by `testuser` for `testowner`"
        )
        mock_dependencies["handle_installation_created"].assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_issues_labeled_event(self, mock_dependencies):
        """Test issues labeled event handling."""
        # Setup
        event_name = "issues"
        payload = {
            "action": "labeled",
            "repository": {"owner": {"login": "testowner"}, "name": "testrepo"}
        }

        # Execute
        await handle_webhook_event(event_name, payload)

        # Assert
        mock_dependencies["create_pr_from_issue"].assert_called_once_with(
            payload=payload, trigger="issue_label", input_from="github"
        )

    @pytest.mark.asyncio
    async def test_issues_opened_event(self, mock_dependencies):
        """Test issues opened event handling."""
        # Setup
        event_name = "issues"
        payload = {
            "action": "opened",
            "repository": {"owner": {"login": "testowner"}, "name": "testrepo"}
        }

        # Execute
        await handle_webhook_event(event_name, payload)

        # Assert
        mock_dependencies["create_gitauto_button_comment"].assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_pull_request_opened_event(self, mock_dependencies):
        """Test pull request opened event handling."""
        # Setup
        event_name = "pull_request"
        payload = {
            "action": "opened",
            "repository": {"owner": {"login": "testowner"}, "name": "testrepo"}
        }

        # Execute
        await handle_webhook_event(event_name, payload)

        # Assert
        mock_dependencies["create_pr_checkbox_comment"].assert_called_once_with(payload=payload)
        mock_dependencies["write_pr_description"].assert_called_once_with(payload=payload)
        mock_dependencies["handle_screenshot_comparison"].assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_workflow_run_completed_success(self, mock_dependencies):
        """Test workflow run completed event with success conclusion."""
        # Setup
        event_name = "workflow_run"
        payload = {
            "action": "completed",
            "workflow_run": {
                "conclusion": "success",
                "id": 123,
                "head_branch": "main"
            },
            "repository": {
                "owner": {"id": 456, "login": "testowner"},
                "id": 789,
                "name": "testrepo"
            },
            "installation": {"id": 101112},
            "sender": {"login": "testuser"}
        }

        # Execute
        await handle_webhook_event(event_name, payload)

        # Assert
        mock_dependencies["handle_coverage_report"].assert_called_once_with(
            owner_id=456,
            owner_name="testowner",
            repo_id=789,
            repo_name="testrepo",
            installation_id=101112,
            run_id=123,
            head_branch="main",
            user_name="testuser"
        )

    @pytest.mark.asyncio
    async def test_handle_exceptions_decorator_behavior(self, mock_dependencies):
        """Test that the handle_exceptions decorator works correctly."""
        # Setup - make one of the mocked functions raise an exception
        mock_dependencies["create_log_group"].side_effect = Exception("Test exception")
        
        event_name = "issues"
        payload = {
            "action": "opened",
            "repository": {"owner": {"login": "testowner"}, "name": "testrepo"}
        }

        # Execute - should not raise exception due to handle_exceptions decorator
        result = await handle_webhook_event(event_name, payload)

        # Assert - function should return None (default_return_value) and not raise
        assert result is None
        mock_dependencies["create_log_group"].assert_called_once()