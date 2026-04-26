# pylint: disable=unused-argument,too-many-lines
# pyright: reportUnusedVariable=false

# Standard imports
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest

# Local imports
from services.claude.evaluate_condition import EvaluationResult
from services.supabase.coverages.get_all_coverages import get_all_coverages
from services.supabase.schedule_pauses.get_schedule_pause import SchedulePause
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
    assert result is None


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
    assert result is None


@patch("services.webhook.schedule_handler.get_schedule_pause")
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
    mock_is_paused.return_value = SchedulePause(
        pause_start="2026-03-01T00:00:00Z", pause_end="2026-04-01T00:00:00Z"
    )
    result = schedule_handler(mock_event)
    assert result is None


@patch("services.webhook.schedule_handler.get_schedule_pause")
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
        "credit_balance_usd": 0,
        "user_message": "Insufficient credits",
        "log_message": "Insufficient credits for test-org/test-repo",
    }
    result = schedule_handler(mock_event)
    assert result is None


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


@patch("services.webhook.schedule_handler.get_clone_url")
@patch("services.webhook.schedule_handler.get_default_branch")
@patch("services.webhook.schedule_handler.create_user_request")
@patch("services.webhook.schedule_handler.get_email_from_commits")
@patch("services.webhook.schedule_handler.get_user_public_info")
@patch("services.webhook.schedule_handler.get_preferred_model")
@patch("services.webhook.schedule_handler.check_purchase_exists")
@patch("services.webhook.schedule_handler.check_availability")
@patch("services.webhook.schedule_handler.get_schedule_pause")
@patch("services.webhook.schedule_handler.get_repository")
@patch("services.webhook.schedule_handler.get_installation_access_token")
def test_schedule_handler_creates_usage_row_with_source_github(
    mock_get_token,
    mock_get_repository,
    mock_is_paused,
    mock_check_availability,
    mock_check_purchase_exists,
    mock_get_preferred_model,
    mock_get_user_public_info,
    mock_get_email_from_commits,
    mock_create_user_request,
    mock_get_default_branch,
    mock_get_clone_url,
    mock_event,
):
    mock_get_token.return_value = "test-token"
    mock_is_paused.return_value = False
    mock_get_repository.return_value = {"trigger_on_schedule": True}
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "credit_balance_usd": 100,
        "user_message": "",
        "log_message": "ok",
    }
    mock_check_purchase_exists.return_value = True
    mock_get_preferred_model.return_value = "claude-opus-4-7"
    mock_get_user_public_info.return_value = MagicMock(
        email="user@example.com", display_name="Test User"
    )
    mock_get_email_from_commits.return_value = None
    mock_create_user_request.return_value = 12345
    mock_get_clone_url.return_value = "https://x-access-token:t@github.com/o/r.git"
    # Bail at "Repository is empty" right after the usage row is created.
    mock_get_default_branch.return_value = None

    result = schedule_handler(mock_event)

    assert result is None
    mock_create_user_request.assert_called_once()
    call_kwargs = mock_create_user_request.call_args.kwargs
    assert call_kwargs["source"] == "github"
    assert call_kwargs["trigger"] == "schedule"
    assert call_kwargs["user_id"] == 789
    assert call_kwargs["user_name"] == "test-user"
    assert call_kwargs["pr_number"] == 0


