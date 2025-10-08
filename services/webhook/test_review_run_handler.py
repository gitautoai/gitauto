from unittest.mock import MagicMock, patch

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
            "login": "test-reviewer",
        },
        "installation": {
            "id": 33333,
        },
    }


@pytest.fixture
def mock_dependencies():
    """Fixture to mock all external dependencies."""
    with patch("services.webhook.review_run_handler.get_installation_access_token") as mock_token, \
         patch("services.webhook.review_run_handler.get_repository") as mock_repo, \
         patch("services.webhook.review_run_handler.create_user_request") as mock_user_req, \
         patch("services.webhook.review_run_handler.get_review_thread_comments") as mock_thread, \
         patch("services.webhook.review_run_handler.reply_to_comment") as mock_reply, \
         patch("services.webhook.review_run_handler.get_remote_file_content") as mock_file, \
         patch("services.webhook.review_run_handler.get_pull_request_files") as mock_pr_files, \
         patch("services.webhook.review_run_handler.update_comment") as mock_update, \
         patch("services.webhook.review_run_handler.is_pull_request_open") as mock_pr_open, \
         patch("services.webhook.review_run_handler.check_branch_exists") as mock_branch, \
         patch("services.webhook.review_run_handler.is_lambda_timeout_approaching") as mock_timeout, \
         patch("services.webhook.review_run_handler.chat_with_agent") as mock_chat, \
         patch("services.webhook.review_run_handler.create_empty_commit") as mock_commit, \
         patch("services.webhook.review_run_handler.update_usage") as mock_usage, \
         patch("services.webhook.review_run_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]"):

        mock_token.return_value = "ghs_test_token"
        mock_repo.return_value = {"id": 98765}
        mock_user_req.return_value = 777
        mock_reply.return_value = "http://comment-url"
        mock_file.return_value = "def main():\n    pass"
        mock_pr_files.return_value = [{"filename": "src/main.py", "status": "modified"}]
        mock_pr_open.return_value = True
        mock_branch.return_value = True
        mock_timeout.return_value = (False, 0)

        yield {
            "token": mock_token,
            "repo": mock_repo,
            "user_req": mock_user_req,
            "thread": mock_thread,
            "reply": mock_reply,
            "file": mock_file,
            "pr_files": mock_pr_files,
            "update": mock_update,
            "pr_open": mock_pr_open,
            "branch": mock_branch,
            "timeout": mock_timeout,
            "chat": mock_chat,
            "commit": mock_commit,
            "usage": mock_usage,
        }


def test_early_return_when_pull_user_not_gitauto(mock_review_comment_payload, mock_dependencies):
    """Test early return when PR user is not GitAuto (line 74)."""
    payload = mock_review_comment_payload.copy()
    payload["pull_request"]["user"]["login"] = "some-other-user"

    result = handle_review_run(payload)

    assert result is None
    mock_dependencies["token"].assert_not_called()


def test_early_return_when_sender_is_gitauto(mock_review_comment_payload, mock_dependencies):
    """Test early return when sender is GitAuto itself (line 80)."""
    payload = mock_review_comment_payload.copy()
    payload["sender"]["login"] = "gitauto-ai[bot]"

    result = handle_review_run(payload)

    assert result is None
    mock_dependencies["thread"].assert_not_called()


def test_fallback_to_single_comment_when_thread_empty(mock_review_comment_payload, mock_dependencies):
    """Test fallback to single comment when thread fetch returns empty (line 105)."""
    mock_dependencies["thread"].return_value = []
    mock_dependencies["chat"].side_effect = [
        ([{"role": "user", "content": "test"}], [], "tool", {}, 100, 50, False, 40),
        ([{"role": "user", "content": "test"}], [], "tool", {}, 100, 50, False, 50),
    ]

    handle_review_run(mock_review_comment_payload)

    mock_dependencies["thread"].assert_called_once()
    mock_dependencies["chat"].assert_called()


def test_fallback_to_single_comment_when_thread_none(mock_review_comment_payload, mock_dependencies):
    """Test fallback to single comment when thread fetch returns None (line 105)."""
    mock_dependencies["thread"].return_value = None
    mock_dependencies["chat"].side_effect = [
        ([{"role": "user", "content": "test"}], [], "tool", {}, 100, 50, False, 40),
        ([{"role": "user", "content": "test"}], [], "tool", {}, 100, 50, False, 50),
    ]

    handle_review_run(mock_review_comment_payload)

    mock_dependencies["thread"].assert_called_once()
    mock_dependencies["chat"].assert_called()


def test_timeout_approaching_breaks_loop(mock_review_comment_payload, mock_dependencies):
    """Test that timeout approaching stops processing (lines 220-223)."""
    mock_dependencies["thread"].return_value = [
        {
            "author": {"login": "reviewer"},
            "body": "Test comment",
            "createdAt": "2025-09-17T12:00:00Z",
        }
    ]
    mock_dependencies["timeout"].return_value = (True, 850)

    with patch("services.webhook.review_run_handler.get_timeout_message") as mock_timeout_msg:
        mock_timeout_msg.return_value = "Timeout message"

        handle_review_run(mock_review_comment_payload)

        mock_timeout_msg.assert_called_once_with(850, "Review run processing")
        assert mock_dependencies["update"].call_count >= 1
        mock_dependencies["chat"].assert_not_called()


