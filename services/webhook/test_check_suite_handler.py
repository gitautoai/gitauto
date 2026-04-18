"""Unit tests for check_suite_handler.py"""

# pyright: reportUnusedVariable=false
# pylint: disable=too-many-lines

# Test to verify imports work correctly
# Standard imports
import hashlib
import random
from unittest.mock import patch

import pytest

from config import GITHUB_APP_USER_NAME, PRODUCT_ID, UTF8
from constants.messages import CHECK_RUN_FAILED_MESSAGE
from services.agents.verify_task_is_complete import VerifyTaskIsCompleteResult
from services.chat_with_agent import AgentResult
from services.webhook.check_suite_handler import handle_check_suite


@pytest.fixture(autouse=True)
def _mock_refresh_mongodb_cache():
    with patch("services.webhook.check_suite_handler.refresh_mongodb_cache"):
        yield


@pytest.fixture
def mock_check_run_payload(test_owner, test_repo):
    """Fixture providing a mock check suite payload."""
    return {
        "action": "completed",
        "check_suite": {
            "id": 12345,
            "head_branch": f"{PRODUCT_ID}/dashboard-20250101-120000-Ab1C",
            "head_sha": "abc123",
            "status": "completed",
            "conclusion": "failure",
            "pull_requests": [
                {
                    "number": 1,
                    "url": "https://api.github.com/repos/owner/repo/pulls/1",
                    "base": {"ref": "main"},
                }
            ],
        },
        "repository": {
            "id": 98765,
            "name": test_repo,
            "owner": {
                "id": 11111,
                "login": test_owner,
                "type": "Organization",
            },
            "clone_url": f"https://github.com/{test_owner}/{test_repo}.git",
            "fork": False,
        },
        "sender": {
            "id": 22222,
            "login": GITHUB_APP_USER_NAME,
        },
        "installation": {
            "id": 33333,
        },
    }


@pytest.fixture
def mock_pr_data():
    """Fixture providing mock PR data."""
    return {
        "title": "Low Test Coverage: src/main.py",
        "body": "Test PR description",
        "user": {"login": "test-user"},
        "base": {"ref": "main"},
    }


@pytest.fixture
def mock_workflow_run_logs():
    """Fixture providing mock workflow run logs."""
    return "Test failure log content"


@pytest.fixture
def mock_file_tree():
    """Fixture providing mock file tree."""
    return "src/\n  main.py\n  test_main.py"


@pytest.fixture
def mock_pr_changes():
    """Fixture providing mock PR changes."""
    return [
        {
            "filename": "src/main.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
        }
    ]


@pytest.mark.asyncio
@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
async def test_handle_check_suite_skips_non_gitauto_branch(
    mock_get_repo, mock_get_token, mock_get_failed_runs, mock_check_run_payload
):
    """Test that handler skips when branch doesn't start with PRODUCT_ID."""
    # Modify head_branch to not start with PRODUCT_ID
    payload = mock_check_run_payload.copy()
    payload["check_suite"] = payload["check_suite"].copy()
    payload["check_suite"]["id"] = random.randint(1000000, 9999999)
    payload["check_suite"]["head_branch"] = "non-gitauto-branch"

    await handle_check_suite(payload)

    # Verify no further processing occurred
    mock_get_token.assert_not_called()
    mock_get_repo.assert_not_called()
    mock_get_failed_runs.assert_not_called()


@pytest.mark.asyncio
@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.get_pull_request")
async def test_handle_check_suite_skips_when_trigger_disabled(
    mock_get_pr,
    mock_get_repo,
    mock_get_token,
    mock_get_failed_runs,
    mock_check_run_payload,
):
    """Test that handler skips when trigger_on_test_failure is disabled."""
    payload = mock_check_run_payload.copy()
    payload["check_suite"] = payload["check_suite"].copy()
    payload["check_suite"]["id"] = random.randint(1000000, 9999999)

    mock_get_token.return_value = "ghs_test_token_for_testing"
    mock_get_failed_runs.return_value = [
        {
            "details_url": "https://github.com/test-owner/test-repo/actions/runs/12345/job/67890",
            "name": "test",
            "head_sha": "abc123",
        }
    ]
    mock_get_pr.return_value = {
        "title": "Low Test Coverage: src/main.py",
        "body": "Test PR description",
        "user": {"login": "test-user"},
        "base": {"ref": "main"},
    }
    mock_get_repo.return_value = {"trigger_on_test_failure": False}

    await handle_check_suite(payload)

    mock_get_token.assert_called_once()
    mock_get_failed_runs.assert_called_once()
    mock_get_pr.assert_called_once()
    mock_get_repo.assert_called_once_with(owner_id=11111, repo_id=98765)


@pytest.mark.asyncio
@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.get_pr_comments")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.ensure_node_packages")
@patch("services.webhook.check_suite_handler.ensure_php_packages")
@patch(
    "services.webhook.check_suite_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.check_suite_handler.git_merge_base_into_pr")
@patch("services.webhook.check_suite_handler.clone_repo_and_install_dependencies")
async def test_handle_check_suite_skips_when_comment_exists(
    _mock_prepare_repo,
    _mock_get_behind,
    _mock_merge_base,
    _mock_ensure_php,
    _mock_start_async,
    mock_create_comment,
    mock_get_pr_comments,
    mock_slack_notify,
    mock_get_pr,
    mock_get_repo,
    mock_get_token,
    mock_get_failed_runs,
    mock_check_run_payload,
):
    """Test that handler skips when relevant comment already exists."""
    payload = mock_check_run_payload.copy()
    payload["check_suite"] = payload["check_suite"].copy()
    payload["check_suite"]["id"] = random.randint(1000000, 9999999)

    mock_get_token.return_value = "ghs_test_token_for_testing"
    mock_get_failed_runs.return_value = [
        {
            "details_url": "https://github.com/test-owner/test-repo/actions/runs/12345/job/67890",
            "name": "test",
            "head_sha": "abc123",
        }
    ]
    mock_get_pr.return_value = {
        "title": "Low Test Coverage: src/main.py",
        "body": "Test PR description",
        "user": {"login": "test-user"},
        "base": {"ref": "main"},
    }
    mock_get_repo.return_value = {"trigger_on_test_failure": True}
    mock_get_pr_comments.return_value = [
        {
            "user": {"login": GITHUB_APP_USER_NAME},
            "body": CHECK_RUN_FAILED_MESSAGE,
            "created_at": "2025-01-01T00:00:00Z",
        }
    ]

    await handle_check_suite(payload)

    mock_get_token.assert_called_once()
    mock_get_failed_runs.assert_called_once()
    mock_get_pr.assert_called_once()
    mock_get_repo.assert_called()
    assert mock_get_pr_comments.call_count == 2
    mock_create_comment.assert_not_called()
    mock_slack_notify.assert_called()


