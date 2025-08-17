from unittest.mock import patch, MagicMock, Mock
import pytest
import time
from datetime import datetime

from services.webhook.check_run_handler import handle_check_run


@pytest.fixture
def mock_payload():
    """Create a mock CheckRunCompletedPayload for testing."""
    return {
        "check_run": {
            "name": "test-check-run",
            "details_url": "https://github.com/owner/repo/actions/runs/123456789/job/987654321",
            "head_sha": "abc123def456",
            "check_suite": {
                "head_branch": "main"
            },
            "pull_requests": [
                {
                    "number": 123,
                    "url": "https://api.github.com/repos/owner/repo/pulls/123"
                }
            ]
        },
        "repository": {
            "id": 987654321,
            "name": "test-repo",
            "clone_url": "https://github.com/owner/test-repo.git",
            "fork": False,
            "owner": {
                "id": 123456,
                "login": "test-owner",
                "type": "Organization"
            }
        },
        "sender": {
            "id": 789012,
            "login": "gitauto-ai[bot]"
        },
        "installation": {
            "id": 12345678
        }
    }


@pytest.fixture
def mock_circleci_payload():
    """Create a mock payload for CircleCI check run."""
    return {
        "check_run": {
            "name": "circleci-test",
            "details_url": "https://app.circleci.com/pipelines/circleci/J2wtzLah5rmzRnx6qn4RyQ/UUb5FLNgQCnif8mB6mQn7s/7/workflows/772ddda7-d6b7-49ad-9123-108d9f8164b5",
            "head_sha": "abc123def456",
            "check_suite": {
                "head_branch": "main"
            },
            "pull_requests": [
                {
                    "number": 123,
                    "url": "https://api.github.com/repos/owner/repo/pulls/123"
                }
            ]
        },
        "repository": {
            "id": 987654321,
            "name": "test-repo",
            "clone_url": "https://github.com/owner/test-repo.git",
            "fork": False,
            "owner": {
                "id": 123456,
                "login": "test-owner",
                "type": "Organization"
            }
        },
        "sender": {
            "id": 789012,
            "login": "gitauto-ai[bot]"
        },
        "installation": {
            "id": 12345678
        }
    }


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies."""
    with patch.multiple(
        "services.webhook.check_run_handler",
        get_installation_access_token=MagicMock(return_value="test-token"),
        get_repository=MagicMock(return_value={"trigger_on_test_failure": True}),
        slack_notify=MagicMock(return_value="thread-123"),
        has_comment_with_text=MagicMock(return_value=False),
        create_comment=MagicMock(return_value="comment-url"),
        create_user_request=MagicMock(return_value="usage-id-123"),
        cancel_workflow_runs=MagicMock(),
        get_pull_request=MagicMock(return_value={"title": "Test PR", "body": "Test body"}),
        get_pull_request_file_changes=MagicMock(return_value=[]),
        get_workflow_run_path=MagicMock(return_value=".github/workflows/test.yml"),
        get_remote_file_content=MagicMock(return_value="workflow content"),
        get_file_tree_list=MagicMock(return_value=(["file1.py", "file2.py"], None)),
        get_workflow_run_logs=MagicMock(return_value="error logs"),
        update_comment=MagicMock(),
        get_retry_workflow_id_hash_pairs=MagicMock(return_value=[]),
        update_retry_workflow_id_hash_pairs=MagicMock(),
        is_lambda_timeout_approaching=MagicMock(return_value=(False, 30)),
        is_pull_request_open=MagicMock(return_value=True),
        check_branch_exists=MagicMock(return_value=True),
        chat_with_agent=MagicMock(return_value=([], [], None, None, 0, 0, False, 50)),
        create_empty_commit=MagicMock(),
        update_usage=MagicMock(),
    ) as mocks:
        yield mocks


def test_handle_check_run_no_owner(mock_payload, mock_dependencies):
    """Test handling when repository has no owner."""
    mock_payload["repository"]["owner"] = None
    
    result = handle_check_run(mock_payload)
    
    # Should return early when no owner
    assert result is None


def test_handle_check_run_wrong_sender(mock_payload, mock_dependencies):
    """Test handling when sender is not GitAuto."""
    mock_payload["sender"]["login"] = "different-bot"
    
    result = handle_check_run(mock_payload)
    
    # Should return early when sender is not GitAuto
    assert result is None


def test_handle_check_run_no_pull_requests(mock_payload, mock_dependencies):
    """Test handling when check run has no associated pull requests."""
    mock_payload["check_run"]["pull_requests"] = []
    
    result = handle_check_run(mock_payload)
    
    # Should return early when no pull requests
    assert result is None


def test_handle_check_run_trigger_disabled(mock_payload, mock_dependencies):
    """Test handling when trigger_on_test_failure is disabled."""
    mock_dependencies["get_repository"].return_value = {"trigger_on_test_failure": False}
    
    result = handle_check_run(mock_payload)
    
    # Should return early when trigger is disabled
    assert result is None


def test_handle_check_run_no_repository_settings(mock_payload, mock_dependencies):
    """Test handling when repository settings are not found."""
    mock_dependencies["get_repository"].return_value = None
    
    result = handle_check_run(mock_payload)
    
    # Should return early when no repository settings
    assert result is None


def test_handle_check_run_comment_already_exists(mock_payload, mock_dependencies):
    """Test handling when permission or stumbled comment already exists."""
    mock_dependencies["has_comment_with_text"].return_value = True
    
    result = handle_check_run(mock_payload)
    
    # Should return early when comment already exists
    assert result is None


def test_handle_check_run_circleci_workflow(mock_circleci_payload, mock_dependencies):
    """Test handling CircleCI workflow."""
    mock_dependencies["get_circleci_token"] = MagicMock(return_value="circleci-token")
    mock_dependencies["get_circleci_workflow_jobs"] = MagicMock(return_value=[
        {"status": "failed", "job_number": 123}
    ])
    mock_dependencies["get_circleci_build_logs"] = MagicMock(return_value="circleci logs")
    
    with patch.multiple(
        "services.webhook.check_run_handler",
        get_circleci_token=mock_dependencies["get_circleci_token"],
        get_circleci_workflow_jobs=mock_dependencies["get_circleci_workflow_jobs"],
        get_circleci_build_logs=mock_dependencies["get_circleci_build_logs"]
    ):
        result = handle_check_run(mock_circleci_payload)
    
    # Should process CircleCI workflow
    mock_dependencies["get_circleci_token"].assert_called_once()
    mock_dependencies["get_circleci_workflow_jobs"].assert_called_once()


def test_handle_check_run_circleci_no_token(mock_circleci_payload, mock_dependencies):
    """Test handling CircleCI workflow without token."""
    with patch("services.webhook.check_run_handler.get_circleci_token", return_value=None):
        result = handle_check_run(mock_circleci_payload)
    
    # Should return early when no CircleCI token
    mock_dependencies["update_comment"].assert_called()


def test_handle_check_run_error_log_404(mock_payload, mock_dependencies):
    """Test handling when error log returns 404."""
    mock_dependencies["get_workflow_run_logs"].return_value = 404
    mock_dependencies["get_installation_permissions"] = MagicMock(return_value="read")
    mock_dependencies["create_permission_url"] = MagicMock(return_value="permission-url")
    
    with patch.multiple(
        "services.webhook.check_run_handler",
        get_installation_permissions=mock_dependencies["get_installation_permissions"],
        create_permission_url=mock_dependencies["create_permission_url"]
    ):
        result = handle_check_run(mock_payload)
    
    # Should handle 404 error log
    mock_dependencies["create_permission_url"].assert_called_once()


def test_handle_check_run_error_log_none(mock_payload, mock_dependencies):
    """Test handling when error log is None."""
    mock_dependencies["get_workflow_run_logs"].return_value = None
    
    result = handle_check_run(mock_payload)
    
    # Should handle None error log
    mock_dependencies["update_comment"].assert_called()


def test_handle_check_run_duplicate_error_hash(mock_payload, mock_dependencies):
    """Test handling when error hash already exists."""
    mock_dependencies["get_retry_workflow_id_hash_pairs"].return_value = [
        "123456789:existing_hash"
    ]
    
    with patch("services.webhook.check_run_handler.hashlib.sha256") as mock_hash:
        mock_hash.return_value.hexdigest.return_value = "existing_hash"
        result = handle_check_run(mock_payload)
    
    # Should return early when error hash already exists
    mock_dependencies["update_comment"].assert_called()


def test_handle_check_run_timeout_approaching(mock_payload, mock_dependencies):
    """Test handling when Lambda timeout is approaching."""
    mock_dependencies["is_lambda_timeout_approaching"].return_value = (True, 890)
    mock_dependencies["get_timeout_message"] = MagicMock(return_value="Timeout message")
    
    with patch("services.webhook.check_run_handler.get_timeout_message", 
               mock_dependencies["get_timeout_message"]):
        result = handle_check_run(mock_payload)
    
    # Should handle timeout
    mock_dependencies["get_timeout_message"].assert_called_once()


def test_handle_check_run_pr_closed_during_execution(mock_payload, mock_dependencies):
    """Test handling when PR is closed during execution."""
    mock_dependencies["is_pull_request_open"].return_value = False
    
    result = handle_check_run(mock_payload)
    
    # Should handle closed PR
    mock_dependencies["update_comment"].assert_called()


def test_handle_check_run_branch_deleted_during_execution(mock_payload, mock_dependencies):
    """Test handling when branch is deleted during execution."""
    mock_dependencies["check_branch_exists"].return_value = False
    
    result = handle_check_run(mock_payload)
    
    # Should handle deleted branch
    mock_dependencies["update_comment"].assert_called()


def test_handle_check_run_workflow_path_404(mock_payload, mock_dependencies):
    """Test handling when workflow path returns 404."""
    mock_dependencies["get_workflow_run_path"].return_value = 404
    
    result = handle_check_run(mock_payload)
    
    # Should handle 404 workflow path
    mock_dependencies["get_remote_file_content"].assert_not_called()


def test_handle_check_run_chat_agent_exploration(mock_payload, mock_dependencies):
    """Test chat agent exploration phase."""
    mock_dependencies["chat_with_agent"].side_effect = [
        ([], [], None, None, 0, 0, True, 60),  # Exploration found files
        ([], [], None, None, 0, 0, True, 70),  # Commit made changes
        ([], [], None, None, 0, 0, False, 80)  # No more exploration
    ]
    
    result = handle_check_run(mock_payload)
    
    # Should call chat_with_agent multiple times
    assert mock_dependencies["chat_with_agent"].call_count >= 2


def test_handle_check_run_retry_limit_reached(mock_payload, mock_dependencies):
    """Test when retry limit is reached."""
    mock_dependencies["chat_with_agent"].side_effect = [
        ([], [], None, None, 0, 0, False, 60),  # No exploration
        ([], [], None, None, 0, 0, True, 70),   # Commit made
        ([], [], None, None, 0, 0, False, 80),  # No exploration
        ([], [], None, None, 0, 0, True, 90),   # Commit made
        ([], [], None, None, 0, 0, False, 95),  # No exploration
        ([], [], None, None, 0, 0, True, 100),  # Commit made
        ([], [], None, None, 0, 0, False, 105), # No exploration
        ([], [], None, None, 0, 0, True, 110),  # Commit made
        ([], [], None, None, 0, 0, False, 115)  # No exploration - should break
    ]
    
    result = handle_check_run(mock_payload)
    
    # Should break after retry limit
    mock_dependencies["create_empty_commit"].assert_called_once()


def test_handle_check_run_circleci_failed_jobs(mock_circleci_payload, mock_dependencies):
    """Test CircleCI with multiple failed jobs."""
    mock_dependencies["get_circleci_token"] = MagicMock(return_value="circleci-token")
    mock_dependencies["get_circleci_workflow_jobs"] = MagicMock(return_value=[
        {"status": "failed", "job_number": 123},
        {"status": "success", "job_number": 124},
        {"status": "failed", "job_number": 125}
    ])
    mock_dependencies["get_circleci_build_logs"] = MagicMock(side_effect=[
        "logs for job 123",
        "logs for job 125"
    ])
    
    with patch.multiple(
        "services.webhook.check_run_handler",
        get_circleci_token=mock_dependencies["get_circleci_token"],
        get_circleci_workflow_jobs=mock_dependencies["get_circleci_workflow_jobs"],
        get_circleci_build_logs=mock_dependencies["get_circleci_build_logs"]
    ):
        result = handle_check_run(mock_circleci_payload)
    
    # Should process only failed jobs
    assert mock_dependencies["get_circleci_build_logs"].call_count == 2


def test_handle_check_run_circleci_no_job_number(mock_circleci_payload, mock_dependencies):
    """Test CircleCI with job missing job_number."""
    mock_dependencies["get_circleci_token"] = MagicMock(return_value="circleci-token")
    mock_dependencies["get_circleci_workflow_jobs"] = MagicMock(return_value=[
        {"status": "failed"}  # Missing job_number
    ])
    mock_dependencies["get_circleci_build_logs"] = MagicMock()
    
    with patch.multiple(
        "services.webhook.check_run_handler",
        get_circleci_token=mock_dependencies["get_circleci_token"],
        get_circleci_workflow_jobs=mock_dependencies["get_circleci_workflow_jobs"],
        get_circleci_build_logs=mock_dependencies["get_circleci_build_logs"]
    ):
        result = handle_check_run(mock_circleci_payload)
    
    # Should not call get_circleci_build_logs for job without number
    mock_dependencies["get_circleci_build_logs"].assert_not_called()


def test_handle_check_run_circleci_build_logs_404(mock_circleci_payload, mock_dependencies):
    """Test CircleCI when build logs return 404."""
    mock_dependencies["get_circleci_token"] = MagicMock(return_value="circleci-token")
    mock_dependencies["get_circleci_workflow_jobs"] = MagicMock(return_value=[
        {"status": "failed", "job_number": 123}
    ])
    mock_dependencies["get_circleci_build_logs"] = MagicMock(return_value=404)
    
    with patch.multiple(
        "services.webhook.check_run_handler",
        get_circleci_token=mock_dependencies["get_circleci_token"],
        get_circleci_workflow_jobs=mock_dependencies["get_circleci_workflow_jobs"],
        get_circleci_build_logs=mock_dependencies["get_circleci_build_logs"]
    ):
        result = handle_check_run(mock_circleci_payload)
    
    # Should handle 404 from build logs
    mock_dependencies["get_circleci_build_logs"].assert_called_once()


def test_handle_check_run_variable_extraction():
    """Test that all variables are extracted correctly from payload."""
    payload = {
        "check_run": {
            "name": "test-check",
            "details_url": "https://github.com/owner/repo/actions/runs/123/job/456",
            "head_sha": "sha123",
            "check_suite": {"head_branch": "feature-branch"},
            "pull_requests": [{"number": 789, "url": "pr-url"}]
        },
        "repository": {
            "id": 111,
            "name": "test-repo",
            "clone_url": "clone-url",
            "fork": True,
            "owner": {"id": 222, "login": "owner", "type": "User"}
        },
        "sender": {"id": 333, "login": "gitauto-ai[bot]"},
        "installation": {"id": 444}
    }
    
    with patch.multiple(
        "services.webhook.check_run_handler",
        get_installation_access_token=MagicMock(return_value="token"),
        get_repository=MagicMock(return_value=None)  # Return early
    ):
        result = handle_check_run(payload)
    
    # Should extract variables correctly (verified by not crashing)
    assert result is None


def test_handle_check_run_fork_repository(mock_payload, mock_dependencies):
    """Test handling with fork repository."""
    mock_payload["repository"]["fork"] = True
    
    result = handle_check_run(mock_payload)
    
    # Should handle fork repository
    mock_dependencies["create_user_request"].assert_called_once()


def test_handle_check_run_user_owner_type(mock_payload, mock_dependencies):
    """Test handling with User owner type."""
    mock_payload["repository"]["owner"]["type"] = "User"
    
    result = handle_check_run(mock_payload)
    
    # Should handle User owner type
    mock_dependencies["create_user_request"].assert_called_once()


@patch("services.webhook.check_run_handler.time.time")
def test_handle_check_run_timing(mock_time, mock_payload, mock_dependencies):
    """Test timing functionality."""
    mock_time.side_effect = [1000.0, 1100.0]  # Start and end times
    
    result = handle_check_run(mock_payload)
    
    # Should track timing
    mock_dependencies["update_usage"].assert_called_once()
    call_args = mock_dependencies["update_usage"].call_args[1]
    assert call_args["total_seconds"] == 100


def test_handle_check_run_complete_flow(mock_payload, mock_dependencies):
    """Test complete successful flow."""
    # Setup for successful completion
    mock_dependencies["chat_with_agent"].side_effect = [
        ([], [], None, None, 0, 0, True, 60),   # Exploration
        ([], [], None, None, 0, 0, True, 70),   # Commit
        ([], [], None, None, 0, 0, False, 80)   # Done
    ]
    
    result = handle_check_run(mock_payload)
    
    # Should complete full flow
    mock_dependencies["create_empty_commit"].assert_called_once()
    mock_dependencies["update_usage"].assert_called_once()
    mock_dependencies["slack_notify"].assert_called()


def test_handle_check_run_error_hash_generation(mock_payload, mock_dependencies):
    """Test error hash generation and storage."""
    test_error_log = "test error log content"
    mock_dependencies["get_workflow_run_logs"].return_value = test_error_log
    
    with patch("services.webhook.check_run_handler.hashlib.sha256") as mock_hash:
        mock_hash_obj = MagicMock()
        mock_hash_obj.hexdigest.return_value = "test_hash_123"
        mock_hash.return_value = mock_hash_obj
        
        result = handle_check_run(mock_payload)
        
        # Should generate hash from error log
        mock_hash.assert_called_once_with(test_error_log.encode(encoding="utf-8"))
        mock_dependencies["update_retry_workflow_id_hash_pairs"].assert_called_once()


def test_handle_check_run_progress_updates(mock_payload, mock_dependencies):
    """Test that progress is updated throughout the process."""
    result = handle_check_run(mock_payload)
    
    # Should update comment multiple times for progress
    assert mock_dependencies["update_comment"].call_count >= 3