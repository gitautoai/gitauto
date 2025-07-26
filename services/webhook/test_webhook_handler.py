from unittest.mock import patch, MagicMock, AsyncMock
import pytest

from services.webhook.webhook_handler import handle_webhook_event


class TestHandleWebhookEvent:
    @pytest.fixture
    def mock_slack_notify(self):
        with patch("services.webhook.webhook_handler.slack_notify") as mock:
            yield mock

    @pytest.fixture
    def mock_handle_installation_created(self):
        with patch("services.webhook.webhook_handler.handle_installation_created", new_callable=AsyncMock) as mock:
            yield mock

    @pytest.fixture
    def mock_delete_installation(self):
        with patch("services.webhook.webhook_handler.delete_installation") as mock:
            yield mock

    @pytest.fixture
    def mock_get_user(self):
        with patch("services.webhook.webhook_handler.get_user") as mock:
            yield mock

    @pytest.fixture
    def mock_get_first_name(self):
        with patch("services.webhook.webhook_handler.get_first_name") as mock:
            yield mock

    @pytest.fixture
    def mock_send_email(self):
        with patch("services.webhook.webhook_handler.send_email") as mock:
            yield mock

    @pytest.fixture
    def mock_get_uninstall_email_text(self):
        with patch("services.webhook.webhook_handler.get_uninstall_email_text") as mock:
            yield mock

    @pytest.fixture
    def mock_get_suspend_email_text(self):
        with patch("services.webhook.webhook_handler.get_suspend_email_text") as mock:
            yield mock

    @pytest.fixture
    def mock_unsuspend_installation(self):
        with patch("services.webhook.webhook_handler.unsuspend_installation") as mock:
            yield mock

    @pytest.fixture
    def mock_handle_installation_repos_added(self):
        with patch("services.webhook.webhook_handler.handle_installation_repos_added", new_callable=AsyncMock) as mock:
            yield mock

    @pytest.fixture
    def mock_create_pr_from_issue(self):
        with patch("services.webhook.webhook_handler.create_pr_from_issue", new_callable=AsyncMock) as mock:
            yield mock

    @pytest.fixture
    def mock_create_gitauto_button_comment(self):
        with patch("services.webhook.webhook_handler.create_gitauto_button_comment") as mock:
            yield mock

    @pytest.fixture
    def mock_handle_pr_checkbox_trigger(self):
        with patch("services.webhook.webhook_handler.handle_pr_checkbox_trigger", new_callable=AsyncMock) as mock:
            yield mock

    @pytest.fixture
    def mock_handle_check_run(self):
        with patch("services.webhook.webhook_handler.handle_check_run") as mock:
            yield mock

    @pytest.fixture
    def mock_create_pr_checkbox_comment(self):
        with patch("services.webhook.webhook_handler.create_pr_checkbox_comment") as mock:
            yield mock

    @pytest.fixture
    def mock_write_pr_description(self):
        with patch("services.webhook.webhook_handler.write_pr_description") as mock:
            yield mock

    @pytest.fixture
    def mock_handle_screenshot_comparison(self):
        with patch("services.webhook.webhook_handler.handle_screenshot_comparison", new_callable=AsyncMock) as mock:
            yield mock

    @pytest.fixture
    def mock_handle_pr_merged(self):
        with patch("services.webhook.webhook_handler.handle_pr_merged") as mock:
            yield mock

    @pytest.fixture
    def mock_update_issue_merged(self):
        with patch("services.webhook.webhook_handler.update_issue_merged") as mock:
            yield mock

    @pytest.fixture
    def mock_handle_review_run(self):
        with patch("services.webhook.webhook_handler.handle_review_run") as mock:
            yield mock

    @pytest.fixture
    def mock_handle_coverage_report(self):
        with patch("services.webhook.webhook_handler.handle_coverage_report") as mock:
            mock.return_value = AsyncMock()
            yield mock

    @pytest.mark.asyncio
    async def test_handle_webhook_event_no_action(self):
        payload = {"some": "data"}
        result = await handle_webhook_event("issues", payload)
        assert result is None

    @pytest.mark.asyncio
    async def test_installation_created(
        self, mock_slack_notify, mock_handle_installation_created
    ):
        payload = {
            "action": "created",
            "installation": {"account": {"login": "test-owner"}},
            "sender": {"login": "test-sender"}
        }
        
        await handle_webhook_event("installation", payload)
        
        mock_slack_notify.assert_called_once_with(
            "🎉 New installation by `test-sender` for `test-owner`"
        )
        mock_handle_installation_created.assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_installation_deleted_with_user_email(
        self, mock_slack_notify, mock_delete_installation, mock_get_user,
        mock_get_first_name, mock_send_email, mock_get_uninstall_email_text
    ):
        # Setup mocks
        mock_get_user.return_value = {"email": "test@example.com", "user_name": "John Doe"}
        mock_get_first_name.return_value = "John"
        mock_get_uninstall_email_text.return_value = ("Subject", "Email text")
        
        payload = {
            "action": "deleted",
            "installation": {"id": 123, "account": {"login": "test-owner"}},
            "sender": {"id": 456, "login": "test-sender"}
        }
        
        await handle_webhook_event("installation", payload)
        
        mock_slack_notify.assert_called_once_with(
            ":skull: Installation deleted by `test-sender` for `test-owner`"
        )
        mock_delete_installation.assert_called_once_with(
            installation_id=123,
            user_id=456,
            user_name="test-sender"
        )
        mock_get_user.assert_called_once_with(456)
        mock_get_first_name.assert_called_once_with("John Doe")
        mock_get_uninstall_email_text.assert_called_once_with("John")
        mock_send_email.assert_called_once_with(
            to="test@example.com",
            subject="Subject",
            text="Email text"
        )

    @pytest.mark.asyncio
    async def test_installation_deleted_without_user_email(
        self, mock_slack_notify, mock_delete_installation, mock_get_user,
        mock_send_email
    ):
        # Setup mocks - user has no email
        mock_get_user.return_value = {"user_name": "John Doe"}  # No email field
        
        payload = {
            "action": "deleted",
            "installation": {"id": 123, "account": {"login": "test-owner"}},
            "sender": {"id": 456, "login": "test-sender"}
        }
        
        await handle_webhook_event("installation", payload)
        
        mock_delete_installation.assert_called_once()
        mock_send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_installation_suspended_with_user_email(
        self, mock_slack_notify, mock_delete_installation, mock_get_user,
        mock_get_first_name, mock_send_email, mock_get_suspend_email_text
    ):
        # Setup mocks
        mock_get_user.return_value = {"email": "test@example.com", "user_name": "John Doe"}
        mock_get_first_name.return_value = "John"
        mock_get_suspend_email_text.return_value = ("Subject", "Email text")
        
        payload = {
            "action": "suspend",
            "installation": {"id": 123, "account": {"login": "test-owner"}},
            "sender": {"id": 456, "login": "test-sender"}
        }
        
        await handle_webhook_event("installation", payload)
        
        mock_slack_notify.assert_called_once_with(
            ":skull: Installation suspended by `test-sender` for `test-owner`"
        )
        mock_delete_installation.assert_called_once_with(
            installation_id=123,
            user_id=456,
            user_name="test-sender"
        )
        mock_get_suspend_email_text.assert_called_once_with("John")
        mock_send_email.assert_called_once_with(
            to="test@example.com",
            subject="Subject",
            text="Email text"
        )

    @pytest.mark.asyncio
    async def test_installation_unsuspended(
        self, mock_slack_notify, mock_unsuspend_installation
    ):
        payload = {
            "action": "unsuspend",
            "installation": {"id": 123, "account": {"login": "test-owner"}},
            "sender": {"login": "test-sender"}
        }
        
        await handle_webhook_event("installation", payload)
        
        mock_slack_notify.assert_called_once_with(
            "🎉 Installation unsuspended by `test-sender` for `test-owner`"
        )
        mock_unsuspend_installation.assert_called_once_with(installation_id=123)

    @pytest.mark.asyncio
    async def test_installation_repositories_added(
        self, mock_handle_installation_repos_added
    ):
        payload = {"action": "added"}
        
        await handle_webhook_event("installation_repositories", payload)
        
        mock_handle_installation_repos_added.assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_issues_labeled(self, mock_create_pr_from_issue):
        payload = {"action": "labeled"}
        
        await handle_webhook_event("issues", payload)
        
        mock_create_pr_from_issue.assert_called_once_with(
            payload=payload, trigger="issue_label", input_from="github"
        )

    @pytest.mark.asyncio
    async def test_issues_opened(self, mock_create_gitauto_button_comment):
        payload = {"action": "opened"}
        
        await handle_webhook_event("issues", payload)
        
        mock_create_gitauto_button_comment.assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_issue_comment_edited_with_checkbox(
        self, mock_handle_pr_checkbox_trigger, mock_create_pr_from_issue
    ):
        payload = {
            "action": "edited",
            "comment": {"body": "Some text\n- [x] Generate PR\nMore text"}
        }
        
        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            await handle_webhook_event("issue_comment", payload)
        
        mock_handle_pr_checkbox_trigger.assert_called_once_with(payload=payload)
        mock_create_pr_from_issue.assert_called_once_with(
            payload=payload, trigger="issue_comment", input_from="github"
        )

    @pytest.mark.asyncio
    async def test_issue_comment_edited_dev_environment(
        self, mock_handle_pr_checkbox_trigger, mock_create_pr_from_issue
    ):
        payload = {
            "action": "edited",
            "comment": {"body": "Some text\n- [x] Generate PR - dev\nMore text"}
        }
        
        with patch("services.webhook.webhook_handler.PRODUCT_ID", "dev"):
            await handle_webhook_event("issue_comment", payload)
        
        mock_create_pr_from_issue.assert_called_once_with(
            payload=payload, trigger="issue_comment", input_from="github"
        )

    @pytest.mark.asyncio
    async def test_check_run_completed_failure(self, mock_handle_check_run):
        payload = {
            "action": "completed",
            "check_run": {"conclusion": "failure"}
        }
        
        await handle_webhook_event("check_run", payload)
        
        mock_handle_check_run.assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_check_run_completed_success(self, mock_handle_check_run):
        payload = {
            "action": "completed",
            "check_run": {"conclusion": "success"}
        }
        
        await handle_webhook_event("check_run", payload)
        
        mock_handle_check_run.assert_not_called()

    @pytest.mark.asyncio
    async def test_pull_request_opened(
        self, mock_create_pr_checkbox_comment, mock_write_pr_description,
        mock_handle_screenshot_comparison
    ):
        payload = {"action": "opened"}
        
        await handle_webhook_event("pull_request", payload)
        
        mock_create_pr_checkbox_comment.assert_called_once_with(payload=payload)
        mock_write_pr_description.assert_called_once_with(payload=payload)
        mock_handle_screenshot_comparison.assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_pull_request_synchronized(
        self, mock_create_pr_checkbox_comment, mock_handle_screenshot_comparison
    ):
        payload = {"action": "synchronize"}
        
        await handle_webhook_event("pull_request", payload)
        
        mock_create_pr_checkbox_comment.assert_called_once_with(payload=payload)
        mock_handle_screenshot_comparison.assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_pull_request_closed_merged_gitauto_pr(
        self, mock_update_issue_merged, mock_slack_notify
    ):
        payload = {
            "action": "closed",
            "pull_request": {
                "merged_at": "2023-01-01T12:00:00Z",
                "head": {"ref": "gitauto/issue-123"},
                "body": "Resolves #123",
                "user": {"login": "gitauto-ai[bot]"}
            },
            "repository": {
                "owner": {"type": "Organization", "login": "test-owner"},
                "name": "test-repo"
            },
            "sender": {"login": "test-sender"}
        }
        
        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            await handle_webhook_event("pull_request", payload)
        
        mock_update_issue_merged.assert_called_once_with(
            owner_type="Organization",
            owner_name="test-owner",
            repo_name="test-repo",
            issue_number=123,
            merged=True
        )
        mock_slack_notify.assert_called_once_with(
            "🎉 PR created by `gitauto-ai[bot]` was merged by `test-sender` for `test-owner/test-repo`"
        )

    @pytest.mark.asyncio
    async def test_pull_request_closed_not_merged(self, mock_update_issue_merged):
        payload = {
            "action": "closed",
            "pull_request": {
                "merged_at": None,  # Not merged
                "head": {"ref": "gitauto/issue-123"},
                "body": "Resolves #123"
            }
        }
        
        await handle_webhook_event("pull_request", payload)
        
        mock_update_issue_merged.assert_not_called()

    @pytest.mark.asyncio
    async def test_pull_request_closed_non_gitauto_pr(self, mock_handle_pr_merged):
        payload = {
            "action": "closed",
            "pull_request": {
                "merged_at": "2023-01-01T12:00:00Z",
                "head": {"ref": "feature/some-feature"},  # Not gitauto branch
                "body": "Some changes"
            }
        }
        
        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            await handle_webhook_event("pull_request", payload)
        
        mock_handle_pr_merged.assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_pull_request_review_comment_created(self, mock_handle_review_run):
        payload = {"action": "created"}
        
        await handle_webhook_event("pull_request_review_comment", payload)
        
        mock_handle_review_run.assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_pull_request_review_comment_edited(self, mock_handle_review_run):
        payload = {"action": "edited"}
        
        await handle_webhook_event("pull_request_review_comment", payload)
        
        mock_handle_review_run.assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_pull_request_review_comment_deleted(self, mock_handle_review_run):
        payload = {"action": "deleted"}
        
        await handle_webhook_event("pull_request_review_comment", payload)
        
        mock_handle_review_run.assert_not_called()

    @pytest.mark.asyncio
    async def test_workflow_run_completed_success(self, mock_handle_coverage_report):
        payload = {
            "action": "completed",
            "workflow_run": {
                "conclusion": "success",
                "id": 123,
                "head_branch": "main"
            },
            "repository": {
                "owner": {"id": 456, "login": "test-owner"},
                "id": 789,
                "name": "test-repo"
            },
            "installation": {"id": 101112},
            "sender": {"login": "test-sender"}
        }
        
        await handle_webhook_event("workflow_run", payload)
        
        mock_handle_coverage_report.assert_called_once_with(
            owner_id=456,
            owner_name="test-owner",
            repo_id=789,
            repo_name="test-repo",
            installation_id=101112,
            run_id=123,
            head_branch="main",
            user_name="test-sender"
        )

    @pytest.mark.asyncio
    async def test_workflow_run_completed_failure(self, mock_handle_coverage_report):
        payload = {
            "action": "completed",
            "workflow_run": {"conclusion": "failure"}
        }
        
        await handle_webhook_event("workflow_run", payload)
        
        mock_handle_coverage_report.assert_not_called()

    @pytest.mark.asyncio
    async def test_unknown_event_type(self):
        payload = {"action": "some_action"}
        
        result = await handle_webhook_event("unknown_event", payload)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_pull_request_closed_invalid_body_format(self, mock_update_issue_merged):
        payload = {
            "action": "closed",
            "pull_request": {
                "merged_at": "2023-01-01T12:00:00Z",
                "head": {"ref": "gitauto/issue-123"},
                "body": "Invalid body format"  # Doesn't start with "Resolves #"
            }
        }
        
        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            await handle_webhook_event("pull_request", payload)
        
        mock_update_issue_merged.assert_not_called()
