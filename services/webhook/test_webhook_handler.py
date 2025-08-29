# Standard imports
from unittest.mock import patch, AsyncMock
import pytest

# Local imports
from services.webhook.webhook_handler import handle_webhook_event


@pytest.fixture
def mock_slack_notify():
    with patch("services.webhook.webhook_handler.slack_notify") as mock:
        yield mock


@pytest.fixture
def mock_delete_installation():
    with patch("services.webhook.webhook_handler.delete_installation") as mock:
        yield mock


@pytest.fixture
def mock_unsuspend_installation():
    with patch("services.webhook.webhook_handler.unsuspend_installation") as mock:
        yield mock


@pytest.fixture
def mock_handle_installation_created():
    with patch("services.webhook.webhook_handler.handle_installation_created") as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_handle_installation_repos_added():
    with patch(
        "services.webhook.webhook_handler.handle_installation_repos_added"
    ) as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_create_pr_from_issue():
    with patch("services.webhook.webhook_handler.create_pr_from_issue") as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_create_gitauto_button_comment():
    with patch(
        "services.webhook.webhook_handler.create_gitauto_button_comment"
    ) as mock:
        yield mock


@pytest.fixture
def mock_handle_pr_checkbox_trigger():
    with patch(
        "services.webhook.webhook_handler.handle_pr_checkbox_trigger",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_handle_check_run():
    with patch("services.webhook.webhook_handler.handle_check_run") as mock:
        yield mock


@pytest.fixture
def mock_create_pr_checkbox_comment():
    with patch("services.webhook.webhook_handler.create_pr_checkbox_comment") as mock:
        yield mock


@pytest.fixture
def mock_write_pr_description():
    with patch("services.webhook.webhook_handler.write_pr_description") as mock:
        yield mock


@pytest.fixture
def mock_handle_screenshot_comparison():
    with patch(
        "services.webhook.webhook_handler.handle_screenshot_comparison",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_handle_pr_merged():
    with patch("services.webhook.webhook_handler.handle_pr_merged") as mock:
        yield mock


@pytest.fixture
def mock_update_issue_merged():
    with patch("services.webhook.webhook_handler.update_issue_merged") as mock:
        yield mock


@pytest.fixture
def mock_handle_review_run():
    with patch("services.webhook.webhook_handler.handle_review_run") as mock:
        yield mock


@pytest.fixture
def mock_handle_coverage_report():
    with patch(
        "services.webhook.webhook_handler.handle_coverage_report",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = None
        yield mock


class TestHandleWebhookEvent:
    @pytest.mark.asyncio
    async def test_handle_webhook_event_no_action(self):
        """Test that the function returns early when no action is provided."""
        payload = {"key": "value"}
        result = await handle_webhook_event(event_name="push", payload=payload)
        assert result is None

    @pytest.mark.asyncio
    async def test_handle_webhook_event_installation_created(
        self, mock_slack_notify, mock_handle_installation_created
    ):
        """Test handling of installation created event."""
        payload = {
            "action": "created",
            "installation": {"account": {"login": "test-owner"}},
            "sender": {"login": "test-sender"},
        }

        await handle_webhook_event(event_name="installation", payload=payload)

        mock_slack_notify.assert_called_once_with(
            "🎉 New installation by `test-sender` for `test-owner`"
        )
        mock_handle_installation_created.assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_handle_webhook_event_installation_deleted(
        self, mock_slack_notify, mock_delete_installation
    ):
        """Test handling of installation deleted event."""
        payload = {
            "action": "deleted",
            "installation": {
                "account": {"login": "test-owner", "id": 11111},
                "id": 12345,
            },
            "sender": {"login": "test-sender", "id": 67890},
        }

        await handle_webhook_event(event_name="installation", payload=payload)

        mock_slack_notify.assert_called_once_with(
            ":skull: Installation deleted by `test-sender` for `test-owner`"
        )
        mock_delete_installation.assert_called_once_with(
            installation_id=12345,
            user_id=67890,
            user_name="test-sender",
        )

    @pytest.mark.asyncio
    async def test_handle_webhook_event_installation_suspended(
        self, mock_slack_notify, mock_delete_installation
    ):
        """Test handling of installation suspended event."""
        payload = {
            "action": "suspend",
            "installation": {
                "account": {"login": "test-owner", "id": 11111},
                "id": 12345,
            },
            "sender": {"login": "test-sender", "id": 67890},
        }

        await handle_webhook_event(event_name="installation", payload=payload)

        mock_slack_notify.assert_called_once_with(
            ":skull: Installation suspended by `test-sender` for `test-owner`"
        )
        mock_delete_installation.assert_called_once_with(
            installation_id=12345,
            user_id=67890,
            user_name="test-sender",
        )

    @pytest.mark.asyncio
    async def test_handle_webhook_event_installation_unsuspended(
        self, mock_slack_notify, mock_unsuspend_installation
    ):
        """Test handling of installation unsuspended event."""
        payload = {
            "action": "unsuspend",
            "installation": {"account": {"login": "test-owner"}, "id": 12345},
            "sender": {"login": "test-sender"},
        }

        await handle_webhook_event(event_name="installation", payload=payload)

        mock_slack_notify.assert_called_once_with(
            "🎉 Installation unsuspended by `test-sender` for `test-owner`"
        )
        mock_unsuspend_installation.assert_called_once_with(installation_id=12345)

    @pytest.mark.asyncio
    async def test_handle_webhook_event_installation_repos_added(
        self, mock_slack_notify, mock_handle_installation_repos_added
    ):
        """Test handling of installation repositories added event."""
        payload = {
            "action": "added",
            "installation": {"account": {"login": "test-owner"}},
            "sender": {"login": "test-sender"},
        }

        await handle_webhook_event(
            event_name="installation_repositories", payload=payload
        )

        mock_slack_notify.assert_not_called()
        mock_handle_installation_repos_added.assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_handle_webhook_event_issues_labeled(self, mock_create_pr_from_issue):
        """Test handling of issues labeled event."""
        payload = {"action": "labeled"}

        await handle_webhook_event(event_name="issues", payload=payload)

        mock_create_pr_from_issue.assert_called_once_with(
            payload=payload, trigger="issue_label", input_from="github"
        )

    @pytest.mark.asyncio
    async def test_handle_webhook_event_issues_opened(
        self, mock_create_gitauto_button_comment
    ):
        """Test handling of issues opened event."""
        payload = {"action": "opened"}

        await handle_webhook_event(event_name="issues", payload=payload)

        mock_create_gitauto_button_comment.assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_handle_webhook_event_issue_comment_edited_dev_env(
        self, mock_handle_pr_checkbox_trigger, mock_create_pr_from_issue
    ):
        """Test handling of issue comment edited event in dev environment."""
        with patch("services.webhook.webhook_handler.PRODUCT_ID", "dev"):
            payload = {
                "action": "edited",
                "comment": {"body": "- [x] Generate PR - dev"},
            }

            await handle_webhook_event(event_name="issue_comment", payload=payload)

            mock_handle_pr_checkbox_trigger.assert_called_once_with(payload=payload)
            mock_create_pr_from_issue.assert_called_once_with(
                payload=payload, trigger="issue_comment", input_from="github"
            )

    @pytest.mark.asyncio
    async def test_handle_webhook_event_issue_comment_edited_prod_env(
        self, mock_handle_pr_checkbox_trigger, mock_create_pr_from_issue
    ):
        """Test handling of issue comment edited event in production environment."""
        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            payload = {
                "action": "edited",
                "comment": {"body": "- [x] Generate PR"},
            }

            await handle_webhook_event(event_name="issue_comment", payload=payload)

            mock_handle_pr_checkbox_trigger.assert_called_once_with(payload=payload)
            mock_create_pr_from_issue.assert_called_once_with(
                payload=payload, trigger="issue_comment", input_from="github"
            )

    @pytest.mark.asyncio
    async def test_handle_webhook_event_issue_comment_edited_no_trigger(
        self, mock_handle_pr_checkbox_trigger, mock_create_pr_from_issue
    ):
        """Test handling of issue comment edited event with no trigger text."""
        payload = {
            "action": "edited",
            "comment": {"body": "Some other comment text"},
        }

        await handle_webhook_event(event_name="issue_comment", payload=payload)

        mock_handle_pr_checkbox_trigger.assert_called_once_with(payload=payload)
        mock_create_pr_from_issue.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_webhook_event_check_run_completed_failure(
        self, mock_handle_check_run
    ):
        """Test handling of check run completed event with failure."""
        payload = {
            "action": "completed",
            "check_run": {"conclusion": "failure"},
        }

        with patch(
            "services.webhook.webhook_handler.GITHUB_CHECK_RUN_FAILURES", ["failure"]
        ):
            await handle_webhook_event(event_name="check_run", payload=payload)

            mock_handle_check_run.assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_handle_webhook_event_check_run_completed_success(
        self, mock_handle_check_run
    ):
        """Test handling of check run completed event with success."""
        payload = {
            "action": "completed",
            "check_run": {"conclusion": "success"},
        }

        await handle_webhook_event(event_name="check_run", payload=payload)

        mock_handle_check_run.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_webhook_event_pull_request_opened(
        self,
        mock_create_pr_checkbox_comment,
        mock_write_pr_description,
        mock_handle_screenshot_comparison,
    ):
        """Test handling of pull request opened event."""
        payload = {"action": "opened"}

        await handle_webhook_event(event_name="pull_request", payload=payload)

        mock_create_pr_checkbox_comment.assert_called_once_with(payload=payload)
        mock_write_pr_description.assert_called_once_with(payload=payload)
        mock_handle_screenshot_comparison.assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_handle_webhook_event_pull_request_synchronize(
        self, mock_create_pr_checkbox_comment, mock_handle_screenshot_comparison
    ):
        """Test handling of pull request synchronize event."""
        payload = {"action": "synchronize"}

        await handle_webhook_event(event_name="pull_request", payload=payload)

        mock_create_pr_checkbox_comment.assert_called_once_with(payload=payload)
        mock_handle_screenshot_comparison.assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_handle_webhook_event_pull_request_closed_no_pull_request(self):
        """Test handling of pull request closed event with no pull_request."""
        payload = {"action": "closed"}

        await handle_webhook_event(event_name="pull_request", payload=payload)

        # Should return early with no errors

    @pytest.mark.asyncio
    async def test_handle_webhook_event_pull_request_closed_not_merged(self):
        """Test handling of pull request closed event that wasn't merged."""
        payload = {
            "action": "closed",
            "pull_request": {"merged_at": None, "head": {"ref": "some-branch"}},
        }

        await handle_webhook_event(event_name="pull_request", payload=payload)

        # Should return early with no errors

    @pytest.mark.asyncio
    async def test_handle_webhook_event_pull_request_closed_non_gitauto_branch(
        self, mock_handle_pr_merged
    ):
        """Test handling of pull request closed event from non-GitAuto branch."""
        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            with patch(
                "services.webhook.webhook_handler.ISSUE_NUMBER_FORMAT", "/issue-"
            ):
                payload = {
                    "action": "closed",
                    "pull_request": {
                        "merged_at": "2023-01-01T00:00:00Z",
                        "head": {"ref": "feature/some-branch"},
                    },
                }

                await handle_webhook_event(event_name="pull_request", payload=payload)

                mock_handle_pr_merged.assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_handle_webhook_event_pull_request_closed_gitauto_branch_no_body(
        self, mock_update_issue_merged, mock_slack_notify
    ):
        """Test handling of pull request closed event from GitAuto branch with no body."""
        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            with patch(
                "services.webhook.webhook_handler.ISSUE_NUMBER_FORMAT", "/issue-"
            ):
                payload = {
                    "action": "closed",
                    "pull_request": {
                        "merged_at": "2023-01-01T00:00:00Z",
                        "head": {"ref": "gitauto/issue-123"},
                        "body": None,
                    },
                }

                await handle_webhook_event(event_name="pull_request", payload=payload)

                mock_update_issue_merged.assert_not_called()
                mock_slack_notify.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_webhook_event_pull_request_closed_gitauto_branch_wrong_body_format(
        self, mock_update_issue_merged, mock_slack_notify
    ):
        """Test handling of pull request closed event from GitAuto branch with wrong body format."""
        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            with patch(
                "services.webhook.webhook_handler.ISSUE_NUMBER_FORMAT", "/issue-"
            ):
                with patch(
                    "services.webhook.webhook_handler.PR_BODY_STARTS_WITH", "Resolves #"
                ):
                    payload = {
                        "action": "closed",
                        "pull_request": {
                            "merged_at": "2023-01-01T00:00:00Z",
                            "head": {"ref": "gitauto/issue-123"},
                            "body": "Fixes issue #123",
                        },
                    }

                    await handle_webhook_event(
                        event_name="pull_request", payload=payload
                    )

                    mock_update_issue_merged.assert_not_called()
                    mock_slack_notify.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_webhook_event_pull_request_closed_gitauto_branch_success(
        self, mock_update_issue_merged, mock_slack_notify
    ):
        """Test handling of pull request closed event from GitAuto branch with success."""
        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            with patch(
                "services.webhook.webhook_handler.ISSUE_NUMBER_FORMAT", "/issue-"
            ):
                with patch(
                    "services.webhook.webhook_handler.PR_BODY_STARTS_WITH", "Resolves #"
                ):
                    payload = {
                        "action": "closed",
                        "pull_request": {
                            "merged_at": "2023-01-01T00:00:00Z",
                            "head": {"ref": "gitauto/issue-123"},
                            "body": "Resolves #123",
                            "user": {"login": "author-name"},
                        },
                        "repository": {
                            "owner": {"type": "Organization", "login": "owner-name"},
                            "name": "repo-name",
                        },
                        "sender": {"login": "sender-name"},
                    }

                    await handle_webhook_event(
                        event_name="pull_request", payload=payload
                    )

                    mock_update_issue_merged.assert_called_once_with(
                        owner_type="Organization",
                        owner_name="owner-name",
                        repo_name="repo-name",
                        issue_number=123,
                        merged=True,
                    )
                    mock_slack_notify.assert_called_once_with(
                        "🎉 PR created by `author-name` was merged by `sender-name` for `owner-name/repo-name`"
                    )

    @pytest.mark.asyncio
    async def test_handle_webhook_event_pull_request_review_comment_created(
        self, mock_handle_review_run
    ):
        """Test handling of pull request review comment created event."""
        payload = {"action": "created"}

        await handle_webhook_event(
            event_name="pull_request_review_comment", payload=payload
        )

        mock_handle_review_run.assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_handle_webhook_event_pull_request_review_comment_edited(
        self, mock_handle_review_run
    ):
        """Test handling of pull request review comment edited event."""
        payload = {"action": "edited"}

        await handle_webhook_event(
            event_name="pull_request_review_comment", payload=payload
        )

        mock_handle_review_run.assert_called_once_with(payload=payload)

    @pytest.mark.asyncio
    async def test_handle_webhook_event_pull_request_review_comment_deleted(
        self, mock_handle_review_run
    ):
        """Test handling of pull request review comment deleted event."""
        payload = {"action": "deleted"}

        await handle_webhook_event(
            event_name="pull_request_review_comment", payload=payload
        )

        mock_handle_review_run.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_webhook_event_workflow_run_completed_success(
        self, mock_handle_coverage_report
    ):
        """Test handling of workflow run completed event with success."""
        payload = {
            "action": "completed",
            "workflow_run": {
                "conclusion": "success",
                "id": 12345,
                "head_branch": "main",
            },
            "repository": {
                "owner": {"id": 67890, "login": "owner-name"},
                "id": 54321,
                "name": "repo-name",
            },
            "installation": {"id": 98765},
            "sender": {"login": "sender-name"},
        }

        await handle_webhook_event(event_name="workflow_run", payload=payload)

        mock_handle_coverage_report.assert_called_once_with(
            owner_id=67890,
            owner_name="owner-name",
            repo_id=54321,
            repo_name="repo-name",
            installation_id=98765,
            run_id=12345,
            head_branch="main",
            user_name="sender-name",
        )

    @pytest.mark.asyncio
    async def test_handle_webhook_event_workflow_run_completed_failure(
        self, mock_handle_coverage_report
    ):
        """Test handling of workflow run completed event with failure."""
        payload = {"action": "completed", "workflow_run": {"conclusion": "failure"}}

        await handle_webhook_event(event_name="workflow_run", payload=payload)

        mock_handle_coverage_report.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_webhook_event_unknown_event(self):
        """Test handling of unknown event."""
        payload = {"action": "some_action"}

        result = await handle_webhook_event(event_name="unknown_event", payload=payload)

        assert result is None
