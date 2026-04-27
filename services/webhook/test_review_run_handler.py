# pylint: disable=unused-argument,too-many-lines
# pyright: reportUnusedVariable=false
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from config import PRODUCT_ID
from services.agents.verify_task_is_complete import VerifyTaskIsCompleteResult
from services.agents.verify_task_is_ready import VerifyTaskIsReadyResult
from services.chat_with_agent import AgentResult
from services.github.pulls.get_review_thread_comments import ReviewThreadResult
from services.webhook.review_run_handler import handle_review_run

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def _mock_refresh_mongodb_cache():
    with patch("services.webhook.review_run_handler.refresh_mongodb_cache"):
        yield


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
            "head": {
                "ref": f"{PRODUCT_ID}/dashboard-20250101-155924-Ab1C",
                "sha": "abc123def456",
            },
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


@patch("services.webhook.review_run_handler.get_pull_request")
@patch("services.webhook.review_run_handler.slack_notify")
@patch("services.webhook.review_run_handler.get_local_file_tree", return_value=[])
@patch("services.webhook.review_run_handler.set_npm_token_env")
@patch("services.webhook.review_run_handler.get_installation_access_token")
@patch("services.webhook.review_run_handler.get_user_public_info")
@patch("services.webhook.review_run_handler.get_repository")
@patch("services.webhook.review_run_handler.create_user_request")
@patch("services.webhook.review_run_handler.get_review_thread_comments")
@patch("services.webhook.review_run_handler.reply_to_comment")
@patch(
    "services.webhook.review_run_handler.format_content_with_line_numbers",
    side_effect=lambda file_path, content: content,
)
@patch("services.webhook.review_run_handler.read_local_file")
@patch("services.webhook.review_run_handler.get_pull_request_files")
@patch("services.webhook.review_run_handler.update_comment")
@patch("services.webhook.review_run_handler.should_bail", return_value=False)
@patch("services.webhook.review_run_handler.chat_with_agent")
@patch("services.webhook.review_run_handler.create_empty_commit")
@patch("services.webhook.review_run_handler.get_reference", return_value="changed_sha")
@patch("services.webhook.review_run_handler.update_usage")
@patch("services.webhook.review_run_handler.ensure_node_packages")
@patch("services.webhook.review_run_handler.clone_repo_and_install_dependencies")
@patch(
    "services.webhook.review_run_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.review_run_handler.git_merge_base_into_pr")
@patch("services.webhook.review_run_handler.ensure_php_packages")
@patch(
    "services.webhook.review_run_handler.verify_task_is_ready", new_callable=AsyncMock
)
@patch("services.webhook.review_run_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]")
@pytest.mark.asyncio
async def test_review_run_handler_accumulates_tokens_correctly(
    _mock_verify_task_is_ready,
    _mock_ensure_php,
    _mock_get_behind,
    _mock_merge_base,
    _mock_prepare_repo,
    _mock_ensure_node_packages,
    mock_update_usage,
    _mock_get_reference,
    mock_create_empty_commit,
    mock_chat_with_agent,
    _mock_should_bail,
    mock_update_comment,
    mock_get_pr_files,
    mock_get_file_content,
    _mock_format,
    mock_reply_to_comment,
    mock_get_thread_comments,
    mock_create_user_request,
    mock_get_repo,
    mock_get_user_public_info,
    mock_get_token,
    _mock_set_npm_token_env,
    _mock_get_local_file_tree,
    _mock_slack_notify,
    _mock_get_pull_request,
    mock_review_comment_payload,
):
    """Test that review run handler accumulates tokens from multiple chat_with_agent calls."""

    # Setup realistic mocks
    mock_get_token.return_value = "ghs_test_token"
    mock_get_user_public_info.return_value = type(
        "UserPublicInfo", (), {"email": "test@test.com", "display_name": "Test"}
    )()
    mock_get_repo.return_value = {"id": 98765, "trigger_on_review_comment": True}
    mock_create_user_request.return_value = 777  # This is the usage_id
    _mock_verify_task_is_ready.return_value = VerifyTaskIsReadyResult()
    mock_get_thread_comments.return_value = ReviewThreadResult(
        comments=[
            {
                "author": {"login": "test-reviewer"},
                "body": "This function could be optimized. Consider using a more efficient algorithm.",
                "createdAt": "2025-09-17T12:00:00Z",
            }
        ]
    )
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
            cost_usd=0.0,
        ),
    ]

    # Execute the function
    await handle_review_run(mock_review_comment_payload, trigger="pr_file_review")

    assert mock_chat_with_agent.call_count == 1

    # Verify execution call includes usage_id for API request tracking
    execution_call_kwargs = mock_chat_with_agent.call_args_list[0].kwargs
    assert execution_call_kwargs["usage_id"] == 777
    assert isinstance(execution_call_kwargs.get("system_message"), str)

    # Verify baseline_tsc_errors is set on base_args
    base_args = execution_call_kwargs["base_args"]
    assert isinstance(base_args.get("baseline_tsc_errors"), set)
    assert base_args["usage_id"] == 777

    # CRITICAL: Verify update_usage was called with accumulated tokens
    mock_update_usage.assert_called_once()
    usage_call_kwargs = mock_update_usage.call_args.kwargs

    assert usage_call_kwargs["usage_id"] == 777
    assert usage_call_kwargs["token_input"] == 120
    assert usage_call_kwargs["token_output"] == 80
    assert usage_call_kwargs["is_completed"] is True

    # Verify other expected parameters
    assert isinstance(usage_call_kwargs.get("total_seconds"), int)
    assert usage_call_kwargs["pr_number"] == 123
    mock_get_repo.assert_called_with(platform="github", owner_id=11111, repo_id=98765)


@patch("services.webhook.review_run_handler.get_pull_request")
@patch("services.webhook.review_run_handler.slack_notify")
@patch("services.webhook.review_run_handler.get_local_file_tree", return_value=[])
@patch("services.webhook.review_run_handler.set_npm_token_env")
@patch("services.webhook.review_run_handler.maybe_switch_to_free_model")
@patch("services.webhook.review_run_handler.verify_task_is_complete")
@patch("services.webhook.review_run_handler.get_installation_access_token")
@patch("services.webhook.review_run_handler.get_user_public_info")
@patch("services.webhook.review_run_handler.get_repository")
@patch("services.webhook.review_run_handler.create_user_request")
@patch("services.webhook.review_run_handler.get_review_thread_comments")
@patch("services.webhook.review_run_handler.reply_to_comment")
@patch(
    "services.webhook.review_run_handler.format_content_with_line_numbers",
    side_effect=lambda file_path, content: content,
)
@patch("services.webhook.review_run_handler.read_local_file")
@patch("services.webhook.review_run_handler.get_pull_request_files")
@patch("services.webhook.review_run_handler.update_comment")
@patch("services.webhook.review_run_handler.should_bail", return_value=False)
@patch("services.webhook.review_run_handler.chat_with_agent")
@patch("services.webhook.review_run_handler.create_empty_commit")
@patch("services.webhook.review_run_handler.get_reference", return_value="changed_sha")
@patch("services.webhook.review_run_handler.update_usage")
@patch("services.webhook.review_run_handler.ensure_node_packages")
@patch("services.webhook.review_run_handler.clone_repo_and_install_dependencies")
@patch(
    "services.webhook.review_run_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.review_run_handler.git_merge_base_into_pr")