def test_timeout_approaching_without_comment_url(mock_review_comment_payload, mock_dependencies):
    """Test timeout handling when comment_url is None (line 221-222)."""
    mock_dependencies["thread"].return_value = [
        {
            "author": {"login": "reviewer"},
            "body": "Test comment",
            "createdAt": "2025-09-17T12:00:00Z",
        }
    ]
    mock_dependencies["reply"].return_value = None
    mock_dependencies["timeout"].return_value = (True, 850)

    with patch("services.webhook.review_run_handler.get_timeout_message") as mock_timeout_msg:
        mock_timeout_msg.return_value = "Timeout message"

        handle_review_run(mock_review_comment_payload)

        mock_timeout_msg.assert_called_once()


def test_pr_closed_during_execution(mock_review_comment_payload, mock_dependencies):
    """Test handling when PR is closed during execution (lines 229-233)."""
    mock_dependencies["thread"].return_value = [
        {
            "author": {"login": "reviewer"},
            "body": "Test comment",
            "createdAt": "2025-09-17T12:00:00Z",
        }
    ]
    mock_dependencies["pr_open"].return_value = False

    handle_review_run(mock_review_comment_payload)

    mock_dependencies["pr_open"].assert_called_once()
    mock_dependencies["chat"].assert_not_called()


def test_pr_closed_without_comment_url(mock_review_comment_payload, mock_dependencies):
    """Test PR closed handling when comment_url is None (line 231-232)."""
    mock_dependencies["thread"].return_value = [
        {
            "author": {"login": "reviewer"},
            "body": "Test comment",
            "createdAt": "2025-09-17T12:00:00Z",
        }
    ]
    mock_dependencies["reply"].return_value = None
    mock_dependencies["pr_open"].return_value = False

    handle_review_run(mock_review_comment_payload)

    mock_dependencies["pr_open"].assert_called_once()


def test_branch_deleted_during_execution(mock_review_comment_payload, mock_dependencies):
    """Test handling when branch is deleted during execution (lines 238-242)."""
    mock_dependencies["thread"].return_value = [
        {
            "author": {"login": "reviewer"},
            "body": "Test comment",
            "createdAt": "2025-09-17T12:00:00Z",
        }
    ]
    mock_dependencies["branch"].return_value = False

    handle_review_run(mock_review_comment_payload)

    mock_dependencies["branch"].assert_called_once()
    mock_dependencies["chat"].assert_not_called()


def test_branch_deleted_without_comment_url(mock_review_comment_payload, mock_dependencies):
    """Test branch deleted handling when comment_url is None (line 240-241)."""
    mock_dependencies["thread"].return_value = [
        {
            "author": {"login": "reviewer"},
            "body": "Test comment",
            "createdAt": "2025-09-17T12:00:00Z",
        }
    ]
    mock_dependencies["reply"].return_value = None
    mock_dependencies["branch"].return_value = False

    handle_review_run(mock_review_comment_payload)

    mock_dependencies["branch"].assert_called_once()


def test_retry_logic_not_explored_but_committed(mock_review_comment_payload, mock_dependencies):
    """Test retry logic when not explored but committed (lines 317-321)."""
    mock_dependencies["thread"].return_value = [
        {
            "author": {"login": "reviewer"},
            "body": "Test comment",
            "createdAt": "2025-09-17T12:00:00Z",
        }
    ]

    mock_dependencies["chat"].side_effect = [
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 40),
        ([{"role": "user"}], [], "tool", {}, 100, 50, True, 50),
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 40),
        ([{"role": "user"}], [], "tool", {}, 100, 50, True, 50),
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 40),
        ([{"role": "user"}], [], "tool", {}, 100, 50, True, 50),
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 40),
        ([{"role": "user"}], [], "tool", {}, 100, 50, True, 50),
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 40),
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 50),
    ]

    handle_review_run(mock_review_comment_payload)

    assert mock_dependencies["chat"].call_count == 8


def test_retry_logic_explored_but_not_committed(mock_review_comment_payload, mock_dependencies):
    """Test retry logic when explored but not committed (lines 324-328)."""
    mock_dependencies["thread"].return_value = [
        {
            "author": {"login": "reviewer"},
            "body": "Test comment",
            "createdAt": "2025-09-17T12:00:00Z",
        }
    ]

    mock_dependencies["chat"].side_effect = [
        ([{"role": "user"}], [], "tool", {}, 100, 50, True, 40),
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 50),
        ([{"role": "user"}], [], "tool", {}, 100, 50, True, 40),
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 50),
        ([{"role": "user"}], [], "tool", {}, 100, 50, True, 40),
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 50),
        ([{"role": "user"}], [], "tool", {}, 100, 50, True, 40),
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 50),
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 40),
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 50),
    ]

    handle_review_run(mock_review_comment_payload)

    assert mock_dependencies["chat"].call_count == 10


