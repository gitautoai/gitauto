# Standard imports
from unittest.mock import patch, MagicMock, AsyncMock, call

# Third-party imports
import pytest

# Local imports
from services.webhook.webhook_handler import handle_webhook_event


@pytest.fixture
def mock_installation_payload():
    """Mock payload for installation events."""
    return {
        "action": "created",
        "installation": {
            "id": 12345,
            "account": {
                "id": 67890,
                "login": "test-org",
                "type": "Organization"
            }
        },
        "sender": {
            "id": 11111,
            "login": "test-user"
        }
    }


@pytest.fixture
def mock_issue_payload():
    """Mock payload for issue events."""
    return {
        "action": "opened",
        "issue": {
            "id": 123,
            "number": 456,
            "title": "Test Issue",
            "body": "Test issue body"
        },
        "repository": {
            "id": 789,
            "name": "test-repo",
            "owner": {
                "id": 67890,
                "login": "test-org",
                "type": "Organization"
            }
        },
        "installation": {
            "id": 12345
        }
    }


@pytest.fixture
def mock_pull_request_payload():
    """Mock payload for pull request events."""
    return {
        "action": "opened",
        "pull_request": {
            "id": 123,
            "number": 456,
            "title": "Test PR",
            "body": "Resolves #789",
            "merged_at": None,
            "head": {
                "ref": "gitauto/issue-789"
            },
            "user": {
                "login": "gitauto-ai[bot]"
            }
        },
        "repository": {
            "id": 789,
            "name": "test-repo",
            "owner": {
                "id": 67890,
                "login": "test-org",
                "type": "Organization"
            }
        },
        "sender": {
            "id": 11111,
            "login": "test-user"
        }
    }


@pytest.fixture
def mock_check_run_payload():
    """Mock payload for check run events."""
    return {
        "action": "completed",
        "check_run": {
            "id": 123,
            "name": "test-check",
            "conclusion": "failure"
        },
        "repository": {
            "id": 789,
            "name": "test-repo"
        }
    }


@pytest.fixture
def mock_workflow_run_payload():
    """Mock payload for workflow run events."""
    return {
        "action": "completed",
        "workflow_run": {
            "id": 123,
            "conclusion": "success",
            "head_branch": "main"
        },
        "repository": {
            "id": 789,
            "name": "test-repo",
            "owner": {
                "id": 67890,
                "login": "test-org"
            }
        },
        "installation": {
            "id": 12345
        },
        "sender": {
            "login": "test-user"
        }
    }


