# Standard imports
from typing import cast
from unittest.mock import MagicMock, patch

# Third-party imports
import pytest
# Local imports
from payloads.aws.event_bridge_scheduler.event_types import \
    EventBridgeSchedulerEvent
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


@pytest.fixture
def mock_base_setup():
    """Fixture for common mock setup."""
    with patch("services.webhook.schedule_handler.get_installation_access_token") as mock_token, \
         patch("services.webhook.schedule_handler.get_repository") as mock_repo, \
         patch("services.webhook.schedule_handler.check_availability") as mock_avail, \
         patch("services.webhook.schedule_handler.get_default_branch") as mock_branch, \
         patch("services.webhook.schedule_handler.get_file_tree") as mock_tree, \
         patch("services.webhook.schedule_handler.get_all_coverages") as mock_cov:

        mock_token.return_value = "test-token"
        mock_repo.return_value = {"trigger_on_schedule": True}
        mock_avail.return_value = {
            "can_proceed": True,
            "billing_type": "exception",
            "requests_left": None,
            "credit_balance_usd": 0,
            "period_end_date": None,
            "user_message": "",
            "log_message": "Exception owner - unlimited access.",
        }
        mock_branch.return_value = ("main", None)
        mock_tree.return_value = []
        mock_cov.return_value = []

        yield {
            "token": mock_token,
            "repo": mock_repo,
            "avail": mock_avail,
            "branch": mock_branch,
            "tree": mock_tree,
            "cov": mock_cov,
        }


