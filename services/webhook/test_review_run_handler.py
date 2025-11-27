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
@patch("services.webhook.review_run_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]")
@pytest.mark.asyncio
async def test_review_run_handler_accumulates_tokens_correctly(
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

    # Mock chat_with_agent to return values that break the loop after 2 calls
    # is_explored=False and is_committed=False breaks the loop (line 314-315)
    mock_chat_with_agent.side_effect = [
        # First call (get mode) - 120 input, 80 output tokens
        (
            [
                {"role": "user", "content": "review"},
                {"role": "assistant", "content": "analysis"},
            ],
            [],
            "analyze_code",
            {"suggestions": ["optimize loop"]},
            120,  # token_input
            80,  # token_output
            False,  # is_explored=False (to break loop)
            40,
        ),
        # Second call (commit mode) - 90 input, 60 output tokens
        (
            [
                {"role": "user", "content": "review"},
                {"role": "assistant", "content": "fix applied"},
            ],
            [],
            "apply_fixes",
            {"files_modified": ["src/main.py"]},
            90,  # token_input
            60,  # token_output
            False,  # is_committed=False (to break loop)
            50,
        ),
    ]

    # Execute the function
    handle_review_run(mock_review_comment_payload)

    # Verify chat_with_agent was called exactly twice (get + commit modes)
    assert mock_chat_with_agent.call_count == 2

    # Verify the calls were made with correct modes
    first_call_kwargs = mock_chat_with_agent.call_args_list[0].kwargs
    second_call_kwargs = mock_chat_with_agent.call_args_list[1].kwargs
    assert first_call_kwargs["mode"] == "get"
    assert second_call_kwargs["mode"] == "commit"

    # Verify both calls include usage_id for API request tracking
    assert first_call_kwargs["usage_id"] == 777
    assert second_call_kwargs["usage_id"] == 777

    # CRITICAL: Verify update_usage was called with ACCUMULATED tokens
    mock_update_usage.assert_called_once()
    usage_call_kwargs = mock_update_usage.call_args.kwargs

    # This is the actual meaningful test - verifies token accumulation works
    assert usage_call_kwargs["usage_id"] == 777
    assert usage_call_kwargs["token_input"] == 210  # 120 + 90 = 210
    assert usage_call_kwargs["token_output"] == 140  # 80 + 60 = 140
    assert usage_call_kwargs["is_completed"] is True

    # Verify other expected parameters
    assert "total_seconds" in usage_call_kwargs
    assert usage_call_kwargs["pr_number"] == 123
