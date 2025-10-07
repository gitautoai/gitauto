"""Unit tests for pr_checkbox_handler.py"""
# pylint: disable=redefined-outer-name,too-many-lines

from unittest.mock import AsyncMock, patch

import pytest
from services.webhook.pr_checkbox_handler import handle_pr_checkbox_trigger


@pytest.fixture
def base_payload():
    """Base payload fixture for PR checkbox tests"""
    return {
        "comment": {
            "id": 123456,
            "body": "- [x] Task 1\n- [ ] Task 2",
            "user": {"login": "test-user"},
        },
        "issue": {
            "number": 1,
            "pull_request": {"url": "https://api.github.com/repos/owner/repo/pulls/1"},
        },
        "repository": {
            "name": "test-repo",
            "owner": {"login": "test-owner"},
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
        }
        yield mock


@pytest.fixture
def mock_is_pull_request_open():
    """Mock is_pull_request_open"""
    with patch("services.webhook.pr_checkbox_handler.is_pull_request_open") as mock:
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
def mock_get_owner():
    """Mock get_owner"""
    with patch("services.webhook.pr_checkbox_handler.get_owner") as mock:
        mock.return_value = {
            "id": 1,
            "user_id": "user-123",
            "stripe_subscription_id": "sub_123",
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


@pytest.fixture
def mock_check_availability():
    """Mock check_availability"""
    with patch("services.webhook.pr_checkbox_handler.check_availability") as mock:
        mock.return_value = {"available": True, "credits_remaining": 100}
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
        mock.return_value = AsyncMock()
        yield mock


@pytest.fixture
def mock_create_comment():
    """Mock create_comment"""
    with patch("services.webhook.pr_checkbox_handler.create_comment") as mock:
        mock.return_value = {"id": 789}
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
        mock.return_value = {"id": "request-123"}
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


def test_handle_pr_checkbox_trigger_not_gitauto_pr(
    base_payload,
    lambda_info,
    mock_get_installation_access_token,
    mock_get_pull_request,
):
    """Test early return when PR is not from GitAuto"""
    mock_get_pull_request.return_value = {
        "user": {"login": "regular-user"},
        "body": "Test PR body",
        "head": {"ref": "test-branch"},
    }

    result = handle_pr_checkbox_trigger(
        payload=base_payload,
        lambda_info=lambda_info,
    )

    assert result is None
    mock_get_installation_access_token.assert_called_once()
    mock_get_pull_request.assert_called_once()


def test_handle_pr_checkbox_trigger_pr_closed(
    base_payload,
    lambda_info,
    mock_get_installation_access_token,
    mock_get_pull_request,
    mock_is_pull_request_open,
):
    """Test early return when PR is closed"""
    mock_is_pull_request_open.return_value = False

    result = handle_pr_checkbox_trigger(
        payload=base_payload,
        lambda_info=lambda_info,
    )

    assert result is None
    mock_get_installation_access_token.assert_called_once()
    mock_get_pull_request.assert_called_once()
    mock_is_pull_request_open.assert_called_once()


def test_handle_pr_checkbox_trigger_no_checkboxes(
    base_payload,
    lambda_info,
    mock_get_installation_access_token,
    mock_get_pull_request,
    mock_is_pull_request_open,
):
    """Test early return when comment has no checkboxes"""
    base_payload["comment"]["body"] = "Just a regular comment"

    result = handle_pr_checkbox_trigger(
        payload=base_payload,
        lambda_info=lambda_info,
    )

    assert result is None
    mock_get_installation_access_token.assert_called_once()
    mock_get_pull_request.assert_called_once()
    mock_is_pull_request_open.assert_called_once()


def test_handle_pr_checkbox_trigger_no_checked_boxes(
    base_payload,
    lambda_info,
    mock_get_installation_access_token,
    mock_get_pull_request,
    mock_is_pull_request_open,
):
    """Test early return when no checkboxes are checked"""
    base_payload["comment"]["body"] = "- [ ] Task 1\n- [ ] Task 2"

    result = handle_pr_checkbox_trigger(
        payload=base_payload,
        lambda_info=lambda_info,
    )

    assert result is None
    mock_get_installation_access_token.assert_called_once()
    mock_get_pull_request.assert_called_once()
    mock_is_pull_request_open.assert_called_once()


def test_handle_pr_checkbox_trigger_no_repository_found(
    base_payload,
    lambda_info,
    mock_get_installation_access_token,
    mock_get_pull_request,
    mock_is_pull_request_open,
    mock_get_repository,
):
    """Test early return when repository is not found"""
    mock_get_repository.return_value = None

    result = handle_pr_checkbox_trigger(
        payload=base_payload,
        lambda_info=lambda_info,
    )

    assert result is None
    mock_get_installation_access_token.assert_called_once()
    mock_get_pull_request.assert_called_once()
    mock_is_pull_request_open.assert_called_once()
    mock_get_repository.assert_called_once()


def test_handle_pr_checkbox_trigger_no_owner_found(
    base_payload,
    lambda_info,
    mock_get_installation_access_token,
    mock_get_pull_request,
    mock_is_pull_request_open,
    mock_get_repository,
    mock_get_owner,
):
    """Test early return when owner is not found"""
    mock_get_owner.return_value = None

    result = handle_pr_checkbox_trigger(
        payload=base_payload,
        lambda_info=lambda_info,
    )

    assert result is None
    mock_get_installation_access_token.assert_called_once()
    mock_get_pull_request.assert_called_once()
    mock_is_pull_request_open.assert_called_once()
    mock_get_repository.assert_called_once()
    mock_get_owner.assert_called_once()


def test_handle_pr_checkbox_trigger_no_user_found(
    base_payload,
    lambda_info,
    mock_get_installation_access_token,
    mock_get_pull_request,
    mock_is_pull_request_open,
    mock_get_repository,
    mock_get_owner,
    mock_get_user,
):
    """Test early return when user is not found"""
    mock_get_user.return_value = None

    result = handle_pr_checkbox_trigger(
        payload=base_payload,
        lambda_info=lambda_info,
    )

    assert result is None
    mock_get_installation_access_token.assert_called_once()
    mock_get_pull_request.assert_called_once()
    mock_is_pull_request_open.assert_called_once()
    mock_get_repository.assert_called_once()
    mock_get_owner.assert_called_once()
    mock_get_user.assert_called_once()


def test_handle_pr_checkbox_trigger_credits_depleted(
    base_payload,
    lambda_info,
    mock_get_installation_access_token,
    mock_get_pull_request,
    mock_is_pull_request_open,
    mock_get_repository,
    mock_get_owner,
    mock_get_user,
    mock_check_availability,
    mock_create_comment,
):
    """Test behavior when credits are depleted"""
    mock_check_availability.return_value = {"available": False, "credits_remaining": 0}

    result = handle_pr_checkbox_trigger(
        payload=base_payload,
        lambda_info=lambda_info,
    )

    assert result is None
    mock_get_installation_access_token.assert_called_once()
    mock_get_pull_request.assert_called_once()
    mock_is_pull_request_open.assert_called_once()
    mock_get_repository.assert_called_once()
    mock_get_owner.assert_called_once()
    mock_get_user.assert_called_once()
    mock_check_availability.assert_called_once()
    mock_create_comment.assert_called_once()


def test_handle_pr_checkbox_trigger_success(
    base_payload,
    lambda_info,
    mock_get_installation_access_token,
    mock_get_pull_request,
    mock_is_pull_request_open,
    mock_get_repository,
    mock_get_owner,
    mock_get_user,
    mock_check_availability,
    mock_extract_selected_files,
    mock_chat_with_agent,
    mock_create_comment,
    mock_update_comment,
    mock_create_user_request,
    mock_update_usage,
    mock_insert_credit,
):
    """Test successful execution of handle_pr_checkbox_trigger"""
    result = handle_pr_checkbox_trigger(
        payload=base_payload,
        lambda_info=lambda_info,
    )

    assert result is None
    mock_get_installation_access_token.assert_called_once()
    mock_get_pull_request.assert_called_once()
    mock_is_pull_request_open.assert_called_once()
    mock_get_repository.assert_called_once()
    mock_get_owner.assert_called_once()
    mock_get_user.assert_called_once()
    mock_check_availability.assert_called_once()
    mock_extract_selected_files.assert_called_once()
    mock_create_comment.assert_called_once()
