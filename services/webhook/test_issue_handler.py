# pylint: disable=unused-argument,too-many-lines
# pyright: reportUnusedVariable=false

import inspect
import json
from typing import cast
from unittest.mock import AsyncMock, patch

import pytest

from config import PRODUCT_ID
from services.chat_with_agent import AgentResult
from services.github.types.github_types import GitHubLabeledPayload
from services.webhook.issue_handler import create_pr_from_issue


@pytest.mark.asyncio
async def test_create_pr_from_issue_wrong_label_early_return():
    """Test early return when wrong label is provided"""
    payload_dict = {
        "action": "labeled",
        "label": {"name": "wrong-label"},  # Not "gitauto"
        "issue": {
            "number": 123,
            "title": "Schedule: Add unit tests to services/test_file.py",
        },
        "repository": {"name": "test_repo"},
    }
    payload = cast(GitHubLabeledPayload, payload_dict)

    lambda_info: dict[str, str | None] = {
        "log_group": "test",
        "log_stream": "test",
        "request_id": "test",
    }

    # Function should complete without errors (early return due to wrong label)
    await create_pr_from_issue(
        payload=payload,
        trigger="issue_label",
        lambda_info=lambda_info,
    )


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.create_user_request")
async def test_lambda_info_parameter_exists(mock_create_user_request):
    """Test that the create_pr_from_issue function accepts lambda_info parameter"""

    # This test just verifies the function signature accepts lambda_info
    # without actually running the complex function logic

    payload_dict = {
        "action": "labeled",
        "label": {"name": "wrong-label"},  # This will cause early return
        "issue": {
            "number": 123,
            "title": "Schedule: Add unit tests to services/test_file.py",
        },
        "repository": {"name": "test_repo"},
    }
    payload = cast(GitHubLabeledPayload, payload_dict)

    lambda_info: dict[str, str | None] = {
        "log_group": "/aws/lambda/pr-agent-prod",
        "log_stream": "2025/09/04/pr-agent-prod[$LATEST]841315c5",
        "request_id": "17921070-5cb6-43ee-8d2e-b5161ae89729",
    }

    # Test with lambda_info
    await create_pr_from_issue(
        payload=payload,
        trigger="issue_label",
        lambda_info=lambda_info,
    )

    # Test without lambda_info (should default to None)
    await create_pr_from_issue(payload=payload, trigger="issue_label")

    # Function calls completed without errors (early return due to wrong label)

    # create_user_request should not be called due to early return
    mock_create_user_request.assert_not_called()


def test_create_pr_from_issue_signature():
    """Test that create_pr_from_issue has the expected signature with lambda_info parameter"""

    sig = inspect.signature(create_pr_from_issue)
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
        "issue_body": "Test issue body",
        "owner": "test_owner",
        "repo": "test_repo",
        "issue_number": 100,
        "issue_title": "Schedule: Add unit tests to services/test_file.py",
        "sender_name": "test_sender",
        "repo_full_name": "test_owner/test_repo",
        "issuer_name": "test_issuer",
        "sender_id": 888,
        "token": "github_token_123",
        "new_branch": "gitauto/issue-100",
        "sender_email": "test@example.com",
        "github_urls": {
            "issues": "https://api.github.com/repos/test_owner/test_repo/issues",
            "pulls": "https://api.github.com/repos/test_owner/test_repo/pulls",
        },
        "is_automation": False,
        "clone_url": "https://github.com/test_owner/test_repo.git",
        "base_branch": "main",
    }


