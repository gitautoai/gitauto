# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false

# Standard imports
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest

# Local imports
from services.claude.evaluate_condition import EvaluationResult
from services.github.branches.get_default_branch import RepoInfo
from services.supabase.coverages.get_all_coverages import get_all_coverages
from services.webhook.schedule_handler import schedule_handler


@pytest.fixture
def mock_event():
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


@patch("services.webhook.schedule_handler.get_installation_access_token")
def test_schedule_handler_no_token(mock_get_token, mock_event):
    mock_get_token.return_value = None
    result = schedule_handler(mock_event)
    assert result["status"] == "skipped"
    assert "Installation" in result["message"]
    assert "no longer exists" in result["message"]


@patch("services.webhook.schedule_handler.get_installation_access_token")
@patch("services.webhook.schedule_handler.get_repository")
def test_schedule_handler_trigger_disabled(
    mock_get_repository, mock_get_token, mock_event
):
    mock_get_token.return_value = "test-token"
    mock_get_repository.return_value = {
        "id": 456,
        "name": "test-repo",
        "trigger_on_schedule": False,
    }
    result = schedule_handler(mock_event)
    assert result["status"] == "skipped"
    assert "trigger_on_schedule is not enabled" in result["message"]


@patch("services.webhook.schedule_handler.is_schedule_paused")
@patch("services.webhook.schedule_handler.get_installation_access_token")
@patch("services.webhook.schedule_handler.get_repository")
def test_schedule_handler_paused(
    mock_get_repository, mock_get_token, mock_is_paused, mock_event
):
    mock_get_token.return_value = "test-token"
    mock_get_repository.return_value = {
        "id": 456,
        "name": "test-repo",
        "trigger_on_schedule": True,
    }
    mock_is_paused.return_value = True
    result = schedule_handler(mock_event)
    assert result["status"] == "skipped"
    assert "schedule is currently paused" in result["message"]


@patch("services.webhook.schedule_handler.is_schedule_paused")
@patch("services.webhook.schedule_handler.get_installation_access_token")
@patch("services.webhook.schedule_handler.get_repository")
@patch("services.webhook.schedule_handler.check_availability")
def test_schedule_handler_access_denied(
    mock_check_availability,
    mock_get_repository,
    mock_get_token,
    mock_is_paused,
    mock_event,
):
    mock_get_token.return_value = "test-token"
    mock_is_paused.return_value = False
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
def test_get_all_coverages_returns_empty_list_not_none(mock_get_all_coverages):
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


def test_get_all_coverages_contract():
    with patch(
        "services.supabase.coverages.get_all_coverages.supabase"
    ) as mock_supabase:
        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = (
            mock_result
        )
        result = get_all_coverages(owner_id=789, repo_id=123)
        assert not result
        assert result is not None
        assert isinstance(result, list)


@patch("services.webhook.schedule_handler.add_labels")
@patch("services.webhook.schedule_handler.create_pull_request")
@patch("services.webhook.schedule_handler.create_empty_commit")
@patch("services.webhook.schedule_handler.create_remote_branch")
@patch("services.webhook.schedule_handler.get_latest_remote_commit_sha")
@patch("services.webhook.schedule_handler.generate_branch_name")
@patch("services.webhook.schedule_handler.get_open_pull_requests")
@patch("services.webhook.schedule_handler.should_skip_test")
@patch("services.webhook.schedule_handler.evaluate_condition")
@patch("services.webhook.schedule_handler.is_schedule_paused")
@patch("services.webhook.schedule_handler.get_installation_access_token")
@patch("services.webhook.schedule_handler.get_repository")
@patch("services.webhook.schedule_handler.check_availability")
@patch("services.webhook.schedule_handler.get_default_branch")
@patch("services.webhook.schedule_handler.get_file_tree")
@patch("services.webhook.schedule_handler.get_all_coverages")
@patch("services.webhook.schedule_handler.get_raw_content")
def test_schedule_handler_skips_export_only_files(
    mock_get_raw_content,
    mock_get_all_coverages,
    mock_get_file_tree,
    mock_get_default_branch,
    mock_check_availability,
    mock_get_repository,
    mock_get_token,
    mock_is_paused,
    mock_evaluate_condition,
    mock_should_skip_test,
    mock_get_open_pull_requests,
    mock_generate_branch_name,
    mock_get_latest_sha,
    mock_create_remote_branch,
    mock_create_empty_commit,
    mock_create_pr,
    mock_add_labels,
    mock_event,
):
    mock_get_token.return_value = "test-token"
    mock_is_paused.return_value = False
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
    mock_get_default_branch.return_value = RepoInfo("main", False, False)
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
    mock_generate_branch_name.return_value = "gitauto/schedule-20240101-120000-ABCD"
    mock_get_latest_sha.return_value = "abc123"
    mock_create_pr.return_value = ("https://github.com/test/repo/pull/1", 1)

    def mock_should_skip_side_effect(file_path, content):
        if (
            "index.ts" in file_path
            and "export" in content
            and "function" not in content
        ):
            return True
        return False

    mock_should_skip_test.side_effect = mock_should_skip_side_effect
    mock_evaluate_condition.return_value = EvaluationResult(True, "has testable logic")
    mock_get_open_pull_requests.return_value = []

    result = schedule_handler(mock_event)

    mock_get_raw_content.assert_any_call(
        owner="test-org",
        repo="test-repo",
        file_path="src/components/Button/index.ts",
        ref="main",
        token="test-token",
    )
    mock_create_pr.assert_called_once()
    call_kwargs = mock_create_pr.call_args.kwargs
    assert "src/utils/helper.ts" in call_kwargs["title"]
    assert result["status"] == "success"