@pytest.mark.asyncio
@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.get_pr_comments")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.get_workflow_run_logs")
@patch("services.webhook.check_suite_handler.clean_logs")
@patch("services.webhook.check_suite_handler.get_retry_error_hashes")
@patch("services.webhook.check_suite_handler.update_retry_error_hashes")
@patch("services.webhook.check_suite_handler.check_older_active_test_failure_request")
@patch("services.webhook.check_suite_handler.should_bail")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.update_usage")
@patch("services.webhook.check_suite_handler.create_empty_commit")
@patch("services.webhook.check_suite_handler.verify_task_is_complete")
@patch("services.webhook.check_suite_handler.ensure_node_packages")
@patch("services.webhook.check_suite_handler.ensure_php_packages")
@patch(
    "services.webhook.check_suite_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.check_suite_handler.git_merge_base_into_pr")
@patch("services.webhook.check_suite_handler.clone_repo_and_install_dependencies")
async def test_handle_check_suite_race_condition_prevention(
    _mock_prepare_repo,
    _mock_get_behind,
    _mock_merge_base,
    _mock_ensure_php,
    _mock_start_async,
    _mock_verify_task,
    _mock_create_empty_commit,
    mock_update_usage,
    mock_update_comment,
    mock_should_bail,
    mock_check_older_active,
    mock_update_retry_hashes,
    mock_get_retry_hashes,
    mock_clean_logs,
    mock_get_workflow_logs,
    mock_get_pr_files,
    mock_get_pr,
    mock_cancel_workflows,
    mock_create_user_request,
    mock_create_comment,
    mock_get_pr_comments,
    mock_slack_notify,
    mock_get_repo,
    mock_get_token,
    mock_get_failed_runs,
    mock_check_run_payload,
):
    """Test that handler properly detects and handles race conditions."""
    # Setup mocks for normal flow until race check
    payload = mock_check_run_payload.copy()
    payload["check_suite"] = payload["check_suite"].copy()
    payload["check_suite"]["id"] = random.randint(1000000, 9999999)

    mock_get_token.return_value = "ghs_test_token_for_testing"
    mock_get_failed_runs.return_value = [
        {
            "details_url": "https://github.com/test-owner/test-repo/actions/runs/12345/job/67890",
            "name": "test",
            "head_sha": "abc123",
        }
    ]
    mock_get_repo.return_value = {"trigger_on_test_failure": True}
    mock_get_pr_comments.return_value = []
    mock_create_comment.return_value = (
        "https://github.com/test/test/issues/1#issuecomment-123"
    )
    mock_create_user_request.return_value = 12345
    mock_cancel_workflows.return_value = None
    mock_get_pr.return_value = {
        "title": "Low Test Coverage: src/main.py",
        "body": "Test PR description",
        "user": {"login": "test-user"},
        "base": {"ref": "main"},
    }
    mock_get_pr_files.return_value = [{"filename": "test.py", "status": "modified"}]
    mock_get_workflow_logs.return_value = "Error: Test failure"
    mock_clean_logs.return_value = "Cleaned error log"
    mock_get_retry_hashes.return_value = []
    mock_update_retry_hashes.return_value = None

    # Let execution loop proceed to race condition check
    mock_should_bail.return_value = False

    # Setup race condition detection - older active request found
    mock_check_older_active.return_value = {
        "id": 11111,
        "created_at": "2025-09-28T14:19:01.247+00:00",
    }

    await handle_check_suite(payload)

    # Verify race prevention logic was triggered
    mock_check_older_active.assert_called_with(
        owner_id=11111, repo_id=98765, pr_number=1, current_usage_id=12345
    )

    # Verify proper cleanup when race detected
    # Check that update_usage was called with correct parameters
    call_args = mock_update_usage.call_args
    assert call_args is not None
    kwargs = call_args.kwargs
    assert kwargs["usage_id"] == 12345
    assert kwargs["token_input"] == 0  # Should be 0 since no LLM calls made yet
    assert kwargs["token_output"] == 0
    assert kwargs["is_completed"] is True
    assert kwargs["pr_number"] == 1
    assert isinstance(kwargs["total_seconds"], int)  # Should be small integer
    assert "retry_error_hashes" in kwargs
    assert "original_error_log" in kwargs
    assert "minimized_error_log" in kwargs

    # Verify notification was sent
    mock_slack_notify.assert_called()
    mock_update_comment.assert_called()


@pytest.mark.asyncio
@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.get_pr_comments")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.get_workflow_run_logs")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.get_retry_error_hashes")
@patch("services.webhook.check_suite_handler.update_retry_error_hashes")
@patch("services.webhook.check_suite_handler.should_bail", return_value=False)
@patch("services.webhook.check_suite_handler.chat_with_agent")
@patch("services.webhook.check_suite_handler.create_empty_commit")
@patch("services.webhook.check_suite_handler.update_usage")
@patch("services.webhook.check_suite_handler.ensure_node_packages")
@patch("services.webhook.check_suite_handler.ensure_php_packages")
@patch(
    "services.webhook.check_suite_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.check_suite_handler.git_merge_base_into_pr")
