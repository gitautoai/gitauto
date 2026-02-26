# pylint: disable=unused-argument
"""Integration tests for review_run_handler.py"""

# pyright: reportUnusedVariable=false

from unittest.mock import AsyncMock, patch

import pytest

from config import PRODUCT_ID
from services.agents.verify_task_is_complete import VerifyTaskIsCompleteResult
from services.chat_with_agent import AgentResult
from services.webhook.review_run_handler import handle_review_run


@pytest.fixture
def mock_review_comment_payload():
    """Realistic review comment payload for PR review handler."""
    return {
        "action": "created",
        "comment": {
            "id": 12345,
            "node_id": "PRRC_kwDOJTestNodeId",
            "path": "src/main.py",
            "subject_type": "line",
            "line": 42,
            "side": "RIGHT",
            "body": "This function could be optimized. Consider using a more efficient algorithm.",
            "user": {"login": "test-reviewer", "type": "User"},
        },
        "pull_request": {
            "number": 123,
            "title": "Add new feature",
            "body": "This PR adds a new feature to the codebase",
            "url": "https://api.github.com/repos/test-owner/test-repo/pulls/123",
            "user": {"login": "gitauto-ai[bot]"},
            "head": {"ref": f"{PRODUCT_ID}/dashboard-20250101-155924-Ab1C", "sha": "abc123def456"},
            "base": {"ref": "main"},
        },
        "repository": {
            "id": 98765,
            "name": "test-repo",
            "owner": {
                "id": 11111,
                "login": "test-owner",
                "type": "Organization",
            },
            "clone_url": "https://github.com/test-owner/test-repo.git",
            "fork": False,
        },
        "sender": {
            "id": 22222,
            "login": "test-reviewer",  # human reviewer
        },
        "installation": {
            "id": 33333,
        },
    }


@patch("services.webhook.review_run_handler.get_installation_access_token")
@patch("services.webhook.review_run_handler.get_repository")
@patch("services.webhook.review_run_handler.create_user_request")
@patch("services.webhook.review_run_handler.get_review_thread_comments")
@patch("services.webhook.review_run_handler.reply_to_comment")
@patch("services.webhook.review_run_handler.get_local_file_content")
@patch("services.webhook.review_run_handler.get_pull_request_files")
@patch("services.webhook.review_run_handler.update_comment")
@patch("services.webhook.review_run_handler.should_bail", return_value=False)
@patch("services.webhook.review_run_handler.chat_with_agent")
@patch("services.webhook.review_run_handler.create_empty_commit")
@patch("services.webhook.review_run_handler.update_usage")
@patch(
    "services.webhook.review_run_handler.ensure_node_packages", new_callable=AsyncMock
)
@patch("services.webhook.review_run_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch(
    "services.webhook.review_run_handler.prepare_repo_for_work", new_callable=AsyncMock
)
@patch("services.webhook.review_run_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]")
@pytest.mark.asyncio
async def test_review_run_handler_accumulates_tokens_correctly(
    _mock_prepare_repo,
    _mock_git_clone_to_efs,
    _mock_ensure_node_packages,
    mock_update_usage,
    mock_create_empty_commit,
    mock_chat_with_agent,
    _mock_should_bail,
    mock_update_comment,
    mock_get_pr_files,
    mock_get_file_content,
    mock_reply_to_comment,
    mock_get_thread_comments,
    mock_create_user_request,
    mock_get_repo,
    mock_get_token,
    mock_review_comment_payload,
):
    """Test that review run handler accumulates tokens from multiple chat_with_agent calls."""

    # Setup realistic mocks
    mock_get_token.return_value = "ghs_test_token"
    mock_get_repo.return_value = {"id": 98765}
    mock_create_user_request.return_value = 777  # This is the usage_id
    mock_get_thread_comments.return_value = [
        {
            "author": {"login": "test-reviewer"},
            "body": "This function could be optimized. Consider using a more efficient algorithm.",
            "createdAt": "2025-09-17T12:00:00Z",
        }
    ]
    mock_reply_to_comment.return_value = "http://comment-url"
    mock_get_file_content.return_value = (
        "def main():\n    # File content here\n    pass"
    )
    mock_get_pr_files.return_value = [
        {"filename": "src/main.py", "status": "modified"},
        {"filename": "src/utils.py", "status": "added"},
    ]
    mock_update_comment.return_value = None
    mock_create_empty_commit.return_value = None

    mock_chat_with_agent.side_effect = [
        AgentResult(
            messages=[
                {"role": "user", "content": "review"},
                {"role": "assistant", "content": "analysis"},
            ],
            token_input=120,
            token_output=80,
            is_completed=True,
            completion_reason="",
            p=40,
            is_planned=False,
        ),
    ]

    # Execute the function
    await handle_review_run(mock_review_comment_payload, trigger="review_comment")

    assert mock_chat_with_agent.call_count == 1

    # Verify execution call includes usage_id for API request tracking
    execution_call_kwargs = mock_chat_with_agent.call_args_list[0].kwargs
    assert execution_call_kwargs["usage_id"] == 777
    assert "system_message" in execution_call_kwargs
    assert isinstance(execution_call_kwargs["system_message"], str)

    # Verify baseline_tsc_errors is set on base_args
    base_args = execution_call_kwargs["base_args"]
    assert "baseline_tsc_errors" in base_args
    assert isinstance(base_args["baseline_tsc_errors"], set)

    # CRITICAL: Verify update_usage was called with accumulated tokens
    mock_update_usage.assert_called_once()
    usage_call_kwargs = mock_update_usage.call_args.kwargs

    assert usage_call_kwargs["usage_id"] == 777
    assert usage_call_kwargs["token_input"] == 120
    assert usage_call_kwargs["token_output"] == 80
    assert usage_call_kwargs["is_completed"] is True

    # Verify other expected parameters
    assert "total_seconds" in usage_call_kwargs
    assert usage_call_kwargs["pr_number"] == 123

    # Verify get_repository was called with owner_id and repo_id
    mock_get_repo.assert_called_once_with(owner_id=11111, repo_id=98765)