def _get_test_payload():
    return cast(
        GitHubLabeledPayload,
        {
            "action": "labeled",
            "label": {"name": PRODUCT_ID},
            "issue": {
                "number": 100,
                "title": "Schedule: Add unit tests to services/test_file.py",
                "body": "Test body",
            },
            "repository": {"name": "test_repo", "full_name": "test_owner/test_repo"},
            "sender": {"login": "test_sender"},
        },
    )


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.get_stripe_customer_id")
@patch("services.webhook.issue_handler.get_repository_features")
@patch("services.webhook.issue_handler.slack_notify")
@patch("services.webhook.issue_handler.update_comment")
@patch("services.webhook.issue_handler.create_progress_bar")
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.add_reaction_to_issue")
@patch("services.webhook.issue_handler.delete_comments_by_identifiers")
@patch("services.webhook.issue_handler.render_text")
@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_can_proceed_false_early_return(
    mock_deconstruct,
    mock_check_availability,
    mock_render_text,
    mock_delete_comments,
    mock_add_reaction,
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

    await create_pr_from_issue(
        payload=_get_test_payload(),
        trigger="issue_label",
    )

    mock_update_comment.assert_called()
    assert mock_slack_notify.call_count == 2

    # Verify get_repository_features was called with owner_id and repo_id
    mock_get_repo_features.assert_called_once_with(owner_id=456, repo_id=789)


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.update_stripe_customer_id")
@patch("services.webhook.issue_handler.create_stripe_customer")
@patch("services.webhook.issue_handler.get_stripe_customer_id")
@patch("services.webhook.issue_handler.get_repository_features")
@patch("services.webhook.issue_handler.slack_notify")
@patch("services.webhook.issue_handler.update_comment")
@patch("services.webhook.issue_handler.create_progress_bar")
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.add_reaction_to_issue")
@patch("services.webhook.issue_handler.delete_comments_by_identifiers")
@patch("services.webhook.issue_handler.render_text")
@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_stripe_customer_id_update(
    mock_deconstruct,
    mock_check_availability,
    mock_render_text,
    mock_delete_comments,
    mock_add_reaction,
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

    await create_pr_from_issue(
        payload=_get_test_payload(),
        trigger="issue_label",
    )

    mock_update_stripe.assert_called_once_with(456, "cus_new123")


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.update_usage")
@patch("services.webhook.issue_handler.get_pull_request_files")
@patch("services.webhook.issue_handler.chat_with_agent")
@patch("services.webhook.issue_handler.create_pull_request")
@patch("services.webhook.issue_handler.create_empty_commit")
@patch("services.webhook.issue_handler.create_remote_branch")
@patch("services.webhook.issue_handler.get_latest_remote_commit_sha")
@patch("services.webhook.issue_handler.should_bail", return_value=False)
@patch("services.webhook.issue_handler.get_remote_file_content_by_url")
@patch("services.webhook.issue_handler.get_base64")
@patch("services.webhook.issue_handler.describe_image")
@patch("services.webhook.issue_handler.extract_image_urls")
@patch("services.webhook.issue_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.create_user_request")
@patch("services.webhook.issue_handler.get_stripe_customer_id")
@patch("services.webhook.issue_handler.get_repository_features")
@patch("services.webhook.issue_handler.slack_notify")
@patch("services.webhook.issue_handler.update_comment")
@patch("services.webhook.issue_handler.create_progress_bar")
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.add_reaction_to_issue")
@patch("services.webhook.issue_handler.delete_comments_by_identifiers")
@patch("services.webhook.issue_handler.render_text")
@patch("services.webhook.issue_handler.get_comments")
@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_image_urls_processing(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_delete_comments,
    mock_add_reaction,
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
    mock_get_latest_sha,
    mock_create_remote_branch,
    mock_create_empty_commit,
    mock_create_pr,
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
    mock_get_latest_sha.return_value = "abc123"
    mock_create_pr.return_value = ("https://github.com/test/repo/pull/1", 1)
    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
        p=0,
        is_planned=False,
    )
    mock_get_pr_files.return_value = []

    await create_pr_from_issue(
        payload=_get_test_payload(),
        trigger="issue_label",
    )

    mock_extract_image_urls.assert_called()
    mock_get_base64.assert_called()
    mock_describe_image.assert_called()


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.update_usage")
@patch("services.webhook.issue_handler.get_pull_request_files")
@patch("services.webhook.issue_handler.chat_with_agent")
@patch("services.webhook.issue_handler.create_pull_request")
@patch("services.webhook.issue_handler.create_empty_commit")
@patch("services.webhook.issue_handler.create_remote_branch")
@patch("services.webhook.issue_handler.get_latest_remote_commit_sha")
@patch("services.webhook.issue_handler.should_bail", return_value=False)
@patch("services.webhook.issue_handler.get_remote_file_content_by_url")
@patch("services.webhook.issue_handler.get_base64")
@patch("services.webhook.issue_handler.extract_image_urls")
@patch("services.webhook.issue_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.create_user_request")
@patch("services.webhook.issue_handler.get_stripe_customer_id")
@patch("services.webhook.issue_handler.get_repository_features")
@patch("services.webhook.issue_handler.slack_notify")
@patch("services.webhook.issue_handler.update_comment")
@patch("services.webhook.issue_handler.create_progress_bar")
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.add_reaction_to_issue")
@patch("services.webhook.issue_handler.delete_comments_by_identifiers")
@patch("services.webhook.issue_handler.render_text")
@patch("services.webhook.issue_handler.get_comments")
@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_image_unsupported_format_skipped(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_delete_comments,
    mock_add_reaction,
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
    mock_get_latest_sha,
    mock_create_remote_branch,
    mock_create_empty_commit,
    mock_create_pr,
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
    mock_get_latest_sha.return_value = "abc123"
    mock_create_pr.return_value = ("https://github.com/test/repo/pull/1", 1)
    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
        p=0,
        is_planned=False,
    )
    mock_get_pr_files.return_value = []

    await create_pr_from_issue(payload=_get_test_payload(), trigger="issue_label")

    mock_get_base64.assert_not_called()


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.update_usage")
@patch("services.webhook.issue_handler.get_pull_request_files")
@patch("services.webhook.issue_handler.chat_with_agent")
@patch("services.webhook.issue_handler.create_pull_request")
@patch("services.webhook.issue_handler.create_empty_commit")
@patch("services.webhook.issue_handler.create_remote_branch")
@patch("services.webhook.issue_handler.get_latest_remote_commit_sha")
@patch("services.webhook.issue_handler.should_bail", return_value=False)
@patch("services.webhook.issue_handler.get_remote_file_content_by_url")
@patch("services.webhook.issue_handler.get_base64")
@patch("services.webhook.issue_handler.describe_image")
@patch("services.webhook.issue_handler.extract_image_urls")
@patch("services.webhook.issue_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.create_user_request")
@patch("services.webhook.issue_handler.get_stripe_customer_id")
@patch("services.webhook.issue_handler.get_repository_features")
@patch("services.webhook.issue_handler.slack_notify")
@patch("services.webhook.issue_handler.update_comment")
@patch("services.webhook.issue_handler.create_progress_bar")
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.add_reaction_to_issue")
@patch("services.webhook.issue_handler.delete_comments_by_identifiers")
@patch("services.webhook.issue_handler.render_text")
@patch("services.webhook.issue_handler.get_comments")
@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_image_base64_fetch_failed(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_delete_comments,
    mock_add_reaction,
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
    mock_get_latest_sha,
    mock_create_remote_branch,
    mock_create_empty_commit,
    mock_create_pr,
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
    mock_get_latest_sha.return_value = "abc123"
    mock_create_pr.return_value = ("https://github.com/test/repo/pull/1", 1)
    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
        p=0,
        is_planned=False,
    )
    mock_get_pr_files.return_value = []

    await create_pr_from_issue(payload=_get_test_payload(), trigger="issue_label")

    mock_get_base64.assert_called_once()
    mock_describe_image.assert_not_called()


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.get_pull_request_files")
@patch("services.webhook.issue_handler.chat_with_agent")
@patch("services.webhook.issue_handler.create_pull_request")
@patch("services.webhook.issue_handler.create_empty_commit")
@patch("services.webhook.issue_handler.create_remote_branch")
@patch("services.webhook.issue_handler.get_latest_remote_commit_sha")
@patch("services.webhook.issue_handler.should_bail", return_value=True)
@patch("services.webhook.issue_handler.get_remote_file_content_by_url")
@patch("services.webhook.issue_handler.extract_image_urls")
@patch("services.webhook.issue_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.create_user_request")
@patch("services.webhook.issue_handler.get_stripe_customer_id")
@patch("services.webhook.issue_handler.get_repository_features")
@patch("services.webhook.issue_handler.slack_notify")
@patch("services.webhook.issue_handler.update_comment")
@patch("services.webhook.issue_handler.update_usage")
@patch("services.webhook.issue_handler.create_progress_bar")
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.add_reaction_to_issue")
@patch("services.webhook.issue_handler.delete_comments_by_identifiers")
@patch("services.webhook.issue_handler.render_text")
@patch("services.webhook.issue_handler.get_comments")
@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_timeout_approaching_breaks_loop(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_delete_comments,
    mock_add_reaction,
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
    mock_get_latest_sha,
    mock_create_remote_branch,
    mock_create_empty_commit,
    mock_create_pr,
    mock_chat_with_agent,
    mock_get_pr_files,
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
    mock_get_latest_sha.return_value = "abc123"
    mock_create_pr.return_value = ("https://github.com/test/repo/pull/1", 1)
    mock_get_pr_files.return_value = []

    await create_pr_from_issue(payload=_get_test_payload(), trigger="issue_label")

    mock_should_bail.assert_called_once()
    mock_chat_with_agent.assert_not_called()


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.get_pull_request_files")
@patch("services.webhook.issue_handler.chat_with_agent")
@patch("services.webhook.issue_handler.create_pull_request")
@patch("services.webhook.issue_handler.create_empty_commit")
@patch("services.webhook.issue_handler.create_remote_branch")
@patch("services.webhook.issue_handler.get_latest_remote_commit_sha")
@patch("services.webhook.issue_handler.should_bail", return_value=True)
@patch("services.webhook.issue_handler.get_remote_file_content_by_url")
@patch("services.webhook.issue_handler.extract_image_urls")
@patch("services.webhook.issue_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.create_user_request")
@patch("services.webhook.issue_handler.get_stripe_customer_id")
@patch("services.webhook.issue_handler.get_repository_features")
@patch("services.webhook.issue_handler.slack_notify")
@patch("services.webhook.issue_handler.update_comment")
@patch("services.webhook.issue_handler.update_usage")
@patch("services.webhook.issue_handler.create_progress_bar")
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.add_reaction_to_issue")
@patch("services.webhook.issue_handler.delete_comments_by_identifiers")
@patch("services.webhook.issue_handler.render_text")
@patch("services.webhook.issue_handler.get_comments")
@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_branch_deleted_breaks_loop(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_delete_comments,
    mock_add_reaction,
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
    mock_get_latest_sha,
    mock_create_remote_branch,
    mock_create_empty_commit,
    mock_create_pr,
    mock_chat_with_agent,
    mock_get_pr_files,
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
    mock_get_latest_sha.return_value = "abc123"
    mock_create_pr.return_value = ("https://github.com/test/repo/pull/1", 1)
    mock_get_pr_files.return_value = []

    await create_pr_from_issue(payload=_get_test_payload(), trigger="issue_label")

    mock_should_bail.assert_called()
    mock_chat_with_agent.assert_not_called()


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.MAX_ITERATIONS", 10)
@patch("services.webhook.issue_handler.verify_task_is_complete")
@patch("services.webhook.issue_handler.get_pull_request_files")
@patch("services.webhook.issue_handler.chat_with_agent")
@patch("services.webhook.issue_handler.create_pull_request")
@patch("services.webhook.issue_handler.create_empty_commit")
@patch("services.webhook.issue_handler.create_remote_branch")
@patch("services.webhook.issue_handler.get_latest_remote_commit_sha")
@patch("services.webhook.issue_handler.should_bail", return_value=False)
@patch("services.webhook.issue_handler.get_remote_file_content_by_url")
@patch("services.webhook.issue_handler.extract_image_urls")
@patch("services.webhook.issue_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.create_user_request")
@patch("services.webhook.issue_handler.get_stripe_customer_id")
@patch("services.webhook.issue_handler.get_repository_features")
@patch("services.webhook.issue_handler.slack_notify")
@patch("services.webhook.issue_handler.update_comment")
@patch("services.webhook.issue_handler.update_usage")
@patch("services.webhook.issue_handler.create_progress_bar")
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.add_reaction_to_issue")
@patch("services.webhook.issue_handler.delete_comments_by_identifiers")
@patch("services.webhook.issue_handler.render_text")
@patch("services.webhook.issue_handler.get_comments")
@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_retry_loop_exhausted_not_explored_but_committed(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_delete_comments,
    mock_add_reaction,
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
    mock_get_latest_sha,
    mock_create_remote_branch,
    mock_create_empty_commit,
    mock_create_pr,
    mock_chat_with_agent,
    mock_get_pr_files,
    mock_verify_task_is_complete,
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
    mock_get_latest_sha.return_value = "abc123"
    mock_create_pr.return_value = ("https://github.com/test/repo/pull/1", 1)
    mock_get_pr_files.return_value = []
    mock_chat_with_agent.side_effect = [
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=10,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=20,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=30,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=40,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=50,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=60,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=70,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=80,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=90,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=95,
            is_planned=False,
        ),
    ]
    mock_verify_task_is_complete.return_value = {
        "success": True,
        "message": "Task completed.",
    }

    await create_pr_from_issue(payload=_get_test_payload(), trigger="issue_label")

    assert mock_chat_with_agent.call_count == 10
    mock_verify_task_is_complete.assert_called_once()


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.MAX_ITERATIONS", 9)
@patch("services.webhook.issue_handler.verify_task_is_complete")
@patch("services.webhook.issue_handler.get_pull_request_files")
@patch("services.webhook.issue_handler.chat_with_agent")
@patch("services.webhook.issue_handler.create_pull_request")
@patch("services.webhook.issue_handler.create_empty_commit")
@patch("services.webhook.issue_handler.create_remote_branch")
@patch("services.webhook.issue_handler.get_latest_remote_commit_sha")
@patch("services.webhook.issue_handler.should_bail", return_value=False)
@patch("services.webhook.issue_handler.get_remote_file_content_by_url")
@patch("services.webhook.issue_handler.extract_image_urls")
@patch("services.webhook.issue_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.create_user_request")
@patch("services.webhook.issue_handler.get_stripe_customer_id")
@patch("services.webhook.issue_handler.get_repository_features")
@patch("services.webhook.issue_handler.slack_notify")
@patch("services.webhook.issue_handler.update_comment")
@patch("services.webhook.issue_handler.update_usage")
@patch("services.webhook.issue_handler.create_progress_bar")
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.add_reaction_to_issue")
@patch("services.webhook.issue_handler.delete_comments_by_identifiers")
@patch("services.webhook.issue_handler.render_text")
@patch("services.webhook.issue_handler.get_comments")
@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_retry_loop_exhausted_explored_but_not_committed(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_delete_comments,
    mock_add_reaction,
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
    mock_get_latest_sha,
    mock_create_remote_branch,
    mock_create_empty_commit,
    mock_create_pr,
    mock_chat_with_agent,
    mock_get_pr_files,
    mock_verify_task_is_complete,
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
    mock_get_latest_sha.return_value = "abc123"
    mock_create_pr.return_value = ("https://github.com/test/repo/pull/1", 1)
    mock_get_pr_files.return_value = []
    mock_chat_with_agent.side_effect = [
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=10,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=20,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=30,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=40,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=50,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=60,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=70,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=80,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=90,
            is_planned=False,
        ),
    ]
    mock_verify_task_is_complete.return_value = {
        "success": True,
        "message": "Task completed.",
    }

    await create_pr_from_issue(payload=_get_test_payload(), trigger="issue_label")

    assert mock_chat_with_agent.call_count == 9
    mock_verify_task_is_complete.assert_called_once()


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.get_pull_request_files")
@patch("services.webhook.issue_handler.chat_with_agent")
@patch("services.webhook.issue_handler.create_pull_request")
@patch("services.webhook.issue_handler.create_empty_commit")
@patch("services.webhook.issue_handler.create_remote_branch")
@patch("services.webhook.issue_handler.get_latest_remote_commit_sha")
@patch("services.webhook.issue_handler.should_bail", return_value=False)
@patch("services.webhook.issue_handler.get_remote_file_content_by_url")
@patch("services.webhook.issue_handler.extract_image_urls")
@patch("services.webhook.issue_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.create_user_request")
@patch("services.webhook.issue_handler.get_stripe_customer_id")
@patch("services.webhook.issue_handler.get_repository_features")
@patch("services.webhook.issue_handler.slack_notify")
@patch("services.webhook.issue_handler.update_comment")
@patch("services.webhook.issue_handler.update_usage")
@patch("services.webhook.issue_handler.create_progress_bar")
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.add_reaction_to_issue")
@patch("services.webhook.issue_handler.delete_comments_by_identifiers")
@patch("services.webhook.issue_handler.render_text")
@patch("services.webhook.issue_handler.get_comments")
@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_retry_counter_reset_on_successful_loop(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_delete_comments,
    mock_add_reaction,
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
    mock_get_latest_sha,
    mock_create_remote_branch,
    mock_create_empty_commit,
    mock_create_pr,
    mock_chat_with_agent,
    mock_get_pr_files,
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
    mock_get_latest_sha.return_value = "abc123"
    mock_create_pr.return_value = ("https://github.com/test/repo/pull/1", 1)
    mock_get_pr_files.return_value = []
    mock_chat_with_agent.side_effect = [
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=10,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=False,
            p=20,
            is_planned=False,
        ),
        AgentResult(
            messages=[],
            token_input=10,
            token_output=5,
            is_completed=True,
            p=100,
            is_planned=False,
        ),
    ]

    await create_pr_from_issue(payload=_get_test_payload(), trigger="issue_label")

    assert mock_chat_with_agent.call_count == 3


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.is_test_file")
@patch("services.webhook.issue_handler.get_pull_request_files")
@patch("services.webhook.issue_handler.chat_with_agent")
@patch("services.webhook.issue_handler.create_pull_request")
@patch("services.webhook.issue_handler.create_empty_commit")
@patch("services.webhook.issue_handler.create_remote_branch")
@patch("services.webhook.issue_handler.get_latest_remote_commit_sha")
@patch("services.webhook.issue_handler.should_bail", return_value=False)
@patch("services.webhook.issue_handler.get_remote_file_content_by_url")
@patch("services.webhook.issue_handler.extract_image_urls")
@patch("services.webhook.issue_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.create_user_request")
@patch("services.webhook.issue_handler.get_stripe_customer_id")
@patch("services.webhook.issue_handler.get_repository_features")
@patch("services.webhook.issue_handler.slack_notify")
@patch("services.webhook.issue_handler.update_comment")
@patch("services.webhook.issue_handler.update_usage")
@patch("services.webhook.issue_handler.create_progress_bar")
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.add_reaction_to_issue")
@patch("services.webhook.issue_handler.delete_comments_by_identifiers")
@patch("services.webhook.issue_handler.render_text")
@patch("services.webhook.issue_handler.get_comments")
@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_non_test_file_skipped_in_header_merge(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_delete_comments,
    mock_add_reaction,
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
    mock_get_latest_sha,
    mock_create_remote_branch,
    mock_create_empty_commit,
    mock_create_pr,
    mock_chat_with_agent,
    mock_get_pr_files,
    mock_is_test_file,
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
    mock_get_latest_sha.return_value = "abc123"
    mock_create_pr.return_value = ("https://github.com/test/repo/pull/1", 1)
    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
        p=50,
        is_planned=False,
    )
    mock_get_pr_files.return_value = [{"filename": "src/main.py"}]
    mock_is_test_file.return_value = False

    await create_pr_from_issue(payload=_get_test_payload(), trigger="issue_label")

    mock_is_test_file.assert_called_with("src/main.py")


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.replace_remote_file_content")
@patch("services.webhook.issue_handler.merge_test_file_headers")
@patch("services.webhook.issue_handler.get_raw_content")
@patch("services.webhook.issue_handler.is_test_file")
@patch("services.webhook.issue_handler.get_pull_request_files")
@patch("services.webhook.issue_handler.chat_with_agent")
@patch("services.webhook.issue_handler.create_pull_request")
@patch("services.webhook.issue_handler.create_empty_commit")
@patch("services.webhook.issue_handler.create_remote_branch")
@patch("services.webhook.issue_handler.get_latest_remote_commit_sha")
@patch("services.webhook.issue_handler.should_bail", return_value=False)
@patch("services.webhook.issue_handler.get_remote_file_content_by_url")
@patch("services.webhook.issue_handler.extract_image_urls")
@patch("services.webhook.issue_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.create_user_request")
@patch("services.webhook.issue_handler.get_stripe_customer_id")
@patch("services.webhook.issue_handler.get_repository_features")
@patch("services.webhook.issue_handler.slack_notify")
@patch("services.webhook.issue_handler.update_comment")
@patch("services.webhook.issue_handler.update_usage")
@patch("services.webhook.issue_handler.create_progress_bar")
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.add_reaction_to_issue")
@patch("services.webhook.issue_handler.delete_comments_by_identifiers")
@patch("services.webhook.issue_handler.render_text")
@patch("services.webhook.issue_handler.get_comments")
@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_test_file_header_merge(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_delete_comments,
    mock_add_reaction,
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
    mock_get_latest_sha,
    mock_create_remote_branch,
    mock_create_empty_commit,
    mock_create_pr,
    mock_chat_with_agent,
    mock_get_pr_files,
    mock_is_test_file,
    mock_get_raw_content,
    mock_merge_headers,
    mock_replace_remote,
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
    mock_get_latest_sha.return_value = "abc123"
    mock_create_pr.return_value = ("https://github.com/test/repo/pull/1", 1)
    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
        p=50,
        is_planned=False,
    )
    mock_get_pr_files.return_value = [{"filename": "tests/test_example.py"}]
    mock_is_test_file.return_value = True
    mock_get_raw_content.return_value = "def test_something(): pass"
    mock_merge_headers.return_value = "import pytest\n\ndef test_something(): pass"

    await create_pr_from_issue(payload=_get_test_payload(), trigger="issue_label")

    mock_is_test_file.assert_called_with("tests/test_example.py")
    mock_get_raw_content.assert_called()
    mock_merge_headers.assert_called()
    mock_replace_remote.assert_called_once()


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.replace_remote_file_content")
@patch("services.webhook.issue_handler.merge_test_file_headers")
@patch("services.webhook.issue_handler.get_raw_content")
@patch("services.webhook.issue_handler.is_test_file")
@patch("services.webhook.issue_handler.get_pull_request_files")
@patch("services.webhook.issue_handler.chat_with_agent")
@patch("services.webhook.issue_handler.create_pull_request")
@patch("services.webhook.issue_handler.create_empty_commit")
@patch("services.webhook.issue_handler.create_remote_branch")
@patch("services.webhook.issue_handler.get_latest_remote_commit_sha")
@patch("services.webhook.issue_handler.should_bail", return_value=False)
@patch("services.webhook.issue_handler.get_remote_file_content_by_url")
@patch("services.webhook.issue_handler.extract_image_urls")
@patch("services.webhook.issue_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.create_user_request")
@patch("services.webhook.issue_handler.get_stripe_customer_id")
@patch("services.webhook.issue_handler.get_repository_features")
@patch("services.webhook.issue_handler.slack_notify")
@patch("services.webhook.issue_handler.update_comment")
@patch("services.webhook.issue_handler.update_usage")
@patch("services.webhook.issue_handler.create_progress_bar")
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.add_reaction_to_issue")
@patch("services.webhook.issue_handler.delete_comments_by_identifiers")
@patch("services.webhook.issue_handler.render_text")
@patch("services.webhook.issue_handler.get_comments")
@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_test_file_header_merge_no_content(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_delete_comments,
    mock_add_reaction,
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
    mock_get_latest_sha,
    mock_create_remote_branch,
    mock_create_empty_commit,
    mock_create_pr,
    mock_chat_with_agent,
    mock_get_pr_files,
    mock_is_test_file,
    mock_get_raw_content,
    mock_merge_headers,
    mock_replace_remote,
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
    mock_get_latest_sha.return_value = "abc123"
    mock_create_pr.return_value = ("https://github.com/test/repo/pull/1", 1)
    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
        p=50,
        is_planned=False,
    )
    mock_get_pr_files.return_value = [{"filename": "tests/test_example.py"}]
    mock_is_test_file.return_value = True
    mock_get_raw_content.return_value = None

    await create_pr_from_issue(payload=_get_test_payload(), trigger="issue_label")

    mock_is_test_file.assert_called()
    mock_get_raw_content.assert_called()
    mock_merge_headers.assert_not_called()
    mock_replace_remote.assert_not_called()


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.replace_remote_file_content")
@patch("services.webhook.issue_handler.merge_test_file_headers")
@patch("services.webhook.issue_handler.get_raw_content")
@patch("services.webhook.issue_handler.is_test_file")
@patch("services.webhook.issue_handler.get_pull_request_files")
@patch("services.webhook.issue_handler.chat_with_agent")
@patch("services.webhook.issue_handler.create_pull_request")
@patch("services.webhook.issue_handler.create_empty_commit")
@patch("services.webhook.issue_handler.create_remote_branch")
@patch("services.webhook.issue_handler.get_latest_remote_commit_sha")
@patch("services.webhook.issue_handler.should_bail", return_value=False)
@patch("services.webhook.issue_handler.get_remote_file_content_by_url")
@patch("services.webhook.issue_handler.extract_image_urls")
@patch("services.webhook.issue_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.create_user_request")
@patch("services.webhook.issue_handler.get_stripe_customer_id")
@patch("services.webhook.issue_handler.get_repository_features")
@patch("services.webhook.issue_handler.slack_notify")
@patch("services.webhook.issue_handler.update_comment")
@patch("services.webhook.issue_handler.update_usage")
@patch("services.webhook.issue_handler.create_progress_bar")
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.add_reaction_to_issue")
@patch("services.webhook.issue_handler.delete_comments_by_identifiers")
@patch("services.webhook.issue_handler.render_text")
@patch("services.webhook.issue_handler.get_comments")
@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_test_file_header_merge_no_change(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_delete_comments,
    mock_add_reaction,
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
    mock_get_latest_sha,
    mock_create_remote_branch,
    mock_create_empty_commit,
    mock_create_pr,
    mock_chat_with_agent,
    mock_get_pr_files,
    mock_is_test_file,
    mock_get_raw_content,
    mock_merge_headers,
    mock_replace_remote,
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
    mock_get_latest_sha.return_value = "abc123"
    mock_create_pr.return_value = ("https://github.com/test/repo/pull/1", 1)
    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
        p=50,
        is_planned=False,
    )
    mock_get_pr_files.return_value = [{"filename": "tests/test_example.py"}]
    mock_is_test_file.return_value = True
    mock_get_raw_content.return_value = "import pytest\n\ndef test_something(): pass"
    mock_merge_headers.return_value = "import pytest\n\ndef test_something(): pass"

    await create_pr_from_issue(payload=_get_test_payload(), trigger="issue_label")

    mock_is_test_file.assert_called()
    mock_get_raw_content.assert_called()
    mock_merge_headers.assert_called()
    mock_replace_remote.assert_not_called()


@patch("services.webhook.issue_handler.send_email")
@pytest.mark.asyncio
@patch("services.webhook.issue_handler.get_credits_depleted_email_text")
@patch("services.webhook.issue_handler.get_user")
@patch("services.webhook.issue_handler.get_owner")
@patch("services.webhook.issue_handler.insert_credit")
@patch("services.webhook.issue_handler.get_pull_request_files")
@patch("services.webhook.issue_handler.chat_with_agent")
@patch("services.webhook.issue_handler.create_pull_request")
@patch("services.webhook.issue_handler.create_empty_commit")
@patch("services.webhook.issue_handler.create_remote_branch")
@patch("services.webhook.issue_handler.get_latest_remote_commit_sha")
@patch("services.webhook.issue_handler.should_bail", return_value=False)
@patch("services.webhook.issue_handler.get_remote_file_content_by_url")
@patch("services.webhook.issue_handler.extract_image_urls")
@patch("services.webhook.issue_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.create_user_request")
@patch("services.webhook.issue_handler.get_stripe_customer_id")
@patch("services.webhook.issue_handler.get_repository_features")
@patch("services.webhook.issue_handler.slack_notify")
@patch("services.webhook.issue_handler.update_comment")
@patch("services.webhook.issue_handler.update_usage")
@patch("services.webhook.issue_handler.create_progress_bar")
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.add_reaction_to_issue")
@patch("services.webhook.issue_handler.delete_comments_by_identifiers")
@patch("services.webhook.issue_handler.render_text")
@patch("services.webhook.issue_handler.get_comments")
@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
async def test_credits_depleted_email_sent(
    mock_deconstruct,
    mock_check_availability,
    mock_get_comments,
    mock_render_text,
    mock_delete_comments,
    mock_add_reaction,
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
    mock_get_latest_sha,
    mock_create_remote_branch,
    mock_create_empty_commit,
    mock_create_pr,
    mock_chat_with_agent,
    mock_get_pr_files,
    mock_insert_credit,
    mock_get_owner,
    mock_get_user,
    mock_get_email_text,
    mock_send_email,
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
    mock_get_latest_sha.return_value = "abc123"
    mock_create_pr.return_value = ("https://github.com/test/repo/pull/1", 1)
    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
        p=50,
        is_planned=False,
    )
    mock_get_pr_files.return_value = [{"filename": "test.py", "status": "modified"}]
    mock_get_owner.return_value = {"id": 456, "credit_balance_usd": 0}
    mock_get_user.return_value = {"id": 888, "email": "user@example.com"}
    mock_get_email_text.return_value = ("Credits Depleted", "Your credits are gone")

    await create_pr_from_issue(payload=_get_test_payload(), trigger="issue_label")

    mock_insert_credit.assert_called_once()
    mock_get_owner.assert_called_with(owner_id=456)
    mock_get_user.assert_called_with(user_id=888)
    mock_get_email_text.assert_called_with("test_sender")
    mock_send_email.assert_called_once_with(
        to="user@example.com", subject="Credits Depleted", text="Your credits are gone"
    )


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.insert_credit")
@patch("services.webhook.issue_handler.should_bail", return_value=False)
@patch("services.webhook.issue_handler.create_empty_commit")
@patch("services.webhook.issue_handler.create_pull_request")
@patch("services.webhook.issue_handler.create_remote_branch")
@patch("services.webhook.issue_handler.get_latest_remote_commit_sha")
@patch("services.webhook.issue_handler.get_remote_file_content_by_url")
@patch("services.webhook.issue_handler.get_comments")
@patch("services.webhook.issue_handler.add_reaction_to_issue")
@patch("services.webhook.issue_handler.slack_notify")
@patch("services.webhook.issue_handler.delete_comments_by_identifiers")
@patch("services.webhook.issue_handler.create_progress_bar")
@patch("services.webhook.issue_handler.update_usage")
@patch("services.webhook.issue_handler.chat_with_agent")
@patch("services.webhook.issue_handler.create_user_request")
@patch("services.webhook.issue_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.get_owner")
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.render_text")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
@patch("services.webhook.issue_handler.get_pull_request_files")
async def test_issue_handler_token_accumulation(
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
    mock_delete_comments_by_identifiers,
    mock_slack_notify,
    mock_add_reaction_to_issue,
    mock_get_comments,
    mock_get_remote_file_content_by_url,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_create_pull_request,
    mock_create_empty_commit,
    mock_should_bail,
    mock_insert_credit,
):
    """Test that issue handler accumulates tokens correctly and calls update_usage"""
    mock_get_pull_request_files.return_value = []

    # Mock the payload deconstruction
    mock_deconstruct_github_payload.return_value = (
        {
            "installation_id": 123,
            "owner_id": 456,
            "owner_type": "User",
            "repo_id": 789,
            "issue_body": "Test issue body",
            "owner": "test_owner",
            "repo": "test_repo",
            "issue_number": 100,
            "issue_title": "Schedule: Add unit tests to services/test_file.py",
            "sender_name": "test_sender",
            "repo_full_name": "test_owner/test_repo",
            "issuer_name": "test_issuer",
            "sender_id": 888,
            "token": "github_token_123",
            "new_branch": "gitauto/issue-100",
            "sender_email": "test@example.com",
            "github_urls": {
                "issues": "https://api.github.com/repos/test_owner/test_repo/issues",
                "pulls": "https://api.github.com/repos/test_owner/test_repo/pulls",
            },
            "is_automation": False,
            "clone_url": "https://github.com/test_owner/test_repo.git",
            "base_branch": "main",
        },
        None,
    )

    mock_render_text.return_value = "Rendered issue body"
    mock_slack_notify.return_value = "thread_123"
    mock_delete_comments_by_identifiers.return_value = None
    mock_create_progress_bar.return_value = "Progress bar content"
    mock_add_reaction_to_issue.return_value = None
    mock_get_comments.return_value = []
    mock_get_remote_file_content_by_url.return_value = ("", "")
    mock_get_latest_remote_commit_sha.return_value = "abc123"
    mock_create_remote_branch.return_value = None

    mock_create_pull_request.return_value = (
        "https://github.com/test/repo/pull/123",
        123,
    )
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
            p=95,
            is_planned=False,
        ),
    ]
    mock_get_pull_request_files.return_value = [
        {"filename": "test.py", "status": "modified"}
    ]

    # Create test payload
    payload = cast(
        GitHubLabeledPayload,
        {
            "action": "labeled",
            "label": {"name": "gitauto"},
            "issue": {
                "number": 100,
                "title": "Schedule: Add unit tests to services/test_file.py",
                "body": "Test body",
            },
            "repository": {"name": "test_repo", "full_name": "test_owner/test_repo"},
            "sender": {"login": "test_sender"},
        },
    )

    # Call the function
    await create_pr_from_issue(
        payload=payload,
        trigger="issue_comment",
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
@patch("services.webhook.issue_handler.insert_credit")
@patch("services.webhook.issue_handler.should_bail", return_value=False)
@patch("services.webhook.issue_handler.create_empty_commit")
@patch("services.webhook.issue_handler.create_pull_request")
@patch("services.webhook.issue_handler.create_remote_branch")
@patch("services.webhook.issue_handler.get_latest_remote_commit_sha")
@patch("services.webhook.issue_handler.get_remote_file_content_by_url")
@patch("services.webhook.issue_handler.get_comments")
@patch("services.webhook.issue_handler.add_reaction_to_issue")
@patch("services.webhook.issue_handler.slack_notify")
@patch("services.webhook.issue_handler.delete_comments_by_identifiers")
@patch("services.webhook.issue_handler.create_progress_bar")
@patch("services.webhook.issue_handler.update_usage")
@patch("services.webhook.issue_handler.update_comment")
@patch("services.webhook.issue_handler.get_repository_features")
@patch("services.webhook.issue_handler.chat_with_agent")
@patch("services.webhook.issue_handler.create_user_request")
@patch("services.webhook.issue_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.get_owner")
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.render_text")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
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
    mock_delete_comments_by_identifiers,
    mock_slack_notify,
    mock_add_reaction_to_issue,
    mock_get_comments,
    mock_get_remote_file_content_by_url,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_create_pull_request,
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
            "issue_body": "Test issue body",
            "owner": "test_owner",
            "repo": "test_repo",
            "issue_number": 100,
            "issue_title": "Schedule: Add unit tests to services/test_file.py",
            "sender_name": "test_sender",
            "repo_full_name": "test_owner/test_repo",
            "issuer_name": "test_issuer",
            "sender_id": 888,
            "token": "github_token_123",
            "new_branch": "gitauto/issue-100",
            "sender_email": "test@example.com",
            "github_urls": {},
            "is_automation": False,
            "clone_url": "https://github.com/test_owner/test_repo.git",
            "base_branch": "main",
        },
        None,
    )

    mock_render_text.return_value = "Rendered issue body"
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 50,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Proceeding",
    }

    mock_render_text.return_value = "Rendered issue body"
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
    mock_delete_comments_by_identifiers.return_value = None
    mock_slack_notify.return_value = "thread_1"
    mock_add_reaction_to_issue.return_value = None
    mock_get_comments.return_value = []
    mock_get_remote_file_content_by_url.return_value = ("", "")
    mock_get_latest_remote_commit_sha.return_value = "abc123"
    mock_create_remote_branch.return_value = None
    mock_create_pull_request.return_value = (
        "https://github.com/test/repo/pull/123",
        123,
    )
    mock_create_empty_commit.return_value = None
    mock_insert_credit.return_value = None

    payload = cast(
        GitHubLabeledPayload,
        {
            "action": "labeled",
            "label": {"name": "gitauto"},
            "issue": {
                "number": 100,
                "title": "Schedule: Add unit tests to services/test_file.py",
                "body": "Test body",
            },
            "repository": {"name": "test_repo", "full_name": "test_owner/test_repo"},
            "sender": {"login": "test_sender"},
        },
    )

    await create_pr_from_issue(
        payload=payload,
        trigger="issue_comment",
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
@patch("services.webhook.issue_handler.insert_credit")
@patch("services.webhook.issue_handler.should_bail", return_value=False)
@patch("services.webhook.issue_handler.create_empty_commit")
@patch("services.webhook.issue_handler.create_pull_request")
@patch("services.webhook.issue_handler.create_remote_branch")
@patch("services.webhook.issue_handler.get_latest_remote_commit_sha")
@patch("services.webhook.issue_handler.get_remote_file_content_by_url")
@patch("services.webhook.issue_handler.get_comments")
@patch("services.webhook.issue_handler.add_reaction_to_issue")
@patch("services.webhook.issue_handler.slack_notify")
@patch("services.webhook.issue_handler.delete_comments_by_identifiers")
@patch("services.webhook.issue_handler.create_progress_bar")
@patch("services.webhook.issue_handler.update_usage")
@patch("services.webhook.issue_handler.update_comment")
@patch("services.webhook.issue_handler.get_repository_features")
@patch("services.webhook.issue_handler.chat_with_agent")
@patch("services.webhook.issue_handler.create_user_request")
@patch("services.webhook.issue_handler.read_local_file")
@patch("services.webhook.issue_handler.find_test_files")
@patch("services.webhook.issue_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.get_owner")
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.render_text")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
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
    mock_delete_comments_by_identifiers,
    mock_slack_notify,
    mock_add_reaction_to_issue,
    mock_get_comments,
    mock_get_remote_file_content_by_url,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_create_pull_request,
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
            "issue_body": "Test issue body",
            "owner": "test_owner",
            "repo": "test_repo",
            "issue_number": 100,
            "issue_title": "Schedule: Add unit tests to src/logger.ts",
            "sender_name": "test_sender",
            "repo_full_name": "test_owner/test_repo",
            "issuer_name": "test_issuer",
            "sender_id": 888,
            "token": "github_token_123",
            "new_branch": "gitauto/issue-100",
            "sender_email": "test@example.com",
            "github_urls": {},
            "is_automation": False,
            "clone_url": "https://github.com/test_owner/test_repo.git",
            "base_branch": "main",
        },
        None,
    )
    mock_render_text.return_value = "Rendered issue body"
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
    mock_read_local_file.return_value = "const x = 1;"

    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
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
    mock_delete_comments_by_identifiers.return_value = None
    mock_slack_notify.return_value = "thread_1"
    mock_add_reaction_to_issue.return_value = None
    mock_get_comments.return_value = []
    mock_get_remote_file_content_by_url.return_value = ("", "")
    mock_get_latest_remote_commit_sha.return_value = "abc123"
    mock_create_remote_branch.return_value = None
    mock_create_pull_request.return_value = (
        "https://github.com/test/repo/pull/123",
        123,
    )
    mock_create_empty_commit.return_value = None
    mock_insert_credit.return_value = None

    payload = cast(
        GitHubLabeledPayload,
        {
            "action": "labeled",
            "label": {"name": "gitauto"},
            "issue": {
                "number": 100,
                "title": "Schedule: Add unit tests to src/logger.ts",
                "body": "Test body",
            },
            "repository": {"name": "test_repo", "full_name": "test_owner/test_repo"},
            "sender": {"login": "test_sender"},
        },
    )

    await create_pr_from_issue(payload=payload, trigger="issue_comment")

    # Verify test_files contents are included in the prompt (not just paths)
    call_kwargs = mock_chat_with_agent.call_args.kwargs
    messages = call_kwargs["messages"]
    user_input = json.loads(messages[0]["content"])
    assert "test_files" in user_input
    assert "test_file_paths" not in user_input
    assert len(user_input["test_files"]) == 3