@patch("services.webhook.check_suite_handler.clone_repo_and_install_dependencies")
async def test_handle_check_suite_full_workflow(
    _mock_prepare_repo,
    _mock_get_behind,
    _mock_merge_base,
    _mock_ensure_php,
    _mock_start_async,
    _mock_update_usage,
    _mock_create_empty_commit,
    mock_chat_agent,
    _mock_should_bail,
    _mock_update_retry_hashes,
    mock_get_retry_hashes,
    _mock_update_comment,
    mock_get_logs,
    mock_get_changes,
    mock_get_pr,
    _mock_cancel_workflow_runs,
    mock_create_user_request,
    mock_create_comment,
    mock_get_pr_comments,
    _mock_slack_notify,
    mock_get_repo,
    mock_get_token,
    mock_get_failed_runs,
    mock_check_run_payload,
):
    """Test the full workflow of handling a check run failure."""
    # Setup mocks
    payload = mock_check_run_payload.copy()
    payload["check_suite"] = payload["check_suite"].copy()
    payload["check_suite"]["id"] = random.randint(1000000, 9999999)

    mock_get_token.return_value = "ghs_test_token_for_testing"
    mock_get_failed_runs.return_value = [
        {
            "details_url": "https://github.com/test-owner/test-repo/actions/runs/12345/job/67890",
            "name": "test",
            "head_sha": "abc123",
        }
    ]
    mock_get_repo.return_value = {"trigger_on_test_failure": True}
    mock_get_pr_comments.return_value = []
    mock_create_comment.return_value = "http://comment-url"
    mock_create_user_request.return_value = "usage-id-123"
    mock_get_pr.return_value = {
        "title": "Low Test Coverage: src/main.py",
        "body": "Test PR description",
        "user": {"login": "test-user"},
        "base": {"ref": "main"},
    }
    mock_get_changes.return_value = [
        {
            "filename": "src/main.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
        }
    ]
    mock_get_logs.return_value = "Test failure log content"
    mock_get_retry_hashes.return_value = []

    mock_chat_agent.side_effect = [
        AgentResult(
            messages=[],
            token_input=50,
            token_output=25,
            is_completed=False,
            completion_reason="",
            p=50,
            is_planned=False,
            cost_usd=0.0,
        ),
        AgentResult(
            messages=[],
            token_input=30,
            token_output=20,
            is_completed=True,
            completion_reason="",
            p=75,
            is_planned=False,
            cost_usd=0.0,
        ),
    ]

    # Execute
    await handle_check_suite(payload)

    # Verify key functions were called
    mock_get_token.assert_called_once()
    mock_get_repo.assert_called()
    mock_create_comment.assert_called_once()
    mock_create_user_request.assert_called_once()
    mock_get_pr.assert_called_once()
    mock_get_changes.assert_called_once()
    mock_get_logs.assert_called_once()
    mock_get_retry_hashes.assert_called_once()
    assert mock_chat_agent.call_count == 2

    # Verify execution call has system_message and baseline_tsc_errors
    execution_call = mock_chat_agent.call_args_list[0]
    assert "system_message" in execution_call.kwargs
    assert isinstance(execution_call.kwargs["system_message"], str)
    base_args = execution_call.kwargs["base_args"]
    assert "baseline_tsc_errors" in base_args
    assert isinstance(base_args["baseline_tsc_errors"], set)


@pytest.mark.asyncio
@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.get_pr_comments")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.get_workflow_run_logs")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.create_permission_url")
@patch("services.webhook.check_suite_handler.get_installation_permissions")
@patch("services.webhook.check_suite_handler.ensure_node_packages")
@patch("services.webhook.check_suite_handler.ensure_php_packages")
@patch(
    "services.webhook.check_suite_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.check_suite_handler.git_merge_base_into_pr")
@patch("services.webhook.check_suite_handler.clone_repo_and_install_dependencies")
async def test_handle_check_suite_with_404_logs(
    _mock_prepare_repo,
    _mock_get_behind,
    _mock_merge_base,
    _mock_ensure_php,
    _mock_start_async,
    mock_get_permissions,
    mock_create_permission_url,
    mock_update_comment,
    mock_get_logs,
    mock_get_changes,
    mock_get_pr,
    _mock_cancel_workflow_runs,
    mock_create_user_request,
    mock_create_comment,
    mock_get_pr_comments,
    _mock_slack_notify,
    mock_get_repo,
    mock_get_token,
    mock_get_failed_runs,
    mock_check_run_payload,
):
    """Test handling when workflow logs return 404."""
    # Setup mocks
    payload = mock_check_run_payload.copy()
    payload["check_suite"] = payload["check_suite"].copy()
    payload["check_suite"]["id"] = random.randint(1000000, 9999999)

    mock_get_token.return_value = "ghs_test_token_for_testing"
    mock_get_failed_runs.return_value = [
        {
            "details_url": "https://github.com/test-owner/test-repo/actions/runs/12345/job/67890",
            "name": "test",
            "head_sha": "abc123",
        }
    ]
    mock_get_repo.return_value = {"trigger_on_test_failure": True}
    mock_get_pr_comments.return_value = []
    mock_create_comment.return_value = "http://comment-url"
    mock_create_user_request.return_value = "usage-id-123"
    mock_get_pr.return_value = {
        "title": "Low Test Coverage: src/main.py",
        "body": "Test PR description",
        "user": {"login": "test-user"},
        "base": {"ref": "main"},
    }
    mock_get_changes.return_value = [
        {
            "filename": "src/main.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
        }
    ]
    mock_get_logs.return_value = 404
    mock_create_permission_url.return_value = "https://permission-url"
    mock_get_permissions.return_value = {"actions": "read"}

    # Execute
    await handle_check_suite(payload)

    # Verify
    mock_get_token.assert_called_once()
    mock_get_repo.assert_called()
    mock_create_comment.assert_called_once()
    mock_create_user_request.assert_called_once()
    mock_get_pr.assert_called_once()
    mock_get_changes.assert_called_once()
    mock_get_logs.assert_called_once()
    mock_create_permission_url.assert_called_once()
    mock_get_permissions.assert_called_once()

    # Verify permission denied message in comment
    mock_update_comment.assert_called()


@pytest.mark.asyncio
@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.get_pr_comments")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.get_workflow_run_logs")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.ensure_node_packages")
@patch("services.webhook.check_suite_handler.ensure_php_packages")
@patch(
    "services.webhook.check_suite_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.check_suite_handler.git_merge_base_into_pr")
@patch("services.webhook.check_suite_handler.clone_repo_and_install_dependencies")
async def test_handle_check_suite_with_none_logs(
    _mock_prepare_repo,
    _mock_get_behind,
    _mock_merge_base,
    _mock_ensure_php,
    _mock_start_async,
    mock_update_comment,
    mock_get_logs,
    mock_get_changes,
    mock_get_pr,
    _mock_cancel_workflow_runs,
    mock_create_user_request,
    mock_create_comment,
    mock_get_pr_comments,
    _mock_slack_notify,
    mock_get_repo,
    mock_get_token,
    mock_get_failed_runs,
    mock_check_run_payload,
):
    """Test handling when workflow logs return None."""
    # Setup mocks
    payload = mock_check_run_payload.copy()
    payload["check_suite"] = payload["check_suite"].copy()
    payload["check_suite"]["id"] = random.randint(1000000, 9999999)

    mock_get_token.return_value = "ghs_test_token_for_testing"
    mock_get_failed_runs.return_value = [
        {
            "details_url": "https://github.com/test-owner/test-repo/actions/runs/12345/job/67890",
            "name": "test",
            "head_sha": "abc123",
        }
    ]
    mock_get_repo.return_value = {"trigger_on_test_failure": True}
    mock_get_pr_comments.return_value = []
    mock_create_comment.return_value = "http://comment-url"
    mock_create_user_request.return_value = "usage-id-123"
    mock_get_pr.return_value = {
        "title": "Low Test Coverage: src/main.py",
        "body": "Test PR description",
        "user": {"login": "test-user"},
        "base": {"ref": "main"},
    }
    mock_get_changes.return_value = [
        {
            "filename": "src/main.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
        }
    ]
    mock_get_logs.return_value = None

    # Execute
    await handle_check_suite(payload)

    # Verify
    mock_get_token.assert_called_once()
    mock_get_repo.assert_called()
    mock_create_comment.assert_called_once()
    mock_create_user_request.assert_called_once()
    mock_get_pr.assert_called_once()
    mock_get_changes.assert_called_once()
    mock_get_logs.assert_called_once()

    # Verify error message in comment
    mock_update_comment.assert_called()


