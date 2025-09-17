"""Integration tests for pr_checkbox_handler.py token accumulation"""

from unittest.mock import patch
import pytest
from services.webhook.pr_checkbox_handler import handle_pr_checkbox_trigger


@pytest.fixture
def mock_issue_comment_payload():
    """Realistic issue comment payload that triggers PR checkbox handler."""
    return {
        "action": "created",
        "comment": {
            "id": 12345,
            "body": "- [x] Generate Tests\n- [x] `src/test.py`\n- [x] `src/main.py`\n- [ ] Some other task",
            "user": {
                "id": 33333,
                "login": "gitauto-ai[bot]",
            },
        },
        "issue": {
            "number": 123,
            "title": "Test PR",
            "pull_request": {
                "url": "https://api.github.com/repos/test-owner/test-repo/pulls/123"
            },
            "user": {"login": "test-user"},
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
            "login": "test-sender",
        },
        "installation": {
            "id": 33333,
        },
    }


@patch("services.webhook.pr_checkbox_handler.get_installation_access_token")
@patch("services.webhook.pr_checkbox_handler.get_repository")
@patch("services.webhook.pr_checkbox_handler.create_user_request")
@patch("services.webhook.pr_checkbox_handler.get_pull_request")
@patch("services.webhook.pr_checkbox_handler.check_availability")
@patch("services.webhook.pr_checkbox_handler.update_comment")
@patch("services.webhook.pr_checkbox_handler.is_pull_request_open")
@patch("services.webhook.pr_checkbox_handler.check_branch_exists")
@patch("services.webhook.pr_checkbox_handler.is_lambda_timeout_approaching")
@patch("services.webhook.pr_checkbox_handler.chat_with_agent")
@patch("services.webhook.pr_checkbox_handler.create_empty_commit")
@patch("services.webhook.pr_checkbox_handler.update_usage")
@patch("services.webhook.pr_checkbox_handler.extract_selected_files")
@patch("services.webhook.pr_checkbox_handler.slack_notify")
@patch("services.webhook.pr_checkbox_handler.PRODUCT_ID", new="gitauto")
@patch("services.webhook.pr_checkbox_handler.GITHUB_APP_USER_NAME", new="gitauto-ai[bot]")
@patch("services.webhook.pr_checkbox_handler.create_comment")
@patch("services.webhook.pr_checkbox_handler.cancel_workflow_runs")
@pytest.mark.asyncio
async def test_pr_checkbox_handler_accumulates_tokens_correctly(
    mock_cancel_workflow_runs,
    mock_create_comment,
    mock_slack_notify,
    mock_extract_selected_files,
    mock_update_usage,
    mock_create_empty_commit,
    mock_chat_with_agent,
    mock_timeout_check,
    mock_check_branch_exists,
    mock_is_pr_open,
    mock_update_comment,
    mock_check_availability,
    mock_get_pr,
    mock_create_user_request,
    mock_get_repo,
    mock_get_token,
    mock_issue_comment_payload,
):
    """Test that PR checkbox handler actually accumulates tokens from multiple chat_with_agent calls."""

    # Setup realistic mocks
    mock_get_token.return_value = "ghs_test_token"
    mock_get_repo.return_value = {"id": 98765}
    mock_create_user_request.return_value = 888  # This is the usage_id
    mock_extract_selected_files.return_value = [
        "src/test.py",
        "src/main.py",
    ]  # Must return files
    mock_slack_notify.return_value = "thread_123"
    mock_create_comment.return_value = "http://comment-url"
    mock_cancel_workflow_runs.return_value = None
    mock_get_pr.return_value = {
        "title": "Test PR",
        "body": "Test PR description",
        "head": {"ref": "feature-branch"},
        "user": {"login": "test-user"},
    }
    mock_check_availability.return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 50,
        "period_end_date": None,
        "user_message": "",
        "log_message": "Proceeding with credit billing",
    }
    mock_is_pr_open.return_value = True
    mock_check_branch_exists.return_value = True
    mock_timeout_check.return_value = (False, 0)
    mock_update_comment.return_value = None
    mock_create_empty_commit.return_value = None

    # Mock chat_with_agent to return values that break the loop after 2 calls
    # is_explored=False and is_committed=False breaks the loop (line 282-283)
    mock_chat_with_agent.side_effect = [
        # First call (get mode) - 100 input, 60 output tokens
        (
            [
                {"role": "user", "content": "test"},
                {"role": "assistant", "content": "response1"},
            ],
            [],
            "search_files",
            {"files": ["test.py"]},
            100,  # token_input
            60,  # token_output
            False,  # is_explored=False (to break loop)
            85,
        ),
        # Second call (commit mode) - 80 input, 45 output tokens
        (
            [
                {"role": "user", "content": "test"},
                {"role": "assistant", "content": "response2"},
            ],
            [],
            "create_tests",
            {"test_file": "test_generated.py"},
            80,  # token_input
            45,  # token_output
            False,  # is_committed=False (to break loop)
            90,
        ),
    ]

    # Execute the function
    await handle_pr_checkbox_trigger(mock_issue_comment_payload)

    # Verify chat_with_agent was called exactly twice (get + commit modes)
    assert mock_chat_with_agent.call_count == 2

    # Verify the calls were made with correct modes
    first_call_kwargs = mock_chat_with_agent.call_args_list[0].kwargs
    second_call_kwargs = mock_chat_with_agent.call_args_list[1].kwargs
    assert first_call_kwargs["mode"] == "get"
    assert second_call_kwargs["mode"] == "commit"

    # Verify both calls include usage_id for API request tracking
    assert first_call_kwargs["usage_id"] == 888
    assert second_call_kwargs["usage_id"] == 888

    # CRITICAL: Verify update_usage was called with ACCUMULATED tokens
    mock_update_usage.assert_called_once()
    usage_call_kwargs = mock_update_usage.call_args.kwargs

    # This is the actual meaningful test - verifies token accumulation works
    assert usage_call_kwargs["usage_id"] == 888
    assert usage_call_kwargs["token_input"] == 180  # 100 + 80 = 180
    assert usage_call_kwargs["token_output"] == 105  # 60 + 45 = 105
    assert usage_call_kwargs["is_completed"] is True

    # Verify other expected parameters
    assert "total_seconds" in usage_call_kwargs
    assert usage_call_kwargs["pr_number"] == 123


