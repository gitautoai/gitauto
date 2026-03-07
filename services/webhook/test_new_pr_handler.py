# pylint: disable=unused-argument,too-many-lines
# pyright: reportUnusedVariable=false

import inspect
import json
from typing import cast
from unittest.mock import AsyncMock, patch

import pytest

from config import PRODUCT_ID
from services.chat_with_agent import AgentResult
from services.github.types.github_types import PrLabeledPayload
from services.webhook.new_pr_handler import handle_new_pr


def test_handle_new_pr_signature():
    """Test that handle_new_pr has the expected signature with lambda_info parameter"""

    sig = inspect.signature(handle_new_pr)
    params = list(sig.parameters.keys())

    # Verify lambda_info parameter exists and is optional
    assert "lambda_info" in params
    lambda_info_param = sig.parameters["lambda_info"]
    assert lambda_info_param.default is None  # Optional parameter with None default


def _get_base_args():
    return {
        "installation_id": 123,
        "owner_id": 456,
        "owner_type": "User",
        "repo_id": 789,
        "pr_body": "Test PR body",
        "owner": "test_owner",
        "repo": "test_repo",
        "pr_number": 100,
        "pr_title": "Schedule: Add unit tests to services/test_file.py",
        "sender_name": "test_sender",
        "repo_full_name": "test_owner/test_repo",
        "pr_creator": "test_creator",
        "sender_id": 888,
        "token": "github_token_123",
        "new_branch": "gitauto/dashboard-20250101-120000-Ab1C",
        "sender_email": "test@example.com",
        "sender_display_name": "Test Sender",
        "github_urls": {
            "issues": "https://api.github.com/repos/test_owner/test_repo/issues",
            "pulls": "https://api.github.com/repos/test_owner/test_repo/pulls",
        },
        "clone_url": "https://github.com/test_owner/test_repo.git",
        "base_branch": "main",
    }


def _get_test_payload():
    return cast(
        PrLabeledPayload,
        {
            "action": "labeled",
            "number": 100,
            "label": {"name": PRODUCT_ID},
            "issue": {
                "number": 100,
                "title": "Schedule: Add unit tests to services/test_file.py",
                "body": "Test body",
            },
            "pull_request": {
                "html_url": "https://github.com/test_owner/test_repo/pull/100",
                "head": {"ref": "gitauto/dashboard-20250101-120000-Ab1C"},
            },
            "repository": {"name": "test_repo", "full_name": "test_owner/test_repo"},
            "sender": {"login": "test_sender"},
        },
    )


@pytest.mark.asyncio
@patch("services.webhook.new_pr_handler.get_stripe_customer_id")
@patch("services.webhook.new_pr_handler.get_repository_features")
@patch("services.webhook.new_pr_handler.slack_notify")
@patch("services.webhook.new_pr_handler.update_comment")
@patch("services.webhook.new_pr_handler.create_progress_bar")
@patch("services.webhook.new_pr_handler.create_comment")
@patch("services.webhook.new_pr_handler.render_text")
@patch("services.webhook.new_pr_handler.check_availability")
@patch("services.webhook.new_pr_handler.deconstruct_github_payload")
async def test_can_proceed_false_early_return(
    mock_deconstruct,
    mock_check_availability,
    mock_render_text,
    mock_create_comment,
    mock_create_progress_bar,
    mock_update_comment,
    mock_slack_notify,
    mock_get_repo_features,
    mock_get_stripe_id,
):
    mock_deconstruct.return_value = (_get_base_args(), None)
    mock_render_text.return_value = "Rendered"
    mock_slack_notify.return_value = "thread_1"
    mock_create_comment.return_value = "comment_url"
    mock_create_progress_bar.return_value = "progress"
    mock_get_repo_features.return_value = {
        "restrict_edit_to_target_test_file_only": False,
        "allow_edit_any_file": True,
    }
    mock_get_stripe_id.return_value = "cus_existing"
    mock_check_availability.return_value = {
        "can_proceed": False,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 0,
        "period_end_date": None,
        "user_message": "No credits available",
        "log_message": "User has no credits",
    }

    await handle_new_pr(
        payload=_get_test_payload(),
        trigger="dashboard",
    )

    mock_update_comment.assert_called()
    assert mock_slack_notify.call_count == 2

    # Verify get_repository_features was called with owner_id and repo_id
    mock_get_repo_features.assert_called_once_with(owner_id=456, repo_id=789)


@pytest.mark.asyncio
@patch("services.webhook.new_pr_handler.update_stripe_customer_id")
@patch("services.webhook.new_pr_handler.create_stripe_customer")
@patch("services.webhook.new_pr_handler.get_stripe_customer_id")
@patch("services.webhook.new_pr_handler.get_repository_features")
@patch("services.webhook.new_pr_handler.slack_notify")
@patch("services.webhook.new_pr_handler.update_comment")
@patch("services.webhook.new_pr_handler.create_progress_bar")
@patch("services.webhook.new_pr_handler.create_comment")
@patch("services.webhook.new_pr_handler.render_text")
@patch("services.webhook.new_pr_handler.check_availability")
@patch("services.webhook.new_pr_handler.deconstruct_github_payload")
async def test_stripe_customer_id_update(
    mock_deconstruct,
    mock_check_availability,
    mock_render_text,
    mock_create_comment,
    mock_create_progress_bar,
    mock_update_comment,
    mock_slack_notify,
    mock_get_repo_features,
    mock_get_stripe_id,
    mock_create_stripe,
    mock_update_stripe,
):
    mock_deconstruct.return_value = (_get_base_args(), None)
    mock_render_text.return_value = "Rendered"
    mock_slack_notify.return_value = "thread_1"
    mock_create_comment.return_value = "comment_url"
    mock_create_progress_bar.return_value = "progress"
    mock_get_repo_features.return_value = {
        "restrict_edit_to_target_test_file_only": False,
        "allow_edit_any_file": True,
    }
    mock_get_stripe_id.return_value = None
    mock_create_stripe.return_value = "cus_new123"
    mock_check_availability.return_value = {
        "can_proceed": False,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 0,
        "period_end_date": None,
        "user_message": "No credits",
        "log_message": "No credits",
    }

    await handle_new_pr(
        payload=_get_test_payload(),
        trigger="dashboard",
    )

    mock_update_stripe.assert_called_once_with(456, "cus_new123", "888:test_sender")


@pytest.mark.asyncio
@patch("services.webhook.new_pr_handler.update_usage")
@patch("services.webhook.new_pr_handler.get_pull_request_files")
@patch("services.webhook.new_pr_handler.chat_with_agent")
@patch("services.webhook.new_pr_handler.create_empty_commit")
@patch("services.webhook.new_pr_handler.should_bail", return_value=False)
@patch("services.webhook.new_pr_handler.get_remote_file_content_by_url")
@patch("services.webhook.new_pr_handler.get_base64")
@patch("services.webhook.new_pr_handler.describe_image")
@patch("services.webhook.new_pr_handler.extract_image_urls")
@patch("services.webhook.new_pr_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.create_user_request")
@patch("services.webhook.new_pr_handler.get_stripe_customer_id")
@patch("services.webhook.new_pr_handler.get_repository_features")
@patch("services.webhook.new_pr_handler.slack_notify")
@patch("services.webhook.new_pr_handler.update_comment")
@patch("services.webhook.new_pr_handler.create_progress_bar")
@patch("services.webhook.new_pr_handler.create_comment")
@patch("services.webhook.new_pr_handler.render_text")
@patch("services.webhook.new_pr_handler.get_comments")
@patch("services.webhook.new_pr_handler.check_availability")
@patch("services.webhook.new_pr_handler.deconstruct_github_payload")
async def test_image_urls_processing(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_create_comment,
    mock_create_progress_bar,
    mock_update_comment,
    mock_slack_notify,
    mock_get_repo_features,
    mock_get_stripe_id,
    mock_create_user_request,
    mock_ensure_node_packages,
    mock_git_clone_to_efs,
    mock_prepare_repo,
    mock_extract_image_urls,
    mock_describe_image,
    mock_get_base64,
    mock_get_remote_file,
    mock_should_bail,
    mock_create_empty_commit,
    mock_chat_with_agent,
    mock_get_pr_files,
    mock_update_usage,
):
    mock_deconstruct.return_value = (_get_base_args(), None)
    mock_render_text.return_value = "Rendered body"
    mock_slack_notify.return_value = "thread_1"
    mock_create_comment.return_value = "comment_url"
    mock_create_progress_bar.return_value = "progress"
    mock_get_repo_features.return_value = {
        "restrict_edit_to_target_test_file_only": False,
        "allow_edit_any_file": True,
    }
    mock_get_stripe_id.return_value = "cus_existing"
    mock_get_remote_file.return_value = ("", "")
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 50,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_get_comments.return_value = ["Comment text"]
    mock_extract_image_urls.side_effect = [
        [{"url": "http://example.com/image.png", "alt": "image"}],
        [{"url": "http://example.com/comment.png", "alt": "comment img"}],
    ]
    mock_get_base64.return_value = "base64encodedimage"
    mock_describe_image.return_value = "Description of the image"
    mock_get_remote_file.return_value = ("", "")
    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
        completion_reason="",
        p=0,
        is_planned=False,
    )
    mock_get_pr_files.return_value = []

    await handle_new_pr(
        payload=_get_test_payload(),
        trigger="dashboard",
    )

    mock_extract_image_urls.assert_called()
    mock_get_base64.assert_called()
    mock_describe_image.assert_called()