@pytest.mark.asyncio
@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.get_pr_comments")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.get_workflow_run_logs")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.get_retry_error_hashes")
@patch("services.webhook.check_suite_handler.update_retry_error_hashes")
@patch("services.webhook.check_suite_handler.update_usage")
@patch("services.webhook.check_suite_handler.clean_logs")
@patch("services.webhook.check_suite_handler.ensure_node_packages")
@patch("services.webhook.check_suite_handler.ensure_php_packages")
@patch(
    "services.webhook.check_suite_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.check_suite_handler.git_merge_base_into_pr")
@patch("services.webhook.check_suite_handler.clone_repo_and_install_dependencies")
async def test_handle_check_suite_with_existing_retry_pair(
    _mock_prepare_repo,
    _mock_get_behind,
    _mock_merge_base,
    _mock_ensure_php,
    _mock_start_async,
    mock_clean_logs,
    mock_update_usage,
    _mock_update_retry_hashes,
    mock_get_retry_hashes,
    mock_update_comment,
    mock_get_logs,
    mock_get_changes,
    mock_get_pr,
    _mock_cancel_workflow_runs,
    mock_create_user_request,
    mock_create_comment,
    mock_get_pr_comments,
    _mock_slack_notify,
    mock_get_repo,
    mock_get_token,
    mock_get_failed_runs,
    mock_check_run_payload,
):
    """Test handling when the workflow/error pair has already been attempted."""
    # Setup mocks
    payload = mock_check_run_payload.copy()
    payload["check_suite"] = payload["check_suite"].copy()
    payload["check_suite"]["id"] = random.randint(1000000, 9999999)

    mock_get_token.return_value = "ghs_test_token_for_testing"
    mock_get_failed_runs.return_value = [
        {
            "details_url": "https://github.com/test-owner/test-repo/actions/runs/12345/job/67890",
            "name": "test",
            "head_sha": "abc123",
        }
    ]
    mock_get_repo.return_value = {"trigger_on_test_failure": True}
    mock_get_pr_comments.return_value = []
    mock_create_comment.return_value = "http://comment-url"
    mock_create_user_request.return_value = "usage-id-123"
    mock_get_pr.return_value = {
        "title": "Low Test Coverage: src/main.py",
        "body": "Test PR description",
        "user": {"login": "test-user"},
        "base": {"ref": "main"},
    }
    mock_get_changes.return_value = [
        {
            "filename": "src/main.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
        }
    ]
    mock_get_logs.return_value = "Test failure log content"
    mock_clean_logs.return_value = "Cleaned test failure log"

    # Mock that this error hash has been seen before
    expected_hash = hashlib.sha256("Test failure log content".encode(UTF8)).hexdigest()
    mock_get_retry_hashes.return_value = [expected_hash]

    # Execute
    await handle_check_suite(payload)

    # Verify
    mock_get_token.assert_called_once()
    mock_get_repo.assert_called()
    mock_create_comment.assert_called_once()
    mock_create_user_request.assert_called_once()
    mock_get_pr.assert_called_once()
    mock_get_changes.assert_called_once()
    mock_get_logs.assert_called_once()
    mock_get_retry_hashes.assert_called_once()
    mock_clean_logs.assert_called_once_with("Test failure log content")

    # Verify update_usage was called with error logs
    mock_update_usage.assert_called_once()
    call_args = mock_update_usage.call_args[1]
    assert call_args["original_error_log"] == "Test failure log content"
    assert call_args["minimized_error_log"] == "Cleaned test failure log"

    # Verify skip message in comment
    mock_update_comment.assert_called()


@pytest.mark.asyncio
@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.get_pr_comments")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.get_workflow_run_logs")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.get_retry_error_hashes")
@patch("services.webhook.check_suite_handler.update_retry_error_hashes")
@patch("services.webhook.check_suite_handler.should_bail", return_value=True)
@patch("services.webhook.check_suite_handler.create_empty_commit")
@patch("services.webhook.check_suite_handler.update_usage")
@patch("services.webhook.check_suite_handler.ensure_node_packages")
@patch("services.webhook.check_suite_handler.ensure_php_packages")
@patch(
    "services.webhook.check_suite_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.check_suite_handler.git_merge_base_into_pr")
@patch("services.webhook.check_suite_handler.clone_repo_and_install_dependencies")
async def test_handle_check_suite_with_closed_pr(
    _mock_prepare_repo,
    _mock_get_behind,
    _mock_merge_base,
    _mock_ensure_php,
    _mock_start_async,
    _mock_update_usage,
    _mock_create_empty_commit,
    mock_should_bail,
    _mock_update_retry_hashes,
    mock_get_retry_hashes,
    mock_update_comment,
    mock_get_logs,
    mock_get_changes,
    mock_get_pr,
    _mock_cancel_workflow_runs,
    mock_create_user_request,
    mock_create_comment,
    mock_get_pr_comments,
    _mock_slack_notify,
    mock_get_repo,
    mock_get_token,
    mock_get_failed_runs,
    mock_check_run_payload,
):
    """Test handling when the PR is closed during processing."""
    # Setup mocks
    payload = mock_check_run_payload.copy()
    payload["check_suite"] = payload["check_suite"].copy()
    payload["check_suite"]["id"] = random.randint(1000000, 9999999)

    mock_get_token.return_value = "ghs_test_token_for_testing"
    mock_get_failed_runs.return_value = [
        {
            "details_url": "https://github.com/test-owner/test-repo/actions/runs/12345/job/67890",
            "name": "test",
            "head_sha": "abc123",
        }
    ]
    mock_get_repo.return_value = {"trigger_on_test_failure": True}
    mock_get_pr_comments.return_value = []
    mock_create_comment.return_value = "http://comment-url"
    mock_create_user_request.return_value = "usage-id-123"
    mock_get_pr.return_value = {
        "title": "Low Test Coverage: src/main.py",
        "body": "Test PR description",
        "user": {"login": "test-user"},
        "base": {"ref": "main"},
    }
    mock_get_changes.return_value = [
        {
            "filename": "src/main.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
        }
    ]
    mock_get_logs.return_value = "Test failure log content"
    mock_get_retry_hashes.return_value = []

    # Execute
    await handle_check_suite(payload)

    # Verify
    mock_get_token.assert_called_once()
    mock_get_repo.assert_called()
    mock_create_comment.assert_called_once()
    mock_create_user_request.assert_called_once()
    mock_get_pr.assert_called_once()
    mock_get_changes.assert_called_once()
    mock_get_logs.assert_called_once()
    mock_should_bail.assert_called()

    # Verify comment was updated (post-loop update)
    mock_update_comment.assert_called()