@patch("services.webhook.schedule_handler.add_labels")
@patch("services.webhook.schedule_handler.create_pull_request")
@patch("services.webhook.schedule_handler.create_empty_commit")
@patch("services.webhook.schedule_handler.create_remote_branch")
@patch("services.webhook.schedule_handler.get_latest_remote_commit_sha")
@patch("services.webhook.schedule_handler.generate_branch_name")
@patch("services.webhook.schedule_handler.get_open_pull_requests")
@patch("services.webhook.schedule_handler.is_schedule_paused")
@patch("services.webhook.schedule_handler.get_installation_access_token")
@patch("services.webhook.schedule_handler.get_repository")
@patch("services.webhook.schedule_handler.check_availability")
@patch("services.webhook.schedule_handler.get_default_branch")
@patch("services.webhook.schedule_handler.get_file_tree")
@patch("services.webhook.schedule_handler.get_all_coverages")
@patch("services.webhook.schedule_handler.get_raw_content")
@patch("services.webhook.schedule_handler.evaluate_condition")
def test_schedule_handler_skips_empty_files(
    mock_evaluate_condition,
    mock_get_raw_content,
    mock_get_all_coverages,
    mock_get_file_tree,
    mock_get_default_branch,
    mock_check_availability,
    mock_get_repository,
    mock_get_token,
    mock_is_paused,
    mock_get_open_pull_requests,
    mock_generate_branch_name,
    mock_get_latest_sha,
    mock_create_remote_branch,
    mock_create_empty_commit,
    mock_create_pr,
    mock_add_labels,
    mock_event,
):
    mock_get_token.return_value = "test-token"
    mock_is_paused.return_value = False
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
    mock_get_default_branch.return_value = RepoInfo("main", False, False)
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
    mock_evaluate_condition.return_value = EvaluationResult(
        True, "has logic worth testing"
    )
    mock_generate_branch_name.return_value = "gitauto/schedule-20240101-120000-ABCD"
    mock_get_latest_sha.return_value = "abc123"
    mock_create_pr.return_value = ("https://github.com/test/repo/pull/2", 2)
    mock_get_open_pull_requests.return_value = []

    result = schedule_handler(mock_event)

    mock_create_pr.assert_called_once()
    call_kwargs = mock_create_pr.call_args.kwargs
    assert "src/app.ts" in call_kwargs["title"]
    assert result["status"] == "success"


