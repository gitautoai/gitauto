# pylint: disable=too-many-lines,unused-argument

# pyright: reportUnusedVariable=false

# Standard imports
import json
from typing import cast
from unittest.mock import patch
import pytest

# Local imports
from config import UTF8
from services.github.types.github_types import (
    CheckSuiteCompletedPayload,
    InstallationRepositoriesPayload,
    PrClosedPayload,
    PrLabeledPayload,
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
def mock_handle_installation_repos_removed():
    with patch(
        "services.webhook.webhook_handler.handle_installation_repos_removed"
    ) as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_handle_new_pr():
    with patch("services.webhook.webhook_handler.handle_new_pr") as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_handle_check_suite():
    with patch("services.webhook.webhook_handler.handle_check_suite") as mock:
        yield mock


@pytest.fixture
def mock_handle_review_run():
    with patch("services.webhook.webhook_handler.handle_review_run") as mock:
        yield mock


@pytest.fixture
def mock_handle_coverage_report():
    with patch("services.webhook.webhook_handler.handle_coverage_report") as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_handle_push():
    with patch("services.webhook.webhook_handler.handle_push") as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_handle_installation_deleted_or_suspended():
    with patch(
        "services.webhook.webhook_handler.handle_installation_deleted_or_suspended"
    ) as mock:
        yield mock


class TestHandleWebhookEvent:
    @pytest.mark.asyncio
    async def test_handle_webhook_event_no_action(self):
        """Test that the function returns early when no action is provided."""
        payload = {"key": "value"}
        result = await handle_webhook_event(event_name="unknown_event", payload=payload)
        assert result is None

    @pytest.mark.asyncio
    async def test_handle_webhook_event_push(self, mock_handle_push):
        """Test handling of push events."""
        payload = {
            "ref": "refs/heads/main",
            "repository": {
                "id": 123,
                "name": "test-repo",
                "owner": {"id": 456, "login": "test-owner"},
            },
            "installation": {"id": 789},
        }

        await handle_webhook_event(event_name="push", payload=payload)

        mock_handle_push.assert_called_once_with(payload=payload)

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
        self, mock_handle_installation_deleted_or_suspended
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

        mock_handle_installation_deleted_or_suspended.assert_called_once_with(
            payload=payload, action="deleted"
        )

    @pytest.mark.asyncio
    async def test_handle_webhook_event_installation_suspended(
        self, mock_handle_installation_deleted_or_suspended
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

        mock_handle_installation_deleted_or_suspended.assert_called_once_with(
            payload=payload, action="suspend"
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
    async def test_handle_webhook_event_pull_request_labeled_dashboard(
        self, mock_handle_new_pr
    ):
        """Test handling of pull request labeled event from dashboard triggers handle_new_pr."""
        payload = {
            "action": "labeled",
            "label": {"name": "gitauto"},
            "pull_request": {
                "number": 42,
                "head": {"ref": "gitauto/dashboard-20250101-120000-Ab12"},
            },
            "sender": {"login": "test-user", "id": 12345},
        }

        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            await handle_webhook_event(event_name="pull_request", payload=payload)

        mock_handle_new_pr.assert_called_once_with(
            payload=payload,
            trigger="dashboard",
            lambda_info=None,
        )

    @pytest.mark.asyncio
    async def test_handle_webhook_event_pull_request_labeled_schedule(
        self, mock_handle_new_pr
    ):
        """Test handling of pull request labeled event from schedule triggers handle_new_pr."""
        payload = {
            "action": "labeled",
            "label": {"name": "gitauto"},
            "pull_request": {
                "number": 42,
                "head": {"ref": "gitauto/schedule-20250101-120000-Ab12"},
            },
            "sender": {"login": "test-user", "id": 12345},
        }

        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            await handle_webhook_event(event_name="pull_request", payload=payload)

        mock_handle_new_pr.assert_called_once_with(
            payload=payload,
            trigger="schedule",
            lambda_info=None,
        )

    @pytest.mark.asyncio
    async def test_handle_webhook_event_pull_request_labeled_non_gitauto_label_ignored(
        self, mock_handle_new_pr
    ):
        """Test that non-gitauto labels (e.g. dependabot's 'dependencies') are ignored."""
        payload = {
            "action": "labeled",
            "label": {"name": "dependencies"},
            "pull_request": {
                "number": 99,
                "head": {"ref": "dependabot/npm_and_yarn/ajv-6.14.0"},
            },
            "sender": {"login": "dependabot[bot]", "id": 49699333},
        }

        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            await handle_webhook_event(event_name="pull_request", payload=payload)

        mock_handle_new_pr.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_webhook_event_pull_request_labeled_bot_sender_ignored(
        self, mock_handle_new_pr
    ):
        """Test that bot senders (other than GitAuto) are rejected even with gitauto label."""
        payload = {
            "action": "labeled",
            "label": {"name": "gitauto"},
            "pull_request": {
                "number": 99,
                "head": {"ref": "dependabot/npm_and_yarn/ajv-6.14.0"},
            },
            "sender": {"login": "dependabot[bot]", "id": 49699333},
        }

        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            await handle_webhook_event(event_name="pull_request", payload=payload)

        mock_handle_new_pr.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_webhook_event_pull_request_labeled_gitauto_bot_allowed(
        self, mock_handle_new_pr
    ):
        """Test that GitAuto's own bot is allowed (for schedule triggers)."""
        payload = {
            "action": "labeled",
            "label": {"name": "gitauto"},
            "pull_request": {
                "number": 42,
                "head": {"ref": "gitauto/schedule-20250101-120000-Ab12"},
            },
            "sender": {"login": "gitauto[bot]", "id": 160085510},
        }

        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"), patch(
            "services.webhook.webhook_handler.GITHUB_APP_USER_ID", 160085510
        ):
            await handle_webhook_event(event_name="pull_request", payload=payload)

        mock_handle_new_pr.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_webhook_event_pull_request_labeled_non_gitauto_branch_ignored(
        self, mock_handle_new_pr
    ):
        """Test that a gitauto label on a non-gitauto branch is ignored."""
        payload = {
            "action": "labeled",
            "label": {"name": "gitauto"},
            "pull_request": {"number": 99, "head": {"ref": "feature/some-branch"}},
            "sender": {"login": "test-user", "id": 12345},
        }

        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            await handle_webhook_event(event_name="pull_request", payload=payload)

        mock_handle_new_pr.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_webhook_event_check_suite_completed_failure(
        self, mock_handle_check_suite
    ):
        """Test handling of check suite completed event with failure."""
        payload = {
            "action": "completed",
            "check_suite": {
                "conclusion": "failure",
                "app": {"slug": "github-actions"},
            },
        }

        with patch(
            "services.webhook.webhook_handler.GITHUB_CHECK_RUN_FAILURES", ["failure"]
        ):
            await handle_webhook_event(event_name="check_suite", payload=payload)

            mock_handle_check_suite.assert_called_once_with(
                payload=payload, lambda_info=None
            )

    @pytest.mark.asyncio
    @patch("services.webhook.webhook_handler.handle_successful_check_suite")
    async def test_handle_webhook_event_check_suite_completed_success(
        self, mock_handle_successful_check_suite, mock_handle_check_suite
    ):
        """Test handling of check suite completed event with success."""
        payload = {
            "action": "completed",
            "check_suite": {
                "conclusion": "success",
                "app": {"slug": "github-actions"},
            },
        }

        await handle_webhook_event(event_name="check_suite", payload=payload)

        mock_handle_check_suite.assert_not_called()
        mock_handle_successful_check_suite.assert_called_once()

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
    async def test_handle_webhook_event_pull_request_closed_non_gitauto_branch(self):
        """Test handling of pull request closed event from non-GitAuto branch."""
        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            payload = {
                "action": "closed",
                "pull_request": {
                    "number": 456,
                    "merged_at": "2023-01-01T00:00:00Z",
                    "head": {"ref": "feature/some-branch"},
                },
            }

            # Should return early without errors (non-GitAuto branches are ignored)
            await handle_webhook_event(event_name="pull_request", payload=payload)

    @pytest.mark.asyncio
    @patch("services.webhook.webhook_handler.get_usage_by_pr")
    @patch("services.webhook.webhook_handler.update_usage")
    async def test_handle_webhook_event_pull_request_closed_gitauto_branch_no_body(
        self,
        mock_update_usage,
        mock_get_usage_by_pr,
        mock_slack_notify,
    ):
        """Test handling of pull request closed event from GitAuto branch with no body (schedule PR)."""
        mock_get_usage_by_pr.return_value = []

        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            payload = {
                "action": "closed",
                "pull_request": {
                    "merged_at": "2023-01-01T00:00:00Z",
                    "head": {"ref": "gitauto/schedule-20250101-1200-abc123"},
                    "body": None,
                    "number": 456,
                    "title": "Test PR",
                },
                "repository": {
                    "id": 789,
                    "owner": {
                        "type": "Organization",
                        "login": "owner-name",
                        "id": 111,
                    },
                    "name": "repo-name",
                },
                "sender": {"login": "sender-name"},
            }

            await handle_webhook_event(event_name="pull_request", payload=payload)

            mock_slack_notify.assert_called_once()

    @pytest.mark.asyncio
    @patch("services.webhook.webhook_handler.get_usage_by_pr")
    @patch("services.webhook.webhook_handler.update_usage")
    async def test_handle_webhook_event_pull_request_closed_gitauto_branch_wrong_body_format(
        self,
        mock_update_usage,
        mock_get_usage_by_pr,
        mock_slack_notify,
    ):
        """Test handling of pull request closed event from GitAuto branch with different body format."""
        mock_get_usage_by_pr.return_value = []

        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            payload = {
                "action": "closed",
                "pull_request": {
                    "merged_at": "2023-01-01T00:00:00Z",
                    "head": {"ref": "gitauto/dashboard-20250101-1200-abc123"},
                    "body": "Fixes issue #123",
                    "number": 456,
                    "title": "Test PR",
                },
                "repository": {
                    "id": 789,
                    "owner": {
                        "type": "Organization",
                        "login": "owner-name",
                        "id": 111,
                    },
                    "name": "repo-name",
                },
                "sender": {"login": "sender-name"},
            }

            await handle_webhook_event(event_name="pull_request", payload=payload)

            mock_slack_notify.assert_called_once()

    @pytest.mark.asyncio
    @patch("services.webhook.webhook_handler.get_usage_by_pr")
    @patch("services.webhook.webhook_handler.update_usage")
    async def test_handle_webhook_event_pull_request_closed_gitauto_branch_success(
        self,
        mock_update_usage,
        mock_get_usage_by_pr,
        mock_slack_notify,
    ):
        """Test handling of pull request closed event from GitAuto branch with success."""
        mock_get_usage_by_pr.return_value = [{"id": 1}, {"id": 2}]

        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            payload = {
                "action": "closed",
                "pull_request": {
                    "merged_at": "2023-01-01T00:00:00Z",
                    "head": {"ref": "gitauto/dashboard-20250101-1200-abc123"},
                    "body": "Automated PR by GitAuto",
                    "user": {"login": "author-name"},
                    "number": 456,
                    "title": "Fix issue #123",
                },
                "repository": {
                    "id": 789,
                    "owner": {
                        "type": "Organization",
                        "login": "owner-name",
                        "id": 111,
                    },
                    "name": "repo-name",
                },
                "sender": {"login": "sender-name"},
            }

            await handle_webhook_event(event_name="pull_request", payload=payload)

            mock_get_usage_by_pr.assert_called_once_with(111, 789, 456)
            assert mock_update_usage.call_count == 2
            mock_update_usage.assert_any_call(usage_id=1, is_merged=True)
            mock_update_usage.assert_any_call(usage_id=2, is_merged=True)
            mock_slack_notify.assert_called_once_with(
                "🎉 PR #456 merged by `sender-name` for `owner-name/repo-name`: Fix issue #123"
            )

    @pytest.mark.asyncio
    async def test_handle_webhook_event_pull_request_review_comment_created(
        self, mock_handle_review_run
    ):
        """Test handling of pull request review comment created event."""
        payload = {"action": "created", "pull_request": {"number": 456}}

        await handle_webhook_event(
            event_name="pull_request_review_comment", payload=payload
        )

        mock_handle_review_run.assert_called_once_with(
            payload=payload, trigger="pr_file_review", lambda_info=None
        )

    @pytest.mark.asyncio
    async def test_handle_webhook_event_pull_request_review_comment_edited(
        self, mock_handle_review_run
    ):
        """Test handling of pull request review comment edited event."""
        payload = {"action": "edited", "pull_request": {"number": 456}}

        await handle_webhook_event(
            event_name="pull_request_review_comment", payload=payload
        )

        mock_handle_review_run.assert_called_once_with(
            payload=payload, trigger="pr_file_review", lambda_info=None
        )

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
                "head_sha": "abc123def456",
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
            head_sha="abc123def456",
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
    async def test_check_suite_completed_type_checking_with_real_payload(
        self, mock_handle_check_suite
    ):
        with open(
            "payloads/github/check_suite/completed_by_circleci.json", "r", encoding=UTF8
        ) as f:
            payload = json.load(f)

        payload["check_suite"]["conclusion"] = "failure"

        await handle_webhook_event("check_suite", payload)

        mock_handle_check_suite.assert_called_once()

        call_args = mock_handle_check_suite.call_args[1]
        received_payload = call_args["payload"]

        assert isinstance(received_payload, dict)
        assert received_payload["action"] == "completed"
        assert received_payload["check_suite"]["conclusion"] == "failure"
        assert received_payload["repository"]["name"] == "circle-ci-test"
        assert received_payload["repository"]["owner"]["login"] == "gitautoai"

    def test_check_suite_completed_payload_cast(self):
        with open(
            "payloads/github/check_suite/completed_by_circleci.json", "r", encoding=UTF8
        ) as f:
            payload = json.load(f)

        casted_payload = cast(CheckSuiteCompletedPayload, payload)

        assert casted_payload["action"] == "completed"
        assert casted_payload["check_suite"]["id"] == 44556199312
        assert casted_payload["check_suite"]["status"] == "completed"
        assert casted_payload["check_suite"]["conclusion"] == "success"
        assert (
            casted_payload["check_suite"]["head_sha"]
            == "c083a8965106b8dff1b251fc3b0bffd194448694"
        )
        assert casted_payload["repository"]["id"] == 1048247380
        assert casted_payload["repository"]["name"] == "circle-ci-test"
        assert casted_payload["repository"]["owner"]["login"] == "gitautoai"
        assert casted_payload["installation"]["id"] == 60314628

    @pytest.mark.asyncio
    async def test_check_suite_success_handled_by_successful_check_run(
        self, mock_handle_check_suite
    ):
        with open(
            "payloads/github/check_suite/completed_by_circleci.json", "r", encoding=UTF8
        ) as f:
            payload = json.load(f)

        payload["check_suite"]["conclusion"] = "success"

        with patch("services.webhook.webhook_handler.handle_successful_check_suite"):
            await handle_webhook_event("check_suite", payload)

        mock_handle_check_suite.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_suite_skipped_not_handled(self, mock_handle_check_suite):
        with open(
            "payloads/github/check_suite/completed_by_circleci.json", "r", encoding=UTF8
        ) as f:
            payload = json.load(f)

        payload["check_suite"]["conclusion"] = "skipped"

        await handle_webhook_event("check_suite", payload)

        mock_handle_check_suite.assert_not_called()

    @pytest.mark.asyncio
    async def test_issues_labeled_is_ignored(self, mock_handle_new_pr):
        """Regular issues.labeled events are no longer handled (we use pull_request.labeled)."""
        with open("payloads/github/issues/labeled.json", "r", encoding=UTF8) as f:
            payload = json.load(f)

        await handle_webhook_event("issues", payload)

        mock_handle_new_pr.assert_not_called()

    def test_github_pull_request_closed_payload_cast(self):
        with open("payloads/github/pull_request/closed.json", "r", encoding=UTF8) as f:
            payload = json.load(f)

        casted_payload = cast(PrClosedPayload, payload)

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
    @patch("services.webhook.webhook_handler.get_usage_by_pr")
    @patch("services.webhook.webhook_handler.update_usage")
    async def test_pull_request_closed_type_checking_with_real_payload(
        self,
        mock_update_usage,
        mock_get_usage_by_pr,
        mock_slack_notify,
    ):
        mock_get_usage_by_pr.return_value = [{"id": 123}]

        with open("payloads/github/pull_request/closed.json", "r", encoding=UTF8) as f:
            payload = json.load(f)

        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto-wes"):
            await handle_webhook_event("pull_request", payload)

            mock_slack_notify.assert_called_once()
            mock_get_usage_by_pr.assert_called_once()
            mock_update_usage.assert_called_once_with(usage_id=123, is_merged=True)

    def test_github_installation_repositories_payload_cast(self):
        with open(
            "payloads/github/installation_repositories/added.json", "r", encoding=UTF8
        ) as f:
            payload = json.load(f)

        casted_payload = cast(InstallationRepositoriesPayload, payload)

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

    @pytest.mark.asyncio
    async def test_installation_repositories_removed_calls_handler(
        self, mock_handle_installation_repos_removed
    ):
        with open(
            "payloads/github/installation_repositories/removed.json", "r", encoding=UTF8
        ) as f:
            payload = json.load(f)

        await handle_webhook_event("installation_repositories", payload)

        mock_handle_installation_repos_removed.assert_called_once()

        call_args = mock_handle_installation_repos_removed.call_args[1]
        received_payload = call_args["payload"]

        assert isinstance(received_payload, dict)
        assert received_payload["action"] == "removed"

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

    @patch("services.webhook.webhook_handler.handle_successful_check_suite")
    @patch("services.webhook.webhook_handler.handle_coverage_report")
    @pytest.mark.asyncio
    async def test_handle_webhook_event_check_suite_completed_circleci_success(
        self, mock_handle_coverage_report, mock_handle_successful_check_suite
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
            head_sha="c083a8965106b8dff1b251fc3b0bffd194448694",
            user_name="hiroshinishio",
            source="circleci",
        )
        mock_handle_successful_check_suite.assert_called_once()

    @patch("services.webhook.webhook_handler.handle_check_suite")
    @pytest.mark.asyncio
    async def test_handle_webhook_event_check_suite_completed_circleci_failure(
        self, mock_handle_check_suite
    ):
        with open(
            "payloads/github/check_suite/completed_by_circleci.json", "r", encoding=UTF8
        ) as f:
            payload = json.load(f)
        payload["check_suite"]["conclusion"] = "failure"

        with patch(
            "services.webhook.webhook_handler.GITHUB_CHECK_RUN_FAILURES", ["failure"]
        ):
            await handle_webhook_event("check_suite", payload)

        mock_handle_check_suite.assert_called_once_with(
            payload=payload, lambda_info=None
        )

    @patch("services.webhook.webhook_handler.handle_successful_check_suite")
    @patch("services.webhook.webhook_handler.handle_coverage_report")
    @pytest.mark.asyncio
    async def test_handle_webhook_event_check_suite_completed_non_circleci(
        self, mock_handle_coverage_report, mock_handle_successful_check_suite
    ):
        with open(
            "payloads/github/check_suite/completed_by_circleci.json", "r", encoding=UTF8
        ) as f:
            payload = json.load(f)
        payload["check_suite"]["app"]["slug"] = "github-actions"

        await handle_webhook_event("check_suite", payload)

        mock_handle_coverage_report.assert_not_called()
        mock_handle_successful_check_suite.assert_called_once()

    def test_pr_labeled_payload_cast(self):
        with open("payloads/github/pull_request/labeled.json", "r", encoding=UTF8) as f:
            payload = json.load(f)

        casted_payload = cast(PrLabeledPayload, payload)

        assert casted_payload["action"] == "labeled"
        assert casted_payload["number"] == 2304
        assert casted_payload["pull_request"]["id"] == 3311605509
        assert casted_payload["pull_request"]["number"] == 2304
        assert (
            casted_payload["pull_request"]["title"]
            == "Low Test Coverage: utils/logs/clean_logs.py"
        )
        assert casted_payload["pull_request"]["state"] == "open"
        assert casted_payload["pull_request"]["merged"] is False
        assert (
            casted_payload["pull_request"]["head"]["ref"]
            == "gitauto-wes/schedule-20260221-225547-4tb2"
        )
        assert casted_payload["pull_request"]["base"]["ref"] == "main"
        assert casted_payload["label"]["id"] == 8502925420
        assert casted_payload["label"]["name"] == "gitauto-wes"
        assert casted_payload["repository"]["id"] == 756737722
        assert casted_payload["repository"]["name"] == "gitauto"
        assert casted_payload["repository"]["owner"]["login"] == "gitautoai"
        assert casted_payload["organization"]["login"] == "gitautoai"
        assert casted_payload["sender"]["login"] == "hiroshinishio"
        assert casted_payload["installation"]["id"] == 60314628

    @pytest.mark.asyncio
    async def test_pull_request_labeled_type_checking_with_real_payload(
        self, mock_handle_new_pr
    ):
        with open("payloads/github/pull_request/labeled.json", "r", encoding=UTF8) as f:
            payload = json.load(f)

        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto-wes"):
            await handle_webhook_event("pull_request", payload)

        mock_handle_new_pr.assert_called_once()

        call_args = mock_handle_new_pr.call_args[1]
        received_payload = call_args["payload"]
        received_trigger = call_args["trigger"]

        assert isinstance(received_payload, dict)
        assert received_payload["action"] == "labeled"
        assert received_payload["number"] == 2304
        assert (
            received_payload["pull_request"]["head"]["ref"]
            == "gitauto-wes/schedule-20260221-225547-4tb2"
        )
        assert received_trigger == "schedule"

    @pytest.mark.asyncio
    async def test_issue_comment_on_non_pr_is_ignored(self, mock_handle_review_run):
        payload = {
            "action": "created",
            "issue": {"number": 1, "title": "Bug"},
            "comment": {"id": 1, "body": "hello"},
            "sender": {"login": "user"},
            "repository": {"owner": {"login": "o"}, "name": "r"},
            "installation": {"id": 1},
        }
        await handle_webhook_event(event_name="issue_comment", payload=payload)
        mock_handle_review_run.assert_not_called()

    @pytest.mark.asyncio
    async def test_issue_comment_from_gitauto_is_ignored(self, mock_handle_review_run):
        payload = {
            "action": "created",
            "issue": {
                "number": 1,
                "pull_request": {"url": "https://api.github.com/repos/o/r/pulls/1"},
            },
            "comment": {"id": 1, "body": "I fixed it"},
            "sender": {"login": "gitauto-ai[bot]"},
            "repository": {"owner": {"login": "o"}, "name": "r"},
            "installation": {"id": 1},
        }
        with patch(
            "services.webhook.webhook_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]"
        ):
            await handle_webhook_event(event_name="issue_comment", payload=payload)
        mock_handle_review_run.assert_not_called()

    @pytest.mark.asyncio
    @patch("services.webhook.webhook_handler.get_pull_request")
    @patch("services.webhook.webhook_handler.get_installation_access_token")
    async def test_issue_comment_on_non_gitauto_pr_is_ignored(
        self,
        mock_get_token,
        mock_get_pr,
        mock_handle_review_run,
    ):
        mock_get_token.return_value = "token"
        mock_get_pr.return_value = {"head": {"ref": "feature/something"}}

        payload = {
            "action": "created",
            "issue": {
                "number": 5,
                "pull_request": {"url": "https://api.github.com/repos/o/r/pulls/5"},
            },
            "comment": {"id": 1, "body": "fix this"},
            "sender": {"login": "user"},
            "repository": {"owner": {"login": "o"}, "name": "r"},
            "installation": {"id": 1},
        }
        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            await handle_webhook_event(event_name="issue_comment", payload=payload)

        mock_handle_review_run.assert_not_called()

    @pytest.mark.asyncio
    @patch("services.webhook.webhook_handler.adapt_pr_comment_to_review_payload")
    @patch("services.webhook.webhook_handler.get_pull_request")
    @patch("services.webhook.webhook_handler.get_installation_access_token")
    async def test_issue_comment_on_gitauto_pr_calls_review_handler(
        self,
        mock_get_token,
        mock_get_pr,
        mock_adapt,
        mock_handle_review_run,
    ):
        mock_get_token.return_value = "token"
        pr = {"head": {"ref": "gitauto/dashboard-20250101-Ab1C"}}
        mock_get_pr.return_value = pr

        adapted = {
            "action": "created",
            "comment": {
                "id": 111,
                "node_id": "IC_111",
                "body": "you didn't complete the task",
                "user": {"login": "reviewer", "type": "User"},
                "path": "",
                "subject_type": "pr_comment",
                "line": 0,
                "side": "",
            },
            "pull_request": pr,
            "repository": {"owner": {"login": "o"}, "name": "r"},
            "organization": {"id": 2},
            "sender": {"login": "reviewer"},
            "installation": {"id": 1},
        }
        mock_adapt.return_value = adapted

        payload = {
            "action": "created",
            "issue": {
                "number": 10,
                "pull_request": {"url": "https://api.github.com/repos/o/r/pulls/10"},
            },
            "comment": {
                "id": 111,
                "node_id": "IC_111",
                "user": {"login": "reviewer", "type": "User"},
                "body": "you didn't complete the task",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
            },
            "sender": {"login": "reviewer"},
            "repository": {"owner": {"login": "o"}, "name": "r"},
            "installation": {"id": 1},
        }
        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            await handle_webhook_event(event_name="issue_comment", payload=payload)

        mock_adapt.assert_called_once()
        mock_handle_review_run.assert_called_once()
        call_kwargs = mock_handle_review_run.call_args[1]
        assert call_kwargs["trigger"] == "pr_comment"
        assert call_kwargs["lambda_info"] is None
        assert call_kwargs["payload"]["pull_request"] == pr
        assert call_kwargs["payload"]["comment"]["path"] == ""
        assert call_kwargs["payload"]["comment"]["subject_type"] == "pr_comment"

    @pytest.mark.asyncio
    async def test_issue_comment_deleted_is_ignored(self, mock_handle_review_run):
        payload = {
            "action": "deleted",
            "issue": {
                "number": 1,
                "pull_request": {"url": "https://api.github.com/repos/o/r/pulls/1"},
            },
            "comment": {"id": 1, "body": "hello"},
            "sender": {"login": "user"},
            "repository": {"owner": {"login": "o"}, "name": "r"},
            "installation": {"id": 1},
        }
        await handle_webhook_event(event_name="issue_comment", payload=payload)
        mock_handle_review_run.assert_not_called()

    @pytest.mark.asyncio
    @patch("services.webhook.webhook_handler.adapt_pr_review_to_review_payload")
    @patch(
        "services.webhook.webhook_handler.get_review_inline_comments", return_value=[]
    )
    @patch(
        "services.webhook.webhook_handler.get_installation_access_token",
        return_value="token",
    )
    async def test_pr_review_changes_requested_calls_review_handler(
        self,
        _mock_get_token,
        _mock_get_inline,
        mock_adapt,
        mock_handle_review_run,
        mock_slack_notify,
    ):
        adapted = {"action": "submitted", "comment": {"body": "change target branch"}}
        mock_adapt.return_value = adapted

        payload = {
            "action": "submitted",
            "review": {
                "id": 100,
                "node_id": "PRR_100",
                "body": "change target branch",
                "user": {"login": "reviewer"},
                "state": "changes_requested",
            },
            "pull_request": {
                "number": 42,
                "head": {"ref": "gitauto/dashboard-20250101-Ab1C"},
            },
            "repository": {"owner": {"login": "o"}, "name": "r"},
            "sender": {"login": "reviewer"},
            "installation": {"id": 1},
        }
        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            await handle_webhook_event(
                event_name="pull_request_review", payload=payload
            )

        mock_adapt.assert_called_once_with(payload=payload)
        mock_handle_review_run.assert_called_once()
        call_kwargs = mock_handle_review_run.call_args[1]
        assert call_kwargs["trigger"] == "pr_review"
        assert call_kwargs["payload"] == adapted
        mock_slack_notify.assert_not_called()

    @pytest.mark.asyncio
    async def test_pr_review_approved_sends_slack_only(
        self, mock_handle_review_run, mock_slack_notify
    ):
        payload = {
            "action": "submitted",
            "review": {
                "id": 101,
                "node_id": "PRR_101",
                "body": "LGTM",
                "user": {"login": "reviewer"},
                "state": "approved",
            },
            "pull_request": {
                "number": 42,
                "head": {"ref": "gitauto/dashboard-20250101-Ab1C"},
            },
            "repository": {"owner": {"login": "o"}, "name": "r"},
            "sender": {"login": "reviewer"},
            "installation": {"id": 1},
        }
        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            await handle_webhook_event(
                event_name="pull_request_review", payload=payload
            )

        mock_slack_notify.assert_not_called()
        mock_handle_review_run.assert_not_called()

    @pytest.mark.asyncio
    @patch("services.webhook.webhook_handler.adapt_pr_review_to_review_payload")
    @patch(
        "services.webhook.webhook_handler.get_review_inline_comments", return_value=[]
    )
    @patch(
        "services.webhook.webhook_handler.get_installation_access_token",
        return_value="token",
    )
    async def test_pr_review_commented_with_body_calls_review_handler(
        self,
        _mock_get_token,
        _mock_get_inline,
        mock_adapt,
        mock_handle_review_run,
        mock_slack_notify,
    ):
        adapted = {"action": "submitted", "comment": {"body": "what about this?"}}
        mock_adapt.return_value = adapted

        payload = {
            "action": "submitted",
            "review": {
                "id": 102,
                "node_id": "PRR_102",
                "body": "what about this?",
                "user": {"login": "reviewer"},
                "state": "commented",
            },
            "pull_request": {
                "number": 42,
                "head": {"ref": "gitauto/dashboard-20250101-Ab1C"},
            },
            "repository": {"owner": {"login": "o"}, "name": "r"},
            "sender": {"login": "reviewer"},
            "installation": {"id": 1},
        }
        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            await handle_webhook_event(
                event_name="pull_request_review", payload=payload
            )

        mock_adapt.assert_called_once_with(payload=payload)
        mock_handle_review_run.assert_called_once()
        call_kwargs = mock_handle_review_run.call_args[1]
        assert call_kwargs["trigger"] == "pr_review"
        mock_slack_notify.assert_not_called()

    @pytest.mark.asyncio
    async def test_pr_review_commented_empty_body_sends_slack_only(
        self, mock_handle_review_run, mock_slack_notify
    ):
        payload = {
            "action": "submitted",
            "review": {
                "id": 103,
                "node_id": "PRR_103",
                "body": "",
                "user": {"login": "reviewer"},
                "state": "commented",
            },
            "pull_request": {
                "number": 42,
                "head": {"ref": "gitauto/dashboard-20250101-Ab1C"},
            },
            "repository": {"owner": {"login": "o"}, "name": "r"},
            "sender": {"login": "reviewer"},
            "installation": {"id": 1},
        }
        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            await handle_webhook_event(
                event_name="pull_request_review", payload=payload
            )

        mock_slack_notify.assert_not_called()
        mock_handle_review_run.assert_not_called()

    @pytest.mark.asyncio
    async def test_pr_review_dismissed_is_ignored(
        self, mock_handle_review_run, mock_slack_notify
    ):
        payload = {
            "action": "dismissed",
            "review": {
                "id": 104,
                "node_id": "PRR_104",
                "body": "old review",
                "user": {"login": "reviewer"},
                "state": "dismissed",
            },
            "pull_request": {
                "number": 42,
                "head": {"ref": "gitauto/dashboard-20250101-Ab1C"},
            },
            "repository": {"owner": {"login": "o"}, "name": "r"},
            "sender": {"login": "reviewer"},
            "installation": {"id": 1},
        }
        await handle_webhook_event(event_name="pull_request_review", payload=payload)

        mock_handle_review_run.assert_not_called()
        mock_slack_notify.assert_not_called()

    @pytest.mark.asyncio
    async def test_pr_review_from_gitauto_is_ignored(
        self, mock_handle_review_run, mock_slack_notify
    ):
        payload = {
            "action": "submitted",
            "review": {
                "id": 105,
                "node_id": "PRR_105",
                "body": "auto review",
                "user": {"login": "gitauto-ai[bot]"},
                "state": "commented",
            },
            "pull_request": {
                "number": 42,
                "head": {"ref": "gitauto/dashboard-20250101-Ab1C"},
            },
            "repository": {"owner": {"login": "o"}, "name": "r"},
            "sender": {"login": "gitauto-ai[bot]"},
            "installation": {"id": 1},
        }
        with patch(
            "services.webhook.webhook_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]"
        ):
            await handle_webhook_event(
                event_name="pull_request_review", payload=payload
            )

        mock_handle_review_run.assert_not_called()
        mock_slack_notify.assert_not_called()

    @pytest.mark.asyncio
    async def test_pr_review_on_non_gitauto_pr_is_ignored(
        self, mock_handle_review_run, mock_slack_notify
    ):
        payload = {
            "action": "submitted",
            "review": {
                "id": 106,
                "node_id": "PRR_106",
                "body": "looks good",
                "user": {"login": "reviewer"},
                "state": "approved",
            },
            "pull_request": {
                "number": 42,
                "head": {"ref": "feature/something"},
            },
            "repository": {"owner": {"login": "o"}, "name": "r"},
            "sender": {"login": "reviewer"},
            "installation": {"id": 1},
        }
        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            await handle_webhook_event(
                event_name="pull_request_review", payload=payload
            )

        mock_handle_review_run.assert_not_called()
        mock_slack_notify.assert_not_called()

    @pytest.mark.asyncio
    async def test_pr_review_null_body_sends_slack_only(
        self, mock_handle_review_run, mock_slack_notify
    ):
        payload = {
            "action": "submitted",
            "review": {
                "id": 107,
                "node_id": "PRR_107",
                "body": None,
                "user": {"login": "reviewer"},
                "state": "changes_requested",
            },
            "pull_request": {
                "number": 42,
                "head": {"ref": "gitauto/dashboard-20250101-Ab1C"},
            },
            "repository": {"owner": {"login": "o"}, "name": "r"},
            "sender": {"login": "reviewer"},
            "installation": {"id": 1},
        }
        with patch("services.webhook.webhook_handler.PRODUCT_ID", "gitauto"):
            await handle_webhook_event(
                event_name="pull_request_review", payload=payload
            )

        mock_slack_notify.assert_not_called()
        mock_handle_review_run.assert_not_called()
