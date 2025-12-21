"""Unit tests for check_suite_handler.py"""

# pylint: disable=too-many-lines

# Test to verify imports work correctly
# Standard imports
import hashlib
import random
from unittest.mock import patch
import pytest
from config import GITHUB_APP_USER_NAME, PRODUCT_ID, UTF8
from services.webhook.check_suite_handler import handle_check_suite


@pytest.fixture
def mock_check_run_payload(test_owner, test_repo):
    """Fixture providing a mock check suite payload."""
    return {
        "action": "completed",
        "check_suite": {
            "id": 12345,
            "head_branch": f"{PRODUCT_ID}/issue-123",
            "head_sha": "abc123",
            "status": "completed",
            "conclusion": "failure",
            "pull_requests": [
                {
                    "number": 1,
                    "url": "https://api.github.com/repos/owner/repo/pulls/1",
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
        "title": "Test PR",
        "body": "Test PR description",
        "user": {"login": "test-user"},
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


@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
def test_handle_check_suite_skips_non_gitauto_branch(
    mock_get_repo, mock_get_token, mock_get_failed_runs, mock_check_run_payload
):
    """Test that handler skips when branch doesn't start with PRODUCT_ID."""
    # Modify head_branch to not start with PRODUCT_ID
    payload = mock_check_run_payload.copy()
    payload["check_suite"] = payload["check_suite"].copy()
    payload["check_suite"]["id"] = random.randint(1000000, 9999999)
    payload["check_suite"]["head_branch"] = "non-gitauto-branch"

    handle_check_suite(payload)

    # Verify no further processing occurred
    mock_get_token.assert_not_called()
    mock_get_repo.assert_not_called()
    mock_get_failed_runs.assert_not_called()


@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
def test_handle_check_suite_skips_when_trigger_disabled(
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
    mock_get_repo.return_value = {"trigger_on_test_failure": False}

    handle_check_suite(payload)

    mock_get_token.assert_called_once()
    mock_get_failed_runs.assert_called_once()
    mock_get_repo.assert_called_once_with(repo_id=98765)


@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.has_comment_with_text")
@patch("services.webhook.check_suite_handler.create_comment")
def test_handle_check_suite_skips_when_comment_exists(
    mock_create_comment,
    mock_has_comment,
    mock_slack_notify,
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
    mock_get_repo.return_value = {"trigger_on_test_failure": True}
    mock_has_comment.return_value = True

    handle_check_suite(payload)

    mock_get_token.assert_called_once()
    mock_get_failed_runs.assert_called_once()
    mock_get_repo.assert_called_once()
    mock_has_comment.assert_called_once()
    mock_create_comment.assert_not_called()
    mock_slack_notify.assert_called()


@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.has_comment_with_text")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.get_workflow_run_logs")
@patch("services.webhook.check_suite_handler.clean_logs")
@patch("services.webhook.check_suite_handler.get_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_suite_handler.update_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_suite_handler.check_older_active_test_failure_request")
@patch("services.webhook.check_suite_handler.is_pull_request_open")
@patch("services.webhook.check_suite_handler.check_branch_exists")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.update_usage")
def test_handle_check_suite_race_condition_prevention(
    mock_update_usage,
    mock_update_comment,
    mock_check_branch_exists,
    mock_is_pull_request_open,
    mock_check_older_active,
    mock_update_retry_pairs,
    mock_get_retry_pairs,
    mock_clean_logs,
    mock_get_workflow_logs,
    mock_get_pr_files,
    mock_get_pr,
    mock_cancel_workflows,
    mock_create_user_request,
    mock_create_comment,
    mock_has_comment,
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
    mock_has_comment.return_value = False
    mock_create_comment.return_value = (
        "https://github.com/test/test/issues/1#issuecomment-123"
    )
    mock_create_user_request.return_value = 12345
    mock_cancel_workflows.return_value = None
    mock_get_pr.return_value = {"title": "Test PR"}
    mock_get_pr_files.return_value = [{"filename": "test.py", "status": "modified"}]
    mock_get_workflow_logs.return_value = "Error: Test failure"
    mock_clean_logs.return_value = "Cleaned error log"
    mock_get_retry_pairs.return_value = []
    mock_update_retry_pairs.return_value = None

    # Setup safety checks to pass
    mock_is_pull_request_open.return_value = True
    mock_check_branch_exists.return_value = True

    # Setup race condition detection - older active request found
    mock_check_older_active.return_value = {
        "id": 11111,
        "created_at": "2025-09-28T14:19:01.247+00:00",
    }

    handle_check_suite(payload)

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
    assert "retry_workflow_id_hash_pairs" in kwargs
    assert "original_error_log" in kwargs
    assert "minimized_error_log" in kwargs

    # Verify notification was sent
    mock_slack_notify.assert_called()
    mock_update_comment.assert_called()


@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.has_comment_with_text")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.get_workflow_run_logs")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.get_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_suite_handler.update_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_suite_handler.is_pull_request_open")
@patch("services.webhook.check_suite_handler.check_branch_exists")
@patch("services.webhook.check_suite_handler.chat_with_agent")
@patch("services.webhook.check_suite_handler.create_empty_commit")
@patch("services.webhook.check_suite_handler.update_usage")
@patch("services.webhook.check_suite_handler.is_lambda_timeout_approaching")
def test_handle_check_suite_full_workflow(
    mock_timeout_check,
    _mock_update_usage,
    _mock_create_empty_commit,
    mock_chat_agent,
    mock_check_branch_exists,
    mock_is_pr_open,
    _mock_update_retry_pairs,
    mock_get_retry_pairs,
    _mock_update_comment,
    mock_get_logs,
    mock_get_changes,
    mock_get_pr,
    _mock_cancel_workflow_runs,
    mock_create_user_request,
    mock_create_comment,
    mock_has_comment,
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
    mock_has_comment.return_value = False
    mock_create_comment.return_value = "http://comment-url"
    mock_create_user_request.return_value = "usage-id-123"
    mock_get_pr.return_value = {
        "title": "Test PR",
        "body": "Test PR description",
        "user": {"login": "test-user"},
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
    mock_get_retry_pairs.return_value = []
    mock_is_pr_open.return_value = True
    mock_check_branch_exists.return_value = True
    mock_timeout_check.return_value = (False, 0)  # No timeout

    mock_chat_agent.side_effect = [
        (
            [],
            [],
            None,
            None,
            50,  # token_input
            25,  # token_output
            False,
            50,
        ),  # First call (get mode) - no exploration
        (
            [],
            [],
            None,
            None,
            30,  # token_input
            20,  # token_output
            False,
            75,
        ),  # Second call (commit mode) - no commit, loop exits
    ]

    # Execute
    handle_check_suite(payload)

    # Verify key functions were called
    mock_get_token.assert_called_once()
    mock_get_repo.assert_called_once()
    mock_create_comment.assert_called_once()
    mock_create_user_request.assert_called_once()
    mock_get_pr.assert_called_once()
    mock_get_changes.assert_called_once()
    mock_get_logs.assert_called_once()
    mock_get_retry_pairs.assert_called_once()
    assert mock_chat_agent.call_count == 2

    # Verify chat_with_agent calls
    first_call = mock_chat_agent.call_args_list[0]
    assert first_call.kwargs["mode"] == "get"
    assert first_call.kwargs["trigger"] == "test_failure"

    second_call = mock_chat_agent.call_args_list[1]
    assert second_call.kwargs["mode"] == "commit"
    assert second_call.kwargs["trigger"] == "test_failure"


@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.has_comment_with_text")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.get_workflow_run_logs")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.create_permission_url")
@patch("services.webhook.check_suite_handler.get_installation_permissions")
def test_handle_check_suite_with_404_logs(
    mock_get_permissions,
    mock_create_permission_url,
    mock_update_comment,
    mock_get_logs,
    mock_get_changes,
    mock_get_pr,
    _mock_cancel_workflow_runs,
    mock_create_user_request,
    mock_create_comment,
    mock_has_comment,
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
    mock_has_comment.return_value = False
    mock_create_comment.return_value = "http://comment-url"
    mock_create_user_request.return_value = "usage-id-123"
    mock_get_pr.return_value = {
        "title": "Test PR",
        "body": "Test PR description",
        "user": {"login": "test-user"},
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
    handle_check_suite(payload)

    # Verify
    mock_get_token.assert_called_once()
    mock_get_repo.assert_called_once()
    mock_create_comment.assert_called_once()
    mock_create_user_request.assert_called_once()
    mock_get_pr.assert_called_once()
    mock_get_changes.assert_called_once()
    mock_get_logs.assert_called_once()
    mock_create_permission_url.assert_called_once()
    mock_get_permissions.assert_called_once()

    # Verify permission denied message in comment
    mock_update_comment.assert_called()


@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.has_comment_with_text")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.get_workflow_run_logs")
@patch("services.webhook.check_suite_handler.update_comment")
def test_handle_check_suite_with_none_logs(
    mock_update_comment,
    mock_get_logs,
    mock_get_changes,
    mock_get_pr,
    _mock_cancel_workflow_runs,
    mock_create_user_request,
    mock_create_comment,
    mock_has_comment,
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
    mock_has_comment.return_value = False
    mock_create_comment.return_value = "http://comment-url"
    mock_create_user_request.return_value = "usage-id-123"
    mock_get_pr.return_value = {
        "title": "Test PR",
        "body": "Test PR description",
        "user": {"login": "test-user"},
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
    handle_check_suite(payload)

    # Verify
    mock_get_token.assert_called_once()
    mock_get_repo.assert_called_once()
    mock_create_comment.assert_called_once()
    mock_create_user_request.assert_called_once()
    mock_get_pr.assert_called_once()
    mock_get_changes.assert_called_once()
    mock_get_logs.assert_called_once()

    # Verify error message in comment
    mock_update_comment.assert_called()


@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.has_comment_with_text")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.get_workflow_run_logs")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.get_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_suite_handler.update_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_suite_handler.update_usage")
@patch("services.webhook.check_suite_handler.clean_logs")
def test_handle_check_suite_with_existing_retry_pair(
    mock_clean_logs,
    mock_update_usage,
    _mock_update_retry_pairs,
    mock_get_retry_pairs,
    mock_update_comment,
    mock_get_logs,
    mock_get_changes,
    mock_get_pr,
    _mock_cancel_workflow_runs,
    mock_create_user_request,
    mock_create_comment,
    mock_has_comment,
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
    mock_has_comment.return_value = False
    mock_create_comment.return_value = "http://comment-url"
    mock_create_user_request.return_value = "usage-id-123"
    mock_get_pr.return_value = {
        "title": "Test PR",
        "body": "Test PR description",
        "user": {"login": "test-user"},
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

    # Mock that this workflow/error pair has been seen before
    # Calculate the expected hash: workflow_id is "runs" from URL, error_log is "Test failure log content"
    expected_hash = hashlib.sha256("Test failure log content".encode(UTF8)).hexdigest()
    mock_get_retry_pairs.return_value = [f"runs:{expected_hash}"]

    # Execute
    handle_check_suite(payload)

    # Verify
    mock_get_token.assert_called_once()
    mock_get_repo.assert_called_once()
    mock_create_comment.assert_called_once()
    mock_create_user_request.assert_called_once()
    mock_get_pr.assert_called_once()
    mock_get_changes.assert_called_once()
    mock_get_logs.assert_called_once()
    mock_get_retry_pairs.assert_called_once()
    mock_clean_logs.assert_called_once_with("Test failure log content")

    # Verify update_usage was called with error logs
    mock_update_usage.assert_called_once()
    call_args = mock_update_usage.call_args[1]
    assert call_args["original_error_log"] == "Test failure log content"
    assert call_args["minimized_error_log"] == "Cleaned test failure log"

    # Verify skip message in comment
    mock_update_comment.assert_called()


@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.has_comment_with_text")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.get_workflow_run_logs")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.get_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_suite_handler.update_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_suite_handler.is_pull_request_open")
def test_handle_check_suite_with_closed_pr(
    mock_is_pr_open,
    _mock_update_retry_pairs,
    mock_get_retry_pairs,
    mock_update_comment,
    mock_get_logs,
    mock_get_changes,
    mock_get_pr,
    _mock_cancel_workflow_runs,
    mock_create_user_request,
    mock_create_comment,
    mock_has_comment,
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
    mock_has_comment.return_value = False
    mock_create_comment.return_value = "http://comment-url"
    mock_create_user_request.return_value = "usage-id-123"
    mock_get_pr.return_value = {
        "title": "Test PR",
        "body": "Test PR description",
        "user": {"login": "test-user"},
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
    mock_get_retry_pairs.return_value = []
    mock_is_pr_open.return_value = False

    # Execute
    handle_check_suite(payload)

    # Verify
    mock_get_token.assert_called_once()
    mock_get_repo.assert_called_once()
    mock_create_comment.assert_called_once()
    mock_create_user_request.assert_called_once()
    mock_get_pr.assert_called_once()
    mock_get_changes.assert_called_once()
    mock_get_logs.assert_called_once()
    mock_is_pr_open.assert_called_once()

    # Verify closed PR message in comment
    mock_update_comment.assert_called()


@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.has_comment_with_text")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.get_workflow_run_logs")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.get_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_suite_handler.update_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_suite_handler.is_pull_request_open")
@patch("services.webhook.check_suite_handler.check_branch_exists")
def test_handle_check_suite_with_deleted_branch(
    mock_branch_exists,
    mock_is_pr_open,
    _mock_update_retry_pairs,
    mock_get_retry_pairs,
    mock_update_comment,
    mock_get_logs,
    mock_get_changes,
    mock_get_pr,
    _mock_cancel_workflow_runs,
    mock_create_user_request,
    mock_create_comment,
    mock_has_comment,
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
    mock_has_comment.return_value = False
    mock_create_comment.return_value = "http://comment-url"
    mock_create_user_request.return_value = "usage-id-123"
    mock_get_pr.return_value = {
        "title": "Test PR",
        "body": "Test PR description",
        "user": {"login": "test-user"},
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
    mock_get_retry_pairs.return_value = []
    mock_is_pr_open.return_value = True
    mock_branch_exists.return_value = False

    # Execute
    handle_check_suite(payload)

    # Verify
    mock_get_token.assert_called_once()
    mock_get_repo.assert_called_once()
    mock_create_comment.assert_called_once()
    mock_create_user_request.assert_called_once()
    mock_get_pr.assert_called_once()
    mock_get_changes.assert_called_once()
    mock_get_logs.assert_called_once()
    mock_branch_exists.assert_called_once()

    # Verify deleted branch message in comment
    mock_update_comment.assert_called()


@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.has_comment_with_text")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.get_workflow_run_logs")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.get_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_suite_handler.update_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_suite_handler.is_pull_request_open")
@patch("services.webhook.check_suite_handler.check_branch_exists")
@patch("services.webhook.check_suite_handler.chat_with_agent")
@patch("services.webhook.check_suite_handler.create_empty_commit")
@patch("services.webhook.check_suite_handler.update_usage")
@patch("services.webhook.check_suite_handler.is_lambda_timeout_approaching")
def test_check_run_handler_token_accumulation(
    mock_timeout_check,
    mock_update_usage,
    _mock_create_empty_commit,
    mock_chat_agent,
    mock_check_branch_exists,
    mock_is_pr_open,
    _mock_update_retry_pairs,
    mock_get_retry_pairs,
    _mock_update_comment,
    mock_get_logs,
    mock_get_changes,
    mock_get_pr,
    _mock_cancel_workflow_runs,
    mock_create_user_request,
    mock_create_comment,
    mock_has_comment,
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
    mock_has_comment.return_value = False
    mock_create_comment.return_value = "http://comment-url"
    mock_create_user_request.return_value = 888
    mock_get_pr.return_value = {
        "title": "Test PR",
        "body": "Test PR description",
        "user": {"login": "test-user"},
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
    mock_get_retry_pairs.return_value = []
    mock_is_pr_open.return_value = True
    mock_check_branch_exists.return_value = True
    mock_timeout_check.return_value = (False, 0)

    # Mock chat_with_agent to return token counts and break loop
    mock_chat_agent.return_value = (
        [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": "AI response"},
        ],
        [],
        "no_action",
        {},
        80,  # input tokens
        45,  # output tokens
        False,  # is_explored/is_committed=False (breaks loop)
        90,
    )

    # Execute
    handle_check_suite(payload)

    # Verify chat_with_agent was called twice (get + commit modes)
    assert mock_chat_agent.call_count == 2

    # Verify update_usage was called with accumulated tokens
    mock_update_usage.assert_called_once()
    call_kwargs = mock_update_usage.call_args.kwargs

    assert call_kwargs["usage_id"] == 888
    assert call_kwargs["token_input"] == 160  # Two calls: 80 + 80
    assert call_kwargs["token_output"] == 90  # Two calls: 45 + 45


@patch("services.webhook.check_suite_handler.get_failed_check_runs_from_check_suite")
@patch("services.webhook.check_suite_handler.get_installation_access_token")
@patch("services.webhook.check_suite_handler.get_repository")
@patch("services.webhook.check_suite_handler.slack_notify")
@patch("services.webhook.check_suite_handler.has_comment_with_text")
@patch("services.webhook.check_suite_handler.create_comment")
@patch("services.webhook.check_suite_handler.create_user_request")
@patch("services.webhook.check_suite_handler.cancel_workflow_runs")
@patch("services.webhook.check_suite_handler.get_pull_request")
@patch("services.webhook.check_suite_handler.get_pull_request_files")
@patch("services.webhook.check_suite_handler.get_workflow_run_logs")
@patch("services.webhook.check_suite_handler.update_comment")
@patch("services.webhook.check_suite_handler.get_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_suite_handler.clean_logs")
@patch("services.webhook.check_suite_handler.check_older_active_test_failure_request")
@patch("services.webhook.check_suite_handler.update_usage")
@patch("services.webhook.check_suite_handler.is_pull_request_open")
@patch("services.webhook.check_suite_handler.check_branch_exists")
def test_handle_check_suite_skips_duplicate_older_request(
    mock_branch_exists,
    mock_is_pr_open,
    mock_update_usage,
    mock_check_older_active,
    mock_clean_logs,
    mock_get_retry_pairs,
    _mock_update_comment,
    mock_get_logs,
    mock_get_changes,
    mock_get_pr,
    _mock_cancel_workflow_runs,
    mock_create_user_request,
    mock_create_comment,
    mock_has_comment,
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
    mock_has_comment.return_value = False
    mock_create_comment.return_value = "http://comment-url"
    mock_slack_notify.return_value = "thread-123"
    mock_create_user_request.return_value = 999
    mock_get_pr.return_value = {
        "title": "Test PR",
        "body": "Test PR description",
        "user": {"login": "test-user"},
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
    mock_get_retry_pairs.return_value = []
    mock_clean_logs.return_value = "Cleaned test failure log"
    mock_is_pr_open.return_value = True
    mock_branch_exists.return_value = True
    mock_check_older_active.return_value = {
        "id": 888,
        "created_at": "2025-09-23T10:00:00Z",
    }

    # Execute
    handle_check_suite(payload)

    # Verify
    mock_get_token.assert_called_once()
    mock_get_repo.assert_called_once()
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