@pytest.mark.asyncio
@patch("services.webhook.new_pr_handler.update_usage")
@patch("services.webhook.new_pr_handler.get_pull_request_files")
@patch("services.webhook.new_pr_handler.chat_with_agent")
@patch("services.webhook.new_pr_handler.create_empty_commit")
@patch("services.webhook.new_pr_handler.should_bail", return_value=False)
@patch("services.webhook.new_pr_handler.get_remote_file_content_by_url")
@patch("services.webhook.new_pr_handler.get_base64")
@patch("services.webhook.new_pr_handler.extract_image_urls")
@patch("services.webhook.new_pr_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.create_user_request")
@patch("services.webhook.new_pr_handler.get_stripe_customer_id")
@patch("services.webhook.new_pr_handler.get_repository_features")
@patch("services.webhook.new_pr_handler.slack_notify")
@patch("services.webhook.new_pr_handler.update_comment")
@patch("services.webhook.new_pr_handler.create_progress_bar")
@patch("services.webhook.new_pr_handler.create_comment")
@patch("services.webhook.new_pr_handler.render_text")
@patch("services.webhook.new_pr_handler.get_comments")
@patch("services.webhook.new_pr_handler.check_availability")
@patch("services.webhook.new_pr_handler.deconstruct_github_payload")
async def test_image_unsupported_format_skipped(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_create_comment,
    mock_create_progress_bar,
    mock_update_comment,
    mock_slack_notify,
    mock_get_repo_features,
    mock_get_stripe_id,
    mock_create_user_request,
    mock_ensure_node_packages,
    mock_git_clone_to_efs,
    mock_prepare_repo,
    mock_extract_image_urls,
    mock_get_base64,
    mock_get_remote_file,
    mock_should_bail,
    mock_create_empty_commit,
    mock_chat_with_agent,
    mock_get_pr_files,
    mock_update_usage,
):
    mock_deconstruct.return_value = (_get_base_args(), None)
    mock_render_text.return_value = "Rendered body"
    mock_slack_notify.return_value = "thread_1"
    mock_create_comment.return_value = "comment_url"
    mock_create_progress_bar.return_value = "progress"
    mock_get_repo_features.return_value = {
        "restrict_edit_to_target_test_file_only": False,
        "allow_edit_any_file": True,
    }
    mock_get_stripe_id.return_value = "cus_existing"
    mock_get_remote_file.return_value = ("", "")
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 50,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_get_comments.return_value = []
    mock_extract_image_urls.return_value = [
        {"url": "http://example.com/image.svg", "alt": "svg image"}
    ]
    mock_get_remote_file.return_value = ("", "")
    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
        completion_reason="",
        p=0,
        is_planned=False,
    )
    mock_get_pr_files.return_value = []

    await handle_new_pr(payload=_get_test_payload(), trigger="dashboard")

    mock_get_base64.assert_not_called()


@pytest.mark.asyncio
@patch("services.webhook.new_pr_handler.update_usage")
@patch("services.webhook.new_pr_handler.get_pull_request_files")
@patch("services.webhook.new_pr_handler.chat_with_agent")
@patch("services.webhook.new_pr_handler.create_empty_commit")
@patch("services.webhook.new_pr_handler.should_bail", return_value=False)
@patch("services.webhook.new_pr_handler.get_remote_file_content_by_url")
@patch("services.webhook.new_pr_handler.get_base64")
@patch("services.webhook.new_pr_handler.describe_image")
@patch("services.webhook.new_pr_handler.extract_image_urls")
@patch("services.webhook.new_pr_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.create_user_request")
@patch("services.webhook.new_pr_handler.get_stripe_customer_id")
@patch("services.webhook.new_pr_handler.get_repository_features")
@patch("services.webhook.new_pr_handler.slack_notify")
@patch("services.webhook.new_pr_handler.update_comment")
@patch("services.webhook.new_pr_handler.create_progress_bar")
@patch("services.webhook.new_pr_handler.create_comment")
@patch("services.webhook.new_pr_handler.render_text")
@patch("services.webhook.new_pr_handler.get_comments")
@patch("services.webhook.new_pr_handler.check_availability")
@patch("services.webhook.new_pr_handler.deconstruct_github_payload")
async def test_image_base64_fetch_failed(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_create_comment,
    mock_create_progress_bar,
    mock_update_comment,
    mock_slack_notify,
    mock_get_repo_features,
    mock_get_stripe_id,
    mock_create_user_request,
    mock_ensure_node_packages,
    mock_git_clone_to_efs,
    mock_prepare_repo,
    mock_extract_image_urls,
    mock_describe_image,
    mock_get_base64,
    mock_get_remote_file,
    mock_should_bail,
    mock_create_empty_commit,
    mock_chat_with_agent,
    mock_get_pr_files,
    mock_update_usage,
):
    mock_deconstruct.return_value = (_get_base_args(), None)
    mock_render_text.return_value = "Rendered body"
    mock_slack_notify.return_value = "thread_1"
    mock_create_comment.return_value = "comment_url"
    mock_create_progress_bar.return_value = "progress"
    mock_get_repo_features.return_value = {
        "restrict_edit_to_target_test_file_only": False,
        "allow_edit_any_file": True,
    }
    mock_get_stripe_id.return_value = "cus_existing"
    mock_get_remote_file.return_value = ("", "")
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 50,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_get_comments.return_value = []
    mock_extract_image_urls.return_value = [
        {"url": "http://example.com/image.png", "alt": "image"}
    ]
    mock_get_base64.return_value = None
    mock_get_remote_file.return_value = ("", "")
    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
        completion_reason="",
        p=0,
        is_planned=False,
    )
    mock_get_pr_files.return_value = []

    await handle_new_pr(payload=_get_test_payload(), trigger="dashboard")

    mock_get_base64.assert_called_once()
    mock_describe_image.assert_not_called()


@pytest.mark.asyncio
@patch(
    "services.webhook.new_pr_handler.read_local_file",
    return_value="def calculate():\n    return 1 + 2\n",
)
@patch("services.webhook.new_pr_handler.get_pull_request_files")
@patch("services.webhook.new_pr_handler.chat_with_agent")
@patch("services.webhook.new_pr_handler.create_empty_commit")
@patch("services.webhook.new_pr_handler.should_bail", return_value=True)
@patch("services.webhook.new_pr_handler.get_remote_file_content_by_url")
@patch("services.webhook.new_pr_handler.extract_image_urls")
@patch("services.webhook.new_pr_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.create_user_request")
@patch("services.webhook.new_pr_handler.get_stripe_customer_id")
@patch("services.webhook.new_pr_handler.get_repository_features")
@patch("services.webhook.new_pr_handler.slack_notify")
@patch("services.webhook.new_pr_handler.update_comment")
@patch("services.webhook.new_pr_handler.update_usage")
@patch("services.webhook.new_pr_handler.create_progress_bar")
@patch("services.webhook.new_pr_handler.create_comment")
@patch("services.webhook.new_pr_handler.render_text")
@patch("services.webhook.new_pr_handler.get_comments")
@patch("services.webhook.new_pr_handler.check_availability")
@patch("services.webhook.new_pr_handler.deconstruct_github_payload")
async def test_timeout_approaching_breaks_loop(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_create_comment,
    mock_create_progress_bar,
    mock_update_usage,
    mock_update_comment,
    mock_slack_notify,
    mock_get_repo_features,
    mock_get_stripe_id,
    mock_create_user_request,
    mock_ensure_node_packages,
    mock_git_clone_to_efs,
    mock_prepare_repo,
    mock_extract_image_urls,
    mock_get_remote_file,
    mock_should_bail,
    mock_create_empty_commit,
    mock_chat_with_agent,
    mock_get_pr_files,
    _mock_read_local_file,
):
    mock_deconstruct.return_value = (_get_base_args(), None)
    mock_render_text.return_value = "Rendered body"
    mock_slack_notify.return_value = "thread_1"
    mock_create_comment.return_value = "comment_url"
    mock_create_progress_bar.return_value = "progress"
    mock_get_repo_features.return_value = {
        "restrict_edit_to_target_test_file_only": False,
        "allow_edit_any_file": True,
    }
    mock_get_stripe_id.return_value = "cus_existing"
    mock_get_remote_file.return_value = ("", "")
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 50,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_get_comments.return_value = []
    mock_extract_image_urls.return_value = []
    mock_get_remote_file.return_value = ("", "")
    mock_get_pr_files.return_value = []

    await handle_new_pr(payload=_get_test_payload(), trigger="dashboard")

    mock_should_bail.assert_called_once()
    mock_chat_with_agent.assert_not_called()