class TestHandleWebhookEvent:
    async def test_handle_webhook_event_no_action(self):
        """Test handling webhook event with no action."""
        # Setup
        event_name = "push"
        payload = {"ref": "refs/heads/main"}
        
        # Execute
        result = await handle_webhook_event(event_name, payload)
        
        # Verify - should return None for events without action
        assert result is None

    @patch("services.webhook.webhook_handler.slack_notify")
    @patch("services.webhook.webhook_handler.handle_installation_created")
    async def test_installation_created(
        self, mock_handle_installation, mock_slack_notify, mock_installation_payload
    ):
        """Test installation created event."""
        # Setup
        mock_handle_installation.return_value = None
        
        # Execute
        await handle_webhook_event("installation", mock_installation_payload)
        
        # Verify
        mock_slack_notify.assert_called_once_with(
            "🎉 New installation by `test-user` for `test-org`"
        )
        mock_handle_installation.assert_called_once_with(payload=mock_installation_payload)

    @patch("services.webhook.webhook_handler.slack_notify")
    @patch("services.webhook.webhook_handler.delete_installation")
    @patch("services.webhook.webhook_handler.get_user")
    @patch("services.webhook.webhook_handler.get_first_name")
    @patch("services.webhook.webhook_handler.send_email")
    @patch("services.webhook.webhook_handler.get_uninstall_email_text")
    @patch("services.webhook.webhook_handler.get_schedulers_by_owner_id")
    @patch("services.webhook.webhook_handler.delete_scheduler")
    async def test_installation_deleted(
        self,
        mock_delete_scheduler,
        mock_get_schedulers,
        mock_get_email_text,
        mock_send_email,
        mock_get_first_name,
        mock_get_user,
        mock_delete_installation,
        mock_slack_notify,
        mock_installation_payload
    ):
        """Test installation deleted event."""
        # Setup
        mock_installation_payload["action"] = "deleted"
        mock_get_user.return_value = {"email": "test@example.com", "user_name": "Test User"}
        mock_get_first_name.return_value = "Test"
        mock_get_email_text.return_value = ("Subject", "Email body")
        mock_get_schedulers.return_value = ["schedule1", "schedule2"]
        
        # Execute
        await handle_webhook_event("installation", mock_installation_payload)
        
        # Verify
        mock_slack_notify.assert_called_once_with(
            ":skull: Installation deleted by `test-user` for `test-org`"
        )
        mock_delete_installation.assert_called_once_with(
            installation_id=12345,
            user_id=11111,
            user_name="test-user"
        )
        mock_get_user.assert_called_once_with(11111)
        mock_send_email.assert_called_once_with(
            to="test@example.com", subject="Subject", text="Email body"
        )
        mock_get_schedulers.assert_called_once_with(67890)
        assert mock_delete_scheduler.call_count == 2
        mock_delete_scheduler.assert_any_call("schedule1")
        mock_delete_scheduler.assert_any_call("schedule2")

    @patch("services.webhook.webhook_handler.slack_notify")
    @patch("services.webhook.webhook_handler.delete_installation")
    @patch("services.webhook.webhook_handler.get_user")
    @patch("services.webhook.webhook_handler.get_schedulers_by_owner_id")
    @patch("services.webhook.webhook_handler.delete_scheduler")
    async def test_installation_deleted_no_user_email(
        self,
        mock_delete_scheduler,
        mock_get_schedulers,
        mock_get_user,
        mock_delete_installation,
        mock_slack_notify,
        mock_installation_payload
    ):
        """Test installation deleted event when user has no email."""
        # Setup
        mock_installation_payload["action"] = "deleted"
        mock_get_user.return_value = None  # No user found
        mock_get_schedulers.return_value = []
        
        # Execute
        await handle_webhook_event("installation", mock_installation_payload)
        
        # Verify
        mock_slack_notify.assert_called_once()
        mock_delete_installation.assert_called_once()
        mock_get_user.assert_called_once_with(11111)

    @patch("services.webhook.webhook_handler.slack_notify")
    @patch("services.webhook.webhook_handler.unsuspend_installation")
    async def test_installation_unsuspended(
        self, mock_unsuspend_installation, mock_slack_notify, mock_installation_payload
    ):
        """Test installation unsuspended event."""
        # Setup
        mock_installation_payload["action"] = "unsuspend"
        
        # Execute
        await handle_webhook_event("installation", mock_installation_payload)
        
        # Verify
        mock_slack_notify.assert_called_once_with(
            "🎉 Installation unsuspended by `test-user` for `test-org`"
        )
        mock_unsuspend_installation.assert_called_once_with(installation_id=12345)

    @patch("services.webhook.webhook_handler.handle_installation_repos_added")
    async def test_installation_repositories_added(
        self, mock_handle_repos_added, mock_installation_payload
    ):
        """Test installation repositories added event."""
        # Setup
        mock_installation_payload["action"] = "added"
        
        # Execute
        await handle_webhook_event("installation_repositories", mock_installation_payload)
        
        # Verify
        mock_handle_repos_added.assert_called_once_with(payload=mock_installation_payload)

    @patch("services.webhook.webhook_handler.create_pr_from_issue")
    async def test_issues_labeled(self, mock_create_pr, mock_issue_payload):
        """Test issues labeled event."""
        # Setup
        mock_issue_payload["action"] = "labeled"
        
        # Execute
        await handle_webhook_event("issues", mock_issue_payload)
        
        # Verify
        mock_create_pr.assert_called_once_with(
            payload=mock_issue_payload, trigger="issue_label", input_from="github"
        )

    @patch("services.webhook.webhook_handler.create_gitauto_button_comment")
    async def test_issues_opened(self, mock_create_comment, mock_issue_payload):
        """Test issues opened event."""
        # Setup
        mock_issue_payload["action"] = "opened"
        
        # Execute
        await handle_webhook_event("issues", mock_issue_payload)
        
        # Verify
        mock_create_comment.assert_called_once_with(payload=mock_issue_payload)

    @patch("services.webhook.webhook_handler.handle_pr_checkbox_trigger")
    async def test_issue_comment_edited(self, mock_handle_checkbox, mock_issue_payload):
        """Test issue comment edited event."""
        # Setup
        mock_issue_payload["action"] = "edited"
        mock_issue_payload["comment"] = {"body": "Some comment"}
        
        # Execute
        await handle_webhook_event("issue_comment", mock_issue_payload)
        
        # Verify
        mock_handle_checkbox.assert_called_once_with(payload=mock_issue_payload)

    @patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto")
    @patch("services.webhook.webhook_handler.handle_pr_checkbox_trigger")
    @patch("services.webhook.webhook_handler.create_pr_from_issue")
    async def test_issue_comment_edited_with_production_checkbox(
        self, mock_create_pr, mock_handle_checkbox, mock_issue_payload
    ):
        """Test issue comment edited with production checkbox."""
        # Setup
        mock_issue_payload["action"] = "edited"
        mock_issue_payload["comment"] = {"body": "- [x] Generate PR"}
        
        # Execute
        await handle_webhook_event("issue_comment", mock_issue_payload)
        
        # Verify
        mock_handle_checkbox.assert_called_once_with(payload=mock_issue_payload)
        mock_create_pr.assert_called_once_with(
            payload=mock_issue_payload, trigger="issue_comment", input_from="github"
        )

    @patch("services.webhook.webhook_handler.GITHUB_CHECK_RUN_FAILURES", ["failure", "cancelled"])
    @patch("services.webhook.webhook_handler.handle_check_run")
    async def test_check_run_completed_failure(
        self, mock_handle_check_run, mock_check_run_payload
    ):
        """Test check run completed with failure conclusion."""
        # Execute
        await handle_webhook_event("check_run", mock_check_run_payload)
        
        # Verify
        mock_handle_check_run.assert_called_once_with(payload=mock_check_run_payload)

    @patch("services.webhook.webhook_handler.GITHUB_CHECK_RUN_FAILURES", ["failure", "cancelled"])
    @patch("services.webhook.webhook_handler.handle_check_run")
    async def test_check_run_completed_success(
        self, mock_handle_check_run, mock_check_run_payload
    ):
        """Test check run completed with success conclusion."""
        # Setup
        mock_check_run_payload["check_run"]["conclusion"] = "success"
        
        # Execute
        await handle_webhook_event("check_run", mock_check_run_payload)
        
        # Verify - should not handle successful check runs
        mock_handle_check_run.assert_not_called()

    @patch("services.webhook.webhook_handler.create_pr_checkbox_comment")
    @patch("services.webhook.webhook_handler.write_pr_description")
    @patch("services.webhook.webhook_handler.handle_screenshot_comparison")
    async def test_pull_request_opened(
        self,
        mock_handle_screenshot,
        mock_write_description,
        mock_create_checkbox,
        mock_pull_request_payload
    ):
        """Test pull request opened event."""
        # Execute
        await handle_webhook_event("pull_request", mock_pull_request_payload)
        
        # Verify
        mock_create_checkbox.assert_called_once_with(payload=mock_pull_request_payload)
        mock_write_description.assert_called_once_with(payload=mock_pull_request_payload)
        mock_handle_screenshot.assert_called_once_with(payload=mock_pull_request_payload)

    @patch("services.webhook.webhook_handler.create_pr_checkbox_comment")
    @patch("services.webhook.webhook_handler.handle_screenshot_comparison")
    async def test_pull_request_synchronized(
        self, mock_handle_screenshot, mock_create_checkbox, mock_pull_request_payload
    ):
        """Test pull request synchronized event."""
        # Setup
        mock_pull_request_payload["action"] = "synchronize"
        
        # Execute
        await handle_webhook_event("pull_request", mock_pull_request_payload)
        
        # Verify
        mock_create_checkbox.assert_called_once_with(payload=mock_pull_request_payload)
        mock_handle_screenshot.assert_called_once_with(payload=mock_pull_request_payload)

    @patch("services.webhook.webhook_handler.handle_coverage_report")
    async def test_workflow_run_completed_success(
        self, mock_handle_coverage, mock_workflow_run_payload
    ):
        """Test workflow run completed with success."""
        # Execute
        await handle_webhook_event("workflow_run", mock_workflow_run_payload)
        
        # Verify
        mock_handle_coverage.assert_called_once_with(
            owner_id=67890,
            owner_name="test-org",
            repo_id=789,
            repo_name="test-repo",
            installation_id=12345,
            run_id=123,
            head_branch="main",
            user_name="test-user"
        )

    @patch("services.webhook.webhook_handler.handle_coverage_report")
    async def test_workflow_run_completed_failure(
        self, mock_handle_coverage, mock_workflow_run_payload
    ):
        """Test workflow run completed with failure."""
        # Setup
        mock_workflow_run_payload["workflow_run"]["conclusion"] = "failure"
        
        # Execute
        await handle_webhook_event("workflow_run", mock_workflow_run_payload)
        
        # Verify - should not handle failed workflow runs
        mock_handle_coverage.assert_not_called()

    async def test_unknown_event_type(self):
        """Test handling unknown event type."""
        # Setup
        payload = {"action": "unknown_action"}
        
        # Execute
        result = await handle_webhook_event("unknown_event", payload)
        
        # Verify - should return None for unknown events
        assert result is None

    async def test_known_event_unknown_action(self):
        """Test handling known event with unknown action."""
        # Setup
        payload = {"action": "unknown_action"}
        
        # Execute
        result = await handle_webhook_event("issues", payload)
        
        # Verify - should return None for unknown actions
        assert result is None

    async def test_pull_request_closed_not_merged(self, mock_pull_request_payload):
        """Test pull request closed event when PR is not merged."""
        # Setup
        mock_pull_request_payload["action"] = "closed"
        mock_pull_request_payload["pull_request"]["merged_at"] = None
        
        # Execute
        result = await handle_webhook_event("pull_request", mock_pull_request_payload)
        
        # Verify - should return early when not merged
        assert result is None

    async def test_pull_request_closed_no_pull_request(self):
        """Test pull request closed event with missing pull_request data."""
        # Setup
        payload = {"action": "closed"}
        
        # Execute
        result = await handle_webhook_event("pull_request", payload)
        
        # Verify - should return early when no pull_request
        assert result is None