@patch("services.webhook.schedule_handler.add_labels")
@patch("services.webhook.schedule_handler.create_pull_request")
@patch("services.webhook.schedule_handler.create_empty_commit")
@patch("services.webhook.schedule_handler.git_checkout")
@patch("services.webhook.schedule_handler.git_fetch")
@patch("services.webhook.schedule_handler.create_remote_branch")
@patch("services.webhook.schedule_handler.get_latest_remote_commit_sha")
@patch("services.webhook.schedule_handler.generate_branch_name")
@patch("services.webhook.schedule_handler.get_open_pull_requests")
@patch("services.webhook.schedule_handler.should_skip_test")
@patch("services.webhook.schedule_handler.evaluate_condition")
@patch("services.webhook.schedule_handler.get_schedule_pause")
@patch("services.webhook.schedule_handler.get_installation_access_token")
@patch("services.webhook.schedule_handler.get_repository")
@patch("services.webhook.schedule_handler.check_availability")
@patch("services.webhook.schedule_handler.get_default_branch")
@patch("services.webhook.schedule_handler.get_file_tree")
@patch("services.webhook.schedule_handler.get_clone_dir")
@patch("services.webhook.schedule_handler.git_clone_to_tmp")
@patch("services.webhook.schedule_handler.get_all_coverages")
@patch("services.webhook.schedule_handler.read_local_file")
def test_schedule_handler_skips_export_only_files(
    mock_read_local_file,
    mock_get_all_coverages,
    _mock_copy_repo,
    _mock_get_clone_dir,
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
    _mock_git_fetch,
    _mock_git_checkout,
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
        "credit_balance_usd": 0,
        "user_message": "",
        "log_message": "Exception owner - unlimited access.",
    }
    mock_get_default_branch.return_value = "main"
    mock_get_file_tree.return_value = [
        {
            "path": "src/components/Button/index.ts",
            "type": "blob",
            "mode": "100644",
            "sha": "abc123",
            "size": 100,
        },
        {
            "path": "src/utils/helper.ts",
            "type": "blob",
            "mode": "100644",
            "sha": "abc123",
            "size": 200,
        },
    ]
    mock_get_all_coverages.return_value = []

    def mock_content_side_effect(file_path=None, **_):
        content_map = {
            "src/components/Button/index.ts": "export * from './Button';\nexport { default } from './Button';",
            "src/utils/helper.ts": "function helper() { return processData(input); }\nexport { helper };",
        }
        return content_map.get(file_path or "")

    mock_read_local_file.side_effect = mock_content_side_effect
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

    mock_read_local_file.assert_any_call(
        file_path="src/components/Button/index.ts",
        base_dir=_mock_get_clone_dir.return_value,
    )
    mock_create_pr.assert_called_once()
    call_kwargs = mock_create_pr.call_args.kwargs
    assert (
        call_kwargs["title"]
        == "Schedule: Add unit and integration tests to `src/utils/helper.ts`"
    )
    assert result is not None


@patch("services.webhook.schedule_handler.add_labels")
@patch("services.webhook.schedule_handler.create_pull_request")
@patch("services.webhook.schedule_handler.create_empty_commit")
@patch("services.webhook.schedule_handler.git_checkout")
@patch("services.webhook.schedule_handler.git_fetch")
@patch("services.webhook.schedule_handler.create_remote_branch")
@patch("services.webhook.schedule_handler.get_latest_remote_commit_sha")
@patch("services.webhook.schedule_handler.generate_branch_name")
@patch("services.webhook.schedule_handler.get_open_pull_requests")
@patch("services.webhook.schedule_handler.get_schedule_pause")
@patch("services.webhook.schedule_handler.get_installation_access_token")
@patch("services.webhook.schedule_handler.get_repository")
@patch("services.webhook.schedule_handler.check_availability")
@patch("services.webhook.schedule_handler.get_default_branch")
@patch("services.webhook.schedule_handler.get_file_tree")
@patch("services.webhook.schedule_handler.get_clone_dir")
@patch("services.webhook.schedule_handler.git_clone_to_tmp")
@patch("services.webhook.schedule_handler.get_all_coverages")
@patch("services.webhook.schedule_handler.read_local_file")
@patch("services.webhook.schedule_handler.evaluate_condition")
def test_schedule_handler_skips_empty_files(
    mock_evaluate_condition,
    mock_read_local_file,
    mock_get_all_coverages,
    _mock_copy_repo,
    _mock_get_clone_dir,
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
    _mock_git_fetch,
    _mock_git_checkout,
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
        "credit_balance_usd": 0,
        "user_message": "",
        "log_message": "Exception owner - unlimited access.",
    }
    mock_get_default_branch.return_value = "main"
    mock_get_file_tree.return_value = [
        {
            "path": "src/index.ts",
            "type": "blob",
            "mode": "100644",
            "sha": "abc123",
            "size": 0,
        },
        {
            "path": "src/app.ts",
            "type": "blob",
            "mode": "100644",
            "sha": "abc123",
            "size": 300,
        },
    ]
    mock_get_all_coverages.return_value = []

    def mock_empty_content_side_effect(file_path=None, **_):
        content_map = {
            "src/index.ts": "   \n\n   ",
            "src/app.ts": "function processData(data) {\n  return data.map(x => x * 2);\n}\nexport { processData };",
        }
        return content_map.get(file_path or "")

    mock_read_local_file.side_effect = mock_empty_content_side_effect
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
    assert (
        call_kwargs["title"]
        == "Schedule: Add unit and integration tests to `src/app.ts`"
    )
    assert result is not None


