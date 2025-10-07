"""Unit tests for pr_checkbox_handler.py"""
# pylint: disable=redefined-outer-name,too-many-lines

from unittest.mock import AsyncMock, patch

import pytest
from services.webhook.pr_checkbox_handler import handle_pr_checkbox_trigger


@pytest.fixture
def base_payload():
    """Base payload fixture for PR checkbox tests"""
    return {
        "sender": {
            "id": 12345,
            "login": "test-user",
        },
        "comment": {
            "id": 123456,
            "body": "- [x] Generate Tests\n\n### Selected Files:\n- [x] file1.py\n- [x] file2.py",
            "user": {"login": "gitauto-ai[bot]"},
        },
        "issue": {
            "number": 1,
            "pull_request": {"url": "https://api.github.com/repos/owner/repo/pulls/1"},
        },
        "repository": {
            "id": 1,
            "name": "test-repo",
            "owner": {"login": "test-owner", "type": "User", "id": 1},
            "clone_url": "https://github.com/test-owner/test-repo.git",
            "fork": False,
        },
        "installation": {"id": 12345},
    }


@pytest.fixture
def lambda_info():
    """Lambda info fixture"""
    return {
        "log_group": "/aws/lambda/test",
        "log_stream": "2025/10/07/test",
        "request_id": "test-request-id",
    }


@pytest.fixture
def mock_get_installation_access_token():
    """Mock get_installation_access_token"""
    with patch(
        "services.webhook.pr_checkbox_handler.get_installation_access_token"
    ) as mock:
        mock.return_value = "test-token"
        yield mock


@pytest.fixture
def mock_get_pull_request():
    """Mock get_pull_request"""
    with patch("services.webhook.pr_checkbox_handler.get_pull_request") as mock:
        mock.return_value = {
            "user": {"login": "gitauto-ai[bot]"},
            "body": "Test PR body",
            "head": {"ref": "test-branch"},
            "title": "Test PR",
        }
        yield mock


@pytest.fixture
def mock_is_pull_request_open():
    """Mock is_pull_request_open"""
    with patch("services.webhook.pr_checkbox_handler.is_pull_request_open") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_check_branch_exists():
    """Mock check_branch_exists"""
    with patch("services.webhook.pr_checkbox_handler.check_branch_exists") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_get_repository():
    """Mock get_repository"""
    with patch("services.webhook.pr_checkbox_handler.get_repository") as mock:
        mock.return_value = {
            "id": 1,
            "owner_id": 1,
            "name": "test-repo",
            "owner": "test-owner",
        }
        yield mock


@pytest.fixture
def mock_check_availability():
    """Mock check_availability"""
    with patch("services.webhook.pr_checkbox_handler.check_availability") as mock:
        mock.return_value = {
            "can_proceed": True,
            "user_message": "",
            "billing_type": "credit",
            "log_message": "Access granted",
        }
        yield mock


@pytest.fixture
def mock_extract_selected_files():
    """Mock extract_selected_files"""
    with patch("services.webhook.pr_checkbox_handler.extract_selected_files") as mock:
        mock.return_value = ["file1.py", "file2.py"]
        yield mock


@pytest.fixture
def mock_chat_with_agent():
    """Mock chat_with_agent"""
    with patch("services.webhook.pr_checkbox_handler.chat_with_agent") as mock:
        mock.return_value = (
            [],  # messages
            [],  # previous_calls
            None,  # tool_name
            None,  # tool_args
            100,  # token_input
            50,  # token_output
            False,  # is_explored/is_committed
            10,  # p
        )
        yield mock


@pytest.fixture
def mock_create_comment():
    """Mock create_comment"""
    with patch("services.webhook.pr_checkbox_handler.create_comment") as mock:
        mock.return_value = "https://github.com/test-owner/test-repo/issues/1#issuecomment-123"
        yield mock


@pytest.fixture
def mock_update_comment():
    """Mock update_comment"""
    with patch("services.webhook.pr_checkbox_handler.update_comment") as mock:
        yield mock


@pytest.fixture
def mock_create_user_request():
    """Mock create_user_request"""
    with patch("services.webhook.pr_checkbox_handler.create_user_request") as mock:
        mock.return_value = "request-123"
        yield mock


@pytest.fixture
def mock_update_usage():
    """Mock update_usage"""
    with patch("services.webhook.pr_checkbox_handler.update_usage") as mock:
        yield mock


@pytest.fixture
def mock_insert_credit():
    """Mock insert_credit"""
    with patch("services.webhook.pr_checkbox_handler.insert_credit") as mock:
        yield mock


@pytest.fixture
def mock_cancel_workflow_runs():
    """Mock cancel_workflow_runs"""
    with patch("services.webhook.pr_checkbox_handler.cancel_workflow_runs") as mock:
        yield mock


@pytest.fixture
def mock_create_empty_commit():
    """Mock create_empty_commit"""
    with patch("services.webhook.pr_checkbox_handler.create_empty_commit") as mock:
        yield mock