@patch("services.webhook.review_run_handler.ensure_php_packages")
@patch(
    "services.webhook.review_run_handler.verify_task_is_ready", new_callable=AsyncMock
)
@patch("services.webhook.review_run_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]")
@patch("services.webhook.review_run_handler.MAX_ITERATIONS", 2)
@pytest.mark.asyncio
async def test_review_run_handler_max_iterations_forces_verification(
    _mock_verify_task_is_ready,
    _mock_ensure_php,
    _mock_get_behind,
    _mock_merge_base,
    _mock_prepare_repo,
    _mock_ensure_node_packages,
    _mock_update_usage,
    _mock_get_reference,
    _mock_create_empty_commit,
    mock_chat_with_agent,
    _mock_should_bail,
    mock_update_comment,
    mock_get_pr_files,
    mock_get_file_content,
    _mock_format,
    mock_reply_to_comment,
    mock_get_thread_comments,
    mock_create_user_request,
    mock_get_repo,
    mock_get_user_public_info,
    mock_get_token,
    mock_verify_task_is_complete,
    mock_maybe_switch,
    _mock_set_npm_token_env,
    _mock_get_local_file_tree,
    _mock_slack_notify,
    _mock_get_pull_request,
    mock_review_comment_payload,
):
    """Test that review run handler forces verify_task_is_complete when MAX_ITERATIONS is reached."""
    mock_maybe_switch.side_effect = lambda **kwargs: kwargs["model_id"]

    mock_get_token.return_value = "ghs_test_token"
    mock_get_user_public_info.return_value = type(
        "UserPublicInfo", (), {"email": "test@test.com", "display_name": "Test"}
    )()
    mock_get_repo.return_value = {"id": 98765, "trigger_on_review_comment": True}
    mock_create_user_request.return_value = 777
    _mock_verify_task_is_ready.return_value = VerifyTaskIsReadyResult()
    mock_get_thread_comments.return_value = ReviewThreadResult(
        comments=[
            {
                "author": {"login": "test-reviewer"},
                "body": "This function could be optimized.",
                "createdAt": "2025-09-17T12:00:00Z",
            }
        ]
    )
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
            cost_usd=0.0,
        ),
        AgentResult(
            messages=[{"role": "user", "content": "review"}],
            token_input=100,
            token_output=60,
            is_completed=False,
            completion_reason="",
            p=60,
            is_planned=False,
            cost_usd=0.0,
        ),
    ]

    await handle_review_run(mock_review_comment_payload, trigger="pr_file_review")

    assert mock_chat_with_agent.call_count == 2
    mock_verify_task_is_complete.assert_called_once()
    # Cost-cap policy: maybe_switch_to_free_model runs once per loop iteration before chat_with_agent.
    assert mock_maybe_switch.call_count == 2


@pytest.fixture
def mock_bot_review_comment_payload():
    """Review comment payload from a bot (e.g. Devin) on a GitAuto PR."""
    return {
        "action": "created",
        "comment": {
            "id": 99999,
            "node_id": "PRRC_kwBotReview",
            "path": "src/main.py",
            "subject_type": "line",
            "line": 10,
            "side": "RIGHT",
            "body": "This variable is unused and should be removed.",
            "user": {"login": "devin-ai[bot]", "type": "Bot"},
        },
        "pull_request": {
            "number": 456,
            "title": "Fix user login",
            "body": "Fixes login bug",
            "url": "https://api.github.com/repos/test-owner/test-repo/pulls/456",
            "user": {"login": "gitauto-ai[bot]"},
            "head": {
                "ref": f"{PRODUCT_ID}/dashboard-20250201-120000-Xy9Z",
                "sha": "def456abc789",
            },
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
            "id": 44444,
            "login": "devin-ai[bot]",
        },
        "installation": {
            "id": 33333,
        },
    }


@patch("services.webhook.review_run_handler.get_pull_request")
@patch("services.webhook.review_run_handler.slack_notify")
@patch("services.webhook.review_run_handler.get_local_file_tree", return_value=[])
@patch("services.webhook.review_run_handler.set_npm_token_env")
@patch("services.webhook.review_run_handler.get_installation_access_token")
@patch("services.webhook.review_run_handler.get_user_public_info")
@patch("services.webhook.review_run_handler.get_repository")
@patch("services.webhook.review_run_handler.create_user_request")
@patch("services.webhook.review_run_handler.get_review_thread_comments")
@patch("services.webhook.review_run_handler.reply_to_comment")
@patch(
    "services.webhook.review_run_handler.format_content_with_line_numbers",
    side_effect=lambda file_path, content: content,
)
@patch("services.webhook.review_run_handler.read_local_file")
@patch("services.webhook.review_run_handler.get_pull_request_files")
@patch("services.webhook.review_run_handler.update_comment")
@patch("services.webhook.review_run_handler.should_bail", return_value=False)
@patch("services.webhook.review_run_handler.chat_with_agent")
@patch("services.webhook.review_run_handler.create_empty_commit")
@patch("services.webhook.review_run_handler.get_reference", return_value="changed_sha")
@patch("services.webhook.review_run_handler.update_usage")
@patch("services.webhook.review_run_handler.ensure_node_packages")
@patch("services.webhook.review_run_handler.clone_repo_and_install_dependencies")
@patch(
    "services.webhook.review_run_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.review_run_handler.git_merge_base_into_pr")
@patch("services.webhook.review_run_handler.ensure_php_packages")
@patch(
    "services.webhook.review_run_handler.verify_task_is_ready", new_callable=AsyncMock
)
@patch("services.webhook.review_run_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]")
@pytest.mark.asyncio
async def test_thread_resolved_during_loop_stops_agent(
    _mock_verify_task_is_ready,
    _mock_ensure_php,
    _mock_get_behind,
    _mock_merge_base,
    _mock_prepare_repo,
    _mock_ensure_node,
    _mock_update_usage,
    _mock_get_reference,
    _mock_create_empty_commit,
    mock_chat_with_agent,
    _mock_should_bail,
    _mock_update_comment,
    mock_get_pr_files,
    mock_get_file_content,
    _mock_format,
    mock_reply_to_comment,
    mock_get_thread_comments,
    mock_create_user_request,
    mock_get_repo,
    mock_get_user_public_info,
    mock_get_token,
    _mock_set_npm_token_env,
    _mock_get_local_file_tree,
    _mock_slack_notify,
    _mock_get_pull_request,
    mock_review_comment_payload,
):
    """Thread resolved while agent is working should stop the loop before chat_with_agent."""
    mock_get_token.return_value = "ghs_test_token"
    mock_get_user_public_info.return_value = type(
        "UserPublicInfo", (), {"email": "test@test.com", "display_name": "Test"}
    )()
    mock_get_repo.return_value = {"id": 98765, "trigger_on_review_comment": True}
    mock_create_user_request.return_value = 777
    mock_reply_to_comment.return_value = "http://comment-url"
    mock_get_file_content.return_value = "def main():\n    pass"
    mock_get_pr_files.return_value = [{"filename": "src/main.py", "status": "modified"}]
    _mock_verify_task_is_ready.return_value = VerifyTaskIsReadyResult()
    # 1st call (pre-loop): not resolved, proceed
    # 2nd call (in-loop): resolved, stop before chat_with_agent
    mock_get_thread_comments.side_effect = [
        ReviewThreadResult(
            comments=[
                {
                    "author": {"login": "test-reviewer"},
                    "body": "Please fix this.",
                    "createdAt": "2025-09-17T12:00:00Z",
                }
            ],
            is_resolved=False,
        ),
        ReviewThreadResult(comments=[], is_resolved=True),
    ]

    await handle_review_run(mock_review_comment_payload, trigger="pr_file_review")

    # chat_with_agent should NOT be called because thread was resolved before it ran
    mock_chat_with_agent.assert_not_called()


