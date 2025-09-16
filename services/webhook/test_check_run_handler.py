"""Unit tests for check_run_handler.py"""

# Test to verify imports work correctly
# Standard imports
import hashlib
from unittest.mock import patch
import pytest
from config import GITHUB_APP_USER_NAME, UTF8
from services.webhook.check_run_handler import handle_check_run


@pytest.fixture
def mock_check_run_payload(test_owner, test_repo):
    """Fixture providing a mock check run payload."""
    return {
        "action": "completed",
        "check_run": {
            "id": 12345,
            "name": "test-check",
            "head_sha": "abc123",
            "details_url": "https://github.com/hiroshinishio/tetris/actions/runs/11393174689/job/31710113401",
            "status": "completed",
            "conclusion": "failure",
            "check_suite": {
                "head_branch": "feature-branch",
            },
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


@patch("services.webhook.check_run_handler.get_installation_access_token")
@patch("services.webhook.check_run_handler.get_repository")
def test_handle_check_run_skips_non_bot_sender(
    mock_get_repo, mock_get_token, mock_check_run_payload
):
    """Test that handler skips when sender is not the bot."""
    # Modify sender to be a non-bot user
    payload = mock_check_run_payload.copy()
    payload["sender"]["login"] = "human-user"

    handle_check_run(payload)

    # Verify no further processing occurred
    mock_get_token.assert_not_called()
    mock_get_repo.assert_not_called()


@patch("services.webhook.check_run_handler.get_installation_access_token")
@patch("services.webhook.check_run_handler.get_repository")
def test_handle_check_run_skips_when_trigger_disabled(
    mock_get_repo, mock_get_token, mock_check_run_payload
):
    """Test that handler skips when trigger_on_test_failure is disabled."""
    mock_get_token.return_value = "ghs_test_token_for_testing"
    mock_get_repo.return_value = {"trigger_on_test_failure": False}

    handle_check_run(mock_check_run_payload)

    mock_get_token.assert_called_once()
    mock_get_repo.assert_called_once_with(repo_id=98765)


@patch("services.webhook.check_run_handler.get_installation_access_token")
@patch("services.webhook.check_run_handler.get_repository")
@patch("services.webhook.check_run_handler.slack_notify")
@patch("services.webhook.check_run_handler.has_comment_with_text")
@patch("services.webhook.check_run_handler.create_comment")
def test_handle_check_run_skips_when_comment_exists(
    mock_create_comment,
    mock_has_comment,
    mock_slack_notify,
    mock_get_repo,
    mock_get_token,
    mock_check_run_payload,
):
    """Test that handler skips when relevant comment already exists."""
    mock_get_token.return_value = "ghs_test_token_for_testing"
    mock_get_repo.return_value = {"trigger_on_test_failure": True}
    mock_has_comment.return_value = True

    handle_check_run(mock_check_run_payload)

    mock_get_token.assert_called_once()
    mock_get_repo.assert_called_once()
    mock_has_comment.assert_called_once()
    mock_create_comment.assert_not_called()
    mock_slack_notify.assert_called()


@patch("services.webhook.check_run_handler.get_installation_access_token")
@patch("services.webhook.check_run_handler.get_repository")
@patch("services.webhook.check_run_handler.slack_notify")
@patch("services.webhook.check_run_handler.has_comment_with_text")
@patch("services.webhook.check_run_handler.create_comment")
@patch("services.webhook.check_run_handler.create_user_request")
@patch("services.webhook.check_run_handler.cancel_workflow_runs")
@patch("services.webhook.check_run_handler.get_pull_request")
@patch("services.webhook.check_run_handler.get_pull_request_file_changes")
@patch("services.webhook.check_run_handler.get_workflow_run_logs")
@patch("services.webhook.check_run_handler.update_comment")
@patch("services.webhook.check_run_handler.get_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_run_handler.update_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_run_handler.is_pull_request_open")
@patch("services.webhook.check_run_handler.check_branch_exists")
@patch("services.webhook.check_run_handler.chat_with_agent")
@patch("services.webhook.check_run_handler.create_empty_commit")
@patch("services.webhook.check_run_handler.update_usage")
@patch("services.webhook.check_run_handler.is_lambda_timeout_approaching")
def test_handle_check_run_full_workflow(
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
    mock_check_run_payload,
):
    """Test the full workflow of handling a check run failure."""
    # Setup mocks
    mock_get_token.return_value = "ghs_test_token_for_testing"
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
            None,
            None,
            False,
            50,
        ),  # First call (get mode) - no exploration
        (
            [],
            [],
            None,
            None,
            None,
            None,
            False,
            75,
        ),  # Second call (commit mode) - no commit, loop exits
    ]

    # Execute
    handle_check_run(mock_check_run_payload)

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