@pytest.fixture
def mock_slack_notify():
    """Mock slack_notify"""
    with patch("services.webhook.pr_checkbox_handler.slack_notify") as mock:
        mock.return_value = "thread-123"
        yield mock


@pytest.fixture
def mock_get_owner():
    """Mock get_owner"""
    with patch("services.webhook.pr_checkbox_handler.get_owner") as mock:
        mock.return_value = {
            "id": 1,
            "credit_balance_usd": 100,
        }
        yield mock


@pytest.fixture
def mock_get_user():
    """Mock get_user"""
    with patch("services.webhook.pr_checkbox_handler.get_user") as mock:
        mock.return_value = {
            "id": "user-123",
            "email": "test@example.com",
        }
        yield mock


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_sender_is_bot(base_payload, lambda_info):
    """Test early return when sender is a bot"""
    base_payload["sender"]["login"] = "bot-user[bot]"

    result = await handle_pr_checkbox_trigger(
        payload=base_payload,
        lambda_info=lambda_info,
    )

    assert result is None


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_comment_not_from_gitauto(
    base_payload, lambda_info
):
    """Test early return when comment is not from GitAuto"""
    base_payload["comment"]["user"]["login"] = "regular-user"

    result = await handle_pr_checkbox_trigger(
        payload=base_payload,
        lambda_info=lambda_info,
    )

    assert result is None


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_no_generate_tests_checkbox(
    base_payload, lambda_info
):
    """Test early return when comment doesn't have Generate Tests checkbox"""
    base_payload["comment"]["body"] = "Just a regular comment"

    result = await handle_pr_checkbox_trigger(
        payload=base_payload,
        lambda_info=lambda_info,
    )

    assert result is None


@pytest.fixture
def mock_product_id():
    """Mock PRODUCT_ID"""
    with patch("services.webhook.pr_checkbox_handler.PRODUCT_ID", "gitauto"):
        yield


@pytest.fixture
def mock_github_app_user_name():
    """Mock GITHUB_APP_USER_NAME"""
    with patch(
        "services.webhook.pr_checkbox_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]"
    ):
        yield


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_no_files_selected(
    base_payload, lambda_info, mock_product_id, mock_extract_selected_files
):
    """Test early return when no files are selected"""
    # mock_product_id ensures PRODUCT_ID is "gitauto" so search_text matches
    mock_extract_selected_files.return_value = []

    result = await handle_pr_checkbox_trigger(
        payload=base_payload,
        lambda_info=lambda_info,
    )

    assert result is None


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_credits_depleted(
    base_payload,
    lambda_info,
    mock_product_id,
    mock_get_installation_access_token,
    mock_extract_selected_files,
    mock_slack_notify,
    mock_check_availability,
    mock_get_pull_request,
    mock_create_comment,
):
    """Test behavior when credits are depleted"""
    mock_check_availability.return_value = {
        "can_proceed": False,
        "user_message": "Credits depleted",
        "billing_type": "credit",
        "log_message": "Access denied: Credits depleted",
    }

    result = await handle_pr_checkbox_trigger(
        payload=base_payload,
        lambda_info=lambda_info,
    )

    assert result is None
    mock_get_installation_access_token.assert_called_once()
    mock_extract_selected_files.assert_called_once()
    mock_slack_notify.assert_called()
    mock_check_availability.assert_called_once()
    mock_create_comment.assert_called_once()


@pytest.mark.asyncio
async def test_handle_pr_checkbox_trigger_success(
    mock_product_id,
    base_payload,
    lambda_info,
    mock_get_installation_access_token,
    mock_extract_selected_files,
    mock_slack_notify,
    mock_check_availability,
    mock_get_pull_request,
    mock_create_comment,
    mock_update_comment,
    mock_create_user_request,
    mock_cancel_workflow_runs,
    mock_get_repository,
    mock_chat_with_agent,
    mock_is_pull_request_open,
    mock_check_branch_exists,
    mock_create_empty_commit,
    mock_update_usage,
    mock_insert_credit,
    mock_get_owner,
    # pylint: disable=redefined-outer-name
):
    """Test successful execution of handle_pr_checkbox_trigger"""
    result = await handle_pr_checkbox_trigger(
        payload=base_payload,
        lambda_info=lambda_info,
    )

    assert result is None
    mock_get_installation_access_token.assert_called_once()
    mock_extract_selected_files.assert_called_once()
    mock_slack_notify.assert_called()
    mock_check_availability.assert_called_once()
    mock_get_pull_request.assert_called_once()
    mock_create_comment.assert_called()
    mock_update_comment.assert_called()
    mock_create_user_request.assert_called_once()
    mock_cancel_workflow_runs.assert_called_once()
    mock_get_repository.assert_called_once()
    mock_chat_with_agent.assert_called()
    mock_is_pull_request_open.assert_called()
    mock_check_branch_exists.assert_called()
    mock_create_empty_commit.assert_called_once()
    mock_update_usage.assert_called_once()
    mock_insert_credit.assert_called_once()