@pytest.mark.asyncio
@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.get_pr_comments")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.get_workflow_run_logs")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.get_retry_error_hashes")
@patch("services.webhook.check_suite_handler.update_retry_error_hashes")
@patch("services.webhook.check_suite_handler.should_bail", return_value=True)
@patch("services.webhook.check_suite_handler.create_empty_commit")
@patch("services.webhook.check_suite_handler.update_usage")
@patch("services.webhook.check_suite_handler.ensure_node_packages")
@patch("services.webhook.check_suite_handler.ensure_php_packages")
@patch(
    "services.webhook.check_suite_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.check_suite_handler.git_merge_base_into_pr")
@patch("services.webhook.check_suite_handler.clone_repo_and_install_dependencies")
async def test_handle_check_suite_with_deleted_branch(
    _mock_prepare_repo,
    _mock_get_behind,
    _mock_merge_base,
    _mock_ensure_php,
    _mock_start_async,
    _mock_update_usage,
    _mock_create_empty_commit,
    mock_should_bail,
    _mock_update_retry_hashes,
    mock_get_retry_hashes,
    mock_update_comment,
    mock_get_logs,
    mock_get_changes,
    mock_get_pr,
    _mock_cancel_workflow_runs,
    mock_create_user_request,
    mock_create_comment,
    mock_get_pr_comments,
    _mock_slack_notify,
    mock_get_repo,
    mock_get_token,
    mock_get_failed_runs,
    mock_check_run_payload,
):
    """Test handling when the branch is deleted during processing."""
    # Setup mocks
    payload = mock_check_run_payload.copy()
    payload["check_suite"] = payload["check_suite"].copy()
    payload["check_suite"]["id"] = random.randint(1000000, 9999999)

    mock_get_token.return_value = "ghs_test_token_for_testing"
    mock_get_failed_runs.return_value = [
        {
            "details_url": "https://github.com/test-owner/test-repo/actions/runs/12345/job/67890",
            "name": "test",
            "head_sha": "abc123",
        }
    ]
    mock_get_repo.return_value = {"trigger_on_test_failure": True}
    mock_get_pr_comments.return_value = []
    mock_create_comment.return_value = "http://comment-url"
    mock_create_user_request.return_value = "usage-id-123"
    mock_get_pr.return_value = {
        "title": "Low Test Coverage: src/main.py",
        "body": "Test PR description",
        "user": {"login": "test-user"},
        "base": {"ref": "main"},
    }
    mock_get_changes.return_value = [
        {
            "filename": "src/main.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
        }
    ]
    mock_get_logs.return_value = "Test failure log content"
    mock_get_retry_hashes.return_value = []

    # Execute
    await handle_check_suite(payload)

    # Verify
    mock_get_token.assert_called_once()
    mock_get_repo.assert_called()
    mock_create_comment.assert_called_once()
    mock_create_user_request.assert_called_once()
    mock_get_pr.assert_called_once()
    mock_get_changes.assert_called_once()
    mock_get_logs.assert_called_once()
    mock_should_bail.assert_called()

    # Verify comment was updated (post-loop update)
    mock_update_comment.assert_called()


@pytest.mark.asyncio
@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.get_pr_comments")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.get_workflow_run_logs")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.get_retry_error_hashes")
@patch("services.webhook.check_suite_handler.update_retry_error_hashes")
@patch("services.webhook.check_suite_handler.should_bail", return_value=False)
@patch("services.webhook.check_suite_handler.chat_with_agent")
@patch("services.webhook.check_suite_handler.create_empty_commit")
@patch("services.webhook.check_suite_handler.update_usage")
@patch("services.webhook.check_suite_handler.ensure_node_packages")
@patch("services.webhook.check_suite_handler.ensure_php_packages")
@patch(
    "services.webhook.check_suite_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.check_suite_handler.git_merge_base_into_pr")
@patch("services.webhook.check_suite_handler.clone_repo_and_install_dependencies")
async def test_check_run_handler_token_accumulation(
    _mock_prepare_repo,
    _mock_get_behind,
    _mock_merge_base,
    _mock_ensure_php,
    _mock_start_async,
    mock_update_usage,
    _mock_create_empty_commit,
    mock_chat_agent,
    _mock_should_bail,
    _mock_update_retry_hashes,
    mock_get_retry_hashes,
    _mock_update_comment,
    mock_get_logs,
    mock_get_changes,
    mock_get_pr,
    _mock_cancel_workflow_runs,
    mock_create_user_request,
    mock_create_comment,
    mock_get_pr_comments,
    _mock_slack_notify,
    mock_get_repo,
    mock_get_token,
    mock_get_failed_runs,
    mock_check_run_payload,
):
    """Test that check run handler accumulates tokens correctly and calls update_usage"""
    # Setup mocks
    payload = mock_check_run_payload.copy()
    payload["check_suite"] = payload["check_suite"].copy()
    payload["check_suite"]["id"] = random.randint(1000000, 9999999)

    mock_get_token.return_value = "ghs_test_token_for_testing"
    mock_get_failed_runs.return_value = [
        {
            "details_url": "https://github.com/test-owner/test-repo/actions/runs/12345/job/67890",
            "name": "test",
            "head_sha": "abc123",
        }
    ]
    mock_get_repo.return_value = {"trigger_on_test_failure": True}
    mock_get_pr_comments.return_value = []
    mock_create_comment.return_value = "http://comment-url"
    mock_create_user_request.return_value = 888
    mock_get_pr.return_value = {
        "title": "Low Test Coverage: src/main.py",
        "body": "Test PR description",
        "user": {"login": "test-user"},
        "base": {"ref": "main"},
    }
    mock_get_changes.return_value = [
        {
            "filename": "src/main.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
        }
    ]
    mock_get_logs.return_value = "Test failure log content"
    mock_get_retry_hashes.return_value = []

    mock_chat_agent.side_effect = [
        AgentResult(
            messages=[{"role": "user", "content": "test"}],
            token_input=80,
            token_output=45,
            is_completed=False,
            completion_reason="",
            p=90,
            is_planned=False,
            cost_usd=0.0,
        ),
        AgentResult(
            messages=[{"role": "user", "content": "test"}],
            token_input=80,
            token_output=45,
            is_completed=True,
            completion_reason="",
            p=95,
            is_planned=False,
            cost_usd=0.0,
        ),
    ]

    # Execute
    await handle_check_suite(payload)

    assert mock_chat_agent.call_count == 2

    # Verify update_usage was called with accumulated tokens
    mock_update_usage.assert_called_once()
    call_kwargs = mock_update_usage.call_args.kwargs

    assert call_kwargs["usage_id"] == 888
    assert call_kwargs["token_input"] == 160  # Two calls: 80 + 80
    assert call_kwargs["token_output"] == 90  # Two calls: 45 + 45


