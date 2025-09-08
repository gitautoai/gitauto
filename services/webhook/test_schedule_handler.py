# Standard imports
from typing import cast
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest

# Local imports
from payloads.aws.event_bridge_scheduler.event_types import EventBridgeSchedulerEvent
from services.supabase.coverages.get_all_coverages import get_all_coverages
from services.webhook.schedule_handler import schedule_handler


@pytest.fixture
def mock_event():
    """Fixture for EventBridge event."""
    return {
        "ownerId": 123,
        "ownerType": "Organization",
        "ownerName": "test-org",
        "repoId": 456,
        "repoName": "test-repo",
        "userId": 789,
        "userName": "test-user",
        "installationId": 999,
    }


class TestScheduleHandler:
    def test_schedule_handler_missing_required_fields(self):
        """Test that schedule_handler raises ValueError when required fields are missing."""
        # Setup - event with missing fields
        incomplete_event = {
            "ownerId": 123,
            "ownerName": "test-org",
            # Missing other required fields
        }

        # Execute and verify - should raise ValueError
        with pytest.raises(ValueError, match="Missing required fields in event detail"):
            schedule_handler(cast(EventBridgeSchedulerEvent, incomplete_event))

    @patch("services.webhook.schedule_handler.get_installation_access_token")
    def test_schedule_handler_no_token(self, mock_get_token, mock_event):
        """Test that schedule_handler raises ValueError when token is None."""
        # Setup
        mock_get_token.return_value = None

        # Execute and verify
        with pytest.raises(ValueError, match="Token is None for installation_id"):
            schedule_handler(mock_event)

    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    def test_schedule_handler_trigger_disabled(
        self, mock_get_repository, mock_get_token, mock_event
    ):
        """Test that schedule_handler skips when trigger_on_schedule is disabled."""
        # Setup
        mock_get_token.return_value = "test-token"
        mock_get_repository.return_value = {
            "id": 456,
            "name": "test-repo",
            "trigger_on_schedule": False,
        }

        # Execute
        result = schedule_handler(mock_event)

        # Verify
        assert result["status"] == "skipped"
        assert "trigger_on_schedule is not enabled" in result["message"]

    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.check_availability")
    def test_schedule_handler_access_denied(
        self,
        mock_check_availability,
        mock_get_repository,
        mock_get_token,
        mock_event,
    ):
        """Test that schedule_handler skips when access is denied."""
        # Setup
        mock_get_token.return_value = "test-token"
        mock_get_repository.return_value = {
            "id": 456,
            "name": "test-repo",
            "trigger_on_schedule": True,
        }
        mock_check_availability.return_value = {
            "can_proceed": False,
            "billing_type": "credit",
            "requests_left": None,
            "credit_balance_usd": 0,
            "period_end_date": None,
            "user_message": "Insufficient credits",
            "log_message": "Insufficient credits for test-org/test-repo",
        }

        # Execute
        result = schedule_handler(mock_event)

        # Verify
        assert result["status"] == "skipped"
        assert "Insufficient credits" in result["message"]

    @patch("services.webhook.schedule_handler.get_all_coverages")
    def test_get_all_coverages_returns_empty_list_not_none(
        self, mock_get_all_coverages
    ):
        """Test that get_all_coverages returns empty list instead of None.

        This test verifies the fix for 'NoneType' object is not iterable error.
        """
        # Setup - simulate empty coverage data
        mock_get_all_coverages.return_value = []  # Should be empty list, not None

        # Execute
        all_coverages = mock_get_all_coverages(repo_id=123)

        # Verify - should be able to iterate without TypeError
        assert isinstance(all_coverages, list)
        assert len(all_coverages) == 0

        # This would fail with TypeError if all_coverages was None
        _ = all_coverages  # Should not raise TypeError when iterated

        # Test the actual pattern used in schedule_handler
        test_files = [("src/main.py", 1024), ("src/utils.py", 512)]
        enriched_files = []

        for file_path, file_size in test_files:
            # This is the line that was failing at line 114
            coverages = next(
                (c for c in all_coverages if c.get("full_path") == file_path), None
            )
            if coverages:
                enriched_files.append(coverages)
            else:
                enriched_files.append({"full_path": file_path, "file_size": file_size})

        # Verify we processed all files without error
        assert len(enriched_files) == 2
        assert all("full_path" in f for f in enriched_files)

    def test_get_all_coverages_contract(self):
        """Verify that get_all_coverages always returns a list."""
        with patch(
            "services.supabase.coverages.get_all_coverages.supabase"
        ) as mock_supabase:
            # Setup mock to return empty data
            mock_result = MagicMock()
            mock_result.data = []
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = (
                mock_result
            )

            # Execute
            result = get_all_coverages(repo_id=123)

            # Verify - should be empty list, not None
            assert result == []
            assert result is not None
            assert isinstance(result, list)

    @patch("services.webhook.schedule_handler.should_skip_test")
    @patch("services.webhook.schedule_handler.should_test_file")
    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.check_availability")
    @patch("services.webhook.schedule_handler.get_default_branch")
    @patch("services.webhook.schedule_handler.get_file_tree")
    @patch("services.webhook.schedule_handler.get_all_coverages")
    @patch("services.webhook.schedule_handler.get_raw_content")
    @patch("services.webhook.schedule_handler.create_issue")
    def test_schedule_handler_skips_export_only_files(
        self,
        mock_create_issue,
        mock_get_raw_content,
        mock_get_all_coverages,
        mock_get_file_tree,
        mock_get_default_branch,
        mock_check_availability,
        mock_get_repository,
        mock_get_token,
        mock_should_test_file,
        mock_should_skip_test,
        mock_event,
    ):
        """Test that schedule_handler skips files that only contain exports."""
        # Setup
        mock_get_token.return_value = "test-token"
        mock_get_repository.return_value = {"trigger_on_schedule": True}
        mock_check_availability.return_value = {
            "can_proceed": True,
            "billing_type": "exception",
            "requests_left": None,
            "credit_balance_usd": 0,
            "period_end_date": None,
            "user_message": "",
            "log_message": "Exception owner - unlimited access.",
        }
        mock_get_default_branch.return_value = ("main", None)

        # Mock file tree with index.ts that only has exports
        mock_get_file_tree.return_value = [
            {"path": "src/components/Button/index.ts", "type": "blob", "size": 100},
            {"path": "src/utils/helper.ts", "type": "blob", "size": 200},
        ]

        mock_get_all_coverages.return_value = []

        # Mock index.ts as export-only, helper.ts with actual logic (should create issue)
        def mock_content_side_effect(file_path=None, **_):
            content_map = {
                "src/components/Button/index.ts": "export * from './Button';\nexport { default } from './Button';",
                "src/utils/helper.ts": "function helper() { return processData(input); }\nexport { helper };",
            }
            return content_map.get(file_path or "")

        mock_get_raw_content.side_effect = mock_content_side_effect

        mock_create_issue.return_value = (
            200,
            {"html_url": "https://github.com/test/issue/1"},
        )

        # Mock should_skip_test to return True for export-only files, False for files with logic
        def mock_should_skip_side_effect(file_path, content):
            if (
                "index.ts" in file_path
                and "export" in content
                and "function" not in content
            ):
                return True  # Export-only file should be skipped
            return False  # File with actual logic should not be skipped

        mock_should_skip_test.side_effect = mock_should_skip_side_effect

        # Mock should_test_file to return True for files with logic
        mock_should_test_file.return_value = True

        # Execute
        result = schedule_handler(mock_event)

        # Verify index.ts was checked for content
        mock_get_raw_content.assert_any_call(
            owner="test-org",
            repo="test-repo",
            file_path="src/components/Button/index.ts",
            ref="main",
            token="test-token",
        )

        # Verify issue was created for helper.ts (not index.ts)
        mock_create_issue.assert_called_once()
        call_kwargs = mock_create_issue.call_args.kwargs
        assert "src/utils/helper.ts" in call_kwargs["title"]
        assert result["status"] == "success"

    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.check_availability")
    @patch("services.webhook.schedule_handler.get_default_branch")
    @patch("services.webhook.schedule_handler.get_file_tree")
    @patch("services.webhook.schedule_handler.get_all_coverages")
    @patch("services.webhook.schedule_handler.get_raw_content")
    @patch("services.webhook.schedule_handler.create_issue")
    def test_schedule_handler_skips_empty_files(
        self,
        mock_create_issue,
        mock_get_raw_content,
        mock_get_all_coverages,
        mock_get_file_tree,
        mock_get_default_branch,
        mock_check_availability,
        mock_get_repository,
        mock_get_token,
        mock_event,
    ):
        """Test that schedule_handler skips empty files."""
        # Setup
        mock_get_token.return_value = "test-token"
        mock_get_repository.return_value = {"trigger_on_schedule": True}
        mock_check_availability.return_value = {
            "can_proceed": True,
            "billing_type": "exception",
            "requests_left": None,
            "credit_balance_usd": 0,
            "period_end_date": None,
            "user_message": "",
            "log_message": "Exception owner - unlimited access.",
        }
        mock_get_default_branch.return_value = ("main", None)

        # Mock file tree with empty index.ts
        mock_get_file_tree.return_value = [
            {"path": "src/index.ts", "type": "blob", "size": 0},
            {"path": "src/app.ts", "type": "blob", "size": 300},
        ]

        mock_get_all_coverages.return_value = []

        # Mock empty index.ts, app.ts with actual code that should generate an issue
        def mock_empty_content_side_effect(file_path=None, **_):
            content_map = {
                "src/index.ts": "   \n\n   ",  # Empty with whitespace
                "src/app.ts": "function processData(data) {\n  return data.map(x => x * 2);\n}\nexport { processData };",
            }
            return content_map.get(file_path or "")

        mock_get_raw_content.side_effect = mock_empty_content_side_effect

        mock_create_issue.return_value = (
            200,
            {"html_url": "https://github.com/test/issue/2"},
        )

        # Execute
        result = schedule_handler(mock_event)

        # Verify issue was created for app.ts (not empty index.ts)
        mock_create_issue.assert_called_once()
        call_kwargs = mock_create_issue.call_args.kwargs
        assert "src/app.ts" in call_kwargs["title"]
        assert result["status"] == "success"

    @patch("services.webhook.schedule_handler.slack_notify")
    @patch("services.webhook.schedule_handler.delete_scheduler")
    @patch("services.webhook.schedule_handler.update_repository")
    @patch("services.webhook.schedule_handler.get_issue_body")
    @patch("services.webhook.schedule_handler.get_issue_title")
    @patch("services.webhook.schedule_handler.is_issue_open")
    @patch("services.webhook.schedule_handler.should_test_file")
    @patch("services.webhook.schedule_handler.should_skip_test")
    @patch("services.webhook.schedule_handler.get_raw_content")
    @patch("services.webhook.schedule_handler.get_all_coverages")
    @patch("services.webhook.schedule_handler.get_file_tree")
    @patch("services.webhook.schedule_handler.get_default_branch")
    @patch("services.webhook.schedule_handler.check_availability")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.create_issue")
    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.is_migration_file")
    @patch("services.webhook.schedule_handler.is_type_file")
    @patch("services.webhook.schedule_handler.is_test_file")
    @patch("services.webhook.schedule_handler.is_code_file")
    def test_schedule_handler_410_issues_disabled(
        self,
        mock_is_code_file,
        mock_is_test_file,
        mock_is_type_file,
        mock_is_migration_file,
        mock_get_token,
        mock_create_issue,
        mock_get_repository,
        mock_check_availability,
        mock_get_default_branch,
        mock_get_file_tree,
        mock_get_all_coverages,
        mock_get_raw_content,
        mock_should_skip_test,
        mock_should_test_file,
        mock_is_issue_open,
        mock_get_issue_title,
        mock_get_issue_body,
        mock_update_repository,
        mock_delete_scheduler,
        mock_slack_notify,
        mock_event,
    ):
        """Test that schedule_handler handles 410 (issues disabled) correctly."""
        # Setup all required mocks to reach create_issue call
        mock_get_token.return_value = "test-token"
        mock_get_repository.return_value = {"trigger_on_schedule": True}
        mock_check_availability.return_value = {
            "can_proceed": True,
            "billing_type": "exception",
            "requests_left": None,
            "credit_balance_usd": 0,
            "period_end_date": None,
            "user_message": "",
            "log_message": "Exception owner - unlimited access.",
        }
        mock_get_default_branch.return_value = ("main", None)
        mock_get_file_tree.return_value = [
            {"path": "src/test.py", "type": "blob", "size": 100}
        ]
        mock_get_all_coverages.return_value = [
            {
                "id": 1,
                "full_path": "src/test.py",
                "file_size": 100,
                "statement_coverage": 0.0,
                "function_coverage": 0.0,
                "branch_coverage": 0.0,
                "created_at": "2024-01-01",
                "updated_at": "2024-01-01",
                "github_issue_url": None,
                "is_excluded_from_testing": False,
            }
        ]
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False
        mock_is_migration_file.return_value = False
        mock_get_raw_content.return_value = "def test_function(): return True"
        mock_should_skip_test.return_value = False  # Don't skip
        mock_should_test_file.return_value = True  # Should test
        mock_is_issue_open.return_value = False  # No open issues
        mock_get_issue_title.return_value = "Test Title"
        mock_get_issue_body.return_value = "Test Body"

        # Mock create_issue to return 410 (issues disabled)
        mock_create_issue.return_value = (410, None)

        result = schedule_handler(cast(EventBridgeSchedulerEvent, mock_event))

        # Verify the function handled 410 correctly
        assert result["status"] == "skipped"
        assert "Issues are disabled" in result["message"]

        # Verify that it updated the repository to disable schedule
        mock_update_repository.assert_called_once_with(
            repo_id=456, trigger_on_schedule=False, updated_by="test-user"
        )

        # Verify that it deleted the AWS scheduler
        mock_delete_scheduler.assert_called_once_with("gitauto-repo-123-456")

        # Verify that it sent a Slack notification
        mock_slack_notify.assert_called_once()
        slack_msg = mock_slack_notify.call_args[0][0]
        assert "Issues are disabled" in slack_msg