@patch("services.webhook.review_run_handler.verify_task_is_complete")
@patch("services.webhook.review_run_handler.get_installation_access_token")
@patch("services.webhook.review_run_handler.get_repository")
@patch("services.webhook.review_run_handler.create_user_request")
@patch("services.webhook.review_run_handler.get_review_thread_comments")
@patch("services.webhook.review_run_handler.reply_to_comment")
@patch("services.webhook.review_run_handler.get_local_file_content")
@patch("services.webhook.review_run_handler.get_pull_request_files")
@patch("services.webhook.review_run_handler.update_comment")
@patch("services.webhook.review_run_handler.should_bail", return_value=False)
@patch("services.webhook.review_run_handler.chat_with_agent")
@patch("services.webhook.review_run_handler.create_empty_commit")
@patch("services.webhook.review_run_handler.update_usage")
@patch(
    "services.webhook.review_run_handler.ensure_node_packages", new_callable=AsyncMock
)
@patch("services.webhook.review_run_handler.git_clone_to_efs", new_callable=AsyncMock)
@patch(
    "services.webhook.review_run_handler.prepare_repo_for_work", new_callable=AsyncMock
)
@patch("services.webhook.review_run_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]")
@patch("services.webhook.review_run_handler.MAX_ITERATIONS", 2)
@pytest.mark.asyncio
async def test_review_run_handler_max_iterations_forces_verification(
    _mock_prepare_repo,
    _mock_git_clone_to_efs,
    _mock_ensure_node_packages,
    _mock_update_usage,
    _mock_create_empty_commit,
    mock_chat_with_agent,
    _mock_should_bail,
    mock_update_comment,
    mock_get_pr_files,
    mock_get_file_content,
    mock_reply_to_comment,
    mock_get_thread_comments,
    mock_create_user_request,
    mock_get_repo,
    mock_get_token,
    mock_verify_task_is_complete,
    mock_review_comment_payload,
):
    """Test that review run handler forces verify_task_is_complete when MAX_ITERATIONS is reached."""

    mock_get_token.return_value = "ghs_test_token"
    mock_get_repo.return_value = {"id": 98765}
    mock_create_user_request.return_value = 777
    mock_get_thread_comments.return_value = [
        {
            "author": {"login": "test-reviewer"},
            "body": "This function could be optimized.",
            "createdAt": "2025-09-17T12:00:00Z",
        }
    ]
    mock_reply_to_comment.return_value = "http://comment-url"
    mock_get_file_content.return_value = "def main():\n    pass"
    mock_get_pr_files.return_value = [
        {"filename": "src/main.py", "status": "modified"},
    ]
    mock_update_comment.return_value = None
    mock_verify_task_is_complete.return_value = VerifyTaskIsCompleteResult(
        success=True,
        message="Task completed.",
    )

    mock_chat_with_agent.side_effect = [
        # MAX_ITERATIONS=2, both return is_completed=False
        AgentResult(
            messages=[{"role": "user", "content": "review"}],
            token_input=120,
            token_output=80,
            is_completed=False,
            completion_reason="",
            p=40,
            is_planned=False,
        ),
        AgentResult(
            messages=[{"role": "user", "content": "review"}],
            token_input=100,
            token_output=60,
            is_completed=False,
            completion_reason="",
            p=60,
            is_planned=False,
        ),
    ]

    await handle_review_run(mock_review_comment_payload, trigger="review_comment")

    assert mock_chat_with_agent.call_count == 2
    mock_verify_task_is_complete.assert_called_once()