@pytest.mark.asyncio
@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.get_pr_comments")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.get_workflow_run_logs")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.get_retry_error_hashes")
@patch("services.webhook.check_suite_handler.clean_logs")
@patch("services.webhook.check_suite_handler.check_older_active_test_failure_request")
@patch("services.webhook.check_suite_handler.update_usage")
@patch("services.webhook.check_suite_handler.create_empty_commit")
@patch("services.webhook.check_suite_handler.verify_task_is_complete")
@patch("services.webhook.check_suite_handler.should_bail", return_value=False)
@patch("services.webhook.check_suite_handler.ensure_node_packages")
@patch("services.webhook.check_suite_handler.ensure_php_packages")
@patch(
    "services.webhook.check_suite_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.check_suite_handler.git_merge_base_into_pr")
@patch("services.webhook.check_suite_handler.clone_repo_and_install_dependencies")
async def test_handle_check_suite_skips_duplicate_older_request(
    _mock_prepare_repo,
    _mock_get_behind,
    _mock_merge_base,
    _mock_ensure_php,
    _mock_start_async,
    _mock_should_bail,
    _mock_verify_task,
    _mock_create_empty_commit,
    mock_update_usage,
    mock_check_older_active,
    mock_clean_logs,
    mock_get_retry_hashes,
    _mock_update_comment,
    mock_get_logs,
    mock_get_changes,
    mock_get_pr,
    _mock_cancel_workflow_runs,
    mock_create_user_request,
    mock_create_comment,
    mock_get_pr_comments,
    mock_slack_notify,
    mock_get_repo,
    mock_get_token,
    mock_get_failed_runs,
    mock_check_run_payload,
):
    """Test that handler skips when older active request is found."""
    # Setup mocks
    payload = mock_check_run_payload.copy()
    payload["check_suite"] = payload["check_suite"].copy()
    payload["check_suite"]["id"] = random.randint(1000000, 9999999)

    mock_get_token.return_value = "ghs_test_token_for_testing"
    mock_get_failed_runs.return_value = [
        {
            "details_url": "https://github.com/test-owner/test-repo/actions/runs/12345/job/67890",
            "name": "test",
            "head_sha": "abc123",
        }
    ]
    mock_get_repo.return_value = {"trigger_on_test_failure": True}
    mock_get_pr_comments.return_value = []
    mock_create_comment.return_value = "http://comment-url"
    mock_slack_notify.return_value = "thread-123"
    mock_create_user_request.return_value = 999
    mock_get_pr.return_value = {
        "title": "Low Test Coverage: src/main.py",
        "body": "Test PR description",
        "user": {"login": "test-user"},
        "base": {"ref": "main"},
    }
    mock_get_changes.return_value = [
        {
            "filename": "src/main.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
        }
    ]
    mock_get_logs.return_value = "Test failure log content"
    mock_get_retry_hashes.return_value = []
    mock_clean_logs.return_value = "Cleaned test failure log"
    mock_check_older_active.return_value = {
        "id": 888,
        "created_at": "2025-09-23T10:00:00Z",
    }

    # Execute
    await handle_check_suite(payload)

    # Verify
    mock_get_token.assert_called_once()
    mock_get_repo.assert_called()
    mock_create_comment.assert_called_once()
    mock_create_user_request.assert_called_once()
    mock_check_older_active.assert_called_once_with(
        owner_id=11111, repo_id=98765, pr_number=1, current_usage_id=999
    )

    # Verify duplicate handling
    mock_update_usage.assert_called_once()
    call_kwargs = mock_update_usage.call_args.kwargs
    assert call_kwargs["usage_id"] == 999
    assert call_kwargs["is_completed"] is True
    assert call_kwargs["token_input"] == 0
    assert call_kwargs["token_output"] == 0

    # Verify Slack notifications
    assert (
        mock_slack_notify.call_count == 3
    )  # Start notification + duplicate notification + completion notification
    duplicate_call = mock_slack_notify.call_args_list[1]
    assert "older active test failure request found" in duplicate_call[0][0]
    assert duplicate_call[0][1] == "thread-123"  # Uses thread_ts


@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.get_pr_comments")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.get_retry_error_hashes")
@patch("services.webhook.check_suite_handler.update_retry_error_hashes")
@pytest.mark.asyncio
@patch("services.webhook.check_suite_handler.should_bail", return_value=False)
@patch("services.webhook.check_suite_handler.chat_with_agent")
@patch("services.webhook.check_suite_handler.create_empty_commit")
@patch("services.webhook.check_suite_handler.update_usage")
@patch("services.webhook.check_suite_handler.get_codecov_token")
@patch("services.webhook.check_suite_handler.get_codecov_commit_coverage")
@patch("services.webhook.check_suite_handler.ensure_node_packages")
@patch("services.webhook.check_suite_handler.ensure_php_packages")
@patch(
    "services.webhook.check_suite_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.check_suite_handler.git_merge_base_into_pr")
