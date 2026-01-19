"""Integration tests for review_run_handler.py token accumulation"""

from unittest.mock import patch
import pytest
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
            "head": {"ref": "feature-branch", "sha": "abc123def456"},
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
@patch("services.webhook.review_run_handler.get_remote_file_content")
@patch("services.webhook.review_run_handler.get_pull_request_files")
@patch("services.webhook.review_run_handler.update_comment")
@patch("services.webhook.review_run_handler.is_pull_request_open")
@patch("services.webhook.review_run_handler.check_branch_exists")
@patch("services.webhook.review_run_handler.is_lambda_timeout_approaching")
@patch("services.webhook.review_run_handler.chat_with_agent")
@patch("services.webhook.review_run_handler.create_empty_commit")
@patch("services.webhook.review_run_handler.update_usage")
@patch("services.webhook.review_run_handler.start_async_install_on_efs")
@patch("services.webhook.review_run_handler.prepare_repo_for_work")
@patch("services.webhook.review_run_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]")
@pytest.mark.asyncio
async def test_review_run_handler_accumulates_tokens_correctly(
    _mock_prepare_repo,
    _mock_start_async,
    mock_update_usage,
    mock_create_empty_commit,
    mock_chat_with_agent,
    mock_timeout_check,
    mock_check_branch_exists,
    mock_is_pr_open,
    mock_update_comment,
    mock_get_pull_files,
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
    mock_get_pull_files.return_value = [
        {"filename": "src/main.py", "status": "modified"},
        {"filename": "src/utils.py", "status": "added"},
    ]
    mock_is_pr_open.return_value = True
    mock_check_branch_exists.return_value = True
    mock_timeout_check.return_value = (False, 0)
    mock_update_comment.return_value = None
    mock_create_empty_commit.return_value = None

    # Mock chat_with_agent to return 5-tuple: (messages, token_input, token_output, is_completed, progress)
    # is_completed=True breaks the loop
    mock_chat_with_agent.side_effect = [
        # First call - 120 input, 80 output tokens
        (
            [
                {"role": "user", "content": "review"},
                {"role": "assistant", "content": "analysis"},
            ],
            120,  # token_input
            80,  # token_output
            True,  # is_completed=True (breaks loop)
            40,  # progress
        ),
    ]

    # Execute the function
    await handle_review_run(mock_review_comment_payload)

    # Verify chat_with_agent was called once (loop breaks on is_completed=True)
    assert mock_chat_with_agent.call_count == 1

    # Verify call includes usage_id for API request tracking
    first_call_kwargs = mock_chat_with_agent.call_args_list[0].kwargs
    assert first_call_kwargs["usage_id"] == 777

    # CRITICAL: Verify update_usage was called with tokens
    mock_update_usage.assert_called_once()
    usage_call_kwargs = mock_update_usage.call_args.kwargs

    # This is the actual meaningful test - verifies token accumulation works
    assert usage_call_kwargs["usage_id"] == 777
    assert usage_call_kwargs["token_input"] == 120
    assert usage_call_kwargs["token_output"] == 80
    assert usage_call_kwargs["is_completed"] is True

    # Verify other expected parameters
    assert "total_seconds" in usage_call_kwargs
    assert usage_call_kwargs["pr_number"] == 123

    # Verify get_repository was called with owner_id and repo_id
    mock_get_repo.assert_called_once_with(owner_id=11111, repo_id=98765)