@patch("services.webhook.review_run_handler.get_pull_request")
@patch("services.webhook.review_run_handler.slack_notify")
@patch("services.webhook.review_run_handler.get_local_file_tree", return_value=[])
@patch("services.webhook.review_run_handler.set_npm_token_env")
@patch("services.webhook.review_run_handler.get_installation_access_token")
@patch("services.webhook.review_run_handler.get_user_public_info")
@patch("services.webhook.review_run_handler.get_repository")
@patch("services.webhook.review_run_handler.create_user_request")
@patch("services.webhook.review_run_handler.get_review_thread_comments")
@patch("services.webhook.review_run_handler.reply_to_comment")
@patch(
    "services.webhook.review_run_handler.format_content_with_line_numbers",
    side_effect=lambda file_path, content: content,
)
@patch("services.webhook.review_run_handler.read_local_file")
@patch("services.webhook.review_run_handler.get_pull_request_files")
@patch("services.webhook.review_run_handler.update_comment")
@patch("services.webhook.review_run_handler.should_bail", return_value=False)
@patch("services.webhook.review_run_handler.chat_with_agent")
@patch("services.webhook.review_run_handler.create_empty_commit")
@patch("services.webhook.review_run_handler.get_reference", return_value="changed_sha")
@patch("services.webhook.review_run_handler.update_usage")
@patch("services.webhook.review_run_handler.ensure_node_packages")
@patch("services.webhook.review_run_handler.clone_repo_and_install_dependencies")
@patch(
    "services.webhook.review_run_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.review_run_handler.git_merge_base_into_pr")
@patch("services.webhook.review_run_handler.ensure_php_packages")
@patch(
    "services.webhook.review_run_handler.verify_task_is_ready", new_callable=AsyncMock
)
@patch("services.webhook.review_run_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]")
@pytest.mark.asyncio
async def test_bot_first_review_comment_is_processed(
    _mock_verify_task_is_ready,
    _mock_ensure_php,
    _mock_get_behind,
    _mock_merge_base,
    _mock_prepare_repo,
    _mock_ensure_node,
    _mock_update_usage,
    _mock_get_reference,
    _mock_create_empty_commit,
    mock_chat_with_agent,
    _mock_should_bail,
    _mock_update_comment,
    mock_get_pr_files,
    mock_get_file_content,
    _mock_format,
    mock_reply_to_comment,
    mock_get_thread_comments,
    mock_create_user_request,
    mock_get_repo,
    mock_get_user_public_info,
    mock_get_token,
    _mock_set_npm_token_env,
    _mock_get_local_file_tree,
    _mock_slack_notify,
    _mock_get_pull_request,
    mock_bot_review_comment_payload,
):
    """Bot's first review comment (no GitAuto reply in thread yet) should be processed."""
    mock_get_token.return_value = "ghs_test_token"
    mock_get_user_public_info.return_value = type(
        "UserPublicInfo", (), {"email": "bot@test.com", "display_name": "Devin"}
    )()
    mock_get_repo.return_value = {"id": 98765, "trigger_on_review_comment": True}
    mock_create_user_request.return_value = 777
    mock_reply_to_comment.return_value = "http://comment-url"
    mock_get_file_content.return_value = "def main():\n    pass"
    mock_get_pr_files.return_value = [{"filename": "src/main.py", "status": "modified"}]
    # Thread has only the bot's comment, no GitAuto reply yet
    mock_get_thread_comments.return_value = ReviewThreadResult(
        comments=[
            {
                "author": {"login": "devin-ai[bot]"},
                "body": "This variable is unused and should be removed.",
                "createdAt": "2025-09-17T12:00:00Z",
            }
        ]
    )

    _mock_verify_task_is_ready.return_value = VerifyTaskIsReadyResult()
    mock_chat_with_agent.return_value = AgentResult(
        messages=[{"role": "user", "content": "review"}],
        token_input=100,
        token_output=50,
        is_completed=True,
        completion_reason="Removed the unused variable as suggested.",
        p=40,
        is_planned=False,
        cost_usd=0.0,
    )

    await handle_review_run(mock_bot_review_comment_payload, trigger="pr_file_review")

    # chat_with_agent was called → handler processed the bot review
    mock_chat_with_agent.assert_called_once()
    # Bot gets a single reply (no progress updates) with the agent's explanation
    mock_reply_to_comment.assert_called()
    reply_body = mock_reply_to_comment.call_args_list[-1].kwargs.get("body", "")
    assert reply_body.count("Removed the unused variable") == 1


@patch("services.webhook.review_run_handler.set_npm_token_env")
@patch("services.webhook.review_run_handler.get_installation_access_token")
@patch("services.webhook.review_run_handler.get_user_public_info")
@patch("services.webhook.review_run_handler.get_review_thread_comments")
@patch("services.webhook.review_run_handler.chat_with_agent")
@patch("services.webhook.review_run_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]")
@pytest.mark.asyncio
async def test_resolved_thread_is_skipped(
    mock_chat_with_agent,
    mock_get_thread_comments,
    mock_get_user_public_info,
    mock_get_token,
    _mock_set_npm_token_env,
    mock_review_comment_payload,
):
    """Review comment on an already-resolved thread should be skipped entirely."""
    mock_get_token.return_value = "ghs_test_token"
    mock_get_user_public_info.return_value = type(
        "UserPublicInfo", (), {"email": "test@test.com", "display_name": "Test"}
    )()
    mock_get_thread_comments.return_value = ReviewThreadResult(
        comments=[
            {
                "author": {"login": "devin-ai[bot]"},
                "body": "This variable is unused.",
                "createdAt": "2025-09-17T12:00:00Z",
            },
        ],
        is_resolved=True,
    )

    await handle_review_run(mock_review_comment_payload, trigger="pr_file_review")

    # chat_with_agent should NOT be called → handler skipped the resolved thread
    mock_chat_with_agent.assert_not_called()