@patch("services.webhook.schedule_handler.add_labels")
@patch("services.webhook.schedule_handler.create_pull_request")
@patch("services.webhook.schedule_handler.create_empty_commit")
@patch("services.webhook.schedule_handler.create_remote_branch")
@patch("services.webhook.schedule_handler.get_latest_remote_commit_sha")
@patch("services.webhook.schedule_handler.generate_branch_name")
@patch("services.webhook.schedule_handler.get_open_pull_requests")
@patch("services.webhook.schedule_handler.evaluate_condition")
@patch("services.webhook.schedule_handler.should_skip_test")
@patch("services.webhook.schedule_handler.is_schedule_paused")
@patch("services.webhook.schedule_handler.get_installation_access_token")
@patch("services.webhook.schedule_handler.get_repository")
@patch("services.webhook.schedule_handler.check_availability")
@patch("services.webhook.schedule_handler.get_default_branch")
@patch("services.webhook.schedule_handler.get_file_tree")
@patch("services.webhook.schedule_handler.get_all_coverages")
@patch("services.webhook.schedule_handler.get_raw_content")
def test_schedule_handler_prioritizes_zero_coverage_files(
    mock_get_raw_content,
    mock_get_all_coverages,
    mock_get_file_tree,
    mock_get_default_branch,
    mock_check_availability,
    mock_get_repository,
    mock_get_token,
    mock_is_paused,
    mock_should_skip_test,
    mock_evaluate_condition,
    mock_get_open_pull_requests,
    mock_generate_branch_name,
    mock_get_latest_sha,
    mock_create_remote_branch,
    mock_create_empty_commit,
    mock_create_pr,
    mock_add_labels,
    mock_event,
):
    mock_get_token.return_value = "test-token"
    mock_is_paused.return_value = False
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
    mock_get_default_branch.return_value = RepoInfo("main", False, False)
    mock_get_file_tree.return_value = [
        {"path": "src/partial.py", "type": "blob", "size": 50},
        {"path": "src/untouched.py", "type": "blob", "size": 100},
        {"path": "src/new_file.py", "type": "blob", "size": 75},
    ]
    mock_get_all_coverages.return_value = [
        {
            "id": 1,
            "full_path": "src/partial.py",
            "owner_id": 123,
            "repo_id": 456,
            "branch_name": "main",
            "created_by": "test-user",
            "updated_by": "test-user",
            "level": "file",
            "file_size": 50,
            "statement_coverage": 50.0,
            "function_coverage": 50.0,
            "branch_coverage": 50.0,
            "line_coverage": 50.0,
            "package_name": None,
            "language": None,
            "uncovered_lines": None,
            "uncovered_functions": None,
            "uncovered_branches": None,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "github_issue_url": None,
            "is_excluded_from_testing": False,
        },
        {
            "id": 2,
            "full_path": "src/untouched.py",
            "owner_id": 123,
            "repo_id": 456,
            "branch_name": "main",
            "created_by": "test-user",
            "updated_by": "test-user",
            "level": "file",
            "file_size": 100,
            "statement_coverage": 0.0,
            "function_coverage": 0.0,
            "branch_coverage": 0.0,
            "line_coverage": 0.0,
            "package_name": None,
            "language": None,
            "uncovered_lines": None,
            "uncovered_functions": None,
            "uncovered_branches": None,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "github_issue_url": None,
            "is_excluded_from_testing": False,
        },
    ]
    mock_get_raw_content.return_value = "def test(): pass"
    mock_should_skip_test.return_value = False
    mock_evaluate_condition.return_value = EvaluationResult(True, "has testable logic")
    mock_get_open_pull_requests.return_value = []
    mock_generate_branch_name.return_value = "gitauto/schedule-20240101-120000-ABCD"
    mock_get_latest_sha.return_value = "abc123"
    mock_create_pr.return_value = ("https://github.com/test/repo/pull/1", 1)

    with patch("services.webhook.schedule_handler.insert_coverages") as mock_insert:
        result = schedule_handler(mock_event)

        assert result["status"] == "success"
        mock_create_pr.assert_called_once()
        call_kwargs = mock_create_pr.call_args.kwargs
        assert "src/new_file.py" in call_kwargs["title"]
        assert "Add unit tests to" in call_kwargs["title"]

        mock_insert.assert_called_once()
        coverage_record = mock_insert.call_args[0][0]
        assert coverage_record["full_path"] == "src/new_file.py"
        assert coverage_record["owner_id"] == 123
        assert coverage_record["repo_id"] == 456
        assert coverage_record["branch_name"] == "main"
        assert coverage_record["created_by"] == "test-user"
        assert coverage_record["updated_by"] == "test-user"
        assert coverage_record["level"] == "file"
        assert coverage_record["file_size"] == 75
        assert coverage_record["statement_coverage"] == 0
        assert coverage_record["function_coverage"] == 0
        assert coverage_record["branch_coverage"] == 0
        assert coverage_record["line_coverage"] == 0
        assert coverage_record["package_name"] is None
        assert coverage_record["language"] is None
        assert (
            coverage_record["github_issue_url"] == "https://github.com/test/repo/pull/1"
        )
        assert coverage_record["is_excluded_from_testing"] is False
        assert coverage_record["uncovered_lines"] is None
        assert coverage_record["uncovered_functions"] is None
        assert coverage_record["uncovered_branches"] is None
        assert "id" not in coverage_record
        assert "created_at" not in coverage_record
        assert "updated_at" not in coverage_record