@pytest.mark.asyncio
@patch(
    "services.webhook.new_pr_handler.read_local_file",
    return_value="def calculate():\n    return 1 + 2\n",
)
@patch("services.webhook.new_pr_handler.get_pull_request_files")
@patch("services.webhook.new_pr_handler.chat_with_agent")
@patch("services.webhook.new_pr_handler.create_empty_commit")
@patch("services.webhook.new_pr_handler.should_bail", return_value=True)
@patch("services.webhook.new_pr_handler.get_remote_file_content_by_url")
@patch("services.webhook.new_pr_handler.extract_image_urls")
@patch("services.webhook.new_pr_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.create_user_request")
@patch("services.webhook.new_pr_handler.get_stripe_customer_id")
@patch("services.webhook.new_pr_handler.get_repository_features")
@patch("services.webhook.new_pr_handler.slack_notify")
@patch("services.webhook.new_pr_handler.update_comment")
@patch("services.webhook.new_pr_handler.update_usage")
@patch("services.webhook.new_pr_handler.create_progress_bar")
@patch("services.webhook.new_pr_handler.create_comment")
@patch("services.webhook.new_pr_handler.render_text")
@patch("services.webhook.new_pr_handler.get_comments")
@patch("services.webhook.new_pr_handler.check_availability")
@patch("services.webhook.new_pr_handler.deconstruct_github_payload")
async def test_branch_deleted_breaks_loop(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_create_comment,
    mock_create_progress_bar,
    mock_update_usage,
    mock_update_comment,
    mock_slack_notify,
    mock_get_repo_features,
    mock_get_stripe_id,
    mock_create_user_request,
    mock_ensure_node_packages,
    mock_git_clone_to_efs,
    mock_prepare_repo,
    mock_extract_image_urls,
    mock_get_remote_file,
    mock_should_bail,
    mock_create_empty_commit,
    mock_chat_with_agent,
    mock_get_pr_files,
    _mock_read_local_file,
):
    mock_deconstruct.return_value = (_get_base_args(), None)
    mock_render_text.return_value = "Rendered body"
    mock_slack_notify.return_value = "thread_1"
    mock_create_comment.return_value = "comment_url"
    mock_create_progress_bar.return_value = "progress"
    mock_get_repo_features.return_value = {
        "restrict_edit_to_target_test_file_only": False,
        "allow_edit_any_file": True,
    }
    mock_get_stripe_id.return_value = "cus_existing"
    mock_get_remote_file.return_value = ("", "")
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 50,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_get_comments.return_value = []
    mock_extract_image_urls.return_value = []
    mock_get_remote_file.return_value = ("", "")
    mock_get_pr_files.return_value = []

    await handle_new_pr(payload=_get_test_payload(), trigger="dashboard")

    mock_should_bail.assert_called()
    mock_chat_with_agent.assert_not_called()


@pytest.mark.asyncio
@patch(
    "services.webhook.new_pr_handler.read_local_file",
    return_value="def calculate():\n    return 1 + 2\n",
)
@patch("services.webhook.new_pr_handler.MAX_ITERATIONS", 10)
@patch("services.webhook.new_pr_handler.verify_task_is_complete")
@patch("services.webhook.new_pr_handler.get_pull_request_files")
@patch("services.webhook.new_pr_handler.chat_with_agent")
@patch("services.webhook.new_pr_handler.create_empty_commit")
@patch("services.webhook.new_pr_handler.should_bail", return_value=False)
@patch("services.webhook.new_pr_handler.get_remote_file_content_by_url")
@patch("services.webhook.new_pr_handler.extract_image_urls")
@patch("services.webhook.new_pr_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.create_user_request")
@patch("services.webhook.new_pr_handler.get_stripe_customer_id")
@patch("services.webhook.new_pr_handler.get_repository_features")
@patch("services.webhook.new_pr_handler.slack_notify")
@patch("services.webhook.new_pr_handler.update_comment")
@patch("services.webhook.new_pr_handler.update_usage")
@patch("services.webhook.new_pr_handler.create_progress_bar")
@patch("services.webhook.new_pr_handler.create_comment")
@patch("services.webhook.new_pr_handler.render_text")
@patch("services.webhook.new_pr_handler.get_comments")
@patch("services.webhook.new_pr_handler.check_availability")
@patch("services.webhook.new_pr_handler.deconstruct_github_payload")
async def test_retry_loop_exhausted_not_explored_but_committed(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_create_comment,
    mock_create_progress_bar,
    mock_update_usage,
    mock_update_comment,
    mock_slack_notify,
    mock_get_repo_features,
    mock_get_stripe_id,
    mock_create_user_request,
    mock_ensure_node_packages,
    mock_git_clone_to_efs,
    mock_prepare_repo,
    mock_extract_image_urls,
    mock_get_remote_file,
    mock_should_bail,
    mock_create_empty_commit,
    mock_chat_with_agent,
    mock_get_pr_files,
    mock_verify_task_is_complete,
    _mock_read_local_file,
):
    mock_deconstruct.return_value = (_get_base_args(), None)
    mock_render_text.return_value = "Rendered body"
    mock_slack_notify.return_value = "thread_1"
    mock_create_comment.return_value = "comment_url"
    mock_create_progress_bar.return_value = "progress"
    mock_get_repo_features.return_value = {
        "restrict_edit_to_target_test_file_only": False,
        "allow_edit_any_file": True,
    }
    mock_get_stripe_id.return_value = "cus_existing"
    mock_get_remote_file.return_value = ("", "")
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 50,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_get_comments.return_value = []
    mock_extract_image_urls.return_value = []
    mock_get_remote_file.return_value = ("", "")
    mock_get_pr_files.return_value = []
    mock_chat_with_agent.side_effect = [
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=10,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=20,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=30,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=40,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=50,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=60,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=70,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=80,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=90,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=95,
            is_planned=False,
        ),
    ]
    mock_verify_task_is_complete.return_value = {
        "success": True,
        "message": "Task completed.",
    }

    await handle_new_pr(payload=_get_test_payload(), trigger="dashboard")

    assert mock_chat_with_agent.call_count == 10
    mock_verify_task_is_complete.assert_called_once()