@patch("services.webhook.review_run_handler.set_npm_token_env")
@patch("services.webhook.review_run_handler.get_installation_access_token")
@patch("services.webhook.review_run_handler.get_user_public_info")
@patch("services.webhook.review_run_handler.get_review_thread_comments")
@patch("services.webhook.review_run_handler.chat_with_agent")
@patch("services.webhook.review_run_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]")
@pytest.mark.asyncio
async def test_bot_reply_after_gitauto_replied_is_skipped(
    mock_chat_with_agent,
    mock_get_thread_comments,
    mock_get_user_public_info,
    mock_get_token,
    _mock_set_npm_token_env,
    mock_bot_review_comment_payload,
):
    """Bot comment in a thread where GitAuto already replied should be skipped (loop prevention)."""
    mock_get_token.return_value = "ghs_test_token"
    mock_get_user_public_info.return_value = type(
        "UserPublicInfo", (), {"email": "bot@test.com", "display_name": "Devin"}
    )()
    # Thread already has a GitAuto reply → this bot comment is a back-and-forth
    mock_get_thread_comments.return_value = ReviewThreadResult(
        comments=[
            {
                "author": {"login": "devin-ai[bot]"},
                "body": "This variable is unused.",
                "createdAt": "2025-09-17T12:00:00Z",
            },
            {
                "author": {"login": "gitauto-ai[bot]"},
                "body": "Thanks for the review! I'm on it.",
                "createdAt": "2025-09-17T12:01:00Z",
            },
            {
                "author": {"login": "devin-ai[bot]"},
                "body": "Actually you also missed another issue.",
                "createdAt": "2025-09-17T12:02:00Z",
            },
        ]
    )

    await handle_review_run(mock_bot_review_comment_payload, trigger="pr_file_review")

    # chat_with_agent should NOT be called → handler skipped the loop
    mock_chat_with_agent.assert_not_called()


@patch("services.webhook.review_run_handler.get_pull_request")
@patch("services.webhook.review_run_handler.slack_notify")
@patch("services.webhook.review_run_handler.get_local_file_tree", return_value=[])
@patch("services.webhook.review_run_handler.set_npm_token_env")
@patch("services.webhook.review_run_handler.get_installation_access_token")
@patch("services.webhook.review_run_handler.get_user_public_info")
@patch("services.webhook.review_run_handler.get_repository")
@patch("services.webhook.review_run_handler.create_user_request")
@patch("services.webhook.review_run_handler.get_review_thread_comments")
@patch("services.webhook.review_run_handler.reply_to_comment")
@patch(
    "services.webhook.review_run_handler.format_content_with_line_numbers",
    side_effect=lambda file_path, content: content,
)
@patch("services.webhook.review_run_handler.read_local_file")
@patch("services.webhook.review_run_handler.get_pull_request_files")
@patch("services.webhook.review_run_handler.update_comment")
@patch("services.webhook.review_run_handler.should_bail", return_value=False)
@patch("services.webhook.review_run_handler.chat_with_agent")
@patch("services.webhook.review_run_handler.create_empty_commit")
@patch("services.webhook.review_run_handler.get_reference", return_value="changed_sha")
@patch("services.webhook.review_run_handler.update_usage")
@patch("services.webhook.review_run_handler.ensure_node_packages")
@patch("services.webhook.review_run_handler.clone_repo_and_install_dependencies")
@patch(
    "services.webhook.review_run_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.review_run_handler.git_merge_base_into_pr")
@patch("services.webhook.review_run_handler.ensure_php_packages")
@patch(
    "services.webhook.review_run_handler.verify_task_is_ready", new_callable=AsyncMock
)
@patch("services.webhook.review_run_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]")
@pytest.mark.asyncio
async def test_human_review_comment_always_processed(
    _mock_verify_task_is_ready,
    _mock_ensure_php,
    _mock_get_behind,
    _mock_merge_base,
    _mock_prepare_repo,
    _mock_ensure_node,
    _mock_update_usage,
    _mock_get_reference,
    _mock_create_empty_commit,
    mock_chat_with_agent,
    _mock_should_bail,
    _mock_update_comment,
    mock_get_pr_files,
    mock_get_file_content,
    _mock_format,
    mock_reply_to_comment,
    mock_get_thread_comments,
    mock_create_user_request,
    mock_get_repo,
    mock_get_user_public_info,
    mock_get_token,
    _mock_set_npm_token_env,
    _mock_get_local_file_tree,
    _mock_slack_notify,
    _mock_get_pull_request,
    mock_review_comment_payload,
):
    """Human review comment should always be processed, even if GitAuto already replied."""
    mock_get_token.return_value = "ghs_test_token"
    mock_get_user_public_info.return_value = type(
        "UserPublicInfo", (), {"email": "test@test.com", "display_name": "Test"}
    )()
    mock_get_repo.return_value = {"id": 98765, "trigger_on_review_comment": True}
    mock_create_user_request.return_value = 777
    mock_reply_to_comment.return_value = "http://comment-url"
    mock_get_file_content.return_value = "def main():\n    pass"
    mock_get_pr_files.return_value = [{"filename": "src/main.py", "status": "modified"}]
    _mock_verify_task_is_ready.return_value = VerifyTaskIsReadyResult()
    # Thread has a prior GitAuto reply, but commenter is human → always process
    mock_get_thread_comments.return_value = ReviewThreadResult(
        comments=[
            {
                "author": {"login": "test-reviewer"},
                "body": "First comment",
                "createdAt": "2025-09-17T12:00:00Z",
            },
            {
                "author": {"login": "gitauto-ai[bot]"},
                "body": "Fixed!",
                "createdAt": "2025-09-17T12:01:00Z",
            },
            {
                "author": {"login": "test-reviewer"},
                "body": "No, this is still wrong.",
                "createdAt": "2025-09-17T12:02:00Z",
            },
        ]
    )

    mock_chat_with_agent.return_value = AgentResult(
        messages=[{"role": "user", "content": "review"}],
        token_input=100,
        token_output=50,
        is_completed=True,
        completion_reason="Fixed the logic as requested.",
        p=40,
        is_planned=False,
        cost_usd=0.0,
    )

    await handle_review_run(mock_review_comment_payload, trigger="pr_file_review")

    # Human comment is always processed regardless of prior GitAuto replies
    mock_chat_with_agent.assert_called_once()
    # Human gets the agent's explanation via update_comment
    final_update_body = _mock_update_comment.call_args_list[-1].kwargs.get("body", "")
    assert final_update_body.count("Fixed the logic") == 1


@pytest.fixture
def mock_pr_comment_payload():
    """PR comment payload (adapted from issue_comment via adapt_pr_comment_to_review_payload)."""
    return {
        "action": "created",
        "comment": {
            "id": 55555,
            "node_id": "IC_55555",
            "body": "you didn't complete the task",
            "user": {"login": "test-reviewer", "type": "User"},
            "path": "",
            "subject_type": "pr_comment",
            "line": 0,
            "side": "",
        },
        "pull_request": {
            "number": 789,
            "title": "Fix login bug",
            "body": "Fixes the login issue",
            "url": "https://api.github.com/repos/test-owner/test-repo/pulls/789",
            "user": {"login": "gitauto-ai[bot]"},
            "head": {
                "ref": f"{PRODUCT_ID}/dashboard-20250301-100000-Zz1A",
                "sha": "fff999aaa111",
            },
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
            "login": "test-reviewer",
        },
        "installation": {
            "id": 33333,
        },
    }