class TestScheduleHandler:
    def test_schedule_handler_missing_required_fields(self):
        """Test that schedule_handler raises ValueError when required fields are missing."""
        incomplete_event = {
            "ownerId": 123,
            "ownerName": "test-org",
        }

        with pytest.raises(ValueError, match="Missing required fields in event detail"):
            schedule_handler(cast(EventBridgeSchedulerEvent, incomplete_event))

    @patch("services.webhook.schedule_handler.delete_scheduler")
    @patch("services.webhook.schedule_handler.get_installation_access_token")
    def test_schedule_handler_no_token(self, mock_get_token, mock_delete_scheduler, mock_event):
        """Test that schedule_handler returns skipped status when token is None."""
        mock_get_token.return_value = None

        result = schedule_handler(mock_event)

        assert result["status"] == "skipped"
        assert "Installation" in result["message"]
        assert "no longer exists" in result["message"]
        mock_delete_scheduler.assert_called_once_with("gitauto-repo-123-456")

    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    def test_schedule_handler_trigger_disabled(
        self, mock_get_repository, mock_get_token, mock_event
    ):
        """Test that schedule_handler skips when trigger_on_schedule is disabled."""
        mock_get_token.return_value = "test-token"
        mock_get_repository.return_value = {
            "id": 456,
            "name": "test-repo",
            "trigger_on_schedule": False,
        }

        result = schedule_handler(mock_event)

        assert result["status"] == "skipped"
        assert "trigger_on_schedule is not enabled" in result["message"]

    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    def test_schedule_handler_no_repository_settings(
        self, mock_get_repository, mock_get_token, mock_event
    ):
        """Test that schedule_handler skips when repository settings are None."""
        mock_get_token.return_value = "test-token"
        mock_get_repository.return_value = None

        result = schedule_handler(mock_event)

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

        result = schedule_handler(mock_event)

        assert result["status"] == "skipped"
        assert "Insufficient credits" in result["message"]

    @patch("services.webhook.schedule_handler.get_all_coverages")
    def test_get_all_coverages_returns_empty_list_not_none(
        self, mock_get_all_coverages
    ):
        """Test that get_all_coverages returns empty list instead of None."""
        mock_get_all_coverages.return_value = []

        all_coverages = mock_get_all_coverages(repo_id=123)

        assert isinstance(all_coverages, list)
        assert len(all_coverages) == 0

        test_files = [("src/main.py", 1024), ("src/utils.py", 512)]
        enriched_files = []

        for file_path, file_size in test_files:
            coverages = next(
                (c for c in all_coverages if c.get("full_path") == file_path), None
            )
            if coverages:
                enriched_files.append(coverages)
            else:
                enriched_files.append({"full_path": file_path, "file_size": file_size})

        assert len(enriched_files) == 2
        assert all("full_path" in f for f in enriched_files)

    def test_get_all_coverages_contract(self):
        """Verify that get_all_coverages always returns a list."""
        with patch(
            "services.supabase.coverages.get_all_coverages.supabase"
        ) as mock_supabase:
            mock_result = MagicMock()
            mock_result.data = []
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = (
                mock_result
            )

            result = get_all_coverages(repo_id=123)

            assert result == []
            assert result is not None
            assert isinstance(result, list)

    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.check_availability")
    @patch("services.webhook.schedule_handler.get_default_branch")
    @patch("services.webhook.schedule_handler.get_file_tree")
    @patch("services.webhook.schedule_handler.get_all_coverages")
    def test_schedule_handler_no_files_found(
        self,
        mock_get_all_coverages,
        mock_get_file_tree,
        mock_get_default_branch,
        mock_check_availability,
        mock_get_repository,
        mock_get_token,
        mock_event,
    ):
        """Test that schedule_handler skips when no files are found (line 162-165)."""
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
        mock_get_file_tree.return_value = []
        mock_get_all_coverages.return_value = []

        result = schedule_handler(mock_event)

        assert result["status"] == "skipped"
        assert "No files found" in result["message"]
        assert "test-org/test-repo" in result["message"]

    @patch("services.webhook.schedule_handler.is_code_file")
    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.check_availability")
    @patch("services.webhook.schedule_handler.get_default_branch")
    @patch("services.webhook.schedule_handler.get_file_tree")
    @patch("services.webhook.schedule_handler.get_all_coverages")
    def test_schedule_handler_skips_non_code_files(
        self,
        mock_get_all_coverages,
        mock_get_file_tree,
        mock_get_default_branch,
        mock_check_availability,
        mock_get_repository,
        mock_get_token,
        mock_is_code_file,
        mock_event,
    ):
        """Test that schedule_handler skips non-code files (line 192-193)."""
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
            {"path": "README.md", "type": "blob", "size": 100}
        ]
        mock_get_all_coverages.return_value = []
        mock_is_code_file.return_value = False

        result = schedule_handler(mock_event)

        assert result["status"] == "skipped"
        assert "No suitable file found" in result["message"]

    @patch("services.webhook.schedule_handler.is_code_file")
    @patch("services.webhook.schedule_handler.is_test_file")
    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.check_availability")
    @patch("services.webhook.schedule_handler.get_default_branch")
    @patch("services.webhook.schedule_handler.get_file_tree")
    @patch("services.webhook.schedule_handler.get_all_coverages")
    def test_schedule_handler_skips_test_files(
        self,
        mock_get_all_coverages,
        mock_get_file_tree,
        mock_get_default_branch,
        mock_check_availability,
        mock_get_repository,
        mock_get_token,
        mock_is_test_file,
        mock_is_code_file,
        mock_event,
    ):
        """Test that schedule_handler skips test files (line 196-197)."""
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
            {"path": "test_main.py", "type": "blob", "size": 100}
        ]
        mock_get_all_coverages.return_value = []
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = True

        result = schedule_handler(mock_event)

        assert result["status"] == "skipped"
        assert "No suitable file found" in result["message"]

    @patch("services.webhook.schedule_handler.is_code_file")
    @patch("services.webhook.schedule_handler.is_test_file")
    @patch("services.webhook.schedule_handler.is_type_file")
    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.check_availability")
    @patch("services.webhook.schedule_handler.get_default_branch")
    @patch("services.webhook.schedule_handler.get_file_tree")
    @patch("services.webhook.schedule_handler.get_all_coverages")
    def test_schedule_handler_skips_type_files(
        self,
        mock_get_all_coverages,
        mock_get_file_tree,
        mock_get_default_branch,
        mock_check_availability,
        mock_get_repository,
        mock_get_token,
        mock_is_type_file,
        mock_is_test_file,
        mock_is_code_file,
        mock_event,
    ):
        """Test that schedule_handler skips type files (line 200-201)."""
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
            {"path": "types.ts", "type": "blob", "size": 100}
        ]
        mock_get_all_coverages.return_value = []
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = True

        result = schedule_handler(mock_event)

        assert result["status"] == "skipped"
        assert "No suitable file found" in result["message"]

    @patch("services.webhook.schedule_handler.is_code_file")
    @patch("services.webhook.schedule_handler.is_test_file")
    @patch("services.webhook.schedule_handler.is_type_file")
    @patch("services.webhook.schedule_handler.is_migration_file")
    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.check_availability")
    @patch("services.webhook.schedule_handler.get_default_branch")
    @patch("services.webhook.schedule_handler.get_file_tree")
    @patch("services.webhook.schedule_handler.get_all_coverages")
    def test_schedule_handler_skips_migration_files(
        self,
        mock_get_all_coverages,
        mock_get_file_tree,
        mock_get_default_branch,
        mock_check_availability,
        mock_get_repository,
        mock_get_token,
        mock_is_migration_file,
        mock_is_type_file,
        mock_is_test_file,
        mock_is_code_file,
        mock_event,
    ):
        """Test that schedule_handler skips migration files (line 204-205)."""
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
            {"path": "migrations/001_initial.sql", "type": "blob", "size": 100}
        ]
        mock_get_all_coverages.return_value = []
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False
        mock_is_migration_file.return_value = True

        result = schedule_handler(mock_event)

        assert result["status"] == "skipped"
        assert "No suitable file found" in result["message"]

    @patch("services.webhook.schedule_handler.is_code_file")
    @patch("services.webhook.schedule_handler.is_test_file")
    @patch("services.webhook.schedule_handler.is_type_file")
    @patch("services.webhook.schedule_handler.is_migration_file")
    @patch("services.webhook.schedule_handler.get_raw_content")
    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.check_availability")
    @patch("services.webhook.schedule_handler.get_default_branch")
    @patch("services.webhook.schedule_handler.get_file_tree")
    @patch("services.webhook.schedule_handler.get_all_coverages")
    def test_schedule_handler_skips_files_excluded_from_testing(
        self,
        mock_get_all_coverages,
        mock_get_file_tree,
        mock_get_default_branch,
        mock_check_availability,
        mock_get_repository,
        mock_get_token,
        mock_get_raw_content,
        mock_is_migration_file,
        mock_is_type_file,
        mock_is_test_file,
        mock_is_code_file,
        mock_event,
    ):
        """Test that schedule_handler skips files excluded from testing (line 224-225)."""
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
            {"path": "src/excluded.py", "type": "blob", "size": 100}
        ]
        mock_get_all_coverages.return_value = [
            {
                "id": 1,
                "full_path": "src/excluded.py",
                "file_size": 100,
                "statement_coverage": 0.0,
                "function_coverage": 0.0,
                "branch_coverage": 0.0,
                "line_coverage": 0.0,
                "uncovered_lines": None,
                "uncovered_functions": None,
                "uncovered_branches": None,
                "created_at": "2024-01-01",
                "updated_at": "2024-01-01",
                "github_issue_url": None,
                "is_excluded_from_testing": True,
            }
        ]
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False
        mock_is_migration_file.return_value = False
        mock_get_raw_content.return_value = "def excluded(): pass"

        result = schedule_handler(mock_event)

        assert result["status"] == "skipped"
        assert "No suitable file found" in result["message"]

    @patch("services.webhook.schedule_handler.is_code_file")
    @patch("services.webhook.schedule_handler.is_test_file")
    @patch("services.webhook.schedule_handler.is_type_file")
    @patch("services.webhook.schedule_handler.is_migration_file")
    @patch("services.webhook.schedule_handler.get_raw_content")
    @patch("services.webhook.schedule_handler.is_issue_open")
    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.check_availability")
    @patch("services.webhook.schedule_handler.get_default_branch")
    @patch("services.webhook.schedule_handler.get_file_tree")
    @patch("services.webhook.schedule_handler.get_all_coverages")
    def test_schedule_handler_skips_files_with_open_issues(
        self,
        mock_get_all_coverages,
        mock_get_file_tree,
        mock_get_default_branch,
        mock_check_availability,
        mock_get_repository,
        mock_get_token,
        mock_is_issue_open,
        mock_get_raw_content,
        mock_is_migration_file,
        mock_is_type_file,
        mock_is_test_file,
        mock_is_code_file,
        mock_event,
    ):
        """Test that schedule_handler skips files with open GitHub issues (line 229-230)."""
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
            {"path": "src/with_issue.py", "type": "blob", "size": 100}
        ]
        mock_get_all_coverages.return_value = [
            {
                "id": 1,
                "full_path": "src/with_issue.py",
                "file_size": 100,
                "statement_coverage": 0.0,
                "function_coverage": 0.0,
                "branch_coverage": 0.0,
                "line_coverage": 0.0,
                "uncovered_lines": None,
                "uncovered_functions": None,
                "uncovered_branches": None,
                "created_at": "2024-01-01",
                "updated_at": "2024-01-01",
                "github_issue_url": "https://github.com/test/issue/1",
                "is_excluded_from_testing": False,
            }
        ]
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False
        mock_is_migration_file.return_value = False
        mock_get_raw_content.return_value = "def with_issue(): pass"
        mock_is_issue_open.return_value = True

        result = schedule_handler(mock_event)

        assert result["status"] == "skipped"
        assert "No suitable file found" in result["message"]

    @patch("services.webhook.schedule_handler.is_code_file")
    @patch("services.webhook.schedule_handler.is_test_file")
    @patch("services.webhook.schedule_handler.is_type_file")
    @patch("services.webhook.schedule_handler.is_migration_file")
    @patch("services.webhook.schedule_handler.get_raw_content")
    @patch("services.webhook.schedule_handler.should_test_file")
    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.check_availability")
    @patch("services.webhook.schedule_handler.get_default_branch")
    @patch("services.webhook.schedule_handler.get_file_tree")
    @patch("services.webhook.schedule_handler.get_all_coverages")
    def test_schedule_handler_skips_files_should_not_test(
        self,
        mock_get_all_coverages,
        mock_get_file_tree,
        mock_get_default_branch,
        mock_check_availability,
        mock_get_repository,
        mock_get_token,
        mock_should_test_file,
        mock_get_raw_content,
        mock_is_migration_file,
        mock_is_type_file,
        mock_is_test_file,
        mock_is_code_file,
        mock_event,
    ):
        """Test that schedule_handler skips files that should not be tested (line 233-234)."""
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
            {"path": "src/no_test.py", "type": "blob", "size": 100}
        ]
        mock_get_all_coverages.return_value = []
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False
        mock_is_migration_file.return_value = False
        mock_get_raw_content.return_value = "def no_test(): pass"
        mock_should_test_file.return_value = False

        result = schedule_handler(mock_event)

        assert result["status"] == "skipped"
        assert "No suitable file found" in result["message"]

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
            {"path": "src/components/Button/index.ts", "type": "blob", "size": 100},
            {"path": "src/utils/helper.ts", "type": "blob", "size": 200},
        ]

        mock_get_all_coverages.return_value = []

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

        def mock_should_skip_side_effect(file_path, content):
            if (
                "index.ts" in file_path
                and "export" in content
                and "function" not in content
            ):
                return True
            return False

        mock_should_skip_test.side_effect = mock_should_skip_side_effect

        mock_should_test_file.return_value = True

        result = schedule_handler(mock_event)

        mock_get_raw_content.assert_any_call(
            owner="test-org",
            repo="test-repo",
            file_path="src/components/Button/index.ts",
            ref="main",
            token="test-token",
        )

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
            {"path": "src/index.ts", "type": "blob", "size": 0},
            {"path": "src/app.ts", "type": "blob", "size": 300},
        ]

        mock_get_all_coverages.return_value = []

        def mock_empty_content_side_effect(file_path=None, **_):
            content_map = {
                "src/index.ts": "   \n\n   ",
                "src/app.ts": "function processData(data) {\n  return data.map(x => x * 2);\n}\nexport { processData };",
            }
            return content_map.get(file_path or "")

        mock_get_raw_content.side_effect = mock_empty_content_side_effect

        mock_create_issue.return_value = (
            200,
            {"html_url": "https://github.com/test/issue/2"},
        )

        result = schedule_handler(mock_event)

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
                "line_coverage": 0.0,
                "uncovered_lines": None,
                "uncovered_functions": None,
                "uncovered_branches": None,
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
        mock_should_skip_test.return_value = False
        mock_should_test_file.return_value = True
        mock_is_issue_open.return_value = False
        mock_get_issue_title.return_value = "Test Title"
        mock_get_issue_body.return_value = "Test Body"

        mock_create_issue.return_value = (410, None)

        result = schedule_handler(cast(EventBridgeSchedulerEvent, mock_event))

        assert result["status"] == "skipped"
        assert "Issues are disabled" in result["message"]

        mock_update_repository.assert_called_once_with(
            repo_id=456, trigger_on_schedule=False, updated_by="test-user"
        )

        mock_delete_scheduler.assert_called_once_with("gitauto-repo-123-456")

        mock_slack_notify.assert_called_once()
        slack_msg = mock_slack_notify.call_args[0][0]
        assert "Issues are disabled" in slack_msg

    @patch("services.webhook.schedule_handler.insert_coverages")
    @patch("services.webhook.schedule_handler.get_issue_body")
    @patch("services.webhook.schedule_handler.get_issue_title")
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
    def test_schedule_handler_success_new_coverage_record(
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
        mock_get_issue_title,
        mock_get_issue_body,
        mock_insert_coverages,
        mock_event,
    ):
        """Test successful issue creation with new coverage record (line 285-291)."""
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
            {"path": "src/new_file.py", "type": "blob", "size": 100}
        ]
        mock_get_all_coverages.return_value = []
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False
        mock_is_migration_file.return_value = False
        mock_get_raw_content.return_value = "def new_function(): return True"
        mock_should_skip_test.return_value = False
        mock_should_test_file.return_value = True
        mock_get_issue_title.return_value = "Test Title"
        mock_get_issue_body.return_value = "Test Body"

        mock_create_issue.return_value = (
            200,
            {"html_url": "https://github.com/test/issue/3"},
        )

        result = schedule_handler(cast(EventBridgeSchedulerEvent, mock_event))

        assert result["status"] == "success"
        assert "created issue for src/new_file.py" in result["message"]

        mock_insert_coverages.assert_called_once()
        inserted_record = mock_insert_coverages.call_args[0][0]
        assert inserted_record["full_path"] == "src/new_file.py"
        assert inserted_record["github_issue_url"] == "https://github.com/test/issue/3"
        assert "id" not in inserted_record
        assert "created_at" not in inserted_record
        assert "updated_at" not in inserted_record

    @patch("services.webhook.schedule_handler.update_issue_url")
    @patch("services.webhook.schedule_handler.get_issue_body")
    @patch("services.webhook.schedule_handler.get_issue_title")
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
    def test_schedule_handler_success_existing_coverage_record(
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
        mock_get_issue_title,
        mock_get_issue_body,
        mock_update_issue_url,
        mock_event,
    ):
        """Test successful issue creation with existing coverage record (line 293-297)."""
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
            {"path": "src/existing.py", "type": "blob", "size": 100}
        ]
        mock_get_all_coverages.return_value = [
            {
                "id": 5,
                "full_path": "src/existing.py",
                "file_size": 100,
                "statement_coverage": 50.0,
                "function_coverage": 50.0,
                "branch_coverage": 50.0,
                "line_coverage": 50.0,
                "uncovered_lines": None,
                "uncovered_functions": None,
                "uncovered_branches": None,
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
        mock_get_raw_content.return_value = "def existing_function(): return True"
        mock_should_skip_test.return_value = False
        mock_should_test_file.return_value = True
        mock_get_issue_title.return_value = "Test Title"
        mock_get_issue_body.return_value = "Test Body"

        mock_create_issue.return_value = (
            200,
            {"html_url": "https://github.com/test/issue/4"},
        )

        result = schedule_handler(cast(EventBridgeSchedulerEvent, mock_event))

        assert result["status"] == "success"
        assert "created issue for src/existing.py" in result["message"]

        mock_update_issue_url.assert_called_once_with(
            repo_id=456,
            file_path="src/existing.py",
            github_issue_url="https://github.com/test/issue/4",
        )

    @patch("services.webhook.schedule_handler.get_issue_body")
    @patch("services.webhook.schedule_handler.get_issue_title")
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
    def test_schedule_handler_failed_issue_creation(
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
        mock_get_issue_title,
        mock_get_issue_body,
        mock_event,
    ):
        """Test failed issue creation (line 303-305)."""
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
            {"path": "src/failed.py", "type": "blob", "size": 100}
        ]
        mock_get_all_coverages.return_value = []
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False
        mock_is_migration_file.return_value = False
        mock_get_raw_content.return_value = "def failed_function(): return True"
        mock_should_skip_test.return_value = False
        mock_should_test_file.return_value = True
        mock_get_issue_title.return_value = "Test Title"
        mock_get_issue_body.return_value = "Test Body"

        mock_create_issue.return_value = (500, None)

        result = schedule_handler(cast(EventBridgeSchedulerEvent, mock_event))

        assert result["status"] == "failed"
        assert "Failed to create issue for src/failed.py" in result["message"]
        assert "status: 500" in result["message"]

    @patch("services.webhook.schedule_handler.get_issue_body")
    @patch("services.webhook.schedule_handler.get_issue_title")
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
    def test_schedule_handler_failed_issue_creation_no_html_url(
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
        mock_get_issue_title,
        mock_get_issue_body,
        mock_event,
    ):
        """Test failed issue creation when response has no html_url (line 284 branch)."""
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
            {"path": "src/no_url.py", "type": "blob", "size": 100}
        ]
        mock_get_all_coverages.return_value = []
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False
        mock_is_migration_file.return_value = False
        mock_get_raw_content.return_value = "def no_url_function(): return True"
        mock_should_skip_test.return_value = False
        mock_should_test_file.return_value = True
        mock_get_issue_title.return_value = "Test Title"
        mock_get_issue_body.return_value = "Test Body"

        mock_create_issue.return_value = (200, {})

        result = schedule_handler(cast(EventBridgeSchedulerEvent, mock_event))

        assert result["status"] == "failed"
        assert "Failed to create issue for src/no_url.py" in result["message"]
        assert "status: 200" in result["message"]

    @patch("services.webhook.schedule_handler.get_issue_body")
    @patch("services.webhook.schedule_handler.get_issue_title")
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
    def test_schedule_handler_failed_issue_creation_none_response(
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
        mock_get_issue_title,
        mock_get_issue_body,
        mock_event,
    ):
        """Test failed issue creation when response is None (line 284 branch)."""
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
            {"path": "src/none_response.py", "type": "blob", "size": 100}
        ]
        mock_get_all_coverages.return_value = []
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False
        mock_is_migration_file.return_value = False
        mock_get_raw_content.return_value = "def none_response_function(): return True"
        mock_should_skip_test.return_value = False
        mock_should_test_file.return_value = True
        mock_get_issue_title.return_value = "Test Title"
        mock_get_issue_body.return_value = "Test Body"

        mock_create_issue.return_value = (200, None)

        result = schedule_handler(cast(EventBridgeSchedulerEvent, mock_event))

        assert result["status"] == "failed"
        assert "Failed to create issue for src/none_response.py" in result["message"]
        assert "status: 200" in result["message"]

    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.check_availability")
    @patch("services.webhook.schedule_handler.get_default_branch")
    @patch("services.webhook.schedule_handler.get_file_tree")
    @patch("services.webhook.schedule_handler.get_all_coverages")
    def test_schedule_handler_all_files_have_100_percent_coverage(
        self,
        mock_get_all_coverages,
        mock_get_file_tree,
        mock_get_default_branch,
        mock_check_availability,
        mock_get_repository,
        mock_get_token,
        mock_event,
    ):
        """Test when all files have 100% coverage (line 240-243)."""
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
            {"path": "src/perfect.py", "type": "blob", "size": 100}
        ]
        mock_get_all_coverages.return_value = [
            {
                "id": 1,
                "full_path": "src/perfect.py",
                "file_size": 100,
                "statement_coverage": 100.0,
                "function_coverage": 100.0,
                "branch_coverage": 100.0,
                "line_coverage": 100.0,
                "uncovered_lines": None,
                "uncovered_functions": None,
                "uncovered_branches": None,
                "created_at": "2024-01-01",
                "updated_at": "2024-01-01",
                "github_issue_url": None,
                "is_excluded_from_testing": False,
            }
        ]

        result = schedule_handler(mock_event)

        assert result["status"] == "skipped"
        assert "No suitable file found" in result["message"]
