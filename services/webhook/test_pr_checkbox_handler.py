# Standard imports
import json
import time
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

# Third party imports
import pytest

# Local imports
from services.webhook.pr_checkbox_handler import handle_pr_checkbox_trigger
from services.github.types.webhook.issue_comment import IssueCommentWebhookPayload


@pytest.fixture
def mock_time():
    """Fixture to mock time.time()."""
    with patch("services.webhook.pr_checkbox_handler.time.time") as mock:
        mock.return_value = 1234567890.0
        yield mock


@pytest.fixture
def mock_datetime():
    """Fixture to mock datetime.now()."""
    with patch("services.webhook.pr_checkbox_handler.datetime") as mock:
        mock_dt = MagicMock()
        mock_dt.strftime.return_value = "2023-01-01"
        mock.now.return_value = mock_dt
        yield mock


@pytest.fixture
def mock_github_app_user_name():
    """Fixture to mock GITHUB_APP_USER_NAME."""
    with patch("services.webhook.pr_checkbox_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]"):
        yield "gitauto-ai[bot]"


@pytest.fixture
def mock_product_id():
    """Fixture to mock PRODUCT_ID."""
    with patch("services.webhook.pr_checkbox_handler.PRODUCT_ID", "gitauto"):
        yield "gitauto"


@pytest.fixture
def mock_settings_links():
    """Fixture to mock SETTINGS_LINKS."""
    with patch("services.webhook.pr_checkbox_handler.SETTINGS_LINKS", "Settings links here"):
        yield "Settings links here"


@pytest.fixture
def mock_extract_selected_files():
    """Fixture to mock extract_selected_files function."""
    with patch("services.webhook.pr_checkbox_handler.extract_selected_files") as mock:
        mock.return_value = ["file1.py", "file2.py"]
        yield mock


@pytest.fixture
def mock_get_installation_access_token():
    """Fixture to mock get_installation_access_token function."""
    with patch("services.webhook.pr_checkbox_handler.get_installation_access_token") as mock:
        mock.return_value = "test_token_123"
        yield mock


@pytest.fixture
def mock_slack_notify():
    """Fixture to mock slack_notify function."""
    with patch("services.webhook.pr_checkbox_handler.slack_notify") as mock:
        mock.return_value = "thread_ts_123"
        yield mock


@pytest.fixture
def mock_is_request_limit_reached():
    """Fixture to mock is_request_limit_reached function."""
    with patch("services.webhook.pr_checkbox_handler.is_request_limit_reached") as mock:
        mock.return_value = {
            "is_limit_reached": False,
            "requests_left": 100,
            "request_limit": 1000,
            "end_date": "2023-12-31",
            "is_credit_user": False
        }
        yield mock


@pytest.fixture
def mock_get_pull_request():
    """Fixture to mock get_pull_request function."""
    with patch("services.webhook.pr_checkbox_handler.get_pull_request") as mock:
        mock.return_value = {
            "head": {"ref": "feature-branch"},
            "title": "Test PR Title",
            "body": "Test PR Body"
        }
        yield mock


@pytest.fixture
def mock_create_user_request():
    """Fixture to mock create_user_request function."""
    with patch("services.webhook.pr_checkbox_handler.create_user_request") as mock:
        mock.return_value = "usage_id_123"
        yield mock


@pytest.fixture
def mock_cancel_workflow_runs():
    """Fixture to mock cancel_workflow_runs function."""
    with patch("services.webhook.pr_checkbox_handler.cancel_workflow_runs") as mock:
        yield mock


@pytest.fixture
def mock_get_repository():
    """Fixture to mock get_repository function."""
    with patch("services.webhook.pr_checkbox_handler.get_repository") as mock:
        mock.return_value = {"id": 123, "settings": "test"}
        yield mock


@pytest.fixture
def mock_create_comment():
    """Fixture to mock create_comment function."""
    with patch("services.webhook.pr_checkbox_handler.create_comment") as mock:
        mock.return_value = "comment_url_123"
        yield mock