@patch("services.webhook.review_run_handler.get_pull_request")
@patch("services.webhook.review_run_handler.slack_notify")
@patch("services.webhook.review_run_handler.get_local_file_tree", return_value=[])
@patch("services.webhook.review_run_handler.set_npm_token_env")
@patch("services.webhook.review_run_handler.get_installation_access_token")
@patch("services.webhook.review_run_handler.get_user_public_info")
@patch("services.webhook.review_run_handler.get_repository")
@patch("services.webhook.review_run_handler.create_user_request")
@patch("services.webhook.review_run_handler.get_review_thread_comments")
@patch("services.webhook.review_run_handler.reply_to_comment")
@patch("services.webhook.review_run_handler.create_comment")
@patch(
    "services.webhook.review_run_handler.format_content_with_line_numbers",
    side_effect=lambda file_path, content: content,
)
@patch("services.webhook.review_run_handler.read_local_file")
@patch("services.webhook.review_run_handler.get_pull_request_files")
@patch("services.webhook.review_run_handler.update_comment")
@patch("services.webhook.review_run_handler.should_bail", return_value=False)
@patch("services.webhook.review_run_handler.chat_with_agent")
@patch("services.webhook.review_run_handler.create_empty_commit")
@patch("services.webhook.review_run_handler.get_reference", return_value="changed_sha")
@patch("services.webhook.review_run_handler.update_usage")
@patch("services.webhook.review_run_handler.ensure_node_packages")
@patch("services.webhook.review_run_handler.clone_repo_and_install_dependencies")
@patch(
    "services.webhook.review_run_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.review_run_handler.git_merge_base_into_pr")
@patch("services.webhook.review_run_handler.ensure_php_packages")
@patch(
    "services.webhook.review_run_handler.verify_task_is_ready", new_callable=AsyncMock
)
@patch("services.webhook.review_run_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]")
@pytest.mark.asyncio
async def test_pr_comment_uses_create_comment_not_reply(
    _mock_verify_task_is_ready,
    _mock_ensure_php,
    _mock_get_behind,
    _mock_merge_base,
    _mock_prepare_repo,
    _mock_ensure_node,
    _mock_update_usage,
    _mock_get_reference,
    _mock_create_empty_commit,
    mock_chat_with_agent,
    _mock_should_bail,
    _mock_update_comment,
    mock_get_pr_files,
    _mock_get_file_content,
    _mock_format,
    mock_create_comment,
    mock_reply_to_comment,
    mock_get_thread_comments,
    mock_create_user_request,
    mock_get_repo,
    mock_get_user_public_info,
    mock_get_token,
    _mock_set_npm_token_env,
    _mock_get_local_file_tree,
    _mock_slack_notify,
    _mock_get_pull_request,
    mock_pr_comment_payload,
):
    """PR comment (no review_path) should use create_comment, not reply_to_comment, and skip thread checks."""
    mock_get_token.return_value = "ghs_test_token"
    mock_get_user_public_info.return_value = type(
        "UserPublicInfo", (), {"email": "test@test.com", "display_name": "Test"}
    )()
    mock_get_repo.return_value = {"id": 98765, "trigger_on_review_comment": True}
    mock_create_user_request.return_value = 777
    mock_create_comment.return_value = "http://new-comment-url"
    mock_get_pr_files.return_value = [{"filename": "src/main.py", "status": "modified"}]
    _mock_verify_task_is_ready.return_value = VerifyTaskIsReadyResult()

    mock_chat_with_agent.return_value = AgentResult(
        messages=[{"role": "user", "content": "review"}],
        token_input=100,
        token_output=50,
        is_completed=True,
        completion_reason="Completed the task as requested.",
        p=40,
        is_planned=False,
        cost_usd=0.0,
    )

    await handle_review_run(mock_pr_comment_payload, trigger="pr_comment")

    # create_comment used for greeting (not reply_to_comment)
    mock_create_comment.assert_called()
    greeting_body = mock_create_comment.call_args_list[0].kwargs.get("body", "")
    assert greeting_body.count("Re:") == 1
    assert greeting_body.count("comment") >= 1

    # reply_to_comment NOT used for greeting
    mock_reply_to_comment.assert_not_called()

    # get_review_thread_comments NOT called (no thread for PR comments)
    mock_get_thread_comments.assert_not_called()

    # read_local_file NOT called (no review_path)
    _mock_get_file_content.assert_not_called()

    # Agent was called
    mock_chat_with_agent.assert_called_once()


@pytest.mark.skip(
    reason="Integration test - calls real Claude API, costs money. Run manually to verify."
)
@patch("services.webhook.review_run_handler.get_pull_request")
@patch("services.webhook.review_run_handler.slack_notify")
@patch("services.webhook.review_run_handler.get_local_file_tree", return_value=[])
@patch("services.webhook.review_run_handler.set_npm_token_env")
@patch("services.webhook.review_run_handler.get_installation_access_token")
@patch("services.webhook.review_run_handler.get_user_public_info")
@patch("services.webhook.review_run_handler.get_repository")
@patch("services.webhook.review_run_handler.create_user_request")
@patch("services.webhook.review_run_handler.get_review_thread_comments")
@patch("services.webhook.review_run_handler.reply_to_comment")
@patch("services.webhook.review_run_handler.create_comment")
@patch(
    "services.webhook.review_run_handler.format_content_with_line_numbers",
    side_effect=lambda file_path, content: content,
)
@patch("services.webhook.review_run_handler.read_local_file")
@patch("services.webhook.review_run_handler.get_pull_request_files")
@patch("services.webhook.review_run_handler.update_comment")
@patch("services.webhook.review_run_handler.should_bail", return_value=False)
@patch("services.webhook.review_run_handler.create_empty_commit")
@patch("services.webhook.review_run_handler.get_reference")
@patch("services.webhook.review_run_handler.update_usage")
@patch("services.webhook.review_run_handler.ensure_node_packages")
@patch("services.webhook.review_run_handler.clone_repo_and_install_dependencies")
@patch(
    "services.webhook.review_run_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.review_run_handler.git_merge_base_into_pr")
