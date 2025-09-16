# Standard imports
import json
from typing import cast
from unittest.mock import patch, AsyncMock
import pytest

# Local imports
from config import UTF8
from services.github.types.github_types import (
    CheckRunCompletedPayload,
    GitHubInstallationPayload,
    GitHubLabeledPayload,
    GitHubPullRequestClosedPayload,
)
from services.github.types.pull_request_webhook_payload import PullRequestWebhookPayload
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
            payload=payload,
            trigger="issue_label",
            input_from="github",
            lambda_info=None,
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

            mock_handle_pr_checkbox_trigger.assert_called_once_with(payload=payload, lambda_info=None)
            mock_create_pr_from_issue.assert_called_once_with(
                payload=payload,
                trigger="issue_comment",
                input_from="github",
                lambda_info=None,
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

            mock_handle_pr_checkbox_trigger.assert_called_once_with(payload=payload, lambda_info=None)
            mock_create_pr_from_issue.assert_called_once_with(
                payload=payload,
                trigger="issue_comment",
                input_from="github",
                lambda_info=None,
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

    @pytest.mark.asyncio
    async def test_check_run_completed_type_checking_with_real_payload(
        self, mock_handle_check_run
    ):
        with open("payloads/github/check_run/completed.json", "r", encoding=UTF8) as f:
            payload = json.load(f)

        await handle_webhook_event("check_run", payload)

        mock_handle_check_run.assert_called_once()

        call_args = mock_handle_check_run.call_args[1]
        received_payload = call_args["payload"]

        assert isinstance(received_payload, dict)
        assert received_payload["action"] == "completed"
        assert received_payload["check_run"]["conclusion"] == "failure"
        assert received_payload["check_run"]["name"] == "MSBuild (3.9)"
        assert received_payload["repository"]["name"] == "tetris"
        assert received_payload["repository"]["owner"]["login"] == "hiroshinishio"

    def test_check_run_completed_payload_cast(self):
        with open("payloads/github/check_run/completed.json", "r", encoding=UTF8) as f:
            payload = json.load(f)

        casted_payload = cast(CheckRunCompletedPayload, payload)

        assert casted_payload["action"] == "completed"
        assert casted_payload["check_run"]["id"] == 31710113401
        assert casted_payload["check_run"]["status"] == "completed"
        assert casted_payload["check_run"]["conclusion"] == "failure"
        assert casted_payload["check_run"]["name"] == "MSBuild (3.9)"
        assert (
            casted_payload["check_run"]["head_sha"]
            == "cf4fb4f60a67e1b8ff1447ba72cb5131e4979ed7"
        )
        assert casted_payload["repository"]["id"] == 871345449
        assert casted_payload["repository"]["name"] == "tetris"
        assert casted_payload["repository"]["owner"]["login"] == "hiroshinishio"
        assert casted_payload["installation"]["id"] == 52733965

    @pytest.mark.asyncio
    async def test_check_run_success_not_handled(self, mock_handle_check_run):
        with open("payloads/github/check_run/completed.json", "r", encoding=UTF8) as f:
            payload = json.load(f)

        payload["check_run"]["conclusion"] = "success"

        await handle_webhook_event("check_run", payload)

        mock_handle_check_run.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_run_skipped_not_handled(self, mock_handle_check_run):
        with open("payloads/github/check_run/completed.json", "r", encoding=UTF8) as f:
            payload = json.load(f)

        payload["check_run"]["conclusion"] = "skipped"

        await handle_webhook_event("check_run", payload)

        mock_handle_check_run.assert_not_called()

    def test_github_labeled_payload_cast(self):
        with open("payloads/github/issues/labeled.json", "r", encoding=UTF8) as f:
            payload = json.load(f)

        casted_payload = cast(GitHubLabeledPayload, payload)

        assert casted_payload["action"] == "labeled"
        assert casted_payload["issue"]["id"] == 2145314834
        assert casted_payload["issue"]["number"] == 13
        assert casted_payload["issue"]["title"] == "Add Python Unit Testing"
        assert casted_payload["label"]["id"] == 6588739585
        assert casted_payload["label"]["name"] == "pragent"
        assert casted_payload["repository"]["id"] == 756737722
        assert casted_payload["repository"]["name"] == "issue-to-pr"
        assert casted_payload["repository"]["owner"]["login"] == "issue-to-pr"
        assert casted_payload["organization"]["login"] == "issue-to-pr"
        assert casted_payload["sender"]["login"] == "hiroshinishio"
        assert casted_payload["installation"]["id"] == 47463026

    @pytest.mark.asyncio
    async def test_issues_labeled_type_checking_with_real_payload(
        self, mock_create_pr_from_issue
    ):
        with open("payloads/github/issues/labeled.json", "r", encoding=UTF8) as f:
            payload = json.load(f)

        await handle_webhook_event("issues", payload)

        mock_create_pr_from_issue.assert_called_once()

        call_args = mock_create_pr_from_issue.call_args[1]
        received_payload = call_args["payload"]

        assert isinstance(received_payload, dict)
        assert received_payload["action"] == "labeled"
        assert received_payload["issue"]["number"] == 13
        assert received_payload["label"]["name"] == "pragent"
        assert received_payload["repository"]["name"] == "issue-to-pr"
        assert received_payload["sender"]["login"] == "hiroshinishio"

    def test_github_pull_request_closed_payload_cast(self):
        with open("payloads/github/pull_request/closed.json", "r", encoding=UTF8) as f:
            payload = json.load(f)

        casted_payload = cast(GitHubPullRequestClosedPayload, payload)

        assert casted_payload["action"] == "closed"
        assert casted_payload["number"] == 715
        assert casted_payload["pull_request"]["id"] == 2460076952
        assert casted_payload["pull_request"]["number"] == 715
        assert (
            casted_payload["pull_request"]["title"]
            == "GitAuto: Low Test Coverage: utils/colorize_log.py"
        )
        assert casted_payload["pull_request"]["merged"] is True
        assert casted_payload["pull_request"]["merged_at"] == "2025-04-15T14:18:29Z"
        assert casted_payload["repository"]["id"] == 756737722
        assert casted_payload["repository"]["name"] == "gitauto"
        assert casted_payload["repository"]["owner"]["login"] == "gitautoai"
        assert casted_payload["organization"]["login"] == "gitautoai"
        assert casted_payload["sender"]["login"] == "hiroshinishio"
        assert casted_payload["installation"]["id"] == 60314628

    @pytest.mark.asyncio
    async def test_pull_request_closed_type_checking_with_real_payload(
        self, mock_update_issue_merged, mock_slack_notify
    ):
        with open("payloads/github/pull_request/closed.json", "r", encoding=UTF8) as f:
            payload = json.load(f)

        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto-wes"), patch(
            "services.webhook.webhook_handler.ISSUE_NUMBER_FORMAT", "/issue-"
        ), patch("services.webhook.webhook_handler.PR_BODY_STARTS_WITH", "Resolves #"):

            await handle_webhook_event("pull_request", payload)

            mock_update_issue_merged.assert_called_once()
            mock_slack_notify.assert_called_once()

            call_args = mock_update_issue_merged.call_args[1]
            assert call_args["owner_type"] == "Organization"
            assert call_args["owner_name"] == "gitautoai"
            assert call_args["repo_name"] == "gitauto"
            assert call_args["issue_number"] == 714
            assert call_args["merged"] is True

    def test_github_installation_payload_cast(self):
        with open(
            "payloads/github/installation_repositories/added.json", "r", encoding=UTF8
        ) as f:
            payload = json.load(f)

        casted_payload = cast(GitHubInstallationPayload, payload)

        assert casted_payload["action"] == "added"
        assert casted_payload["installation"]["id"] == 52733965
        assert casted_payload["installation"]["account"]["login"] == "hiroshinishio"
        assert casted_payload["installation"]["target_type"] == "User"
        assert casted_payload["repository_selection"] == "selected"
        assert len(casted_payload["repositories_added"]) == 1
        assert casted_payload["repositories_added"][0]["id"] == 416759137
        assert casted_payload["repositories_added"][0]["name"] == "slack-analysis"
        assert len(casted_payload["repositories_removed"]) == 0
        assert casted_payload["sender"]["login"] == "hiroshinishio"
        assert casted_payload["requester"] is None

    @pytest.mark.asyncio
    async def test_installation_created_type_checking_with_real_payload(
        self, mock_slack_notify, mock_handle_installation_created
    ):
        with open("payloads/github/installation/created.json", "r", encoding=UTF8) as f:
            payload = json.load(f)

        await handle_webhook_event("installation", payload)

        mock_slack_notify.assert_called_once_with(
            "🎉 New installation by `nikitamalinov` for `issue-to-pr`"
        )
        mock_handle_installation_created.assert_called_once()

        call_args = mock_handle_installation_created.call_args[1]
        received_payload = call_args["payload"]

        assert isinstance(received_payload, dict)
        assert received_payload["action"] == "created"
        assert received_payload["installation"]["id"] == 47406978
        assert received_payload["sender"]["login"] == "nikitamalinov"

    @pytest.mark.asyncio
    async def test_installation_repositories_added_type_checking_with_real_payload(
        self, mock_handle_installation_repos_added
    ):
        with open(
            "payloads/github/installation_repositories/added.json", "r", encoding=UTF8
        ) as f:
            payload = json.load(f)

        await handle_webhook_event("installation_repositories", payload)

        mock_handle_installation_repos_added.assert_called_once()

        call_args = mock_handle_installation_repos_added.call_args[1]
        received_payload = call_args["payload"]

        assert isinstance(received_payload, dict)
        assert received_payload["action"] == "added"
        assert received_payload["installation"]["id"] == 52733965
        assert received_payload["sender"]["login"] == "hiroshinishio"

    def test_pull_request_webhook_payload_cast(self):
        with open("payloads/github/pull_request/opened.json", "r", encoding=UTF8) as f:
            payload = json.load(f)

        casted_payload = cast(PullRequestWebhookPayload, payload)

        assert casted_payload["action"] == "opened"
        assert casted_payload["number"] == 517
        assert casted_payload["pull_request"]["id"] == 2310561810
        assert casted_payload["pull_request"]["number"] == 517
        assert (
            casted_payload["pull_request"]["title"]
            == "GitAuto: Add an integration test to is_repo_forked() in services/github/repo_manager.py"
        )
        assert casted_payload["pull_request"]["state"] == "open"
        assert casted_payload["pull_request"]["merged"] is False
        assert casted_payload["repository"]["id"] == 756737722
        assert casted_payload["repository"]["name"] == "gitauto"
        assert casted_payload["repository"]["owner"]["login"] == "gitautoai"
        assert casted_payload["organization"]["login"] == "gitautoai"
        assert casted_payload["sender"]["login"] == "gitauto-for-dev[bot]"
        assert casted_payload["installation"]["id"] == 60314628

    @pytest.mark.asyncio
    async def test_pull_request_opened_type_checking_with_real_payload(
        self,
        mock_create_pr_checkbox_comment,
        mock_write_pr_description,
        mock_handle_screenshot_comparison,
    ):
        with open("payloads/github/pull_request/opened.json", "r", encoding=UTF8) as f:
            payload = json.load(f)

        await handle_webhook_event("pull_request", payload)

        mock_create_pr_checkbox_comment.assert_called_once()
        mock_write_pr_description.assert_called_once()
        mock_handle_screenshot_comparison.assert_called_once()

        call_args = mock_create_pr_checkbox_comment.call_args[1]
        received_payload = call_args["payload"]

        assert isinstance(received_payload, dict)
        assert received_payload["action"] == "opened"
        assert received_payload["number"] == 517
        assert (
            received_payload["pull_request"]["title"]
            == "GitAuto: Add an integration test to is_repo_forked() in services/github/repo_manager.py"
        )
        assert received_payload["repository"]["name"] == "gitauto"

    @patch("services.webhook.webhook_handler.handle_coverage_report")
    @pytest.mark.asyncio
    async def test_handle_webhook_event_check_suite_completed_circleci_success(
        self, mock_handle_coverage_report
    ):
        with open(
            "payloads/github/check_suite/completed_by_circleci.json", "r", encoding=UTF8
        ) as f:
            payload = json.load(f)

        await handle_webhook_event("check_suite", payload)

        mock_handle_coverage_report.assert_called_once_with(
            owner_id=159883862,
            owner_name="gitautoai",
            repo_id=1048247380,
            repo_name="circle-ci-test",
            installation_id=60314628,
            run_id=44556199312,
            head_branch="wes",
            user_name="hiroshinishio",
            source="circleci",
        )

    @patch("services.webhook.webhook_handler.handle_coverage_report")
    @pytest.mark.asyncio
    async def test_handle_webhook_event_check_suite_completed_circleci_failure(
        self, mock_handle_coverage_report
    ):
        with open(
            "payloads/github/check_suite/completed_by_circleci.json", "r", encoding=UTF8
        ) as f:
            payload = json.load(f)
        payload["check_suite"]["conclusion"] = "failure"

        await handle_webhook_event("check_suite", payload)

        mock_handle_coverage_report.assert_not_called()

    @patch("services.webhook.webhook_handler.handle_coverage_report")
    @pytest.mark.asyncio
    async def test_handle_webhook_event_check_suite_completed_non_circleci(
        self, mock_handle_coverage_report
    ):
        with open(
            "payloads/github/check_suite/completed_by_circleci.json", "r", encoding=UTF8
        ) as f:
            payload = json.load(f)
        payload["check_suite"]["app"]["slug"] = "github-actions"

        await handle_webhook_event("check_suite", payload)

        mock_handle_coverage_report.assert_not_called()