@patch("services.webhook.check_run_handler.get_installation_access_token")
@patch("services.webhook.check_run_handler.get_repository")
@patch("services.webhook.check_run_handler.slack_notify")
@patch("services.webhook.check_run_handler.has_comment_with_text")
@patch("services.webhook.check_run_handler.create_comment")
@patch("services.webhook.check_run_handler.create_user_request")
@patch("services.webhook.check_run_handler.cancel_workflow_runs")
@patch("services.webhook.check_run_handler.get_pull_request")
@patch("services.webhook.check_run_handler.get_pull_request_file_changes")
@patch("services.webhook.check_run_handler.get_workflow_run_logs")
@patch("services.webhook.check_run_handler.update_comment")
@patch("services.webhook.check_run_handler.create_permission_url")
@patch("services.webhook.check_run_handler.get_installation_permissions")
def test_handle_check_run_with_404_logs(
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
    mock_check_run_payload,
):
    """Test handling when workflow logs return 404."""
    # Setup mocks
    mock_get_token.return_value = "ghs_test_token_for_testing"
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
    handle_check_run(mock_check_run_payload)

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


@patch("services.webhook.check_run_handler.get_installation_access_token")
@patch("services.webhook.check_run_handler.get_repository")
@patch("services.webhook.check_run_handler.slack_notify")
@patch("services.webhook.check_run_handler.has_comment_with_text")
@patch("services.webhook.check_run_handler.create_comment")
@patch("services.webhook.check_run_handler.create_user_request")
@patch("services.webhook.check_run_handler.cancel_workflow_runs")
@patch("services.webhook.check_run_handler.get_pull_request")
@patch("services.webhook.check_run_handler.get_pull_request_file_changes")
@patch("services.webhook.check_run_handler.get_workflow_run_logs")
@patch("services.webhook.check_run_handler.update_comment")
def test_handle_check_run_with_none_logs(
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
    mock_check_run_payload,
):
    """Test handling when workflow logs return None."""
    # Setup mocks
    mock_get_token.return_value = "ghs_test_token_for_testing"
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
    handle_check_run(mock_check_run_payload)

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


@patch("services.webhook.check_run_handler.get_installation_access_token")
@patch("services.webhook.check_run_handler.get_repository")
@patch("services.webhook.check_run_handler.slack_notify")
@patch("services.webhook.check_run_handler.has_comment_with_text")
@patch("services.webhook.check_run_handler.create_comment")
@patch("services.webhook.check_run_handler.create_user_request")
@patch("services.webhook.check_run_handler.cancel_workflow_runs")
@patch("services.webhook.check_run_handler.get_pull_request")
@patch("services.webhook.check_run_handler.get_pull_request_file_changes")
@patch("services.webhook.check_run_handler.get_workflow_run_logs")
@patch("services.webhook.check_run_handler.update_comment")
@patch("services.webhook.check_run_handler.get_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_run_handler.update_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_run_handler.update_usage")
@patch("services.webhook.check_run_handler.clean_logs")
def test_handle_check_run_with_existing_retry_pair(
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
    mock_check_run_payload,
):
    """Test handling when the workflow/error pair has already been attempted."""
    # Setup mocks
    mock_get_token.return_value = "ghs_test_token_for_testing"
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
    handle_check_run(mock_check_run_payload)

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


@patch("services.webhook.check_run_handler.get_installation_access_token")
@patch("services.webhook.check_run_handler.get_repository")
@patch("services.webhook.check_run_handler.slack_notify")
@patch("services.webhook.check_run_handler.has_comment_with_text")
@patch("services.webhook.check_run_handler.create_comment")
@patch("services.webhook.check_run_handler.create_user_request")
@patch("services.webhook.check_run_handler.cancel_workflow_runs")
@patch("services.webhook.check_run_handler.get_pull_request")
@patch("services.webhook.check_run_handler.get_pull_request_file_changes")
@patch("services.webhook.check_run_handler.get_workflow_run_logs")
@patch("services.webhook.check_run_handler.update_comment")
@patch("services.webhook.check_run_handler.get_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_run_handler.update_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_run_handler.is_pull_request_open")
def test_handle_check_run_with_closed_pr(
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
    mock_check_run_payload,
):
    """Test handling when the PR is closed during processing."""
    # Setup mocks
    mock_get_token.return_value = "ghs_test_token_for_testing"
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
    handle_check_run(mock_check_run_payload)

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


@patch("services.webhook.check_run_handler.get_installation_access_token")
@patch("services.webhook.check_run_handler.get_repository")
@patch("services.webhook.check_run_handler.slack_notify")
@patch("services.webhook.check_run_handler.has_comment_with_text")
@patch("services.webhook.check_run_handler.create_comment")
@patch("services.webhook.check_run_handler.create_user_request")
@patch("services.webhook.check_run_handler.cancel_workflow_runs")
@patch("services.webhook.check_run_handler.get_pull_request")
@patch("services.webhook.check_run_handler.get_pull_request_file_changes")
@patch("services.webhook.check_run_handler.get_workflow_run_logs")
@patch("services.webhook.check_run_handler.update_comment")
@patch("services.webhook.check_run_handler.get_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_run_handler.update_retry_workflow_id_hash_pairs")
@patch("services.webhook.check_run_handler.is_pull_request_open")
@patch("services.webhook.check_run_handler.check_branch_exists")
def test_handle_check_run_with_deleted_branch(
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
    mock_check_run_payload,
):
    """Test handling when the branch is deleted during processing."""
    # Setup mocks
    mock_get_token.return_value = "ghs_test_token_for_testing"
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
    handle_check_run(mock_check_run_payload)

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