@patch("services.webhook.review_run_handler.ensure_php_packages")
@patch(
    "services.webhook.review_run_handler.verify_task_is_ready", new_callable=AsyncMock
)
@patch("services.claude.tools.tools.tools_to_call")
@patch("services.webhook.review_run_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]")
@pytest.mark.asyncio
async def test_question_comment_agent_replies_without_code_changes(
    _mock_tools_to_call,
    _mock_verify_task_is_ready,
    _mock_ensure_php,
    _mock_get_behind,
    _mock_merge_base,
    _mock_prepare_repo,
    _mock_ensure_node,
    _mock_update_usage,
    mock_get_reference,
    mock_create_empty_commit,
    _mock_should_bail,
    _mock_update_comment,
    mock_get_pr_files,
    _mock_get_file_content,
    _mock_format,
    mock_create_comment,
    mock_reply_to_comment,
    mock_get_thread_comments,
    mock_create_user_request,
    mock_get_repo,
    mock_get_user_public_info,
    mock_get_token,
    _mock_set_npm_token_env,
    _mock_get_local_file_tree,
    _mock_slack_notify,
    _mock_get_pull_request,
    mock_pr_comment_payload,
):
    """Integration test: real Claude call for a question comment. Agent should just reply, no code changes."""
    mock_pr_comment_payload["comment"][
        "body"
    ] = "Why did you use a dictionary here instead of a dataclass?"
    mock_get_token.return_value = "ghs_test_token"
    mock_get_user_public_info.return_value = type(
        "UserPublicInfo", (), {"email": "test@test.com", "display_name": "Test"}
    )()
    mock_get_repo.return_value = {"id": 98765, "trigger_on_review_comment": True}
    mock_create_user_request.return_value = 777
    mock_create_comment.return_value = "http://new-comment-url"
    mock_get_pr_files.return_value = [{"filename": "src/main.py", "status": "modified"}]
    _mock_verify_task_is_ready.return_value = VerifyTaskIsReadyResult()
    # HEAD SHA unchanged = agent made no commits
    mock_get_reference.return_value = "fff999aaa111"

    # Mock tools_to_call so Claude's tool calls don't hit real APIs
    mock_verify = AsyncMock(
        return_value=VerifyTaskIsCompleteResult(
            success=True, message="Task completed. No changes were needed."
        )
    )
    _mock_tools_to_call.__getitem__ = lambda self, key: (
        mock_verify if key == "verify_task_is_complete" else lambda **kwargs: "mocked"
    )
    _mock_tools_to_call.__contains__ = lambda self, key: True

    await handle_review_run(mock_pr_comment_payload, trigger="pr_comment")

    # Final reply posted via create_comment (PR comment, not inline review)
    final_calls = mock_create_comment.call_args_list
    assert len(final_calls) >= 1
    # At least one call should contain the agent's explanation
    all_bodies = " ".join(c.kwargs.get("body", "") for c in final_calls)
    assert len(all_bodies) > 50  # Agent wrote a real explanation

    # reply_to_comment NOT used (PR comment path)
    mock_reply_to_comment.assert_not_called()

    # Empty commit NOT created (agent just replied, no code changes)
    mock_create_empty_commit.assert_not_called()


@pytest.fixture
def mock_bot_pr_comment_payload():
    """Bot PR-level comment payload (no file path, from a bot like github-actions)."""
    return {
        "action": "created",
        "comment": {
            "id": 66666,
            "node_id": "IC_66666",
            "body": (FIXTURES_DIR / "security_hub_comment.txt").read_text(),
            "user": {"login": "github-actions[bot]", "type": "Bot"},
            "path": "",
            "subject_type": "pr_comment",
            "line": 0,
            "side": "",
        },
        "pull_request": {
            "number": 85,
            "title": "Low Test Coverage: rates.go",
            "body": "Adds tests for rates.go",
            "url": "https://api.github.com/repos/test-owner/test-repo/pulls/85",
            "user": {"login": "gitauto-ai[bot]"},
            "head": {
                "ref": f"{PRODUCT_ID}/coverage-20250101-Ab1C",
                "sha": "aaa111bbb222",
            },
            "base": {"ref": "develop"},
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
            "id": 55555,
            "login": "github-actions[bot]",
        },
        "installation": {
            "id": 33333,
        },
    }


@patch("services.webhook.review_run_handler.set_npm_token_env")
@patch("services.webhook.review_run_handler.get_installation_access_token")
@patch("services.webhook.review_run_handler.get_user_public_info")
@patch("services.webhook.review_run_handler.get_pull_request_files")
@patch("services.webhook.review_run_handler.chat_with_agent")
@patch("services.webhook.review_run_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]")
@pytest.mark.asyncio
async def test_bot_pr_comment_irrelevant_to_pr_files_is_skipped(
    mock_chat_with_agent,
    mock_get_pr_files,
    mock_get_user_public_info,
    mock_get_token,
    _mock_set_npm_token_env,
    mock_bot_pr_comment_payload,
):
    """Bot PR-level comment that doesn't mention any PR file paths should be skipped."""
    mock_get_token.return_value = "ghs_test_token"
    mock_get_user_public_info.return_value = type(
        "UserPublicInfo", (), {"email": "bot@test.com", "display_name": "GH Actions"}
    )()
    mock_get_pr_files.return_value = [
        {"filename": "internal/models/core/rates_test.go", "status": "added"},
    ]

    await handle_review_run(mock_bot_pr_comment_payload, trigger="pr_comment")

    mock_chat_with_agent.assert_not_called()


@patch("services.webhook.review_run_handler.get_pull_request")
@patch("services.webhook.review_run_handler.slack_notify")
@patch("services.webhook.review_run_handler.get_local_file_tree", return_value=[])
@patch("services.webhook.review_run_handler.set_npm_token_env")
@patch("services.webhook.review_run_handler.get_installation_access_token")
@patch("services.webhook.review_run_handler.get_user_public_info")
@patch("services.webhook.review_run_handler.get_repository")
@patch("services.webhook.review_run_handler.create_user_request")
@patch("services.webhook.review_run_handler.get_review_thread_comments")
@patch("services.webhook.review_run_handler.reply_to_comment")
@patch("services.webhook.review_run_handler.create_comment")
@patch(
    "services.webhook.review_run_handler.format_content_with_line_numbers",
    side_effect=lambda file_path, content: content,
)
@patch("services.webhook.review_run_handler.read_local_file")
@patch("services.webhook.review_run_handler.get_pull_request_files")
@patch("services.webhook.review_run_handler.update_comment")
@patch("services.webhook.review_run_handler.should_bail", return_value=False)
@patch("services.webhook.review_run_handler.chat_with_agent")
@patch("services.webhook.review_run_handler.create_empty_commit")
@patch("services.webhook.review_run_handler.get_reference", return_value="changed_sha")
@patch("services.webhook.review_run_handler.update_usage")
@patch("services.webhook.review_run_handler.ensure_node_packages")
@patch("services.webhook.review_run_handler.clone_repo_and_install_dependencies")
@patch(
    "services.webhook.review_run_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.review_run_handler.git_merge_base_into_pr")
@patch("services.webhook.review_run_handler.ensure_php_packages")
@patch(
    "services.webhook.review_run_handler.verify_task_is_ready", new_callable=AsyncMock
)
@patch("services.webhook.review_run_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]")
@pytest.mark.asyncio
async def test_bot_pr_comment_mentioning_pr_file_is_processed(
    _mock_verify_task_is_ready,
    _mock_ensure_php,
    _mock_get_behind,
    _mock_merge_base,
    _mock_prepare_repo,
    _mock_ensure_node,
    _mock_update_usage,
    _mock_get_reference,
    _mock_create_empty_commit,
    mock_chat_with_agent,
    _mock_should_bail,
    _mock_update_comment,
    mock_get_pr_files,
    _mock_get_file_content,
    _mock_format,
    mock_create_comment,
    mock_reply_to_comment,
    mock_get_thread_comments,
    mock_create_user_request,
    mock_get_repo,
    mock_get_user_public_info,
    mock_get_token,
    _mock_set_npm_token_env,
    _mock_get_local_file_tree,
    _mock_slack_notify,
    _mock_get_pull_request,
    mock_bot_pr_comment_payload,
):
    """Bot PR-level comment that mentions a PR file path should be processed."""
    mock_bot_pr_comment_payload["comment"][
        "body"
    ] = "Lint error in internal/models/core/rates_test.go"
    mock_get_token.return_value = "ghs_test_token"
    mock_get_user_public_info.return_value = type(
        "UserPublicInfo", (), {"email": "bot@test.com", "display_name": "GH Actions"}
    )()
    mock_get_repo.return_value = {"id": 98765, "trigger_on_review_comment": True}
    mock_create_user_request.return_value = 777
    mock_create_comment.return_value = "http://new-comment-url"
    mock_get_pr_files.return_value = [
        {"filename": "internal/models/core/rates_test.go", "status": "added"},
    ]
    _mock_verify_task_is_ready.return_value = VerifyTaskIsReadyResult()

    mock_chat_with_agent.return_value = AgentResult(
        messages=[{"role": "user", "content": "review"}],
        token_input=100,
        token_output=50,
        is_completed=True,
        completion_reason="Addressed the lint error.",
        p=40,
        is_planned=False,
        cost_usd=0.0,
    )

    await handle_review_run(mock_bot_pr_comment_payload, trigger="pr_comment")

    mock_chat_with_agent.assert_called_once()