@pytest.mark.asyncio
@patch(
    "services.webhook.new_pr_handler.read_local_file",
    return_value="def calculate():\n    return 1 + 2\n",
)
@patch("services.webhook.new_pr_handler.MAX_ITERATIONS", 9)
@patch("services.webhook.new_pr_handler.verify_task_is_complete")
@patch("services.webhook.new_pr_handler.get_pull_request_files")
@patch("services.webhook.new_pr_handler.chat_with_agent")
@patch("services.webhook.new_pr_handler.create_empty_commit")
@patch("services.webhook.new_pr_handler.should_bail", return_value=False)
@patch("services.webhook.new_pr_handler.get_remote_file_content_by_url")
@patch("services.webhook.new_pr_handler.extract_image_urls")
@patch("services.webhook.new_pr_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.create_user_request")
@patch("services.webhook.new_pr_handler.get_stripe_customer_id")
@patch("services.webhook.new_pr_handler.get_repository_features")
@patch("services.webhook.new_pr_handler.slack_notify")
@patch("services.webhook.new_pr_handler.update_comment")
@patch("services.webhook.new_pr_handler.update_usage")
@patch("services.webhook.new_pr_handler.create_progress_bar")
@patch("services.webhook.new_pr_handler.create_comment")
@patch("services.webhook.new_pr_handler.render_text")
@patch("services.webhook.new_pr_handler.get_comments")
@patch("services.webhook.new_pr_handler.check_availability")
@patch("services.webhook.new_pr_handler.deconstruct_github_payload")
async def test_retry_loop_exhausted_explored_but_not_committed(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_create_comment,
    mock_create_progress_bar,
    mock_update_usage,
    mock_update_comment,
    mock_slack_notify,
    mock_get_repo_features,
    mock_get_stripe_id,
    mock_create_user_request,
    mock_ensure_node_packages,
    mock_git_clone_to_efs,
    mock_prepare_repo,
    mock_extract_image_urls,
    mock_get_remote_file,
    mock_should_bail,
    mock_create_empty_commit,
    mock_chat_with_agent,
    mock_get_pr_files,
    mock_verify_task_is_complete,
    _mock_read_local_file,
):
    mock_deconstruct.return_value = (_get_base_args(), None)
    mock_render_text.return_value = "Rendered body"
    mock_slack_notify.return_value = "thread_1"
    mock_create_comment.return_value = "comment_url"
    mock_create_progress_bar.return_value = "progress"
    mock_get_repo_features.return_value = {
        "restrict_edit_to_target_test_file_only": False,
        "allow_edit_any_file": True,
    }
    mock_get_stripe_id.return_value = "cus_existing"
    mock_get_remote_file.return_value = ("", "")
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 50,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_get_comments.return_value = []
    mock_extract_image_urls.return_value = []
    mock_get_remote_file.return_value = ("", "")
    mock_get_pr_files.return_value = []
    mock_chat_with_agent.side_effect = [
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=10,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=20,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=30,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=40,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=50,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=60,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=70,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=80,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=90,
            is_planned=False,
        ),
    ]
    mock_verify_task_is_complete.return_value = {
        "success": True,
        "message": "Task completed.",
    }

    await handle_new_pr(payload=_get_test_payload(), trigger="dashboard")

    assert mock_chat_with_agent.call_count == 9
    mock_verify_task_is_complete.assert_called_once()


@pytest.mark.asyncio
@patch(
    "services.webhook.new_pr_handler.read_local_file",
    return_value="def calculate():\n    return 1 + 2\n",
)
@patch("services.webhook.new_pr_handler.get_pull_request_files")
@patch("services.webhook.new_pr_handler.chat_with_agent")
@patch("services.webhook.new_pr_handler.create_empty_commit")
@patch("services.webhook.new_pr_handler.should_bail", return_value=False)
@patch("services.webhook.new_pr_handler.get_remote_file_content_by_url")
@patch("services.webhook.new_pr_handler.extract_image_urls")
@patch("services.webhook.new_pr_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.create_user_request")
@patch("services.webhook.new_pr_handler.get_stripe_customer_id")
@patch("services.webhook.new_pr_handler.get_repository_features")
@patch("services.webhook.new_pr_handler.slack_notify")
@patch("services.webhook.new_pr_handler.update_comment")
@patch("services.webhook.new_pr_handler.update_usage")
@patch("services.webhook.new_pr_handler.create_progress_bar")
@patch("services.webhook.new_pr_handler.create_comment")
@patch("services.webhook.new_pr_handler.render_text")
@patch("services.webhook.new_pr_handler.get_comments")
@patch("services.webhook.new_pr_handler.check_availability")
@patch("services.webhook.new_pr_handler.deconstruct_github_payload")
async def test_retry_counter_reset_on_successful_loop(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_create_comment,
    mock_create_progress_bar,
    mock_update_usage,
    mock_update_comment,
    mock_slack_notify,
    mock_get_repo_features,
    mock_get_stripe_id,
    mock_create_user_request,
    mock_ensure_node_packages,
    mock_git_clone_to_efs,
    mock_prepare_repo,
    mock_extract_image_urls,
    mock_get_remote_file,
    mock_should_bail,
    mock_create_empty_commit,
    mock_chat_with_agent,
    mock_get_pr_files,
    _mock_read_local_file,
):
    mock_deconstruct.return_value = (_get_base_args(), None)
    mock_render_text.return_value = "Rendered body"
    mock_slack_notify.return_value = "thread_1"
    mock_create_comment.return_value = "comment_url"
    mock_create_progress_bar.return_value = "progress"
    mock_get_repo_features.return_value = {
        "restrict_edit_to_target_test_file_only": False,
        "allow_edit_any_file": True,
    }
    mock_get_stripe_id.return_value = "cus_existing"
    mock_get_remote_file.return_value = ("", "")
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 50,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_get_comments.return_value = []
    mock_extract_image_urls.return_value = []
    mock_get_remote_file.return_value = ("", "")
    mock_get_pr_files.return_value = []
    mock_chat_with_agent.side_effect = [
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=10,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            completion_reason="",
            p=20,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=True,
            completion_reason="",
            p=100,
            is_planned=False,
        ),
    ]

    await handle_new_pr(payload=_get_test_payload(), trigger="dashboard")

    assert mock_chat_with_agent.call_count == 3


@pytest.mark.asyncio
@patch(
    "services.webhook.new_pr_handler.read_local_file",
    return_value="def calculate():\n    return 1 + 2\n",
)
@patch("services.webhook.new_pr_handler.is_test_file")
@patch("services.webhook.new_pr_handler.get_pull_request_files")
@patch("services.webhook.new_pr_handler.chat_with_agent")
@patch("services.webhook.new_pr_handler.create_empty_commit")
@patch("services.webhook.new_pr_handler.should_bail", return_value=False)
@patch("services.webhook.new_pr_handler.get_remote_file_content_by_url")
@patch("services.webhook.new_pr_handler.extract_image_urls")
@patch("services.webhook.new_pr_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.create_user_request")
@patch("services.webhook.new_pr_handler.get_stripe_customer_id")
@patch("services.webhook.new_pr_handler.get_repository_features")
@patch("services.webhook.new_pr_handler.slack_notify")
@patch("services.webhook.new_pr_handler.update_comment")
@patch("services.webhook.new_pr_handler.update_usage")
@patch("services.webhook.new_pr_handler.create_progress_bar")
@patch("services.webhook.new_pr_handler.create_comment")
@patch("services.webhook.new_pr_handler.render_text")
@patch("services.webhook.new_pr_handler.get_comments")
@patch("services.webhook.new_pr_handler.check_availability")
@patch("services.webhook.new_pr_handler.deconstruct_github_payload")
async def test_non_test_file_skipped_in_header_merge(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_create_comment,
    mock_create_progress_bar,
    mock_update_usage,
    mock_update_comment,
    mock_slack_notify,
    mock_get_repo_features,
    mock_get_stripe_id,
    mock_create_user_request,
    mock_ensure_node_packages,
    mock_git_clone_to_efs,
    mock_prepare_repo,
    mock_extract_image_urls,
    mock_get_remote_file,
    mock_should_bail,
    mock_create_empty_commit,
    mock_chat_with_agent,
    mock_get_pr_files,
    mock_is_test_file,
    _mock_read_local_file,
):
    mock_deconstruct.return_value = (_get_base_args(), None)
    mock_render_text.return_value = "Rendered body"
    mock_slack_notify.return_value = "thread_1"
    mock_create_comment.return_value = "comment_url"
    mock_create_progress_bar.return_value = "progress"
    mock_get_repo_features.return_value = {
        "restrict_edit_to_target_test_file_only": False,
        "allow_edit_any_file": True,
    }
    mock_get_stripe_id.return_value = "cus_existing"
    mock_get_remote_file.return_value = ("", "")
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 50,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_get_comments.return_value = []
    mock_extract_image_urls.return_value = []
    mock_get_remote_file.return_value = ("", "")
    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
        completion_reason="",
        p=50,
        is_planned=False,
    )
    mock_get_pr_files.return_value = [{"filename": "src/main.py"}]
    mock_is_test_file.return_value = False

    await handle_new_pr(payload=_get_test_payload(), trigger="dashboard")

    mock_is_test_file.assert_called_with("src/main.py")