@patch("services.webhook.schedule_handler.add_labels")
@patch("services.webhook.schedule_handler.create_pull_request")
@patch("services.webhook.schedule_handler.create_empty_commit")
@patch("services.webhook.schedule_handler.create_remote_branch")
@patch("services.webhook.schedule_handler.get_latest_remote_commit_sha")
@patch("services.webhook.schedule_handler.generate_branch_name")
@patch("services.webhook.schedule_handler.get_open_pull_requests")
@patch("services.webhook.schedule_handler.should_skip_test")
@patch("services.webhook.schedule_handler.evaluate_condition")
@patch("services.webhook.schedule_handler.is_schedule_paused")
@patch("services.webhook.schedule_handler.get_installation_access_token")
@patch("services.webhook.schedule_handler.get_repository")
@patch("services.webhook.schedule_handler.check_availability")
@patch("services.webhook.schedule_handler.get_default_branch")
@patch("services.webhook.schedule_handler.get_file_tree")
@patch("services.webhook.schedule_handler.get_all_coverages")
@patch("services.webhook.schedule_handler.get_raw_content")
def test_schedule_handler_skips_ai_eval_when_tests_exist(
    mock_get_raw_content,
    mock_get_all_coverages,
    mock_get_file_tree,
    mock_get_default_branch,
    mock_check_availability,
    mock_get_repository,
    mock_get_token,
    mock_is_paused,
    mock_evaluate_condition,
    mock_should_skip_test,
    mock_get_open_pull_requests,
    mock_generate_branch_name,
    mock_get_latest_sha,
    mock_create_remote_branch,
    mock_create_empty_commit,
    mock_create_pr,
    mock_add_labels,
    mock_event,
):
    """When a file already has existing test files, skip the AI evaluation
    and select it immediately - it's proven testable."""
    mock_get_token.return_value = "test-token"
    mock_is_paused.return_value = False
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
    mock_get_default_branch.return_value = RepoInfo("main", False, False)
    # File tree has both a source file and its test file (mirror directory)
    mock_get_file_tree.return_value = [
        {"path": "src/services/getPolicyInfo.ts", "type": "blob", "size": 500},
        {
            "path": "test/spec/services/getPolicyInfo.test.ts",
            "type": "blob",
            "size": 300,
        },
    ]
    mock_get_all_coverages.return_value = [
        {
            "id": 1,
            "full_path": "src/services/getPolicyInfo.ts",
            "owner_id": 123,
            "repo_id": 456,
            "branch_name": "main",
            "created_by": "test-user",
            "updated_by": "test-user",
            "level": "file",
            "file_size": 500,
            "statement_coverage": 100.0,
            "function_coverage": 100.0,
            "branch_coverage": 93.7,
            "line_coverage": 100.0,
            "package_name": None,
            "language": None,
            "uncovered_lines": None,
            "uncovered_functions": None,
            "uncovered_branches": None,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "github_issue_url": None,
            "is_excluded_from_testing": False,
        },
    ]
    mock_get_raw_content.return_value = (
        "import { GraphqlContext } from '../context';\n"
        "const getPolicyInfo = async ({ policyId, context }) => {\n"
        "  const result = await context.mongoClient.db().collection('Policy').findOne({});\n"
        "  return result;\n"
        "};\n"
        "export default getPolicyInfo;"
    )
    mock_should_skip_test.return_value = False
    mock_get_open_pull_requests.return_value = []
    mock_generate_branch_name.return_value = "gitauto/schedule-20240101-120000-ABCD"
    mock_get_latest_sha.return_value = "abc123"
    mock_create_pr.return_value = ("https://github.com/test/repo/pull/1", 1)

    with patch("services.webhook.schedule_handler.update_issue_url"):
        result = schedule_handler(mock_event)

    assert result["status"] == "success"
    mock_create_pr.assert_called_once()
    call_kwargs = mock_create_pr.call_args.kwargs
    assert "src/services/getPolicyInfo.ts" in call_kwargs["title"]
    # AI evaluation should NOT have been called - existing tests prove testability
    mock_evaluate_condition.assert_not_called()