@patch("services.webhook.schedule_handler.add_labels")
@patch("services.webhook.schedule_handler.create_pull_request")
@patch("services.webhook.schedule_handler.create_empty_commit")
@patch("services.webhook.schedule_handler.git_checkout")
@patch("services.webhook.schedule_handler.git_fetch")
@patch("services.webhook.schedule_handler.create_remote_branch")
@patch("services.webhook.schedule_handler.get_latest_remote_commit_sha")
@patch("services.webhook.schedule_handler.generate_branch_name")
@patch("services.webhook.schedule_handler.get_open_pull_requests")
@patch("services.webhook.schedule_handler.evaluate_condition")
@patch("services.webhook.schedule_handler.should_skip_test")
@patch("services.webhook.schedule_handler.get_schedule_pause")
@patch("services.webhook.schedule_handler.get_installation_access_token")
@patch("services.webhook.schedule_handler.get_repository")
@patch("services.webhook.schedule_handler.check_availability")
@patch("services.webhook.schedule_handler.get_default_branch")
@patch("services.webhook.schedule_handler.get_file_tree")
@patch("services.webhook.schedule_handler.get_clone_dir")
@patch("services.webhook.schedule_handler.git_clone_to_tmp")
@patch("services.webhook.schedule_handler.get_all_coverages")
@patch("services.webhook.schedule_handler.read_local_file")
def test_schedule_handler_prioritizes_zero_coverage_files(
    mock_read_local_file,
    mock_get_all_coverages,
    _mock_copy_repo,
    _mock_get_clone_dir,
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
    _mock_git_fetch,
    _mock_git_checkout,
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
        "credit_balance_usd": 0,
        "user_message": "",
        "log_message": "Exception owner - unlimited access.",
    }
    mock_get_default_branch.return_value = "main"
    mock_get_file_tree.return_value = [
        {
            "path": "src/partial.py",
            "type": "blob",
            "mode": "100644",
            "sha": "abc123",
            "size": 50,
        },
        {
            "path": "src/untouched.py",
            "type": "blob",
            "mode": "100644",
            "sha": "abc123",
            "size": 100,
        },
        {
            "path": "src/new_file.py",
            "type": "blob",
            "mode": "100644",
            "sha": "abc123",
            "size": 75,
        },
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
    mock_read_local_file.return_value = "def test(): pass"
    mock_should_skip_test.return_value = False
    mock_evaluate_condition.return_value = EvaluationResult(True, "has testable logic")
    mock_get_open_pull_requests.return_value = []
    mock_generate_branch_name.return_value = "gitauto/schedule-20240101-120000-ABCD"
    mock_get_latest_sha.return_value = "abc123"
    mock_create_pr.return_value = ("https://github.com/test/repo/pull/1", 1)

    with patch("services.webhook.schedule_handler.insert_coverages") as mock_insert:
        result = schedule_handler(mock_event)

        assert result is not None
        mock_create_pr.assert_called_once()
        call_kwargs = mock_create_pr.call_args.kwargs
        assert (
            call_kwargs["title"]
            == "Schedule: Add unit and integration tests to `src/new_file.py`"
        )

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
        assert coverage_record["statement_coverage"] is None
        assert coverage_record["function_coverage"] is None
        assert coverage_record["branch_coverage"] is None
        assert coverage_record["line_coverage"] is None
        assert coverage_record["package_name"] is None
        assert coverage_record["language"] is None
        assert (
            coverage_record["github_issue_url"] == "https://github.com/test/repo/pull/1"
        )
        assert coverage_record["is_excluded_from_testing"] is False
        assert coverage_record["uncovered_lines"] is None
        assert coverage_record["uncovered_functions"] is None
        assert coverage_record["uncovered_branches"] is None
        # CoveragesInsert must not carry DB-managed columns
        assert set(coverage_record.keys()).isdisjoint(
            {"id", "created_at", "updated_at"}
        )


@patch("services.webhook.schedule_handler.add_labels")
@patch("services.webhook.schedule_handler.create_pull_request")
@patch("services.webhook.schedule_handler.create_empty_commit")
@patch("services.webhook.schedule_handler.git_checkout")
@patch("services.webhook.schedule_handler.git_fetch")
@patch("services.webhook.schedule_handler.create_remote_branch")
@patch("services.webhook.schedule_handler.get_latest_remote_commit_sha")
@patch("services.webhook.schedule_handler.generate_branch_name")
@patch("services.webhook.schedule_handler.get_open_pull_requests")
@patch("services.webhook.schedule_handler.should_skip_test")
@patch("services.webhook.schedule_handler.evaluate_condition")
@patch("services.webhook.schedule_handler.get_schedule_pause")
@patch("services.webhook.schedule_handler.get_installation_access_token")
@patch("services.webhook.schedule_handler.get_repository")
@patch("services.webhook.schedule_handler.check_availability")
@patch("services.webhook.schedule_handler.get_default_branch")
@patch("services.webhook.schedule_handler.get_file_tree")
@patch("services.webhook.schedule_handler.get_clone_dir")
@patch("services.webhook.schedule_handler.git_clone_to_tmp")
@patch("services.webhook.schedule_handler.get_all_coverages")
@patch("services.webhook.schedule_handler.read_local_file")
def test_schedule_handler_skips_ai_eval_when_tests_exist(
    mock_read_local_file,
    mock_get_all_coverages,
    _mock_copy_repo,
    _mock_get_clone_dir,
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
    _mock_git_fetch,
    _mock_git_checkout,
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
        "credit_balance_usd": 0,
        "user_message": "",
        "log_message": "Exception owner - unlimited access.",
    }
    mock_get_default_branch.return_value = "main"
    # File tree has both a source file and its test file (mirror directory)
    mock_get_file_tree.return_value = [
        {
            "path": "src/services/getPolicyInfo.ts",
            "type": "blob",
            "mode": "100644",
            "sha": "abc123",
            "size": 500,
        },
        {
            "path": "test/spec/services/getPolicyInfo.test.ts",
            "type": "blob",
            "mode": "100644",
            "sha": "def456",
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
    mock_read_local_file.return_value = (
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

    assert result is not None
    mock_create_pr.assert_called_once()
    call_kwargs = mock_create_pr.call_args.kwargs
    assert (
        call_kwargs["title"]
        == "Schedule: Achieve 100% test coverage for `src/services/getPolicyInfo.ts`"
    )
    # AI evaluation should NOT have been called - existing tests prove testability
    mock_evaluate_condition.assert_not_called()


@patch("services.webhook.schedule_handler.get_open_pull_requests")
@patch("services.webhook.schedule_handler.should_skip_test")
@patch("services.webhook.schedule_handler.get_schedule_pause")
@patch("services.webhook.schedule_handler.get_installation_access_token")
@patch("services.webhook.schedule_handler.get_repository")
@patch("services.webhook.schedule_handler.check_availability")
@patch("services.webhook.schedule_handler.get_default_branch")
@patch("services.webhook.schedule_handler.get_file_tree")
@patch("services.webhook.schedule_handler.get_clone_dir")
@patch("services.webhook.schedule_handler.git_clone_to_tmp")
@patch("services.webhook.schedule_handler.get_all_coverages")
@patch("services.webhook.schedule_handler.read_local_file")
def test_schedule_handler_skips_file_with_open_pr_on_different_branch(
    mock_read_local_file,
    mock_get_all_coverages,
    _mock_copy_repo,
    _mock_get_clone_dir,
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
        "credit_balance_usd": 0,
        "user_message": "",
        "log_message": "Exception owner - unlimited access.",
    }
    mock_get_default_branch.return_value = "master"
    mock_get_file_tree.return_value = [
        {
            "path": "src/app.php",
            "type": "blob",
            "mode": "100644",
            "sha": "abc123",
            "size": 100,
        },
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
    mock_read_local_file.return_value = "<?php function test() { return 1; }"
    mock_should_skip_test.return_value = False
    # Open PR targeting a DIFFERENT branch but for the same file
    mock_get_open_pull_requests.return_value = [
        {
            "number": 100,
            "title": "Schedule: Add unit and integration tests to src/app.php",
            "base": {"ref": "release/20260311"},
            "user": {"login": "gitauto-ai[bot]"},
        },
    ]

    result = schedule_handler(mock_event)

    assert result is None


@patch("services.webhook.schedule_handler.get_open_pull_requests")
@patch("services.webhook.schedule_handler.should_skip_test")
@patch("services.webhook.schedule_handler.get_schedule_pause")
@patch("services.webhook.schedule_handler.get_installation_access_token")
@patch("services.webhook.schedule_handler.get_repository")
@patch("services.webhook.schedule_handler.check_availability")
@patch("services.webhook.schedule_handler.get_default_branch")
@patch("services.webhook.schedule_handler.get_file_tree")
@patch("services.webhook.schedule_handler.get_clone_dir")
@patch("services.webhook.schedule_handler.git_clone_to_tmp")
@patch("services.webhook.schedule_handler.get_all_coverages")
@patch("services.webhook.schedule_handler.read_local_file")
def test_schedule_handler_skips_file_with_open_pr_different_title_format(
    mock_read_local_file,
    mock_get_all_coverages,
    _mock_copy_repo,
    _mock_get_clone_dir,
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
        "credit_balance_usd": 0,
        "user_message": "",
        "log_message": "Exception owner - unlimited access.",
    }
    mock_get_default_branch.return_value = "master"
    mock_get_file_tree.return_value = [
        {
            "path": "src/app.php",
            "type": "blob",
            "mode": "100644",
            "sha": "abc123",
            "size": 100,
        },
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
    mock_read_local_file.return_value = "<?php function test() { return 1; }"
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

    assert result is None


@patch("services.webhook.schedule_handler.get_open_pull_requests")
@patch("services.webhook.schedule_handler.evaluate_condition")
@patch("services.webhook.schedule_handler.should_skip_test")
@patch("services.webhook.schedule_handler.get_schedule_pause")
@patch("services.webhook.schedule_handler.get_installation_access_token")
@patch("services.webhook.schedule_handler.get_repository")
@patch("services.webhook.schedule_handler.check_availability")
@patch("services.webhook.schedule_handler.get_default_branch")
@patch("services.webhook.schedule_handler.get_file_tree")
@patch("services.webhook.schedule_handler.get_clone_dir")
@patch("services.webhook.schedule_handler.git_clone_to_tmp")
@patch("services.webhook.schedule_handler.get_all_coverages")
@patch("services.webhook.schedule_handler.read_local_file")
@patch("services.webhook.schedule_handler.get_checklist_hash")
def test_schedule_handler_skips_none_coverage_as_fully_covered(
    mock_get_checklist_hash,
    mock_read_local_file,
    mock_get_all_coverages,
    _mock_copy_repo,
    _mock_get_clone_dir,
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
        "credit_balance_usd": 0,
        "user_message": "",
        "log_message": "Exception owner - unlimited access.",
    }
    mock_get_default_branch.return_value = "main"
    mock_get_file_tree.return_value = [
        {
            "path": "src/fully_covered_php.php",
            "type": "blob",
            "mode": "100644",
            "sha": "abc123",
            "size": 50,
        },
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
            "impl_blob_sha": "abc123",
            "test_blob_sha": None,
            "checklist_hash": "already_checked",
            "quality_checks": {"business_logic": {}},
        },
    ]
    mock_read_local_file.return_value = "<?php function test() {}"
    mock_should_skip_test.return_value = False
    mock_evaluate_condition.return_value = EvaluationResult(True, "has testable logic")
    mock_get_open_pull_requests.return_value = []
    # Return the same hash as stored in coverage data so needs_quality_reevaluation returns False
    mock_get_checklist_hash.return_value = "already_checked"

    result = schedule_handler(mock_event)

    # All files skipped (100% coverage + quality already checked), no PR created
    assert result is None


@patch("services.webhook.schedule_handler.add_labels")
@patch("services.webhook.schedule_handler.create_pull_request")
@patch("services.webhook.schedule_handler.create_empty_commit")
@patch("services.webhook.schedule_handler.git_checkout")
@patch("services.webhook.schedule_handler.git_fetch")
@patch("services.webhook.schedule_handler.create_remote_branch")
@patch("services.webhook.schedule_handler.get_latest_remote_commit_sha")
@patch("services.webhook.schedule_handler.generate_branch_name")
@patch("services.webhook.schedule_handler.get_open_pull_requests")
@patch("services.webhook.schedule_handler.evaluate_condition")
@patch("services.webhook.schedule_handler.should_skip_test")
@patch("services.webhook.schedule_handler.get_schedule_pause")
@patch("services.webhook.schedule_handler.get_installation_access_token")
@patch("services.webhook.schedule_handler.get_repository")
@patch("services.webhook.schedule_handler.check_availability")
@patch("services.webhook.schedule_handler.get_default_branch")
@patch("services.webhook.schedule_handler.get_file_tree")
@patch("services.webhook.schedule_handler.get_clone_dir")
@patch("services.webhook.schedule_handler.git_clone_to_tmp")
@patch("services.webhook.schedule_handler.get_all_coverages")
@patch("services.webhook.schedule_handler.read_local_file")
def test_schedule_handler_all_none_coverage_treated_as_candidate(
    mock_read_local_file,
    mock_get_all_coverages,
    _mock_copy_repo,
    _mock_get_clone_dir,
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
    _mock_git_fetch,
    _mock_git_checkout,
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
        "credit_balance_usd": 0,
        "user_message": "",
        "log_message": "Exception owner - unlimited access.",
    }
    mock_get_default_branch.return_value = "main"
    mock_get_file_tree.return_value = [
        {
            "path": "web/pickup/finishp.php",
            "type": "blob",
            "mode": "100644",
            "sha": "abc123",
            "size": 500,
        },
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
    mock_read_local_file.return_value = (
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
    assert result is not None
    mock_create_pr.assert_called_once()
    call_kwargs = mock_create_pr.call_args.kwargs
    # No existing test file in file tree → "Add unit and integration tests to" (not "Achieve 100%")
    assert (
        call_kwargs["title"]
        == "Schedule: Add unit and integration tests to `web/pickup/finishp.php`"
    )
    # Body should include the happy-path test guidance and exclude metric bullets for all-None coverage.
    body = call_kwargs["body"]
    has_metric_rows = any(
        metric in body
        for metric in (
            "Line Coverage:",
            "Statement Coverage:",
            "Function Coverage:",
            "Branch Coverage:",
        )
    )
    assert not has_metric_rows
    happy_start = body.find("Create tests for happy paths")
    assert happy_start >= 0


@patch("services.webhook.schedule_handler.add_labels")
@patch("services.webhook.schedule_handler.create_pull_request")
@patch("services.webhook.schedule_handler.create_empty_commit")
@patch("services.webhook.schedule_handler.git_checkout")
@patch("services.webhook.schedule_handler.git_fetch")
@patch("services.webhook.schedule_handler.create_remote_branch")
@patch("services.webhook.schedule_handler.get_latest_remote_commit_sha")
@patch("services.webhook.schedule_handler.generate_branch_name")
@patch("services.webhook.schedule_handler.get_open_pull_requests")
@patch("services.webhook.schedule_handler.evaluate_condition")
@patch("services.webhook.schedule_handler.should_skip_test")
@patch("services.webhook.schedule_handler.get_schedule_pause")
@patch("services.webhook.schedule_handler.get_installation_access_token")
@patch("services.webhook.schedule_handler.get_repository")
@patch("services.webhook.schedule_handler.check_availability")
@patch("services.webhook.schedule_handler.get_default_branch")
@patch("services.webhook.schedule_handler.get_file_tree")
@patch("services.webhook.schedule_handler.get_clone_dir")
@patch("services.webhook.schedule_handler.git_clone_to_tmp")
@patch("services.webhook.schedule_handler.get_all_coverages")
@patch("services.webhook.schedule_handler.read_local_file")
def test_schedule_handler_partial_none_coverage_omits_none_metric(
    mock_read_local_file,
    mock_get_all_coverages,
    _mock_copy_repo,
    _mock_get_clone_dir,
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
    _mock_git_fetch,
    _mock_git_checkout,
    mock_create_empty_commit,
    mock_create_pr,
    mock_add_labels,
    mock_event,
):
    """PHP file with stmt=50, func=50, branch=None, existing test file.
    Title should be 'Achieve 100%' (has existing tests), body should omit branch metric.
    """
    mock_get_token.return_value = "test-token"
    mock_is_paused.return_value = False
    mock_get_repository.return_value = {"trigger_on_schedule": True}
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "exception",
        "credit_balance_usd": 0,
        "user_message": "",
        "log_message": "Exception owner - unlimited access.",
    }
    mock_get_default_branch.return_value = "main"
    # File tree includes both source and test file
    mock_get_file_tree.return_value = [
        {
            "path": "src/services/payment.php",
            "type": "blob",
            "mode": "100644",
            "sha": "abc123",
            "size": 300,
        },
        {
            "path": "tests/services/paymentTest.php",
            "type": "blob",
            "mode": "100644",
            "sha": "abc123",
            "size": 200,
        },
    ]
    mock_get_all_coverages.return_value = [
        {
            "id": 1,
            "full_path": "src/services/payment.php",
            "owner_id": 123,
            "repo_id": 456,
            "branch_name": "main",
            "created_by": "test-user",
            "updated_by": "test-user",
            "level": "file",
            "file_size": 300,
            "statement_coverage": 50.0,
            "function_coverage": 50.0,
            "branch_coverage": None,
            "line_coverage": 50.0,
            "package_name": None,
            "language": "php",
            "uncovered_lines": "10, 15, 20",
            "uncovered_functions": "processRefund",
            "uncovered_branches": None,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "github_issue_url": None,
            "is_excluded_from_testing": False,
        },
    ]
    mock_read_local_file.return_value = (
        "<?php\nclass PaymentService {\n"
        "    public function processPayment() { return true; }\n"
        "    public function processRefund() { return false; }\n"
        "}"
    )
    mock_should_skip_test.return_value = False
    mock_evaluate_condition.return_value = EvaluationResult(True, "has testable logic")
    mock_get_open_pull_requests.return_value = []
    mock_generate_branch_name.return_value = "gitauto/schedule-20240101-120000-ABCD"
    mock_get_latest_sha.return_value = "abc123"
    mock_create_pr.return_value = ("https://github.com/test/repo/pull/1", 1)

    with patch("services.webhook.schedule_handler.update_issue_url"):
        result = schedule_handler(mock_event)

    assert result is not None
    mock_create_pr.assert_called_once()
    call_kwargs = mock_create_pr.call_args.kwargs
    # Existing test file found → "Achieve 100% test coverage for"
    assert (
        call_kwargs["title"]
        == "Schedule: Achieve 100% test coverage for `src/services/payment.php`"
    )
    # Body shows line/statement/function metrics (50% each) but NOT branch (None = not measured)
    body = call_kwargs["body"]
    assert body.find("Line Coverage: 50%") >= 0
    assert body.find("Statement Coverage: 50%") >= 0
    assert body.find("Function Coverage: 50%") >= 0
    assert body.find("Branch Coverage:") == -1


@patch("services.webhook.schedule_handler.get_all_coverages")
@patch("services.webhook.schedule_handler.git_checkout")
@patch("services.webhook.schedule_handler.git_fetch")
@patch("services.webhook.schedule_handler.git_clone_to_tmp")
@patch("services.webhook.schedule_handler.get_file_tree")
@patch("services.webhook.schedule_handler.get_clone_dir")
@patch("services.webhook.schedule_handler.get_clone_url")
@patch("services.webhook.schedule_handler.get_default_branch")
@patch("services.webhook.schedule_handler.check_availability")
@patch("services.webhook.schedule_handler.get_repository")
@patch("services.webhook.schedule_handler.get_schedule_pause")
@patch("services.webhook.schedule_handler.get_installation_access_token")
def test_get_file_tree_reads_from_clone_dir(
    mock_get_token,
    mock_is_paused,
    mock_get_repository,
    mock_check_availability,
    mock_get_default_branch,
    mock_get_clone_url,
    mock_get_clone_dir,
    mock_get_file_tree,
    _mock_clone_to_tmp,
    _mock_git_fetch,
    _mock_git_checkout,
    mock_get_all_coverages,
    mock_event,
):
    """Verify get_file_tree reads from /tmp clone_dir."""
    mock_get_token.return_value = "test-token"
    mock_is_paused.return_value = None
    mock_get_repository.return_value = {"trigger_on_schedule": True}
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "exception",
        "credit_balance_usd": 0,
        "user_message": "",
        "log_message": "Exception owner - unlimited access.",
    }
    mock_get_default_branch.return_value = "master"
    mock_get_clone_url.return_value = (
        "https://x-access-token:test-token@github.com/test-org/test-repo.git"
    )
    mock_get_clone_dir.return_value = "/tmp/test-org/test-repo"

    mock_get_file_tree.return_value = [
        {
            "path": "src/app.ts",
            "type": "blob",
            "mode": "100644",
            "sha": "a1",
            "size": 50,
        },
    ]
    mock_get_all_coverages.return_value = []

    schedule_handler(mock_event)

    # get_file_tree should be called with clone_dir (/tmp)
    mock_get_file_tree.assert_called_once_with(
        clone_dir="/tmp/test-org/test-repo", ref="master"
    )