@pytest.mark.asyncio
@patch(
    "services.webhook.new_pr_handler.read_local_file",
    return_value="def calculate():\n    return 1 + 2\n",
)
@patch("services.webhook.new_pr_handler.replace_remote_file_content")
@patch("services.webhook.new_pr_handler.merge_test_file_headers")
@patch("services.webhook.new_pr_handler.get_raw_content")
@patch("services.webhook.new_pr_handler.is_test_file")
@patch("services.webhook.new_pr_handler.get_pull_request_files")
@patch("services.webhook.new_pr_handler.chat_with_agent")
@patch("services.webhook.new_pr_handler.create_empty_commit")
@patch("services.webhook.new_pr_handler.should_bail", return_value=False)
@patch("services.webhook.new_pr_handler.get_remote_file_content_by_url")
@patch("services.webhook.new_pr_handler.extract_image_urls")
@patch("services.webhook.new_pr_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.create_user_request")
@patch("services.webhook.new_pr_handler.get_stripe_customer_id")
@patch("services.webhook.new_pr_handler.get_repository_features")
@patch("services.webhook.new_pr_handler.slack_notify")
@patch("services.webhook.new_pr_handler.update_comment")
@patch("services.webhook.new_pr_handler.update_usage")
@patch("services.webhook.new_pr_handler.create_progress_bar")
@patch("services.webhook.new_pr_handler.create_comment")
@patch("services.webhook.new_pr_handler.render_text")
@patch("services.webhook.new_pr_handler.get_comments")
@patch("services.webhook.new_pr_handler.check_availability")
@patch("services.webhook.new_pr_handler.deconstruct_github_payload")
async def test_test_file_header_merge(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_create_comment,
    mock_create_progress_bar,
    mock_update_usage,
    mock_update_comment,
    mock_slack_notify,
    mock_get_repo_features,
    mock_get_stripe_id,
    mock_create_user_request,
    mock_ensure_node_packages,
    mock_git_clone_to_efs,
    mock_prepare_repo,
    mock_extract_image_urls,
    mock_get_remote_file,
    mock_should_bail,
    mock_create_empty_commit,
    mock_chat_with_agent,
    mock_get_pr_files,
    mock_is_test_file,
    mock_get_raw_content,
    mock_merge_headers,
    mock_replace_remote,
    _mock_read_local_file,
):
    mock_deconstruct.return_value = (_get_base_args(), None)
    mock_render_text.return_value = "Rendered body"
    mock_slack_notify.return_value = "thread_1"
    mock_create_comment.return_value = "comment_url"
    mock_create_progress_bar.return_value = "progress"
    mock_get_repo_features.return_value = {
        "restrict_edit_to_target_test_file_only": False,
        "allow_edit_any_file": True,
    }
    mock_get_stripe_id.return_value = "cus_existing"
    mock_get_remote_file.return_value = ("", "")
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 50,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_get_comments.return_value = []
    mock_extract_image_urls.return_value = []
    mock_get_remote_file.return_value = ("", "")
    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
        completion_reason="",
        p=50,
        is_planned=False,
    )
    mock_get_pr_files.return_value = [{"filename": "tests/test_example.py"}]
    mock_is_test_file.return_value = True
    mock_get_raw_content.return_value = "def test_something(): pass"
    mock_merge_headers.return_value = "import pytest\n\ndef test_something(): pass"

    await handle_new_pr(payload=_get_test_payload(), trigger="dashboard")

    mock_is_test_file.assert_called_with("tests/test_example.py")
    mock_get_raw_content.assert_called()
    mock_merge_headers.assert_called()
    mock_replace_remote.assert_called_once()


@pytest.mark.asyncio
@patch(
    "services.webhook.new_pr_handler.read_local_file",
    return_value="def calculate():\n    return 1 + 2\n",
)
@patch("services.webhook.new_pr_handler.replace_remote_file_content")
@patch("services.webhook.new_pr_handler.merge_test_file_headers")
@patch("services.webhook.new_pr_handler.get_raw_content")
@patch("services.webhook.new_pr_handler.is_test_file")
@patch("services.webhook.new_pr_handler.get_pull_request_files")
@patch("services.webhook.new_pr_handler.chat_with_agent")
@patch("services.webhook.new_pr_handler.create_empty_commit")
@patch("services.webhook.new_pr_handler.should_bail", return_value=False)
@patch("services.webhook.new_pr_handler.get_remote_file_content_by_url")
@patch("services.webhook.new_pr_handler.extract_image_urls")
@patch("services.webhook.new_pr_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.create_user_request")
@patch("services.webhook.new_pr_handler.get_stripe_customer_id")
@patch("services.webhook.new_pr_handler.get_repository_features")
@patch("services.webhook.new_pr_handler.slack_notify")
@patch("services.webhook.new_pr_handler.update_comment")
@patch("services.webhook.new_pr_handler.update_usage")
@patch("services.webhook.new_pr_handler.create_progress_bar")
@patch("services.webhook.new_pr_handler.create_comment")
@patch("services.webhook.new_pr_handler.render_text")
@patch("services.webhook.new_pr_handler.get_comments")
@patch("services.webhook.new_pr_handler.check_availability")
@patch("services.webhook.new_pr_handler.deconstruct_github_payload")
async def test_test_file_header_merge_no_content(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_create_comment,
    mock_create_progress_bar,
    mock_update_usage,
    mock_update_comment,
    mock_slack_notify,
    mock_get_repo_features,
    mock_get_stripe_id,
    mock_create_user_request,
    mock_ensure_node_packages,
    mock_git_clone_to_efs,
    mock_prepare_repo,
    mock_extract_image_urls,
    mock_get_remote_file,
    mock_should_bail,
    mock_create_empty_commit,
    mock_chat_with_agent,
    mock_get_pr_files,
    mock_is_test_file,
    mock_get_raw_content,
    mock_merge_headers,
    mock_replace_remote,
    _mock_read_local_file,
):
    mock_deconstruct.return_value = (_get_base_args(), None)
    mock_render_text.return_value = "Rendered body"
    mock_slack_notify.return_value = "thread_1"
    mock_create_comment.return_value = "comment_url"
    mock_create_progress_bar.return_value = "progress"
    mock_get_repo_features.return_value = {
        "restrict_edit_to_target_test_file_only": False,
        "allow_edit_any_file": True,
    }
    mock_get_stripe_id.return_value = "cus_existing"
    mock_get_remote_file.return_value = ("", "")
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 50,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_get_comments.return_value = []
    mock_extract_image_urls.return_value = []
    mock_get_remote_file.return_value = ("", "")
    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
        completion_reason="",
        p=50,
        is_planned=False,
    )
    mock_get_pr_files.return_value = [{"filename": "tests/test_example.py"}]
    mock_is_test_file.return_value = True
    mock_get_raw_content.return_value = None

    await handle_new_pr(payload=_get_test_payload(), trigger="dashboard")

    mock_is_test_file.assert_called()
    mock_get_raw_content.assert_called()
    mock_merge_headers.assert_not_called()
    mock_replace_remote.assert_not_called()


@pytest.mark.asyncio
@patch(
    "services.webhook.new_pr_handler.read_local_file",
    return_value="def calculate():\n    return 1 + 2\n",
)
@patch("services.webhook.new_pr_handler.replace_remote_file_content")
@patch("services.webhook.new_pr_handler.merge_test_file_headers")
@patch("services.webhook.new_pr_handler.get_raw_content")
@patch("services.webhook.new_pr_handler.is_test_file")
@patch("services.webhook.new_pr_handler.get_pull_request_files")
@patch("services.webhook.new_pr_handler.chat_with_agent")
@patch("services.webhook.new_pr_handler.create_empty_commit")
@patch("services.webhook.new_pr_handler.should_bail", return_value=False)
@patch("services.webhook.new_pr_handler.get_remote_file_content_by_url")
@patch("services.webhook.new_pr_handler.extract_image_urls")
@patch("services.webhook.new_pr_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.create_user_request")
@patch("services.webhook.new_pr_handler.get_stripe_customer_id")
@patch("services.webhook.new_pr_handler.get_repository_features")
@patch("services.webhook.new_pr_handler.slack_notify")
@patch("services.webhook.new_pr_handler.update_comment")
@patch("services.webhook.new_pr_handler.update_usage")
@patch("services.webhook.new_pr_handler.create_progress_bar")
@patch("services.webhook.new_pr_handler.create_comment")
@patch("services.webhook.new_pr_handler.render_text")
@patch("services.webhook.new_pr_handler.get_comments")
@patch("services.webhook.new_pr_handler.check_availability")
@patch("services.webhook.new_pr_handler.deconstruct_github_payload")
async def test_test_file_header_merge_no_change(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_create_comment,
    mock_create_progress_bar,
    mock_update_usage,
    mock_update_comment,
    mock_slack_notify,
    mock_get_repo_features,
    mock_get_stripe_id,
    mock_create_user_request,
    mock_ensure_node_packages,
    mock_git_clone_to_efs,
    mock_prepare_repo,
    mock_extract_image_urls,
    mock_get_remote_file,
    mock_should_bail,
    mock_create_empty_commit,
    mock_chat_with_agent,
    mock_get_pr_files,
    mock_is_test_file,
    mock_get_raw_content,
    mock_merge_headers,
    mock_replace_remote,
    _mock_read_local_file,
):
    mock_deconstruct.return_value = (_get_base_args(), None)
    mock_render_text.return_value = "Rendered body"
    mock_slack_notify.return_value = "thread_1"
    mock_create_comment.return_value = "comment_url"
    mock_create_progress_bar.return_value = "progress"
    mock_get_repo_features.return_value = {
        "restrict_edit_to_target_test_file_only": False,
        "allow_edit_any_file": True,
    }
    mock_get_stripe_id.return_value = "cus_existing"
    mock_get_remote_file.return_value = ("", "")
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 50,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_get_comments.return_value = []
    mock_extract_image_urls.return_value = []
    mock_get_remote_file.return_value = ("", "")
    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
        completion_reason="",
        p=50,
        is_planned=False,
    )
    mock_get_pr_files.return_value = [{"filename": "tests/test_example.py"}]
    mock_is_test_file.return_value = True
    mock_get_raw_content.return_value = "import pytest\n\ndef test_something(): pass"
    mock_merge_headers.return_value = "import pytest\n\ndef test_something(): pass"

    await handle_new_pr(payload=_get_test_payload(), trigger="dashboard")

    mock_is_test_file.assert_called()
    mock_get_raw_content.assert_called()
    mock_merge_headers.assert_called()
    mock_replace_remote.assert_not_called()