def test_retry_count_reset_when_both_explored_and_committed(mock_review_comment_payload, mock_dependencies):
    """Test retry count resets when both explored and committed (line 331)."""
    mock_dependencies["thread"].return_value = [
        {
            "author": {"login": "reviewer"},
            "body": "Test comment",
            "createdAt": "2025-09-17T12:00:00Z",
        }
    ]

    mock_dependencies["chat"].side_effect = [
        ([{"role": "user"}], [], "tool", {}, 100, 50, True, 40),
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 50),
        ([{"role": "user"}], [], "tool", {}, 100, 50, True, 40),
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 50),
        ([{"role": "user"}], [], "tool", {}, 100, 50, True, 40),
        ([{"role": "user"}], [], "tool", {}, 100, 50, True, 50),
        ([{"role": "user"}], [], "tool", {}, 100, 50, True, 40),
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 50),
        ([{"role": "user"}], [], "tool", {}, 100, 50, True, 40),
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 50),
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 40),
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 50),
    ]

    handle_review_run(mock_review_comment_payload)

    assert mock_dependencies["chat"].call_count == 12


def test_token_accumulation_across_multiple_iterations(mock_review_comment_payload, mock_dependencies):
    """Test that tokens accumulate correctly across multiple chat iterations."""
    mock_dependencies["thread"].return_value = [
        {
            "author": {"login": "reviewer"},
            "body": "Test comment",
            "createdAt": "2025-09-17T12:00:00Z",
        }
    ]

    mock_dependencies["chat"].side_effect = [
        ([{"role": "user"}], [], "tool", {}, 120, 80, False, 40),
        ([{"role": "user"}], [], "tool", {}, 90, 60, False, 50),
    ]

    handle_review_run(mock_review_comment_payload)

    usage_call = mock_dependencies["usage"].call_args.kwargs
    assert usage_call["token_input"] == 210
    assert usage_call["token_output"] == 140
    assert usage_call["is_completed"] is True


def test_complete_flow_with_thread_comments(mock_review_comment_payload, mock_dependencies):
    """Test complete flow with thread comments present."""
    mock_dependencies["thread"].return_value = [
        {
            "author": {"login": "reviewer1"},
            "body": "First comment",
            "createdAt": "2025-09-17T12:00:00Z",
        },
        {
            "author": {"login": "reviewer2"},
            "body": "Second comment",
            "createdAt": "2025-09-17T12:05:00Z",
        },
    ]

    mock_dependencies["chat"].side_effect = [
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 40),
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 50),
    ]

    handle_review_run(mock_review_comment_payload)

    mock_dependencies["thread"].assert_called_once()
    mock_dependencies["reply"].assert_called_once()
    mock_dependencies["commit"].assert_called_once()
    mock_dependencies["usage"].assert_called_once()


def test_usage_record_creation_and_update(mock_review_comment_payload, mock_dependencies):
    """Test that usage record is created and updated correctly."""
    mock_dependencies["thread"].return_value = [
        {
            "author": {"login": "reviewer"},
            "body": "Test comment",
            "createdAt": "2025-09-17T12:00:00Z",
        }
    ]

    mock_dependencies["chat"].side_effect = [
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 40),
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 50),
    ]

    handle_review_run(mock_review_comment_payload)

    mock_dependencies["user_req"].assert_called_once()
    user_req_call = mock_dependencies["user_req"].call_args.kwargs
    assert user_req_call["user_id"] == 22222
    assert user_req_call["user_name"] == "test-reviewer"
    assert user_req_call["trigger"] == "review_comment"

    mock_dependencies["usage"].assert_called_once()
    usage_call = mock_dependencies["usage"].call_args.kwargs
    assert usage_call["usage_id"] == 777
    assert usage_call["pr_number"] == 123


def test_chat_with_agent_called_with_correct_modes(mock_review_comment_payload, mock_dependencies):
    """Test that chat_with_agent is called with correct modes."""
    mock_dependencies["thread"].return_value = [
        {
            "author": {"login": "reviewer"},
            "body": "Test comment",
            "createdAt": "2025-09-17T12:00:00Z",
        }
    ]

    mock_dependencies["chat"].side_effect = [
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 40),
        ([{"role": "user"}], [], "tool", {}, 100, 50, False, 50),
    ]

    handle_review_run(mock_review_comment_payload)

    assert mock_dependencies["chat"].call_count == 2
    first_call = mock_dependencies["chat"].call_args_list[0].kwargs
    second_call = mock_dependencies["chat"].call_args_list[1].kwargs
    assert first_call["mode"] == "get"
    assert second_call["mode"] == "commit"
    assert first_call["usage_id"] == 777
    assert second_call["usage_id"] == 777