@pytest.fixture
def mock_batched_review_payload():
    """Payload for a review comment that has a pull_request_review_id (part of a multi-comment review)."""
    return {
        "action": "created",
        "comment": {
            "id": 12345,
            "node_id": "PRRC_kwDOJTestNodeId",
            "path": "src/main.py",
            "subject_type": "line",
            "line": 42,
            "side": "RIGHT",
            "body": "Fix this function.",
            "user": {"login": "test-reviewer", "type": "User"},
            "pull_request_review_id": 77777,
        },
        "pull_request": {
            "number": 123,
            "title": "Add new feature",
            "body": "This PR adds a new feature",
            "url": "https://api.github.com/repos/test-owner/test-repo/pulls/123",
            "user": {"login": "gitauto-ai[bot]"},
            "head": {
                "ref": f"{PRODUCT_ID}/dashboard-20250101-155924-Ab1C",
                "sha": "abc123def456",
            },
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
        "sender": {"id": 22222, "login": "test-reviewer"},
        "installation": {"id": 33333},
    }


@patch(
    "services.webhook.review_run_handler.insert_webhook_delivery", return_value=False
)
@patch("services.webhook.review_run_handler.get_review_summary_comment")
@patch("services.webhook.review_run_handler.set_npm_token_env")
@patch("services.webhook.review_run_handler.get_installation_access_token")
@patch("services.webhook.review_run_handler.get_user_public_info")
@patch("services.webhook.review_run_handler.get_repository")
@patch("services.webhook.review_run_handler.check_purchase_exists")
@patch("services.webhook.review_run_handler.get_email_from_commits")
@patch("services.webhook.review_run_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]")
@pytest.mark.asyncio
async def test_batch_dedup_second_invocation_returns_early(
    _mock_get_email,
    _mock_check_purchase,
    mock_get_repo,
    mock_get_user_public_info,
    mock_get_token,
    _mock_set_npm_token_env,
    _mock_get_review_summary_comment,
    mock_insert_webhook_delivery,
    mock_batched_review_payload,
):
    """Second invocation for same review_id should return early (insert_webhook_delivery returns False)."""
    mock_get_token.return_value = "ghs_test_token"
    mock_get_user_public_info.return_value = type(
        "UserPublicInfo", (), {"email": "test@test.com", "display_name": "Test"}
    )()
    mock_get_repo.return_value = {"id": 98765, "trigger_on_review_comment": True}

    result = await handle_review_run(
        mock_batched_review_payload, trigger="pr_file_review"
    )

    assert result is None
    mock_insert_webhook_delivery.assert_called_once_with(
        platform="github",
        delivery_id="review-dedup-98765-123-77777",
        event_name="pr_file_review_dedup",
    )


@patch("services.webhook.review_run_handler.get_pull_request")
@patch("services.webhook.review_run_handler.slack_notify")
@patch("services.webhook.review_run_handler.get_local_file_tree", return_value=[])
@patch("services.webhook.review_run_handler.set_npm_token_env")
@patch("services.webhook.review_run_handler.get_installation_access_token")
@patch("services.webhook.review_run_handler.get_user_public_info")
@patch("services.webhook.review_run_handler.get_repository")
@patch("services.webhook.review_run_handler.create_user_request")
@patch("services.webhook.review_run_handler.get_review_thread_comments")
@patch("services.webhook.review_run_handler.reply_to_comment")
@patch(
    "services.webhook.review_run_handler.format_content_with_line_numbers",
    side_effect=lambda file_path, content: content,
)
@patch("services.webhook.review_run_handler.read_local_file")
@patch("services.webhook.review_run_handler.get_pull_request_files")
@patch("services.webhook.review_run_handler.update_comment")
@patch("services.webhook.review_run_handler.should_bail", return_value=False)
@patch("services.webhook.review_run_handler.chat_with_agent")
@patch("services.webhook.review_run_handler.create_empty_commit")
@patch("services.webhook.review_run_handler.get_reference", return_value="changed_sha")
@patch("services.webhook.review_run_handler.update_usage")
@patch("services.webhook.review_run_handler.ensure_node_packages")
@patch("services.webhook.review_run_handler.clone_repo_and_install_dependencies")
@patch(
    "services.webhook.review_run_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.review_run_handler.git_merge_base_into_pr")
@patch("services.webhook.review_run_handler.ensure_php_packages")
@patch(
    "services.webhook.review_run_handler.verify_task_is_ready", new_callable=AsyncMock
)
@patch("services.webhook.review_run_handler.insert_webhook_delivery", return_value=True)
@patch("services.webhook.review_run_handler.get_review_inline_comments")
@patch(
    "services.webhook.review_run_handler.get_review_summary_comment", return_value=""
)
@patch("services.webhook.review_run_handler.check_purchase_exists")
@patch("services.webhook.review_run_handler.get_email_from_commits")
@patch("services.webhook.review_run_handler.time")
@patch("services.webhook.review_run_handler.get_pr_comments", return_value=[])
@patch("services.webhook.review_run_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]")
@pytest.mark.asyncio
async def test_batch_builds_combined_review_comment(
    _mock_get_pr_comments,
    mock_time,
    _mock_get_email,
    _mock_check_purchase,
    _mock_get_review_summary_comment,
    mock_get_review_inline_comments,
    _mock_insert_webhook_delivery,
    _mock_verify_task_is_ready,
    _mock_ensure_php,
    _mock_merge_base,
    _mock_get_behind,
    _mock_prepare_repo,
    _mock_ensure_node,
    _mock_update_usage,
    _mock_get_reference,
    _mock_create_empty_commit,
    mock_chat_with_agent,
    _mock_should_bail,
    _mock_update_comment,
    mock_get_pr_files,
    mock_get_file_content,
    _mock_format,
    mock_reply_to_comment,
    _mock_get_thread_comments,
    mock_create_user_request,
    mock_get_repo,
    mock_get_user_public_info,
    mock_get_token,
    _mock_set_npm_token_env,
    _mock_get_local_file_tree,
    _mock_slack_notify,
    _mock_get_pull_request,
    mock_batched_review_payload,
):
    """When batched, review_comment should combine all inline comments from the review."""
    mock_time.time.return_value = 1000.0
    mock_time.sleep = lambda x: None
    mock_get_token.return_value = "ghs_test_token"
    mock_get_user_public_info.return_value = type(
        "UserPublicInfo", (), {"email": "test@test.com", "display_name": "Test"}
    )()
    mock_get_repo.return_value = {"id": 98765, "trigger_on_review_comment": True}
    mock_create_user_request.return_value = 777
    _mock_verify_task_is_ready.return_value = VerifyTaskIsReadyResult()
    mock_reply_to_comment.return_value = "http://comment-url"
    mock_get_file_content.return_value = "def main():\n    pass"
    mock_get_pr_files.return_value = [{"filename": "src/main.py", "status": "modified"}]

    # Return 3 inline comments for the review
    mock_get_review_inline_comments.return_value = [
        {"id": 1, "body": "Fix this", "path": "src/main.py", "line": 10},
        {"id": 2, "body": "Rename var", "path": "src/main.py", "line": 20},
        {"id": 3, "body": "Add test", "path": "src/utils.py", "line": 5},
    ]

    _mock_get_thread_comments.return_value = type(
        "ThreadCheck", (), {"is_resolved": False}
    )()

    mock_chat_with_agent.return_value = AgentResult(
        messages=[{"role": "user", "content": "review"}],
        token_input=100,
        token_output=50,
        is_completed=True,
        completion_reason="Done.",
        p=40,
        is_planned=False,
        cost_usd=0.0,
    )

    await handle_review_run(mock_batched_review_payload, trigger="pr_file_review")

    mock_chat_with_agent.assert_called_once()
    call_kwargs = mock_chat_with_agent.call_args.kwargs
    base_args = call_kwargs["base_args"]
    review_comment = base_args["review_comment"]
    # Verify combined comment structure
    assert review_comment.count("3 inline comments") == 1
    assert review_comment.count("Comment 1:") == 1
    assert review_comment.count("Comment 2:") == 1
    assert review_comment.count("Comment 3:") == 1
    assert review_comment.count("Fix this") == 1
    assert review_comment.count("Rename var") == 1
    assert review_comment.count("Add test") == 1
    # Verify file content was read for both unique paths
    assert mock_get_file_content.call_count == 2


@patch("services.webhook.review_run_handler.refresh_mongodb_cache")
@patch("services.webhook.review_run_handler.get_pull_request")
@patch("services.webhook.review_run_handler.slack_notify")
@patch("services.webhook.review_run_handler.get_local_file_tree", return_value=[])
@patch("services.webhook.review_run_handler.set_npm_token_env")
@patch("services.webhook.review_run_handler.get_installation_access_token")
@patch("services.webhook.review_run_handler.get_user_public_info")
@patch("services.webhook.review_run_handler.get_repository")
@patch("services.webhook.review_run_handler.create_user_request")
@patch("services.webhook.review_run_handler.get_review_thread_comments")
@patch("services.webhook.review_run_handler.reply_to_comment")
@patch(
    "services.webhook.review_run_handler.format_content_with_line_numbers",
    side_effect=lambda file_path, content: content,
)
@patch("services.webhook.review_run_handler.read_local_file")
@patch("services.webhook.review_run_handler.get_pull_request_files")
@patch("services.webhook.review_run_handler.update_comment")
@patch("services.webhook.review_run_handler.should_bail", return_value=False)
@patch("services.webhook.review_run_handler.chat_with_agent")
@patch("services.webhook.review_run_handler.create_empty_commit")
@patch("services.webhook.review_run_handler.get_reference", return_value="changed_sha")
@patch("services.webhook.review_run_handler.update_usage")
@patch("services.webhook.review_run_handler.ensure_node_packages")
@patch("services.webhook.review_run_handler.clone_repo_and_install_dependencies")
@patch(
    "services.webhook.review_run_handler.get_head_commit_count_behind_base",
    return_value=0,
)
@patch("services.webhook.review_run_handler.git_merge_base_into_pr")
@patch("services.webhook.review_run_handler.ensure_php_packages")
@patch(
    "services.webhook.review_run_handler.verify_task_is_ready", new_callable=AsyncMock
)
@patch("services.webhook.review_run_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]")
@pytest.mark.asyncio
async def test_review_run_handler_returns_none_on_stale_pr_branch(
    _mock_verify_task_is_ready,
    _mock_ensure_php,
    _mock_get_behind,
    _mock_merge_base,
    mock_prepare_repo,
    _mock_ensure_node_packages,
    _mock_update_usage,
    _mock_get_reference,
    _mock_create_empty_commit,
    mock_chat_with_agent,
    _mock_should_bail,
    _mock_update_comment,
    mock_get_pr_files,
    mock_get_file_content,
    _mock_format,
    mock_reply_to_comment,
    mock_get_thread_comments,
    mock_create_user_request,
    mock_get_repo,
    mock_get_user_public_info,
    mock_get_token,
    _mock_set_npm_token_env,
    _mock_get_local_file_tree,
    _mock_slack_notify,
    _mock_get_pull_request,
    mock_refresh_mongodb,
    mock_review_comment_payload,
):
    """Sentry AGENT-3KB cascade in review_run_handler shape: when the PR branch was deleted before the webhook landed, clone_repo_and_install_dependencies now returns False. The handler must short-circuit BEFORE chat_with_agent or any other downstream work — that's how we keep AGENT-3KC/3KD-style cascades from firing."""
    mock_get_token.return_value = "ghs_test_token"
    mock_get_user_public_info.return_value = type(
        "UserPublicInfo", (), {"email": "test@test.com", "display_name": "Test"}
    )()
    mock_get_repo.return_value = {"id": 98765, "trigger_on_review_comment": True}
    mock_create_user_request.return_value = 777
    _mock_verify_task_is_ready.return_value = VerifyTaskIsReadyResult()
    mock_get_thread_comments.return_value = ReviewThreadResult(
        comments=[
            {
                "author": {"login": "test-reviewer"},
                "body": "Could you optimize this loop?",
                "createdAt": "2025-09-17T12:00:00Z",
            }
        ]
    )
    mock_reply_to_comment.return_value = "http://comment-url"
    mock_get_file_content.return_value = "def main():\n    pass"
    mock_get_pr_files.return_value = [{"filename": "src/main.py", "status": "modified"}]
    mock_prepare_repo.return_value = False

    result = await handle_review_run(
        mock_review_comment_payload, trigger="pr_file_review"
    )

    assert result is None
    mock_prepare_repo.assert_called_once()
    # Critical: nothing downstream of clone runs.
    mock_chat_with_agent.assert_not_called()
    mock_refresh_mongodb.assert_not_called()


def test_agent_result_concurrent_push_field_defaults_false_review_run():
    """review_run handler breaks its agent loop + skips final empty commit when
    AgentResult.concurrent_push_detected is True. Verify the new field exists
    and defaults to False so existing AgentResult(...) construction stays valid."""
    result = AgentResult(
        messages=[],
        token_input=0,
        token_output=0,
        is_completed=False,
        completion_reason="",
        p=0,
        is_planned=False,
        cost_usd=0.0,
    )
    assert result.concurrent_push_detected is False

    raced = AgentResult(
        messages=[],
        token_input=0,
        token_output=0,
        is_completed=False,
        completion_reason="",
        p=0,
        is_planned=False,
        cost_usd=0.0,
        concurrent_push_detected=True,
    )
    assert raced.concurrent_push_detected is True