@patch("services.webhook.new_pr_handler.update_email_send")
@patch("services.webhook.new_pr_handler.insert_email_send", return_value=True)
@patch("services.webhook.new_pr_handler.send_email")
@pytest.mark.asyncio
@patch(
    "services.webhook.new_pr_handler.read_local_file",
    return_value="def calculate():\n    return 1 + 2\n",
)
@patch("services.webhook.new_pr_handler.get_credits_depleted_email_text")
@patch("services.webhook.new_pr_handler.get_user")
@patch("services.webhook.new_pr_handler.get_owner")
@patch("services.webhook.new_pr_handler.insert_credit")
@patch("services.webhook.new_pr_handler.get_pull_request_files")
@patch("services.webhook.new_pr_handler.chat_with_agent")
@patch("services.webhook.new_pr_handler.create_empty_commit")
@patch("services.webhook.new_pr_handler.should_bail", return_value=False)
@patch("services.webhook.new_pr_handler.get_remote_file_content_by_url")
@patch("services.webhook.new_pr_handler.extract_image_urls")
@patch("services.webhook.new_pr_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.create_user_request")
@patch("services.webhook.new_pr_handler.get_stripe_customer_id")
@patch("services.webhook.new_pr_handler.get_repository_features")
@patch("services.webhook.new_pr_handler.slack_notify")
@patch("services.webhook.new_pr_handler.update_comment")
@patch("services.webhook.new_pr_handler.update_usage")
@patch("services.webhook.new_pr_handler.create_progress_bar")
@patch("services.webhook.new_pr_handler.create_comment")
@patch("services.webhook.new_pr_handler.render_text")
@patch("services.webhook.new_pr_handler.get_comments")
@patch("services.webhook.new_pr_handler.check_availability")
@patch("services.webhook.new_pr_handler.deconstruct_github_payload")
async def test_credits_depleted_email_sent(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_create_comment,
    mock_create_progress_bar,
    mock_update_usage,
    mock_update_comment,
    mock_slack_notify,
    mock_get_repo_features,
    mock_get_stripe_id,
    mock_create_user_request,
    mock_ensure_node_packages,
    mock_git_clone_to_efs,
    mock_prepare_repo,
    mock_extract_image_urls,
    mock_get_remote_file,
    mock_should_bail,
    mock_create_empty_commit,
    mock_chat_with_agent,
    mock_get_pr_files,
    mock_insert_credit,
    mock_get_owner,
    mock_get_user,
    mock_get_email_text,
    _mock_read_local_file,
    mock_send_email,
    _mock_insert_email_send,
    _mock_update_email_send,
):
    mock_deconstruct.return_value = (_get_base_args(), None)
    mock_render_text.return_value = "Rendered body"
    mock_slack_notify.return_value = "thread_1"
    mock_create_comment.return_value = "comment_url"
    mock_create_progress_bar.return_value = "progress"
    mock_get_repo_features.return_value = {
        "restrict_edit_to_target_test_file_only": False,
        "allow_edit_any_file": True,
    }
    mock_get_stripe_id.return_value = "cus_existing"
    mock_get_remote_file.return_value = ("", "")
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 50,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_get_comments.return_value = []
    mock_extract_image_urls.return_value = []
    mock_get_remote_file.return_value = ("", "")
    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
        completion_reason="",
        p=50,
        is_planned=False,
    )
    mock_get_pr_files.return_value = [{"filename": "test.py", "status": "modified"}]
    mock_get_owner.return_value = {"id": 456, "credit_balance_usd": 0}
    mock_get_user.return_value = {"id": 888, "email": "user@example.com"}
    mock_get_email_text.return_value = ("Credits Depleted", "Your credits are gone")

    await handle_new_pr(payload=_get_test_payload(), trigger="dashboard")

    mock_insert_credit.assert_called_once()
    mock_get_owner.assert_called_with(owner_id=456)
    mock_get_user.assert_called_with(user_id=888)
    mock_get_email_text.assert_called_with("test_sender")
    mock_send_email.assert_called_once_with(
        to="user@example.com", subject="Credits Depleted", text="Your credits are gone"
    )


@pytest.mark.asyncio
@patch(
    "services.webhook.new_pr_handler.read_local_file",
    return_value="def calculate():\n    return 1 + 2\n",
)
@patch("services.webhook.new_pr_handler.insert_credit")
@patch("services.webhook.new_pr_handler.should_bail", return_value=False)
@patch("services.webhook.new_pr_handler.create_empty_commit")
@patch("services.webhook.new_pr_handler.get_remote_file_content_by_url")
@patch("services.webhook.new_pr_handler.get_comments")
@patch("services.webhook.new_pr_handler.slack_notify")
@patch("services.webhook.new_pr_handler.create_progress_bar")
@patch("services.webhook.new_pr_handler.update_usage")
@patch("services.webhook.new_pr_handler.chat_with_agent")
@patch("services.webhook.new_pr_handler.create_user_request")
@patch("services.webhook.new_pr_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.get_owner")
@patch("services.webhook.new_pr_handler.create_comment")
@patch("services.webhook.new_pr_handler.check_availability")
@patch("services.webhook.new_pr_handler.render_text")
@patch("services.webhook.new_pr_handler.deconstruct_github_payload")
@patch("services.webhook.new_pr_handler.get_pull_request_files")
async def test_new_pr_handler_token_accumulation(
    mock_get_pull_request_files,
    mock_deconstruct_github_payload,
    mock_render_text,
    mock_check_availability,
    mock_create_comment,
    mock_get_owner,
    mock_ensure_node_packages,
    mock_git_clone_to_efs,
    mock_prepare_repo,
    mock_create_user_request,
    mock_chat_with_agent,
    mock_update_usage,
    mock_create_progress_bar,
    mock_slack_notify,
    mock_get_comments,
    mock_get_remote_file_content_by_url,
    mock_create_empty_commit,
    mock_should_bail,
    mock_insert_credit,
    _mock_read_local_file,
):
    """Test that PR handler accumulates tokens correctly and calls update_usage"""
    mock_get_pull_request_files.return_value = []

    # Mock the payload deconstruction
    mock_deconstruct_github_payload.return_value = (
        {
            "installation_id": 123,
            "owner_id": 456,
            "owner_type": "User",
            "repo_id": 789,
            "pr_body": "Test PR body",
            "owner": "test_owner",
            "repo": "test_repo",
            "pr_number": 100,
            "pr_title": "Schedule: Add unit tests to services/test_file.py",
            "sender_name": "test_sender",
            "repo_full_name": "test_owner/test_repo",
            "pr_creator": "test_creator",
            "sender_id": 888,
            "token": "github_token_123",
            "new_branch": "gitauto/dashboard-20250101-120000-Ab1C",
            "sender_email": "test@example.com",
            "sender_display_name": "Test Sender",
            "github_urls": {
                "issues": "https://api.github.com/repos/test_owner/test_repo/issues",
                "pulls": "https://api.github.com/repos/test_owner/test_repo/pulls",
            },
            "clone_url": "https://github.com/test_owner/test_repo.git",
            "base_branch": "main",
        },
        None,
    )
    mock_render_text.return_value = "Rendered PR body"
    mock_slack_notify.return_value = "thread_123"
    mock_create_progress_bar.return_value = "Progress bar content"
    mock_get_comments.return_value = []
    mock_get_remote_file_content_by_url.return_value = ("", "")
    mock_create_empty_commit.return_value = None
    mock_insert_credit.return_value = None

    # Mock availability check to allow proceeding
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 50,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Proceeding with credit billing",
    }

    mock_create_comment.return_value = "https://api.github.com/repos/test/comment/123"
    mock_get_owner.return_value = {"id": 456, "credit_balance_usd": 100}
    mock_create_user_request.return_value = 999

    # Mock chat_with_agent - first call makes progress, second signals completion
    mock_chat_with_agent.side_effect = [
        AgentResult(
            messages=[
                {"role": "user", "content": "test"},
                {"role": "assistant", "content": "AI response"},
            ],
            token_input=75,
            token_output=35,
            is_completed=False,
            completion_reason="",
            p=90,
            is_planned=False,
        ),
        AgentResult(
            messages=[
                {"role": "user", "content": "test"},
                {"role": "assistant", "content": "AI response"},
            ],
            token_input=75,
            token_output=35,
            is_completed=True,
            completion_reason="",
            p=95,
            is_planned=False,
        ),
    ]
    mock_get_pull_request_files.return_value = [
        {"filename": "test.py", "status": "modified"}
    ]

    # Create test payload
    payload = cast(
        PrLabeledPayload,
        {
            "action": "labeled",
            "number": 100,
            "label": {"name": "gitauto"},
            "issue": {
                "number": 100,
                "title": "Schedule: Add unit tests to services/test_file.py",
                "body": "Test body",
            },
            "pull_request": {
                "html_url": "https://github.com/test_owner/test_repo/pull/100",
                "head": {"ref": "gitauto/dashboard-20250101-120000-Ab1C"},
            },
            "repository": {"name": "test_repo", "full_name": "test_owner/test_repo"},
            "sender": {"login": "test_sender"},
        },
    )

    # Call the function
    await handle_new_pr(
        payload=payload,
        trigger="dashboard",
        lambda_info={
            "log_group": "/aws/lambda/test",
            "log_stream": "test_stream",
            "request_id": "test_request_123",
        },
    )

    # Verify ensure_node_packages was called with base_args
    mock_ensure_node_packages.assert_called_once()

    # Verify update_usage was called with accumulated tokens
    mock_update_usage.assert_called_once()
    call_kwargs = mock_update_usage.call_args.kwargs

    assert call_kwargs["usage_id"] == 999
    # chat_with_agent is called twice (explore + commit), each returns 75/35 tokens
    assert call_kwargs["token_input"] == 150  # Two calls: 75 + 75
    assert call_kwargs["token_output"] == 70  # Two calls: 35 + 35


