from unittest.mock import patch, Mock, MagicMock
import pytest
from datetime import datetime

from services.webhook.check_run_handler import handle_check_run


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies for check_run_handler."""
    with patch.multiple(
        'services.webhook.check_run_handler',
        get_installation_access_token=Mock(return_value="test-token"),
        get_repository=Mock(return_value={"trigger_on_test_failure": True}),
        slack_notify=Mock(return_value="thread-123"),
        create_comment=Mock(return_value="comment-url"),
        create_user_request=Mock(return_value="usage-123"),
        cancel_workflow_runs=Mock(),
        get_pull_request=Mock(return_value={"title": "Test PR", "body": "Test body"}),
        get_pull_request_file_changes=Mock(return_value=[]),
        get_remote_file_content=Mock(return_value="workflow content"),
        get_workflow_run_path=Mock(return_value=".github/workflows/test.yml"),
        get_file_tree_list=Mock(return_value=("file tree", None)),
        get_workflow_run_logs=Mock(return_value="error logs"),
        get_retry_workflow_id_hash_pairs=Mock(return_value=[]),
        update_retry_workflow_id_hash_pairs=Mock(),
        has_comment_with_text=Mock(return_value=False),
        update_comment=Mock(),
        chat_with_agent=Mock(return_value=([], [], None, None, 0, 0, False, 10)),
        create_empty_commit=Mock(),
        update_usage=Mock(),
        is_pull_request_open=Mock(return_value=True),
        check_branch_exists=Mock(return_value=True),
        is_lambda_timeout_approaching=Mock(return_value=(False, 30)),
        get_circleci_token=Mock(return_value="circleci-token"),
        get_circleci_workflow_jobs=Mock(return_value=[]),
        get_circleci_build_logs=Mock(return_value="circleci logs"),
    ) as mocks:
        yield mocks


@pytest.fixture
def sample_github_payload():
    """Sample GitHub check run payload."""
    return {
        "check_run": {
            "name": "test-check",
            "details_url": "https://github.com/owner/repo/actions/runs/123456789/job/987654321",
            "head_sha": "abc123",
            "check_suite": {
                "head_branch": "main"
            },
            "pull_requests": [
                {
                    "number": 42,
                    "url": "https://api.github.com/repos/owner/repo/pulls/42"
                }
            ]
        },
        "repository": {
            "name": "test-repo",
            "id": 123456,
            "owner": {
                "login": "test-owner",
                "id": 789,
                "type": "Organization"
            },
            "clone_url": "https://github.com/test-owner/test-repo.git",
            "fork": False
        },
        "sender": {
            "id": 999,
            "login": "gitauto-for-dev[bot]"
        },
        "installation": {
            "id": 12345
        }
    }


@pytest.fixture
def sample_circleci_payload():
    """Sample CircleCI check run payload."""
    return {
        "check_run": {
            "name": "circleci-test",
            "details_url": "https://app.circleci.com/pipelines/circleci/J2wtzLah5rmzRnx6qn4RyQ/UUb5FLNgQCnif8mB6mQn7s/7/workflows/772ddda7-d6b7-49ad-9123-108d9f8164b5",
            "head_sha": "def456",
            "check_suite": {
                "head_branch": "feature-branch"
            },
            "pull_requests": [
                {
                    "number": 24,
                    "url": "https://api.github.com/repos/owner/repo/pulls/24"
                }
            ]
        },
        "repository": {
            "name": "circleci-repo",
            "id": 654321,
            "owner": {
                "login": "circleci-owner",
                "id": 987,
                "type": "User"
            },
            "clone_url": "https://github.com/circleci-owner/circleci-repo.git",
            "fork": False
        },
        "sender": {
            "id": 999,
            "login": "gitauto-for-dev[bot]"
        },
        "installation": {
            "id": 54321
        }
    }


def test_handle_check_run_github_actions_success(mock_dependencies, sample_github_payload):
    """Test successful handling of GitHub Actions check run."""
    # Execute
    handle_check_run(sample_github_payload)
    
    # Verify key interactions
    mock_dependencies['get_installation_access_token'].assert_called_once_with(installation_id=12345)
    mock_dependencies['get_repository'].assert_called_once_with(repo_id=123456)
    mock_dependencies['slack_notify'].assert_called()
    mock_dependencies['create_comment'].assert_called_once()
    mock_dependencies['get_workflow_run_logs'].assert_called_once()
    mock_dependencies['create_empty_commit'].assert_called_once()
    mock_dependencies['update_usage'].assert_called_once()


def test_handle_check_run_circleci_success(mock_dependencies, sample_circleci_payload):
    """Test successful handling of CircleCI check run."""
    # Setup CircleCI-specific mocks
    mock_dependencies['get_circleci_workflow_jobs'].return_value = [
        {"status": "failed", "job_number": 123}
    ]
    
    # Execute
    handle_check_run(sample_circleci_payload)
    
    # Verify CircleCI-specific interactions
    mock_dependencies['get_circleci_token'].assert_called_once_with(987)
    mock_dependencies['get_circleci_workflow_jobs'].assert_called_once()
    mock_dependencies['get_circleci_build_logs'].assert_called_once()


def test_handle_check_run_wrong_sender_returns_early(mock_dependencies, sample_github_payload):
    """Test that function returns early if sender is not GitAuto."""
    # Modify payload to have different sender
    sample_github_payload["sender"]["login"] = "different-bot"
    
    # Execute
    handle_check_run(sample_github_payload)
    
    # Verify no processing occurred
    mock_dependencies['get_installation_access_token'].assert_not_called()
    mock_dependencies['slack_notify'].assert_not_called()


def test_handle_check_run_no_pull_requests_returns_early(mock_dependencies, sample_github_payload):
    """Test that function returns early if no pull requests are associated."""
    # Remove pull requests
    sample_github_payload["check_run"]["pull_requests"] = []
    
    # Execute
    handle_check_run(sample_github_payload)
    
    # Verify no processing occurred
    mock_dependencies['get_installation_access_token'].assert_not_called()
    mock_dependencies['slack_notify'].assert_not_called()


def test_handle_check_run_trigger_disabled_returns_early(mock_dependencies, sample_github_payload):
    """Test that function returns early if trigger_on_test_failure is disabled."""
    # Disable trigger
    mock_dependencies['get_repository'].return_value = {"trigger_on_test_failure": False}
    
    # Execute
    handle_check_run(sample_github_payload)
    
    # Verify processing stopped after repository check
    mock_dependencies['get_repository'].assert_called_once()
    mock_dependencies['slack_notify'].assert_not_called()


def test_handle_check_run_no_repository_settings_returns_early(mock_dependencies, sample_github_payload):
    """Test that function returns early if no repository settings found."""
    # No repository settings
    mock_dependencies['get_repository'].return_value = None
    
    # Execute
    handle_check_run(sample_github_payload)
    
    # Verify processing stopped
    mock_dependencies['get_repository'].assert_called_once()
    mock_dependencies['slack_notify'].assert_not_called()


def test_handle_check_run_existing_comment_returns_early(mock_dependencies, sample_github_payload):
    """Test that function returns early if permission/stumbled comment exists."""
    # Comment already exists
    mock_dependencies['has_comment_with_text'].return_value = True
    
    # Execute
    handle_check_run(sample_github_payload)
    
    # Verify processing stopped after comment check
    mock_dependencies['has_comment_with_text'].assert_called_once()
    mock_dependencies['create_comment'].assert_not_called()


def test_handle_check_run_permission_denied_error_log(mock_dependencies, sample_github_payload):
    """Test handling of permission denied (404) error log."""
    # Setup 404 error log
    mock_dependencies['get_workflow_run_logs'].return_value = 404
    mock_dependencies['get_installation_permissions'] = Mock(return_value="limited")
    
    with patch('services.webhook.check_run_handler.get_installation_permissions', 
               return_value="limited") as mock_perms:
        # Execute
        handle_check_run(sample_github_payload)
        
        # Verify permission handling
        mock_perms.assert_called_once()
        mock_dependencies['update_comment'].assert_called()


def test_handle_check_run_no_error_log_found(mock_dependencies, sample_github_payload):
    """Test handling when no error log is found."""
    # Setup None error log
    mock_dependencies['get_workflow_run_logs'].return_value = None
    
    # Execute
    handle_check_run(sample_github_payload)
    
    # Verify handling
    mock_dependencies['update_comment'].assert_called()
    mock_dependencies['slack_notify'].assert_called()


def test_handle_check_run_duplicate_error_hash_skipped(mock_dependencies, sample_github_payload):
    """Test that duplicate error hash is skipped."""
    # Setup existing error hash
    error_log = "test error log"
    mock_dependencies['get_workflow_run_logs'].return_value = error_log
    
    # Calculate expected hash
    import hashlib
    from config import UTF8
    expected_hash = hashlib.sha256(error_log.encode(encoding=UTF8)).hexdigest()
    workflow_id = "123456789"
    expected_pair = f"{workflow_id}:{expected_hash}"
    
    # Setup existing pairs
    mock_dependencies['get_retry_workflow_id_hash_pairs'].return_value = [expected_pair]
    
    # Execute
    handle_check_run(sample_github_payload)
    
    # Verify skipping
    mock_dependencies['update_comment'].assert_called()
    mock_dependencies['chat_with_agent'].assert_not_called()


def test_handle_check_run_circleci_no_token_returns_early(mock_dependencies, sample_circleci_payload):
    """Test CircleCI handling when no token is configured."""
    # No CircleCI token
    mock_dependencies['get_circleci_token'].return_value = None
    
    # Execute
    handle_check_run(sample_circleci_payload)
    
    # Verify early return
    mock_dependencies['get_circleci_token'].assert_called_once()
    mock_dependencies['get_circleci_workflow_jobs'].assert_not_called()
    mock_dependencies['update_comment'].assert_called()


def test_handle_check_run_circleci_no_failed_jobs(mock_dependencies, sample_circleci_payload):
    """Test CircleCI handling when no failed jobs are found."""
    # No failed jobs
    mock_dependencies['get_circleci_workflow_jobs'].return_value = [
        {"status": "success", "job_number": 123}
    ]
    
    # Execute
    handle_check_run(sample_circleci_payload)
    
    # Verify handling
    mock_dependencies['get_circleci_workflow_jobs'].assert_called_once()
    mock_dependencies['get_circleci_build_logs'].assert_not_called()


def test_handle_check_run_pr_closed_during_execution(mock_dependencies, sample_github_payload):
    """Test handling when PR is closed during execution."""
    # Setup PR as closed during execution
    mock_dependencies['is_pull_request_open'].return_value = False
    
    # Execute
    handle_check_run(sample_github_payload)
    
    # Verify handling
    mock_dependencies['is_pull_request_open'].assert_called()
    mock_dependencies['update_comment'].assert_called()


def test_handle_check_run_branch_deleted_during_execution(mock_dependencies, sample_github_payload):
    """Test handling when branch is deleted during execution."""
    # Setup branch as deleted during execution
    mock_dependencies['check_branch_exists'].return_value = False
    
    # Execute
    handle_check_run(sample_github_payload)
    
    # Verify handling
    mock_dependencies['check_branch_exists'].assert_called()
    mock_dependencies['update_comment'].assert_called()


def test_handle_check_run_timeout_approaching(mock_dependencies, sample_github_payload):
    """Test handling when Lambda timeout is approaching."""
    # Setup timeout approaching
    mock_dependencies['is_lambda_timeout_approaching'].return_value = (True, 270)
    
    with patch('services.webhook.check_run_handler.get_timeout_message', 
               return_value="Timeout message") as mock_timeout:
        # Execute
        handle_check_run(sample_github_payload)
        
        # Verify timeout handling
        mock_timeout.assert_called_once()
        mock_dependencies['update_comment'].assert_called()


def test_handle_check_run_no_owner_returns_early(mock_dependencies, sample_github_payload):
    """Test that function returns early if repository has no owner."""
    # Remove owner
    sample_github_payload["repository"]["owner"] = None
    
    # Execute
    handle_check_run(sample_github_payload)
    
    # Verify early return
    mock_dependencies['get_installation_access_token'].assert_not_called()


def test_handle_check_run_workflow_path_404(mock_dependencies, sample_github_payload):
    """Test handling when workflow path returns 404."""
    # Setup workflow path as 404
    mock_dependencies['get_workflow_run_path'].return_value = 404
    
    # Execute
    handle_check_run(sample_github_payload)
    
    # Verify handling - workflow_content should be empty
    mock_dependencies['get_workflow_run_path'].assert_called_once()
    mock_dependencies['get_remote_file_content'].assert_not_called()


@pytest.mark.parametrize("status_code", [404, 401, 500])
def test_handle_check_run_circleci_build_logs_errors(mock_dependencies, sample_circleci_payload, status_code):
    """Test CircleCI build logs with various error responses."""
    # Setup failed job and error response
    mock_dependencies['get_circleci_workflow_jobs'].return_value = [
        {"status": "failed", "job_number": 123}
    ]
    mock_dependencies['get_circleci_build_logs'].return_value = status_code
    
    # Execute
    handle_check_run(sample_circleci_payload)
    
    # Verify handling
    mock_dependencies['get_circleci_build_logs'].assert_called_once()


def test_handle_check_run_chat_agent_loop_termination(mock_dependencies, sample_github_payload):
    """Test that chat agent loop terminates correctly."""
    # Setup chat agent to return no exploration and no commits
    mock_dependencies['chat_with_agent'].return_value = ([], [], None, None, 0, 0, False, 10)
    
    # Execute
    handle_check_run(sample_github_payload)
    
    # Verify chat agent was called (should terminate after first iteration)
    assert mock_dependencies['chat_with_agent'].call_count >= 2  # At least explore and commit calls


def test_handle_check_run_retry_count_exceeded(mock_dependencies, sample_github_payload):
    """Test that retry count limit is respected."""
    # Setup chat agent to return exploration but no commits (triggers retry)
    mock_dependencies['chat_with_agent'].side_effect = [
        ([], [], None, None, 0, 0, True, 10),   # explore: found files
        ([], [], None, None, 0, 0, False, 10),  # commit: no changes
    ] * 5  # Repeat to exceed retry limit
    
    # Execute
    handle_check_run(sample_github_payload)
    
    # Verify retry limit was respected (should stop after 3 retries)
    assert mock_dependencies['chat_with_agent'].call_count <= 10  # Max calls with retries


def test_handle_check_run_final_usage_update(mock_dependencies, sample_github_payload):
    """Test that final usage is updated correctly."""
    # Execute
    handle_check_run(sample_github_payload)
    
    # Verify usage update
    mock_dependencies['update_usage'].assert_called_once()
    call_args = mock_dependencies['update_usage'].call_args[1]
    assert call_args['usage_id'] == "usage-123"
    assert call_args['is_completed'] is True
    assert 'total_seconds' in call_args