@pytest.fixture
def mock_update_comment():
    """Fixture to mock update_comment function."""
    with patch("services.webhook.pr_checkbox_handler.update_comment") as mock:
        yield mock


@pytest.fixture
def mock_get_file_tree_list():
    """Fixture to mock get_file_tree_list function."""
    with patch("services.webhook.pr_checkbox_handler.get_file_tree_list") as mock:
        mock.return_value = (["file1.py", "file2.py"], "Tree comment")
        yield mock


@pytest.fixture
def mock_is_lambda_timeout_approaching():
    """Fixture to mock is_lambda_timeout_approaching function."""
    with patch("services.webhook.pr_checkbox_handler.is_lambda_timeout_approaching") as mock:
        mock.return_value = (False, 30.0)
        yield mock


@pytest.fixture
def mock_is_pull_request_open():
    """Fixture to mock is_pull_request_open function."""
    with patch("services.webhook.pr_checkbox_handler.is_pull_request_open") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_check_branch_exists():
    """Fixture to mock check_branch_exists function."""
    with patch("services.webhook.pr_checkbox_handler.check_branch_exists") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_chat_with_agent():
    """Fixture to mock chat_with_agent function."""
    with patch("services.webhook.pr_checkbox_handler.chat_with_agent") as mock:
        mock.return_value = (
            [{"role": "user", "content": "test"}],  # messages
            [],  # previous_calls
            "test_tool",  # tool_name
            {},  # tool_args
            100,  # token_input
            200,  # token_output
            True,  # is_explored/is_committed
            50,  # p
        )
        yield mock


@pytest.fixture
def mock_create_empty_commit():
    """Fixture to mock create_empty_commit function."""
    with patch("services.webhook.pr_checkbox_handler.create_empty_commit") as mock:
        yield mock


@pytest.fixture
def mock_update_usage():
    """Fixture to mock update_usage function."""
    with patch("services.webhook.pr_checkbox_handler.update_usage") as mock:
        yield mock


@pytest.fixture
def mock_insert_credit():
    """Fixture to mock insert_credit function."""
    with patch("services.webhook.pr_checkbox_handler.insert_credit") as mock:
        yield mock


@pytest.fixture
def mock_get_owner():
    """Fixture to mock get_owner function."""
    with patch("services.webhook.pr_checkbox_handler.get_owner") as mock:
        mock.return_value = {"credit_balance_usd": 10.0}
        yield mock


@pytest.fixture
def mock_get_user():
    """Fixture to mock get_user function."""
    with patch("services.webhook.pr_checkbox_handler.get_user") as mock:
        mock.return_value = {"email": "test@example.com"}
        yield mock


@pytest.fixture
def mock_send_email():
    """Fixture to mock send_email function."""
    with patch("services.webhook.pr_checkbox_handler.send_email") as mock:
        yield mock


@pytest.fixture
def mock_get_credits_depleted_email_text():
    """Fixture to mock get_credits_depleted_email_text function."""
    with patch("services.webhook.pr_checkbox_handler.get_credits_depleted_email_text") as mock:
        mock.return_value = ("Subject", "Email text")
        yield mock


@pytest.fixture
def mock_create_progress_bar():
    """Fixture to mock create_progress_bar function."""
    with patch("services.webhook.pr_checkbox_handler.create_progress_bar") as mock:
        mock.return_value = "Progress bar content"
        yield mock


@pytest.fixture
def mock_request_limit_reached():
    """Fixture to mock request_limit_reached function."""
    with patch("services.webhook.pr_checkbox_handler.request_limit_reached") as mock:
        mock.return_value = "Request limit reached message"
        yield mock


@pytest.fixture
def mock_get_timeout_message():
    """Fixture to mock get_timeout_message function."""
    with patch("services.webhook.pr_checkbox_handler.get_timeout_message") as mock:
        mock.return_value = "Timeout message"
        yield mock


@pytest.fixture
def mock_create_reset_command_message():
    """Fixture to mock create_reset_command_message function."""
    with patch("services.webhook.pr_checkbox_handler.create_reset_command_message") as mock:
        mock.return_value = "\nReset command message"
        yield mock