@pytest.mark.asyncio
@patch(
    "services.webhook.new_pr_handler.read_local_file",
    return_value="def calculate():\n    return 1 + 2\n",
)
@patch("services.webhook.new_pr_handler.insert_credit")
@patch("services.webhook.new_pr_handler.should_bail", return_value=False)
@patch("services.webhook.new_pr_handler.create_empty_commit")
@patch("services.webhook.new_pr_handler.get_remote_file_content_by_url")
@patch("services.webhook.new_pr_handler.get_comments")
@patch("services.webhook.new_pr_handler.slack_notify")
@patch("services.webhook.new_pr_handler.create_progress_bar")
@patch("services.webhook.new_pr_handler.update_usage")
@patch("services.webhook.new_pr_handler.update_comment")
@patch("services.webhook.new_pr_handler.get_repository_features")
@patch("services.webhook.new_pr_handler.chat_with_agent")
@patch("services.webhook.new_pr_handler.create_user_request")
@patch("services.webhook.new_pr_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.get_owner")
@patch("services.webhook.new_pr_handler.create_comment")
@patch("services.webhook.new_pr_handler.check_availability")
@patch("services.webhook.new_pr_handler.render_text")
@patch("services.webhook.new_pr_handler.deconstruct_github_payload")
async def test_restrict_edit_to_target_test_file_only_passed_to_chat_with_agent(
    mock_deconstruct_github_payload,
    mock_render_text,
    mock_check_availability,
    mock_create_comment,
    mock_get_owner,
    mock_ensure_node_packages,
    mock_git_clone_to_efs,
    mock_prepare_repo,
    mock_create_user_request,
    mock_chat_with_agent,
    mock_get_repository_features,
    mock_update_comment,
    mock_update_usage,
    mock_create_progress_bar,
    mock_slack_notify,
    mock_get_comments,
    mock_get_remote_file_content_by_url,
    mock_create_empty_commit,
    mock_should_bail,
    mock_insert_credit,
    _mock_read_local_file,
):
    mock_deconstruct_github_payload.return_value = (
        {
            "installation_id": 123,
            "owner_id": 456,
            "owner_type": "User",
            "repo_id": 789,
            "pr_body": "Test PR body",
            "owner": "test_owner",
            "repo": "test_repo",
            "pr_number": 100,
            "pr_title": "Schedule: Add unit tests to services/test_file.py",
            "sender_name": "test_sender",
            "repo_full_name": "test_owner/test_repo",
            "pr_creator": "test_creator",
            "sender_id": 888,
            "token": "github_token_123",
            "new_branch": "gitauto/dashboard-20250101-120000-Ab1C",
            "sender_email": "test@example.com",
            "sender_display_name": "Test Sender",
            "github_urls": {},
            "clone_url": "https://github.com/test_owner/test_repo.git",
            "base_branch": "main",
        },
        None,
    )
    mock_render_text.return_value = "Rendered PR body"
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 50,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Proceeding",
    }

    mock_render_text.return_value = "Rendered PR body"
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 50,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_create_comment.return_value = "https://api.github.com/comment/1"
    mock_get_owner.return_value = {"id": 456, "credit_balance_usd": 100}
    mock_create_user_request.return_value = 999
    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
        completion_reason="",
        p=0,
        is_planned=False,
    )
    mock_get_repository_features.return_value = {
        "restrict_edit_to_target_test_file_only": False,
        "allow_edit_any_file": True,
    }
    mock_update_comment.return_value = None
    mock_update_usage.return_value = None
    mock_create_progress_bar.return_value = "Progress: 0%"
    mock_slack_notify.return_value = "thread_1"
    mock_get_comments.return_value = []
    mock_get_remote_file_content_by_url.return_value = ("", "")
    mock_create_empty_commit.return_value = None
    mock_insert_credit.return_value = None

    payload = cast(
        PrLabeledPayload,
        {
            "action": "labeled",
            "number": 100,
            "label": {"name": "gitauto"},
            "issue": {
                "number": 100,
                "title": "Schedule: Add unit tests to services/test_file.py",
                "body": "Test body",
            },
            "pull_request": {
                "html_url": "https://github.com/test_owner/test_repo/pull/100",
                "head": {"ref": "gitauto/dashboard-20250101-120000-Ab1C"},
            },
            "repository": {"name": "test_repo", "full_name": "test_owner/test_repo"},
            "sender": {"login": "test_sender"},
        },
    )

    await handle_new_pr(
        payload=payload,
        trigger="dashboard",
    )

    call_kwargs = mock_chat_with_agent.call_args.kwargs
    assert call_kwargs["restrict_edit_to_target_test_file_only"] is False
    assert call_kwargs["allow_edit_any_file"] is True
    assert "system_message" in call_kwargs
    assert isinstance(call_kwargs["system_message"], str)

    # Verify baseline_tsc_errors is set on base_args
    base_args = call_kwargs["base_args"]
    assert "baseline_tsc_errors" in base_args
    assert isinstance(base_args["baseline_tsc_errors"], set)