@pytest.mark.asyncio
@patch("services.webhook.issue_handler.insert_credit")
@patch("services.webhook.issue_handler.should_bail", return_value=False)
@patch("services.webhook.issue_handler.create_empty_commit")
@patch("services.webhook.issue_handler.create_pull_request")
@patch("services.webhook.issue_handler.create_remote_branch")
@patch("services.webhook.issue_handler.get_latest_remote_commit_sha")
@patch("services.webhook.issue_handler.get_remote_file_content_by_url")
@patch("services.webhook.issue_handler.get_comments")
@patch("services.webhook.issue_handler.add_reaction_to_issue")
@patch("services.webhook.issue_handler.slack_notify")
@patch("services.webhook.issue_handler.delete_comments_by_identifiers")
@patch("services.webhook.issue_handler.create_progress_bar")
@patch("services.webhook.issue_handler.update_usage")
@patch("services.webhook.issue_handler.update_comment")
@patch("services.webhook.issue_handler.get_repository_features")
@patch("services.webhook.issue_handler.chat_with_agent")
@patch("services.webhook.issue_handler.create_user_request")
@patch("services.webhook.issue_handler.read_local_file")
@patch("services.webhook.issue_handler.find_test_files")
@patch("services.webhook.issue_handler.prepare_repo_for_work", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.ensure_node_packages", new_callable=AsyncMock)
@patch("services.webhook.issue_handler.get_owner")
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.render_text")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
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
    mock_delete_comments_by_identifiers,
    mock_slack_notify,
    mock_add_reaction_to_issue,
    mock_get_comments,
    mock_get_remote_file_content_by_url,
    mock_get_latest_remote_commit_sha,
    mock_create_remote_branch,
    mock_create_pull_request,
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
            "issue_body": "Test issue body",
            "owner": "test_owner",
            "repo": "test_repo",
            "issue_number": 100,
            "issue_title": "Schedule: Add unit tests to src/logger.ts",
            "sender_name": "test_sender",
            "repo_full_name": "test_owner/test_repo",
            "issuer_name": "test_issuer",
            "sender_id": 888,
            "token": "github_token_123",
            "new_branch": "gitauto/issue-100",
            "sender_email": "test@example.com",
            "github_urls": {},
            "is_automation": False,
            "clone_url": "https://github.com/test_owner/test_repo.git",
            "base_branch": "main",
        },
        None,
    )
    mock_render_text.return_value = "Rendered issue body"
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
    mock_read_local_file.return_value = "const x = 1;"

    mock_chat_with_agent.return_value = AgentResult(
        messages=[],
        token_input=10,
        token_output=5,
        is_completed=True,
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
    mock_delete_comments_by_identifiers.return_value = None
    mock_slack_notify.return_value = "thread_1"
    mock_add_reaction_to_issue.return_value = None
    mock_get_comments.return_value = []
    mock_get_remote_file_content_by_url.return_value = ("", "")
    mock_get_latest_remote_commit_sha.return_value = "abc123"
    mock_create_remote_branch.return_value = None
    mock_create_pull_request.return_value = (
        "https://github.com/test/repo/pull/123",
        123,
    )
    mock_create_empty_commit.return_value = None
    mock_insert_credit.return_value = None

    payload = cast(
        GitHubLabeledPayload,
        {
            "action": "labeled",
            "label": {"name": "gitauto"},
            "issue": {
                "number": 100,
                "title": "Schedule: Add unit tests to src/logger.ts",
                "body": "Test body",
            },
            "repository": {"name": "test_repo", "full_name": "test_owner/test_repo"},
            "sender": {"login": "test_sender"},
        },
    )

    await create_pr_from_issue(payload=payload, trigger="issue_comment")

    # Verify only paths are included (not contents) when >5 test files
    call_kwargs = mock_chat_with_agent.call_args.kwargs
    messages = call_kwargs["messages"]
    user_input = json.loads(messages[0]["content"])
    assert "test_file_paths" in user_input
    assert "test_files" not in user_input
    assert len(user_input["test_file_paths"]) == 7
    # Verify read_local_file was NOT called (no contents loaded)
    mock_read_local_file.assert_not_called()