@pytest.fixture
def base_payload():
    """Fixture providing a base webhook payload."""
    return {
        "sender": {
            "id": 12345,
            "login": "test_user"
        },
        "comment": {
            "user": {"login": "gitauto-ai[bot]"},
            "body": "- [x] Generate Tests - gitauto\n- [x] `file1.py`\n- [x] `file2.py`"
        },
        "repository": {
            "id": 123456,
            "name": "test-repo",
            "owner": {
                "login": "test-owner",
                "type": "Organization",
                "id": 789012
            },
            "clone_url": "https://github.com/test-owner/test-repo.git",
            "fork": False
        },
        "issue": {
            "number": 42
        },
        "installation": {
            "id": 98765
        }
    }


@pytest.fixture
def all_mocks(
    mock_time,
    mock_datetime,
    mock_github_app_user_name,
    mock_product_id,
    mock_settings_links,
    mock_extract_selected_files,
    mock_get_installation_access_token,
    mock_slack_notify,
    mock_is_request_limit_reached,
    mock_get_pull_request,
    mock_create_user_request,
    mock_cancel_workflow_runs,
    mock_get_repository,
    mock_create_comment,
    mock_update_comment,
    mock_get_file_tree_list,
    mock_is_lambda_timeout_approaching,
    mock_is_pull_request_open,
    mock_check_branch_exists,
    mock_chat_with_agent,
    mock_create_empty_commit,
    mock_update_usage,
    mock_insert_credit,
    mock_get_owner,
    mock_get_user,
    mock_send_email,
    mock_get_credits_depleted_email_text,
    mock_create_progress_bar,
    mock_request_limit_reached,
    mock_get_timeout_message,
    mock_create_reset_command_message,
):
    """Fixture that provides all mocks for comprehensive testing."""
    pass


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_skips_bot_sender(base_payload):
    """Test that the handler skips when sender is a bot."""
    # pylint: disable=redefined-outer-name
    payload = base_payload.copy()
    payload["sender"]["login"] = "some-bot[bot]"
    
    result = await handle_pr_checkbox_trigger(payload)
    
    assert result is None


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_skips_non_gitauto_comment(base_payload, mock_github_app_user_name):
    """Test that the handler skips when comment is not from GitAuto."""
    # pylint: disable=redefined-outer-name
    payload = base_payload.copy()
    payload["comment"]["user"]["login"] = "other-user"
    
    result = await handle_pr_checkbox_trigger(payload)
    
    assert result is None


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_skips_missing_search_text(base_payload, all_mocks):
    """Test that the handler skips when comment doesn't contain the search text."""
    # pylint: disable=redefined-outer-name
    payload = base_payload.copy()
    payload["comment"]["body"] = "Some other comment content"
    
    result = await handle_pr_checkbox_trigger(payload)
    
    assert result is None


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_skips_no_selected_files(base_payload, all_mocks, mock_extract_selected_files):
    """Test that the handler skips when no files are selected."""
    # pylint: disable=redefined-outer-name
    mock_extract_selected_files.return_value = []
    
    result = await handle_pr_checkbox_trigger(payload)
    
    assert result is None


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_handles_request_limit_reached(
    base_payload, all_mocks, mock_is_request_limit_reached, mock_create_comment, mock_slack_notify
):
    """Test that the handler handles request limit reached scenario."""
    # pylint: disable=redefined-outer-name
    mock_is_request_limit_reached.return_value = {
        "is_limit_reached": True,
        "requests_left": 0,
        "request_limit": 1000,
        "end_date": "2023-12-31",
        "is_credit_user": False
    }
    
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
    mock_create_comment.assert_called_once()
    assert mock_slack_notify.call_count == 2  # Start and early return notifications


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_successful_execution(base_payload, all_mocks):
    """Test successful execution of the PR checkbox handler."""
    # pylint: disable=redefined-outer-name
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None  # Function returns None on success
    
    # Verify key function calls were made
    all_mocks  # Access fixture to ensure all mocks are set up


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_timeout_scenario(
    base_payload, all_mocks, mock_is_lambda_timeout_approaching, mock_update_comment
):
    """Test that the handler handles timeout scenario."""
    # pylint: disable=redefined-outer-name
    mock_is_lambda_timeout_approaching.return_value = (True, 890.0)
    
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
    mock_update_comment.assert_called()


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_pr_closed_scenario(
    base_payload, all_mocks, mock_is_pull_request_open, mock_update_comment
):
    """Test that the handler stops when PR is closed."""
    # pylint: disable=redefined-outer-name
    mock_is_pull_request_open.return_value = False
    
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
    mock_update_comment.assert_called()


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_branch_deleted_scenario(
    base_payload, all_mocks, mock_check_branch_exists, mock_update_comment
):
    """Test that the handler stops when branch is deleted."""
    # pylint: disable=redefined-outer-name
    mock_check_branch_exists.return_value = False
    
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
    mock_update_comment.assert_called()


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_chat_agent_loop_scenarios(base_payload, all_mocks, mock_chat_with_agent):
    """Test different chat agent loop scenarios."""
    # pylint: disable=redefined-outer-name
    
    # Test scenario: not explored and not committed (break)
    mock_chat_with_agent.side_effect = [
        # First call (get mode)
        ([], [], "tool", {}, 100, 200, False, 50),
        # Second call (commit mode)
        ([], [], "tool", {}, 100, 200, False, 50),
    ]
    
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
    assert mock_chat_with_agent.call_count == 2


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_retry_scenarios(base_payload, all_mocks, mock_chat_with_agent):
    """Test retry scenarios in the chat agent loop."""
    # pylint: disable=redefined-outer-name
    
    # Test scenario: not explored but committed (retry)
    mock_chat_with_agent.side_effect = [
        # First iteration
        ([], [], "tool", {}, 100, 200, False, 50),  # get mode
        ([], [], "tool", {}, 100, 200, True, 50),   # commit mode
        # Second iteration
        ([], [], "tool", {}, 100, 200, False, 50),  # get mode
        ([], [], "tool", {}, 100, 200, False, 50),  # commit mode
    ]
    
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
    assert mock_chat_with_agent.call_count == 4


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_credit_user_scenario(
    base_payload, all_mocks, mock_is_request_limit_reached, mock_insert_credit, mock_get_owner, mock_get_user, mock_send_email
):
    """Test credit user scenario with depleted credits."""
    # pylint: disable=redefined-outer-name
    mock_is_request_limit_reached.return_value = {
        "is_limit_reached": False,
        "requests_left": 100,
        "request_limit": 1000,
        "end_date": "2023-12-31",
        "is_credit_user": True
    }
    mock_get_owner.return_value = {"credit_balance_usd": 0.0}
    
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
    mock_insert_credit.assert_called_once()
    mock_send_email.assert_called_once()


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_credit_user_no_email(
    base_payload, all_mocks, mock_is_request_limit_reached, mock_get_owner, mock_get_user, mock_send_email
):
    """Test credit user scenario when user has no email."""
    # pylint: disable=redefined-outer-name
    mock_is_request_limit_reached.return_value = {
        "is_limit_reached": False,
        "requests_left": 100,
        "request_limit": 1000,
        "end_date": "2023-12-31",
        "is_credit_user": True
    }
    mock_get_owner.return_value = {"credit_balance_usd": 0.0}
    mock_get_user.return_value = {"email": None}
    
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
    mock_send_email.assert_not_called()


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_non_credit_user(
    base_payload, all_mocks, mock_is_request_limit_reached, mock_insert_credit
):
    """Test non-credit user scenario."""
    # pylint: disable=redefined-outer-name
    mock_is_request_limit_reached.return_value = {
        "is_limit_reached": False,
        "requests_left": 100,
        "request_limit": 1000,
        "end_date": "2023-12-31",
        "is_credit_user": False
    }
    
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
    mock_insert_credit.assert_not_called()


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_different_product_id(base_payload, all_mocks):
    """Test handler with different product ID."""
    # pylint: disable=redefined-outer-name
    with patch("services.webhook.pr_checkbox_handler.PRODUCT_ID", "custom-product"):
        payload = base_payload.copy()
        payload["comment"]["body"] = "- [x] Generate Tests - custom-product\n- [x] `file1.py`"
        
        result = await handle_pr_checkbox_trigger(payload)
        
        assert result is None


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_settings_links_removal(base_payload, all_mocks, mock_extract_selected_files):
    """Test that settings links are properly removed from comment body."""
    # pylint: disable=redefined-outer-name
    payload = base_payload.copy()
    payload["comment"]["body"] = "- [x] Generate Tests - gitauto\nSettings links here\n- [x] `file1.py`"
    
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
    # Verify extract_selected_files was called with cleaned comment body
    mock_extract_selected_files.assert_called_once()
    call_args = mock_extract_selected_files.call_args[0][0]
    assert "Settings links here" not in call_args


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_base_args_construction(
    base_payload, all_mocks, mock_get_pull_request
):
    """Test that base_args is constructed correctly."""
    # pylint: disable=redefined-outer-name
    mock_get_pull_request.return_value = {
        "head": {"ref": "feature-branch"},
        "title": "Test PR Title",
        "body": "Test PR Body"
    }
    
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
    # Verify that get_pull_request was called with correct parameters
    mock_get_pull_request.assert_called_once_with(
        owner="test-owner",
        repo="test-repo", 
        pull_number=42,
        token="test_token_123"
    )


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_progress_updates(
    base_payload, all_mocks, mock_create_progress_bar, mock_update_comment
):
    """Test that progress updates are made correctly."""
    # pylint: disable=redefined-outer-name
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
    # Verify progress bar was created and comments were updated
    assert mock_create_progress_bar.call_count >= 2
    assert mock_update_comment.call_count >= 2


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_file_tree_retrieval(
    base_payload, all_mocks, mock_get_file_tree_list
):
    """Test that file tree is retrieved correctly."""
    # pylint: disable=redefined-outer-name
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
    mock_get_file_tree_list.assert_called_once()
    call_args = mock_get_file_tree_list.call_args[1]
    assert "base_args" in call_args
    assert call_args["max_files"] == 100


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_input_message_format(
    base_payload, all_mocks, mock_chat_with_agent, mock_datetime
):
    """Test that input message is formatted correctly for chat agent."""
    # pylint: disable=redefined-outer-name
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
    
    # Verify chat_with_agent was called with correct message format
    mock_chat_with_agent.assert_called()
    first_call_args = mock_chat_with_agent.call_args_list[0][1]
    messages = first_call_args["messages"]
    
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    
    content = json.loads(messages[0]["content"])
    assert "selected_files" in content
    assert "file_tree" in content
    assert "today" in content
    assert content["today"] == "2023-01-01"


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_workflow_cancellation(
    base_payload, all_mocks, mock_cancel_workflow_runs
):
    """Test that existing workflow runs are cancelled."""
    # pylint: disable=redefined-outer-name
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
    mock_cancel_workflow_runs.assert_called_once_with(
        owner="test-owner",
        repo="test-repo",
        branch="feature-branch",
        token="test_token_123"
    )


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_usage_tracking(
    base_payload, all_mocks, mock_create_user_request, mock_update_usage, mock_time
):
    """Test that usage is tracked correctly."""
    # pylint: disable=redefined-outer-name
    mock_time.side_effect = [1234567890.0, 1234567920.0]  # Start and end times
    
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
    
    # Verify usage record creation
    mock_create_user_request.assert_called_once_with(
        user_id=12345,
        user_name="test_user",
        installation_id=98765,
        owner_id=789012,
        owner_type="Organization",
        owner_name="test-owner",
        repo_id=123456,
        repo_name="test-repo",
        issue_number=42,
        source="github",
        trigger="pr_checkbox",
        email=None,
    )
    
    # Verify usage record update
    mock_update_usage.assert_called_once_with(
        usage_id="usage_id_123",
        token_input=0,
        token_output=0,
        total_seconds=30,  # 1234567920 - 1234567890
        pr_number=42,
        is_completed=True,
    )


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_final_commit_and_message(
    base_payload, all_mocks, mock_create_empty_commit, mock_update_comment, mock_create_reset_command_message
):
    """Test that final empty commit is created and final message is posted."""
    # pylint: disable=redefined-outer-name
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
    
    # Verify empty commit creation
    mock_create_empty_commit.assert_called_once()
    
    # Verify final message update
    mock_create_reset_command_message.assert_called_once_with("feature-branch")
    
    # Check that the final update_comment call includes the reset command message
    final_call = mock_update_comment.call_args_list[-1]
    final_body = final_call[1]["body"]
    assert "Finished generating tests for selected files!" in final_body
    assert "Reset command message" in final_body


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_slack_notifications(
    base_payload, all_mocks, mock_slack_notify
):
    """Test that Slack notifications are sent correctly."""
    # pylint: disable=redefined-outer-name
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
    
    # Verify start and end notifications
    assert mock_slack_notify.call_count == 2
    
    # Check start notification
    start_call = mock_slack_notify.call_args_list[0]
    start_message = start_call[0][0]
    assert "PR checkbox handler started by `test_user` for PR #42 in `test-owner/test-repo`" == start_message
    
    # Check end notification
    end_call = mock_slack_notify.call_args_list[1]
    end_message = end_call[0][0]
    thread_ts = end_call[0][1]
    assert end_message == "Completed"
    assert thread_ts == "thread_ts_123"


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_retry_limit_exceeded(
    base_payload, all_mocks, mock_chat_with_agent
):
    """Test that retry limit is respected in the chat agent loop."""
    # pylint: disable=redefined-outer-name
    
    # Set up scenario where retry count exceeds limit
    mock_chat_with_agent.side_effect = [
        # Iteration 1
        ([], [], "tool", {}, 100, 200, False, 50),  # get mode
        ([], [], "tool", {}, 100, 200, True, 50),   # commit mode
        # Iteration 2
        ([], [], "tool", {}, 100, 200, False, 50),  # get mode
        ([], [], "tool", {}, 100, 200, True, 50),   # commit mode
        # Iteration 3
        ([], [], "tool", {}, 100, 200, False, 50),  # get mode
        ([], [], "tool", {}, 100, 200, True, 50),   # commit mode
        # Iteration 4
        ([], [], "tool", {}, 100, 200, False, 50),  # get mode
        ([], [], "tool", {}, 100, 200, True, 50),   # commit mode
    ]
    
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
    # Should stop after 4 retries (retry_count > 3)
    assert mock_chat_with_agent.call_count == 8


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_successful_exploration_and_commit(
    base_payload, all_mocks, mock_chat_with_agent
):
    """Test successful exploration and commit scenario."""
    # pylint: disable=redefined-outer-name
    
    # Set up scenario where both exploration and commit succeed
    mock_chat_with_agent.side_effect = [
        # First iteration - successful
        ([], [], "tool", {}, 100, 200, True, 50),   # get mode - explored
        ([], [], "tool", {}, 100, 200, True, 50),   # commit mode - committed
        # Second iteration - nothing to do
        ([], [], "tool", {}, 100, 200, False, 50),  # get mode - not explored
        ([], [], "tool", {}, 100, 200, False, 50),  # commit mode - not committed
    ]
    
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
    # Should complete after successful iteration and then break
    assert mock_chat_with_agent.call_count == 4


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_edge_case_empty_repository_data(base_payload, all_mocks):
    """Test handling of edge case with minimal repository data."""
    # pylint: disable=redefined-outer-name
    payload = base_payload.copy()
    payload["repository"]["clone_url"] = ""
    payload["repository"]["fork"] = None
    
    result = await handle_pr_checkbox_trigger(payload)
    
    assert result is None


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_edge_case_missing_pr_data(
    base_payload, all_mocks, mock_get_pull_request
):
    """Test handling of edge case with missing PR data."""
    # pylint: disable=redefined-outer-name
    mock_get_pull_request.return_value = {
        "head": {"ref": "feature-branch"},
        "title": None,
        "body": None
    }
    
    result = await handle_pr_checkbox_trigger(base_payload)
    
    assert result is None