@patch("services.webhook.schedule_handler.get_open_pull_requests")
@patch("services.webhook.schedule_handler.should_skip_test")
@patch("services.webhook.schedule_handler.is_schedule_paused")
@patch("services.webhook.schedule_handler.get_installation_access_token")
@patch("services.webhook.schedule_handler.get_repository")
@patch("services.webhook.schedule_handler.check_availability")
@patch("services.webhook.schedule_handler.get_default_branch")
@patch("services.webhook.schedule_handler.get_file_tree")
@patch("services.webhook.schedule_handler.get_all_coverages")
@patch("services.webhook.schedule_handler.get_raw_content")
def test_schedule_handler_skips_file_with_open_pr_on_different_branch(
    mock_get_raw_content,
    mock_get_all_coverages,
    mock_get_file_tree,
    mock_get_default_branch,
    mock_check_availability,
    mock_get_repository,
    mock_get_token,
    mock_is_paused,
    mock_should_skip_test,
    mock_get_open_pull_requests,
    mock_event,
):
    mock_get_token.return_value = "test-token"
    mock_is_paused.return_value = False
    mock_get_repository.return_value = {
        "trigger_on_schedule": True,
        "target_branch": "master",
    }
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "exception",
        "requests_left": None,
        "credit_balance_usd": 0,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Exception owner - unlimited access.",
    }
    mock_get_default_branch.return_value = RepoInfo("master", False, False)
    mock_get_file_tree.return_value = [
        {"path": "src/app.php", "type": "blob", "size": 100},
    ]
    mock_get_all_coverages.return_value = [
        {
            "id": 1,
            "full_path": "src/app.php",
            "owner_id": 123,
            "repo_id": 456,
            "branch_name": "master",
            "created_by": "test-user",
            "updated_by": "test-user",
            "level": "file",
            "file_size": 100,
            "statement_coverage": 10.0,
            "function_coverage": 50.0,
            "branch_coverage": 100.0,
            "line_coverage": 10.0,
            "package_name": None,
            "language": "php",
            "uncovered_lines": None,
            "uncovered_functions": None,
            "uncovered_branches": None,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "github_issue_url": None,
            "is_excluded_from_testing": False,
        },
    ]
    mock_get_raw_content.return_value = "<?php function test() { return 1; }"
    mock_should_skip_test.return_value = False
    # Open PR targeting a DIFFERENT branch but for the same file
    mock_get_open_pull_requests.return_value = [
        {
            "number": 100,
            "title": "Schedule: Add unit tests to src/app.php",
            "base": {"ref": "release/20260311"},
            "user": {"login": "gitauto-ai[bot]"},
        },
    ]

    result = schedule_handler(mock_event)

    assert result["status"] == "skipped"
    assert "No suitable file found" in result["message"]