@pytest.mark.asyncio
@patch("services.webhook.new_pr_handler.insert_credit")
@patch("services.webhook.new_pr_handler.should_bail", return_value=False)
@patch("services.webhook.new_pr_handler.create_empty_commit")
@patch("services.webhook.new_pr_handler.get_remote_file_content_by_url")
@patch("services.webhook.new_pr_handler.get_comments")
@patch("services.webhook.new_pr_handler.slack_notify")
@patch("services.webhook.new_pr_handler.create_progress_bar")
@patch("services.webhook.new_pr_handler.update_usage")
@patch("services.webhook.new_pr_handler.update_comment")
@patch("services.webhook.new_pr_handler.get_repository_features")
@patch("services.webhook.new_pr_handler.chat_with_agent")
@patch("services.webhook.new_pr_handler.create_user_request")
@patch("services.webhook.new_pr_handler.read_local_file")
@patch("services.webhook.new_pr_handler.find_test_files")
@patch("services.webhook.new_pr_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.get_owner")
@patch("services.webhook.new_pr_handler.create_comment")
@patch("services.webhook.new_pr_handler.check_availability")
@patch("services.webhook.new_pr_handler.render_text")
@patch("services.webhook.new_pr_handler.deconstruct_github_payload")
async def test_few_test_files_include_contents_in_prompt(
    mock_deconstruct_github_payload,
    mock_render_text,
    mock_check_availability,
    mock_create_comment,
    mock_get_owner,
    mock_ensure_node_packages,
    mock_git_clone_to_efs,
    mock_prepare_repo,
    mock_find_test_files,
    mock_read_local_file,
    mock_create_user_request,
    mock_chat_with_agent,
    mock_get_repository_features,
    mock_update_comment,
    mock_update_usage,
    mock_create_progress_bar,
    mock_slack_notify,
    mock_get_comments,
    mock_get_remote_file_content_by_url,
    mock_create_empty_commit,
    mock_should_bail,
    mock_insert_credit,
):
    mock_deconstruct_github_payload.return_value = (
        {
            "installation_id": 123,
            "owner_id": 456,
            "owner_type": "User",
            "repo_id": 789,
            "pr_body": "Test PR body",
            "owner": "test_owner",
            "repo": "test_repo",
            "pr_number": 100,
            "pr_title": "Schedule: Add unit tests to src/logger.ts",
            "sender_name": "test_sender",
            "repo_full_name": "test_owner/test_repo",
            "pr_creator": "test_creator",
            "sender_id": 888,
            "token": "github_token_123",
            "new_branch": "gitauto/dashboard-20250101-120000-Ab1C",
            "sender_email": "test@example.com",
            "sender_display_name": "Test Sender",
            "github_urls": {},
            "clone_url": "https://github.com/test_owner/test_repo.git",
            "base_branch": "main",
        },
        None,
    )
    mock_render_text.return_value = "Rendered PR body"
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 50,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_create_comment.return_value = "https://api.github.com/comment/1"
    mock_get_owner.return_value = {"id": 456, "credit_balance_usd": 100}
    mock_create_user_request.return_value = 999

    # Return 3 test files (<=5 threshold)
    mock_find_test_files.return_value = [
        "tests/test_logger.ts",
        "tests/logger.spec.ts",
        "tests/logger.test.ts",
    ]
    mock_read_local_file.return_value = (
        "function log(msg: string) { console.log(msg); }"
    )

    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
        completion_reason="",
        p=0,
        is_planned=False,
    )
    mock_get_repository_features.return_value = {
        "restrict_edit_to_target_test_file_only": False,
        "allow_edit_any_file": True,
    }
    mock_update_comment.return_value = None
    mock_update_usage.return_value = None
    mock_create_progress_bar.return_value = "Progress: 0%"
    mock_slack_notify.return_value = "thread_1"
    mock_get_comments.return_value = []
    mock_get_remote_file_content_by_url.return_value = ("", "")
    mock_create_empty_commit.return_value = None
    mock_insert_credit.return_value = None

    payload = cast(
        PrLabeledPayload,
        {
            "action": "labeled",
            "number": 100,
            "label": {"name": "gitauto"},
            "issue": {
                "number": 100,
                "title": "Schedule: Add unit tests to src/logger.ts",
                "body": "Test body",
            },
            "pull_request": {
                "html_url": "https://github.com/test_owner/test_repo/pull/100",
                "head": {"ref": "gitauto/dashboard-20250101-120000-Ab1C"},
            },
            "repository": {"name": "test_repo", "full_name": "test_owner/test_repo"},
            "sender": {"login": "test_sender"},
        },
    )

    await handle_new_pr(payload=payload, trigger="dashboard")

    # Verify test_files contents are included in the prompt (not just paths)
    call_kwargs = mock_chat_with_agent.call_args.kwargs
    messages = call_kwargs["messages"]
    user_input = json.loads(messages[0]["content"])
    assert "test_files" in user_input
    assert "test_file_paths" not in user_input
    assert len(user_input["test_files"]) == 3


@pytest.mark.asyncio
@patch("services.webhook.new_pr_handler.insert_credit")
@patch("services.webhook.new_pr_handler.should_bail", return_value=False)
@patch("services.webhook.new_pr_handler.create_empty_commit")
@patch("services.webhook.new_pr_handler.get_remote_file_content_by_url")
@patch("services.webhook.new_pr_handler.get_comments")
@patch("services.webhook.new_pr_handler.slack_notify")
@patch("services.webhook.new_pr_handler.create_progress_bar")
@patch("services.webhook.new_pr_handler.update_usage")
@patch("services.webhook.new_pr_handler.update_comment")
@patch("services.webhook.new_pr_handler.get_repository_features")
@patch("services.webhook.new_pr_handler.chat_with_agent")
@patch("services.webhook.new_pr_handler.create_user_request")
@patch("services.webhook.new_pr_handler.read_local_file")
@patch("services.webhook.new_pr_handler.find_test_files")
@patch("services.webhook.new_pr_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.new_pr_handler.get_owner")
@patch("services.webhook.new_pr_handler.create_comment")
@patch("services.webhook.new_pr_handler.check_availability")
@patch("services.webhook.new_pr_handler.render_text")
@patch("services.webhook.new_pr_handler.deconstruct_github_payload")
async def test_many_test_files_include_paths_only_in_prompt(
    mock_deconstruct_github_payload,
    mock_render_text,
    mock_check_availability,
    mock_create_comment,
    mock_get_owner,
    mock_ensure_node_packages,
    mock_git_clone_to_efs,
    mock_prepare_repo,
    mock_find_test_files,
    mock_read_local_file,
    mock_create_user_request,
    mock_chat_with_agent,
    mock_get_repository_features,
    mock_update_comment,
    mock_update_usage,
    mock_create_progress_bar,
    mock_slack_notify,
    mock_get_comments,
    mock_get_remote_file_content_by_url,
    mock_create_empty_commit,
    mock_should_bail,
    mock_insert_credit,
):
    mock_deconstruct_github_payload.return_value = (
        {
            "installation_id": 123,
            "owner_id": 456,
            "owner_type": "User",
            "repo_id": 789,
            "pr_body": "Test PR body",
            "owner": "test_owner",
            "repo": "test_repo",
            "pr_number": 100,
            "pr_title": "Schedule: Add unit tests to src/logger.ts",
            "sender_name": "test_sender",
            "repo_full_name": "test_owner/test_repo",
            "pr_creator": "test_creator",
            "sender_id": 888,
            "token": "github_token_123",
            "new_branch": "gitauto/dashboard-20250101-120000-Ab1C",
            "sender_email": "test@example.com",
            "sender_display_name": "Test Sender",
            "github_urls": {},
            "clone_url": "https://github.com/test_owner/test_repo.git",
            "base_branch": "main",
        },
        None,
    )
    mock_render_text.return_value = "Rendered PR body"
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 50,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_create_comment.return_value = "https://api.github.com/comment/1"
    mock_get_owner.return_value = {"id": 456, "credit_balance_usd": 100}
    mock_create_user_request.return_value = 999

    # Return 7 test files (>5 threshold)
    mock_find_test_files.return_value = [f"tests/test_logger_{i}.ts" for i in range(7)]
    mock_read_local_file.return_value = (
        "function log(msg: string) { console.log(msg); }"
    )

    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
        completion_reason="",
        p=0,
        is_planned=False,
    )
    mock_get_repository_features.return_value = {
        "restrict_edit_to_target_test_file_only": False,
        "allow_edit_any_file": True,
    }
    mock_update_comment.return_value = None
    mock_update_usage.return_value = None
    mock_create_progress_bar.return_value = "Progress: 0%"
    mock_slack_notify.return_value = "thread_1"
    mock_get_comments.return_value = []
    mock_get_remote_file_content_by_url.return_value = ("", "")
    mock_create_empty_commit.return_value = None
    mock_insert_credit.return_value = None

    payload = cast(
        PrLabeledPayload,
        {
            "action": "labeled",
            "number": 100,
            "label": {"name": "gitauto"},
            "issue": {
                "number": 100,
                "title": "Schedule: Add unit tests to src/logger.ts",
                "body": "Test body",
            },
            "pull_request": {
                "html_url": "https://github.com/test_owner/test_repo/pull/100",
                "head": {"ref": "gitauto/dashboard-20250101-120000-Ab1C"},
            },
            "repository": {"name": "test_repo", "full_name": "test_owner/test_repo"},
            "sender": {"login": "test_sender"},
        },
    )

    await handle_new_pr(payload=payload, trigger="dashboard")

    # Verify only paths are included (not contents) when >5 test files
    call_kwargs = mock_chat_with_agent.call_args.kwargs
    messages = call_kwargs["messages"]
    user_input = json.loads(messages[0]["content"])
    assert "test_file_paths" in user_input
    assert "test_files" not in user_input
    assert len(user_input["test_file_paths"]) == 7
    # Verify read_local_file was called only once (for impl file, not for test files)
    mock_read_local_file.assert_called_once()