@pytest.mark.asyncio
async def test_pr_checkbox_handler_early_exit_conditions():
    """Test that handler exits early for various conditions without calling chat_with_agent."""

    # Test with bot sender - should exit early
    bot_payload = {
        "action": "created",
        "comment": {
            "body": "- [x] Generate Tests",
            "user": {"login": "gitauto-ai[bot]"},
        },
        "issue": {
            "number": 123,
            "pull_request": {"url": "https://api.github.com/test"},
        },
        "repository": {"id": 123, "name": "test", "owner": {"id": 1, "login": "test"}},
        "sender": {"id": 1, "login": "user[bot]"},  # Bot sender
        "installation": {"id": 123},
    }

    with patch("services.webhook.pr_checkbox_handler.chat_with_agent") as mock_chat:
        await handle_pr_checkbox_trigger(bot_payload)
        # Should not call chat_with_agent for bot senders
        mock_chat.assert_not_called()


@pytest.mark.asyncio
async def test_pr_checkbox_handler_wrong_comment_body():
    """Test that handler exits early when comment doesn't contain the trigger text."""

    wrong_body_payload = {
        "action": "created",
        "comment": {
            "body": "Just a regular comment",
            "user": {"login": "gitauto-ai[bot]"},
        },
        "issue": {
            "number": 123,
            "pull_request": {"url": "https://api.github.com/test"},
        },
        "repository": {"id": 123, "name": "test", "owner": {"id": 1, "login": "test"}},
        "sender": {"id": 1, "login": "human-user"},
        "installation": {"id": 123},
    }

    with patch("services.webhook.pr_checkbox_handler.chat_with_agent") as mock_chat:
        await handle_pr_checkbox_trigger(wrong_body_payload)
        # Should not call chat_with_agent for wrong comment body
        mock_chat.assert_not_called()