@patch("services.webhook.schedule_handler.get_open_pull_requests")
@patch("services.webhook.schedule_handler.should_skip_test")
@patch("services.webhook.schedule_handler.is_schedule_paused")
@patch("services.webhook.schedule_handler.get_installation_access_token")
@patch("services.webhook.schedule_handler.get_repository")
@patch("services.webhook.schedule_handler.check_availability")
@patch("services.webhook.schedule_handler.get_default_branch")
@patch("services.webhook.schedule_handler.get_file_tree")
@patch("services.webhook.schedule_handler.get_all_coverages")
@patch("services.webhook.schedule_handler.get_raw_content")
def test_schedule_handler_skips_file_with_open_pr_different_title_format(
    mock_get_raw_content,
    mock_get_all_coverages,
    mock_get_file_tree,
    mock_get_default_branch,
    mock_check_availability,
    mock_get_repository,
    mock_get_token,
    mock_is_paused,
    mock_should_skip_test,
    mock_get_open_pull_requests,
    mock_event,
):
    """Dedup works even when the existing PR uses an old title format, because the
    check is a file-path substring match, not an exact title match."""
    mock_get_token.return_value = "test-token"
    mock_is_paused.return_value = False
    mock_get_repository.return_value = {
        "trigger_on_schedule": True,
        "target_branch": "master",
    }
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "exception",
        "requests_left": None,
        "credit_balance_usd": 0,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Exception owner - unlimited access.",
    }
    mock_get_default_branch.return_value = RepoInfo("master", False, False)
    mock_get_file_tree.return_value = [
        {"path": "src/app.php", "type": "blob", "size": 100},
    ]
    mock_get_all_coverages.return_value = [
        {
            "id": 1,
            "full_path": "src/app.php",
            "owner_id": 123,
            "repo_id": 456,
            "branch_name": "master",
            "created_by": "test-user",
            "updated_by": "test-user",
            "level": "file",
            "file_size": 100,
            "statement_coverage": 10.0,
            "function_coverage": 50.0,
            "branch_coverage": 100.0,
            "line_coverage": 10.0,
            "package_name": None,
            "language": "php",
            "uncovered_lines": None,
            "uncovered_functions": None,
            "uncovered_branches": None,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "github_issue_url": None,
            "is_excluded_from_testing": False,
        },
    ]
    mock_get_raw_content.return_value = "<?php function test() { return 1; }"
    mock_should_skip_test.return_value = False
    # Old title format ("for uncovered code in") differs from current ("to"/"Achieve 100%")
    mock_get_open_pull_requests.return_value = [
        {
            "number": 100,
            "title": "Schedule: Add unit tests for uncovered code in src/app.php",
            "base": {"ref": "release/20260311"},
            "user": {"login": "gitauto-ai[bot]"},
        },
    ]

    result = schedule_handler(mock_event)

    assert result["status"] == "skipped"
    assert "No suitable file found" in result["message"]


@patch("services.webhook.schedule_handler.get_open_pull_requests")
@patch("services.webhook.schedule_handler.evaluate_condition")
@patch("services.webhook.schedule_handler.should_skip_test")
@patch("services.webhook.schedule_handler.is_schedule_paused")
@patch("services.webhook.schedule_handler.get_installation_access_token")
@patch("services.webhook.schedule_handler.get_repository")
@patch("services.webhook.schedule_handler.check_availability")
@patch("services.webhook.schedule_handler.get_default_branch")
@patch("services.webhook.schedule_handler.get_file_tree")
@patch("services.webhook.schedule_handler.get_all_coverages")
@patch("services.webhook.schedule_handler.get_raw_content")
def test_schedule_handler_skips_none_coverage_as_fully_covered(
    mock_get_raw_content,
    mock_get_all_coverages,
    mock_get_file_tree,
    mock_get_default_branch,
    mock_check_availability,
    mock_get_repository,
    mock_get_token,
    mock_is_paused,
    mock_should_skip_test,
    mock_evaluate_condition,
    mock_get_open_pull_requests,
    mock_event,
):
    """Files with 100% statement/function and None branch (e.g. PHP) should be skipped."""
    mock_get_token.return_value = "test-token"
    mock_is_paused.return_value = False
    mock_get_repository.return_value = {
        "id": 456,
        "name": "test-repo",
        "trigger_on_schedule": True,
        "target_branch": "main",
    }
    mock_check_availability.return_value = {
        "can_proceed": True,
        "requests_left": None,
        "credit_balance_usd": 0,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Exception owner - unlimited access.",
    }
    mock_get_default_branch.return_value = RepoInfo("main", False, False)
    mock_get_file_tree.return_value = [
        {"path": "src/fully_covered_php.php", "type": "blob", "size": 50},
    ]
    mock_get_all_coverages.return_value = [
        {
            "id": 1,
            "full_path": "src/fully_covered_php.php",
            "owner_id": 123,
            "repo_id": 456,
            "branch_name": "main",
            "created_by": "test-user",
            "updated_by": "test-user",
            "level": "file",
            "file_size": 50,
            "statement_coverage": 100.0,
            "function_coverage": 100.0,
            "branch_coverage": None,
            "line_coverage": 100.0,
            "package_name": None,
            "language": "php",
            "uncovered_lines": None,
            "uncovered_functions": None,
            "uncovered_branches": None,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "github_issue_url": None,
            "is_excluded_from_testing": False,
        },
    ]
    mock_get_raw_content.return_value = "<?php function test() {}"
    mock_should_skip_test.return_value = False
    mock_evaluate_condition.return_value = EvaluationResult(True, "has testable logic")
    mock_get_open_pull_requests.return_value = []

    result = schedule_handler(mock_event)

    # All files skipped (100% stmt + 100% func + None branch = fully covered), no PR created
    assert result["status"] == "skipped"