@patch("services.webhook.check_suite_handler.clone_repo_and_install_dependencies")
async def test_handle_check_suite_codecov_failure(
    _mock_prepare_repo,
    _mock_get_behind,
    _mock_merge_base,
    _mock_ensure_php,
    _mock_start_async,
    mock_get_codecov_coverage,
    mock_get_codecov_token,
    _mock_update_usage,
    _mock_create_empty_commit,
    mock_chat_agent,
    _mock_should_bail,
    _mock_update_retry_hashes,
    mock_get_retry_hashes,
    _mock_update_comment,
    mock_get_changes,
    mock_get_pr,
    _mock_cancel_workflow_runs,
    mock_create_user_request,
    mock_create_comment,
    mock_get_pr_comments,
    _mock_slack_notify,
    mock_get_repo,
    mock_get_token,
    mock_get_failed_runs,
    mock_check_run_payload,
):
    """Test handling codecov check run failures with coverage data."""
    payload = mock_check_run_payload.copy()
    payload["check_suite"] = payload["check_suite"].copy()
    payload["check_suite"]["id"] = random.randint(1000000, 9999999)

    mock_get_token.return_value = "ghs_test_token_for_testing"
    mock_get_failed_runs.return_value = [
        {
            "details_url": "https://codecov.io/gh/test-owner/test-repo/commit/abc123",
            "name": "codecov/project",
            "head_sha": "abc123",
            "output": {
                "title": "Coverage decreased",
                "summary": "Coverage decreased by 2.5%",
                "text": "Detailed coverage report",
            },
        }
    ]
    mock_get_repo.return_value = {"trigger_on_test_failure": True}
    mock_get_pr_comments.return_value = []
    mock_create_comment.return_value = "http://comment-url"
    mock_create_user_request.return_value = "usage-id-123"
    mock_get_pr.return_value = {
        "title": "Low Test Coverage: src/main.py",
        "body": "Test PR description",
        "user": {"login": "test-user"},
        "base": {"ref": "main"},
    }
    mock_get_changes.return_value = [
        {
            "filename": "src/main.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
        }
    ]
    mock_get_retry_hashes.return_value = []
    mock_get_codecov_token.return_value = "codecov_token_123"
    mock_get_codecov_coverage.return_value = [
        {
            "name": "src/main.py",
            "coverage": 75.0,
            "uncovered_lines": [10, 15, 20],
            "partially_covered_lines": [25],
        }
    ]
    mock_chat_agent.side_effect = [
        AgentResult(
            messages=[],
            token_input=50,
            token_output=25,
            is_completed=False,
            completion_reason="",
            p=50,
            is_planned=False,
            cost_usd=0.0,
        ),
        AgentResult(
            messages=[],
            token_input=30,
            token_output=20,
            is_completed=True,
            completion_reason="",
            p=75,
            is_planned=False,
            cost_usd=0.0,
        ),
    ]

    await handle_check_suite(payload)

    mock_get_codecov_token.assert_called_once_with(11111)
    mock_get_codecov_coverage.assert_called_once_with(
        owner="gitautoai",
        repo="gitauto",
        commit_sha="abc123",
        codecov_token="codecov_token_123",
        service="github",
    )
    assert mock_chat_agent.call_count == 2


@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.get_pr_comments")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.get_retry_error_hashes")
@patch("services.webhook.check_suite_handler.update_retry_error_hashes")
@pytest.mark.asyncio
@patch("services.webhook.check_suite_handler.should_bail", return_value=False)
@patch("services.webhook.check_suite_handler.chat_with_agent")
@patch("services.webhook.check_suite_handler.create_empty_commit")
@patch("services.webhook.check_suite_handler.update_usage")
@patch("services.webhook.check_suite_handler.get_codecov_token")
@patch("services.webhook.check_suite_handler.ensure_node_packages")
@patch("services.webhook.check_suite_handler.ensure_php_packages")
@patch(
    "services.webhook.check_suite_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.check_suite_handler.git_merge_base_into_pr")
@patch("services.webhook.check_suite_handler.clone_repo_and_install_dependencies")
async def test_handle_check_suite_codecov_no_token(
    _mock_prepare_repo,
    _mock_get_behind,
    _mock_merge_base,
    _mock_ensure_php,
    _mock_start_async,
    mock_get_codecov_token,
    _mock_update_usage,
    _mock_create_empty_commit,
    mock_chat_agent,
    _mock_should_bail,
    _mock_update_retry_hashes,
    mock_get_retry_hashes,
    _mock_update_comment,
    mock_get_changes,
    mock_get_pr,
    _mock_cancel_workflow_runs,
    mock_create_user_request,
    mock_create_comment,
    mock_get_pr_comments,
    _mock_slack_notify,
    mock_get_repo,
    mock_get_token,
    mock_get_failed_runs,
    mock_check_run_payload,
):
    """Test handling codecov failures when no codecov token is configured."""
    payload = mock_check_run_payload.copy()
    payload["check_suite"] = payload["check_suite"].copy()
    payload["check_suite"]["id"] = random.randint(1000000, 9999999)

    mock_get_token.return_value = "ghs_test_token_for_testing"
    mock_get_failed_runs.return_value = [
        {
            "details_url": "https://codecov.io/gh/test-owner/test-repo/commit/abc123",
            "name": "codecov/project",
            "head_sha": "abc123",
            "output": {
                "title": "Coverage decreased",
                "summary": "Coverage decreased by 2.5%",
                "text": "Detailed coverage report",
            },
        }
    ]
    mock_get_repo.return_value = {"trigger_on_test_failure": True}
    mock_get_pr_comments.return_value = []
    mock_create_comment.return_value = "http://comment-url"
    mock_create_user_request.return_value = "usage-id-123"
    mock_get_pr.return_value = {
        "title": "Low Test Coverage: src/main.py",
        "body": "Test PR description",
        "user": {"login": "test-user"},
        "base": {"ref": "main"},
    }
    mock_get_changes.return_value = [
        {
            "filename": "src/main.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
        }
    ]
    mock_get_retry_hashes.return_value = []
    mock_get_codecov_token.return_value = None
    mock_chat_agent.side_effect = [
        AgentResult(
            messages=[],
            token_input=50,
            token_output=25,
            is_completed=False,
            completion_reason="",
            p=50,
            is_planned=False,
            cost_usd=0.0,
        ),
        AgentResult(
            messages=[],
            token_input=30,
            token_output=20,
            is_completed=True,
            completion_reason="",
            p=75,
            is_planned=False,
            cost_usd=0.0,
        ),
    ]

    await handle_check_suite(payload)

    mock_get_codecov_token.assert_called_once_with(11111)
    assert mock_chat_agent.call_count == 2