@patch("services.webhook.schedule_handler.add_labels")
@patch("services.webhook.schedule_handler.create_pull_request")
@patch("services.webhook.schedule_handler.create_empty_commit")
@patch("services.webhook.schedule_handler.create_remote_branch")
@patch("services.webhook.schedule_handler.get_latest_remote_commit_sha")
@patch("services.webhook.schedule_handler.generate_branch_name")
@patch("services.webhook.schedule_handler.get_open_pull_requests")
@patch("services.webhook.schedule_handler.evaluate_condition")
@patch("services.webhook.schedule_handler.should_skip_test")
@patch("services.webhook.schedule_handler.is_schedule_paused")
@patch("services.webhook.schedule_handler.get_installation_access_token")
@patch("services.webhook.schedule_handler.get_repository")
@patch("services.webhook.schedule_handler.check_availability")
@patch("services.webhook.schedule_handler.get_default_branch")
@patch("services.webhook.schedule_handler.get_file_tree")
@patch("services.webhook.schedule_handler.get_all_coverages")
@patch("services.webhook.schedule_handler.get_raw_content")
def test_schedule_handler_all_none_coverage_treated_as_candidate(
    mock_get_raw_content,
    mock_get_all_coverages,
    mock_get_file_tree,
    mock_get_default_branch,
    mock_check_availability,
    mock_get_repository,
    mock_get_token,
    mock_is_paused,
    mock_should_skip_test,
    mock_evaluate_condition,
    mock_get_open_pull_requests,
    mock_generate_branch_name,
    mock_get_latest_sha,
    mock_create_remote_branch,
    mock_create_empty_commit,
    mock_create_pr,
    mock_add_labels,
    mock_event,
):
    """Files with all three coverage metrics as None (never measured) should be
    treated as candidates, not skipped as fully covered.
    E.g. web/pickup/finishp.php: stmt=None, func=None, branch=None."""
    mock_get_token.return_value = "test-token"
    mock_is_paused.return_value = False
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
    mock_get_default_branch.return_value = RepoInfo("main", False, False)
    mock_get_file_tree.return_value = [
        {"path": "web/pickup/finishp.php", "type": "blob", "size": 500},
    ]
    mock_get_all_coverages.return_value = [
        {
            "id": 1,
            "full_path": "web/pickup/finishp.php",
            "owner_id": 123,
            "repo_id": 456,
            "branch_name": "main",
            "created_by": "test-user",
            "updated_by": "test-user",
            "level": "file",
            "file_size": 500,
            "statement_coverage": None,
            "function_coverage": None,
            "branch_coverage": None,
            "line_coverage": None,
            "package_name": None,
            "language": "php",
            "uncovered_lines": None,
            "uncovered_functions": None,
            "uncovered_branches": None,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "github_issue_url": None,
            "is_excluded_from_testing": False,
        },
    ]
    mock_get_raw_content.return_value = (
        "<?php session_start(); $ctrl = new Controller(); $ret = $ctrl->execute();"
    )
    mock_should_skip_test.return_value = False
    mock_evaluate_condition.return_value = EvaluationResult(True, "has testable logic")
    mock_get_open_pull_requests.return_value = []
    mock_generate_branch_name.return_value = "gitauto/schedule-20240101-120000-ABCD"
    mock_get_latest_sha.return_value = "abc123"
    mock_create_pr.return_value = ("https://github.com/test/repo/pull/1", 1)

    with patch("services.webhook.schedule_handler.insert_coverages"):
        result = schedule_handler(mock_event)

    # File with all-None coverage should become a candidate and get a PR created
    assert result["status"] == "success"
    mock_create_pr.assert_called_once()
    call_kwargs = mock_create_pr.call_args.kwargs
    assert "web/pickup/finishp.php" in call_kwargs["title"]