@pytest.mark.asyncio
@patch("services.webhook.check_suite_handler.verify_task_is_complete")
@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.get_pr_comments")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.get_workflow_run_logs")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.get_retry_error_hashes")
@patch("services.webhook.check_suite_handler.update_retry_error_hashes")
@patch("services.webhook.check_suite_handler.should_bail", return_value=False)
@patch("services.webhook.check_suite_handler.chat_with_agent")
@patch("services.webhook.check_suite_handler.create_empty_commit")
@patch("services.webhook.check_suite_handler.update_usage")
@patch("services.webhook.check_suite_handler.ensure_node_packages")
@patch("services.webhook.check_suite_handler.ensure_php_packages")
@patch(
    "services.webhook.check_suite_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.check_suite_handler.git_merge_base_into_pr")
@patch("services.webhook.check_suite_handler.clone_repo_and_install_dependencies")
@patch("services.webhook.check_suite_handler.MAX_ITERATIONS", 2)
async def test_handle_check_suite_max_iterations_forces_verification(
    _mock_prepare_repo,
    _mock_get_behind,
    _mock_merge_base,
    _mock_ensure_php,
    _mock_start_async,
    _mock_update_usage,
    _mock_create_empty_commit,
    mock_chat_agent,
    _mock_should_bail,
    _mock_update_retry_hashes,
    mock_get_retry_hashes,
    _mock_update_comment,
    mock_get_logs,
    mock_get_changes,
    mock_get_pr,
    _mock_cancel_workflow_runs,
    mock_create_user_request,
    mock_create_comment,
    mock_get_pr_comments,
    _mock_slack_notify,
    mock_get_repo,
    mock_get_token,
    mock_get_failed_runs,
    mock_verify_task_is_complete,
    mock_check_run_payload,
):
    """Test that handler forces verify_task_is_complete when MAX_ITERATIONS is reached."""
    payload = mock_check_run_payload.copy()
    payload["check_suite"] = payload["check_suite"].copy()
    payload["check_suite"]["id"] = random.randint(1000000, 9999999)

    mock_get_token.return_value = "ghs_test_token_for_testing"
    mock_get_failed_runs.return_value = [
        {
            "details_url": "https://github.com/test-owner/test-repo/actions/runs/12345/job/67890",
            "name": "test",
            "head_sha": "abc123",
        }
    ]
    mock_get_repo.return_value = {"trigger_on_test_failure": True}
    mock_get_pr_comments.return_value = []
    mock_create_comment.return_value = "http://comment-url"
    mock_create_user_request.return_value = "usage-id-123"
    mock_get_pr.return_value = {
        "title": "Low Test Coverage: src/main.py",
        "body": "Test PR description",
        "user": {"login": "test-user"},
        "base": {"ref": "main"},
    }
    mock_get_changes.return_value = [
        {
            "filename": "src/main.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
        }
    ]
    mock_get_logs.return_value = "Test failure log content"
    mock_get_retry_hashes.return_value = []
    mock_verify_task_is_complete.return_value = VerifyTaskIsCompleteResult(
        success=True,
        message="Task completed.",
    )

    mock_chat_agent.side_effect = [
        AgentResult(
            messages=[],
            token_input=50,
            token_output=25,
            is_completed=False,
            completion_reason="",
            p=50,
            is_planned=False,
            cost_usd=0.0,
        ),
        AgentResult(
            messages=[],
            token_input=30,
            token_output=20,
            is_completed=False,
            completion_reason="",
            p=75,
            is_planned=False,
            cost_usd=0.0,
        ),
    ]

    await handle_check_suite(payload)

    assert mock_chat_agent.call_count == 2
    mock_verify_task_is_complete.assert_called_once()


@pytest.mark.asyncio
@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.get_pr_comments")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.get_workflow_run_logs")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.get_retry_error_hashes")
@patch("services.webhook.check_suite_handler.update_retry_error_hashes")
@patch("services.webhook.check_suite_handler.update_usage")
@patch("services.webhook.check_suite_handler.ensure_node_packages")
@patch("services.webhook.check_suite_handler.ensure_php_packages")
@patch(
    "services.webhook.check_suite_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.check_suite_handler.git_merge_base_into_pr")
@patch("services.webhook.check_suite_handler.clone_repo_and_install_dependencies")
async def test_handle_check_suite_skips_same_error_hash_across_workflow_ids(
    _mock_prepare_repo,
    _mock_get_behind,
    _mock_merge_base,
    _mock_ensure_php,
    _mock_start_async,
    mock_update_usage,
    _mock_update_retry_hashes,
    mock_get_retry_hashes,
    _mock_update_comment,
    mock_get_logs,
    mock_get_changes,
    mock_get_pr,
    _mock_cancel_workflow_runs,
    mock_create_user_request,
    mock_create_comment,
    mock_get_pr_comments,
    mock_slack_notify,
    mock_get_repo,
    mock_get_token,
    mock_get_failed_runs,
    mock_check_run_payload,
):
    """Test that handler skips when same error hash already exists, even with a different workflow ID."""
    payload = mock_check_run_payload.copy()
    payload["check_suite"] = payload["check_suite"].copy()
    payload["check_suite"]["id"] = random.randint(1000000, 9999999)

    mock_get_token.return_value = "ghs_test_token_for_testing"
    mock_get_failed_runs.return_value = [
        {
            "details_url": "https://github.com/test-owner/test-repo/actions/runs/99999/job/67890",
            "name": "test",
            "head_sha": "abc123",
        }
    ]
    mock_get_repo.return_value = {"trigger_on_test_failure": True}
    mock_get_pr_comments.return_value = []
    mock_create_comment.return_value = "http://comment-url"
    mock_slack_notify.return_value = "thread-123"
    mock_create_user_request.return_value = 777
    mock_get_pr.return_value = {
        "title": "Fix failing tests",
        "body": "Test PR description",
        "user": {"login": "test-user"},
        "base": {"ref": "main"},
    }
    mock_get_changes.return_value = [
        {
            "filename": "src/main.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
        }
    ]

    # Same error log content every time - hash will be identical
    error_log = "OOM killed: process used too much memory"
    mock_get_logs.return_value = error_log
    error_hash = hashlib.sha256(error_log.encode(encoding=UTF8)).hexdigest()

    # One previous run with the same error hash
    mock_get_retry_hashes.return_value = [error_hash]

    await handle_check_suite(payload)

    # Should skip - no chat_with_agent call, just update_usage and return
    mock_update_usage.assert_called_once()
    call_kwargs = mock_update_usage.call_args.kwargs
    assert call_kwargs["usage_id"] == 777
    assert call_kwargs["token_input"] == 0
    assert call_kwargs["token_output"] == 0
    assert call_kwargs["is_completed"] is True

    # Verify the skip message mentions the error was already tried
    slack_calls = [call[0][0] for call in mock_slack_notify.call_args_list]
    assert any("already tried to fix this error" in msg for msg in slack_calls)
