"""Unit tests for pr_checkbox_handler.py"""
# pylint: disable=redefined-outer-name,too-many-lines

from unittest.mock import patch

import pytest
from services.webhook.pr_checkbox_handler import handle_pr_checkbox_trigger


@pytest.fixture
def base_payload():
    """Base payload for testing."""
    return {
        "action": "created",
        "comment": {
            "id": 12345,
            "body": "- [x] Generate Tests\n- [x] `src/test.py`\n- [x] `src/main.py`",
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


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies."""
    with patch("services.webhook.pr_checkbox_handler.get_installation_access_token") as mock_token, \
         patch("services.webhook.pr_checkbox_handler.slack_notify") as mock_slack, \
         patch("services.webhook.pr_checkbox_handler.check_availability") as mock_availability, \
         patch("services.webhook.pr_checkbox_handler.get_pull_request") as mock_get_pr, \
         patch("services.webhook.pr_checkbox_handler.create_comment") as mock_create_comment, \
         patch("services.webhook.pr_checkbox_handler.update_comment") as mock_update_comment, \
         patch("services.webhook.pr_checkbox_handler.create_user_request") as mock_create_request, \
         patch("services.webhook.pr_checkbox_handler.cancel_workflow_runs") as mock_cancel, \
         patch("services.webhook.pr_checkbox_handler.get_repository") as mock_get_repo, \
         patch("services.webhook.pr_checkbox_handler.extract_selected_files") as mock_extract, \
         patch("services.webhook.pr_checkbox_handler.is_lambda_timeout_approaching") as mock_timeout, \
         patch("services.webhook.pr_checkbox_handler.is_pull_request_open") as mock_pr_open, \
         patch("services.webhook.pr_checkbox_handler.check_branch_exists") as mock_branch_exists, \
         patch("services.webhook.pr_checkbox_handler.chat_with_agent") as mock_chat, \
         patch("services.webhook.pr_checkbox_handler.create_empty_commit") as mock_empty_commit, \
         patch("services.webhook.pr_checkbox_handler.update_usage") as mock_update_usage, \
         patch("services.webhook.pr_checkbox_handler.insert_credit") as mock_insert_credit, \
         patch("services.webhook.pr_checkbox_handler.get_owner") as mock_get_owner, \
         patch("services.webhook.pr_checkbox_handler.get_user") as mock_get_user, \
         patch("services.webhook.pr_checkbox_handler.send_email") as mock_send_email, \
         patch("services.webhook.pr_checkbox_handler.get_credits_depleted_email_text") as mock_email_text, \
         patch("services.webhook.pr_checkbox_handler.get_timeout_message") as mock_timeout_msg, \
         patch("services.webhook.pr_checkbox_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]"), \
         patch("services.webhook.pr_checkbox_handler.PRODUCT_ID", "gitauto"), \
         patch("services.webhook.pr_checkbox_handler.SETTINGS_LINKS", ""):

        mock_token.return_value = "ghs_test_token"
        mock_slack.return_value = "thread_123"
        mock_get_pr.return_value = {
            "title": "Test PR",
            "body": "Test PR description",
            "head": {"ref": "feature-branch"},
        }
        mock_create_comment.return_value = "http://comment-url"
        mock_create_request.return_value = 888
        mock_get_repo.return_value = {"id": 98765}
        mock_extract.return_value = ["src/test.py", "src/main.py"]

        yield {
            "token": mock_token,
            "slack": mock_slack,
            "availability": mock_availability,
            "get_pr": mock_get_pr,
            "create_comment": mock_create_comment,
            "update_comment": mock_update_comment,
            "create_request": mock_create_request,
            "cancel": mock_cancel,
            "get_repo": mock_get_repo,
            "extract": mock_extract,
            "timeout": mock_timeout,
            "pr_open": mock_pr_open,
            "branch_exists": mock_branch_exists,
            "chat": mock_chat,
            "empty_commit": mock_empty_commit,
            "update_usage": mock_update_usage,
            "insert_credit": mock_insert_credit,
            "get_owner": mock_get_owner,
            "get_user": mock_get_user,
            "send_email": mock_send_email,
            "email_text": mock_email_text,
            "timeout_msg": mock_timeout_msg,
        }


@pytest.mark.asyncio
async def test_skips_when_sender_is_bot(base_payload):
    """Test that handler exits early when sender is a bot."""
    base_payload["sender"]["login"] = "some-bot[bot]"

    with patch("services.webhook.pr_checkbox_handler.slack_notify") as mock_slack:
        await handle_pr_checkbox_trigger(base_payload)
        mock_slack.assert_not_called()


@pytest.mark.asyncio
async def test_skips_when_comment_author_not_gitauto(base_payload):
    """Test that handler exits early when comment author is not GitAuto (line 69-70)."""
    base_payload["comment"]["user"]["login"] = "some-other-user"

    with patch("services.webhook.pr_checkbox_handler.slack_notify") as mock_slack, \
         patch("services.webhook.pr_checkbox_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]"):
        await handle_pr_checkbox_trigger(base_payload)
        mock_slack.assert_not_called()


@pytest.mark.asyncio
async def test_skips_when_no_files_selected(base_payload, mock_dependencies):
    """Test that handler exits early when no files are selected (line 83-84)."""
    mock_dependencies["extract"].return_value = []

    await handle_pr_checkbox_trigger(base_payload)
    mock_dependencies["slack"].assert_not_called()


@pytest.mark.asyncio
async def test_access_denied_creates_comment_and_exits(base_payload, mock_dependencies):
    """Test access denied path (lines 149-154)."""
    mock_dependencies["availability"].return_value = {
        "can_proceed": False,
        "user_message": "Access denied: insufficient credits",
        "log_message": "User has no credits remaining",
        "billing_type": "credit",
    }

    await handle_pr_checkbox_trigger(base_payload)

    mock_dependencies["create_comment"].assert_called_once()
    call_kwargs = mock_dependencies["create_comment"].call_args.kwargs
    assert call_kwargs["body"] == "Access denied: insufficient credits"

    assert mock_dependencies["slack"].call_count == 2
    second_call = mock_dependencies["slack"].call_args_list[1]
    assert second_call[0][0] == "User has no credits remaining"

    mock_dependencies["chat"].assert_not_called()


@pytest.mark.asyncio
async def test_timeout_handling_breaks_loop(base_payload, mock_dependencies):
    """Test timeout handling (lines 212-217)."""
    mock_dependencies["availability"].return_value = {
        "can_proceed": True,
        "billing_type": "subscription",
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_dependencies["timeout"].return_value = (True, 890.5)
    mock_dependencies["timeout_msg"].return_value = "Timeout: 890.5 seconds elapsed"

    await handle_pr_checkbox_trigger(base_payload)

    mock_dependencies["timeout_msg"].assert_called_once_with(890.5, "PR test generation processing")
    mock_dependencies["update_comment"].assert_called()

    timeout_call = None
    for call in mock_dependencies["update_comment"].call_args_list:
        if "Timeout" in call.kwargs.get("body", ""):
            timeout_call = call
            break
    assert timeout_call is not None
    assert "Timeout: 890.5 seconds elapsed" in timeout_call.kwargs["body"]


@pytest.mark.asyncio
async def test_pr_closed_during_execution(base_payload, mock_dependencies):
    """Test PR closed during execution (lines 220-226)."""
    mock_dependencies["availability"].return_value = {
        "can_proceed": True,
        "billing_type": "subscription",
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_dependencies["timeout"].return_value = (False, 0)
    mock_dependencies["pr_open"].return_value = False

    await handle_pr_checkbox_trigger(base_payload)

    update_calls = mock_dependencies["update_comment"].call_args_list
    pr_closed_call = None
    for call in update_calls:
        body = call.kwargs.get("body", "")
        if "Process stopped: Pull request" in body and "was closed" in body:
            pr_closed_call = call
            break

    assert pr_closed_call is not None
    assert "Pull request #123 was closed during execution" in pr_closed_call.kwargs["body"]


@pytest.mark.asyncio
async def test_branch_deleted_during_execution(base_payload, mock_dependencies):
    """Test branch deleted during execution (lines 228-234)."""
    mock_dependencies["availability"].return_value = {
        "can_proceed": True,
        "billing_type": "subscription",
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_dependencies["timeout"].return_value = (False, 0)
    mock_dependencies["pr_open"].return_value = True
    mock_dependencies["branch_exists"].return_value = False

    await handle_pr_checkbox_trigger(base_payload)

    update_calls = mock_dependencies["update_comment"].call_args_list
    branch_deleted_call = None
    for call in update_calls:
        body = call.kwargs.get("body", "")
        if "Process stopped: Branch" in body and "has been deleted" in body:
            branch_deleted_call = call
            break

    assert branch_deleted_call is not None
    assert "Branch 'feature-branch' has been deleted" in branch_deleted_call.kwargs["body"]


@pytest.mark.asyncio
async def test_retry_logic_not_explored_and_committed(base_payload, mock_dependencies):
    """Test retry logic when not explored but committed (lines 285-289)."""
    mock_dependencies["availability"].return_value = {
        "can_proceed": True,
        "billing_type": "subscription",
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_dependencies["timeout"].return_value = (False, 0)
    mock_dependencies["pr_open"].return_value = True
    mock_dependencies["branch_exists"].return_value = True

    # Simulate: not explored but committed, retry 4 times then break
    mock_dependencies["chat"].side_effect = [
        ([], [], "tool", {}, 10, 5, False, 10),  # get mode
        ([], [], "tool", {}, 10, 5, True, 20),   # commit mode - retry 1
        ([], [], "tool", {}, 10, 5, False, 30),  # get mode
        ([], [], "tool", {}, 10, 5, True, 40),   # commit mode - retry 2
        ([], [], "tool", {}, 10, 5, False, 50),  # get mode
        ([], [], "tool", {}, 10, 5, True, 60),   # commit mode - retry 3
        ([], [], "tool", {}, 10, 5, False, 70),  # get mode
        ([], [], "tool", {}, 10, 5, True, 80),   # commit mode - retry 4, should break
    ]

    await handle_pr_checkbox_trigger(base_payload)

    assert mock_dependencies["chat"].call_count == 8


@pytest.mark.asyncio
async def test_retry_logic_explored_but_not_committed(base_payload, mock_dependencies):
    """Test retry logic when explored but not committed (lines 291-295)."""
    mock_dependencies["availability"].return_value = {
        "can_proceed": True,
        "billing_type": "subscription",
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_dependencies["timeout"].return_value = (False, 0)
    mock_dependencies["pr_open"].return_value = True
    mock_dependencies["branch_exists"].return_value = True

    # Simulate: explored but not committed, retry 4 times then break
    mock_dependencies["chat"].side_effect = [
        ([], [], "tool", {}, 10, 5, True, 10),   # get mode
        ([], [], "tool", {}, 10, 5, False, 20),  # commit mode - retry 1
        ([], [], "tool", {}, 10, 5, True, 30),   # get mode
        ([], [], "tool", {}, 10, 5, False, 40),  # commit mode - retry 2
        ([], [], "tool", {}, 10, 5, True, 50),   # get mode
        ([], [], "tool", {}, 10, 5, False, 60),  # commit mode - retry 3
        ([], [], "tool", {}, 10, 5, True, 70),   # get mode
        ([], [], "tool", {}, 10, 5, False, 80),  # commit mode - retry 4, should break
    ]

    await handle_pr_checkbox_trigger(base_payload)

    assert mock_dependencies["chat"].call_count == 8


@pytest.mark.asyncio
async def test_retry_logic_resets_on_success(base_payload, mock_dependencies):
    """Test retry logic resets counter on success (line 297)."""
    mock_dependencies["availability"].return_value = {
        "can_proceed": True,
        "billing_type": "subscription",
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_dependencies["timeout"].return_value = (False, 0)
    mock_dependencies["pr_open"].return_value = True
    mock_dependencies["branch_exists"].return_value = True

    # Simulate: both explored and committed, retry counter resets
    mock_dependencies["chat"].side_effect = [
        ([], [], "tool", {}, 10, 5, True, 10),   # get mode - explored
        ([], [], "tool", {}, 10, 5, True, 20),   # commit mode - committed, reset counter
        ([], [], "tool", {}, 10, 5, False, 30),  # get mode - not explored
        ([], [], "tool", {}, 10, 5, False, 40),  # commit mode - not committed, break
    ]

    await handle_pr_checkbox_trigger(base_payload)

    assert mock_dependencies["chat"].call_count == 4


@pytest.mark.asyncio
async def test_credit_billing_with_depleted_credits_sends_email(base_payload, mock_dependencies):
    """Test credit depletion email notification (lines 322-331)."""
    mock_dependencies["availability"].return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_dependencies["timeout"].return_value = (False, 0)
    mock_dependencies["pr_open"].return_value = True
    mock_dependencies["branch_exists"].return_value = True
    mock_dependencies["chat"].side_effect = [
        ([], [], "tool", {}, 10, 5, False, 10),
        ([], [], "tool", {}, 10, 5, False, 20),
    ]

    mock_dependencies["get_owner"].return_value = {
        "id": 11111,
        "credit_balance_usd": 0,
    }
    mock_dependencies["get_user"].return_value = {
        "id": 22222,
        "email": "test@example.com",
    }
    mock_dependencies["email_text"].return_value = ("Credits Depleted", "Your credits are depleted")

    await handle_pr_checkbox_trigger(base_payload)

    mock_dependencies["insert_credit"].assert_called_once_with(
        owner_id=11111,
        transaction_type="usage",
        usage_id=888
    )
    mock_dependencies["get_owner"].assert_called_once_with(owner_id=11111)
    mock_dependencies["get_user"].assert_called_once_with(user_id=22222)
    mock_dependencies["email_text"].assert_called_once_with("test-sender")
    mock_dependencies["send_email"].assert_called_once_with(
        to="test@example.com",
        subject="Credits Depleted",
        text="Your credits are depleted"
    )


@pytest.mark.asyncio
async def test_credit_billing_with_positive_balance_no_email(base_payload, mock_dependencies):
    """Test no email sent when credits still available."""
    mock_dependencies["availability"].return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_dependencies["timeout"].return_value = (False, 0)
    mock_dependencies["pr_open"].return_value = True
    mock_dependencies["branch_exists"].return_value = True
    mock_dependencies["chat"].side_effect = [
        ([], [], "tool", {}, 10, 5, False, 10),
        ([], [], "tool", {}, 10, 5, False, 20),
    ]

    mock_dependencies["get_owner"].return_value = {
        "id": 11111,
        "credit_balance_usd": 50,
    }

    await handle_pr_checkbox_trigger(base_payload)

    mock_dependencies["insert_credit"].assert_called_once()
    mock_dependencies["get_owner"].assert_called_once()
    mock_dependencies["get_user"].assert_not_called()
    mock_dependencies["send_email"].assert_not_called()


@pytest.mark.asyncio
async def test_credit_billing_no_owner_found(base_payload, mock_dependencies):
    """Test no email sent when owner not found."""
    mock_dependencies["availability"].return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_dependencies["timeout"].return_value = (False, 0)
    mock_dependencies["pr_open"].return_value = True
    mock_dependencies["branch_exists"].return_value = True
    mock_dependencies["chat"].side_effect = [
        ([], [], "tool", {}, 10, 5, False, 10),
        ([], [], "tool", {}, 10, 5, False, 20),
    ]

    mock_dependencies["get_owner"].return_value = None

    await handle_pr_checkbox_trigger(base_payload)

    mock_dependencies["insert_credit"].assert_called_once()
    mock_dependencies["get_owner"].assert_called_once()
    mock_dependencies["get_user"].assert_not_called()
    mock_dependencies["send_email"].assert_not_called()


@pytest.mark.asyncio
async def test_credit_billing_no_user_email(base_payload, mock_dependencies):
    """Test no email sent when user has no email."""
    mock_dependencies["availability"].return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_dependencies["timeout"].return_value = (False, 0)
    mock_dependencies["pr_open"].return_value = True
    mock_dependencies["branch_exists"].return_value = True
    mock_dependencies["chat"].side_effect = [
        ([], [], "tool", {}, 10, 5, False, 10),
        ([], [], "tool", {}, 10, 5, False, 20),
    ]

    mock_dependencies["get_owner"].return_value = {
        "id": 11111,
        "credit_balance_usd": 0,
    }
    mock_dependencies["get_user"].return_value = {
        "id": 22222,
        "email": None,
    }

    await handle_pr_checkbox_trigger(base_payload)

    mock_dependencies["insert_credit"].assert_called_once()
    mock_dependencies["get_owner"].assert_called_once()
    mock_dependencies["get_user"].assert_called_once()
    mock_dependencies["send_email"].assert_not_called()


@pytest.mark.asyncio
async def test_subscription_billing_no_credit_insert(base_payload, mock_dependencies):
    """Test subscription billing doesn't insert credit."""
    mock_dependencies["availability"].return_value = {
        "can_proceed": True,
        "billing_type": "subscription",
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_dependencies["timeout"].return_value = (False, 0)
    mock_dependencies["pr_open"].return_value = True
    mock_dependencies["branch_exists"].return_value = True
    mock_dependencies["chat"].side_effect = [
        ([], [], "tool", {}, 10, 5, False, 10),
        ([], [], "tool", {}, 10, 5, False, 20),
    ]

    await handle_pr_checkbox_trigger(base_payload)

    mock_dependencies["insert_credit"].assert_not_called()
    mock_dependencies["get_owner"].assert_not_called()


@pytest.mark.asyncio
async def test_token_accumulation_across_multiple_iterations(base_payload, mock_dependencies):
    """Test token accumulation across multiple chat iterations."""
    mock_dependencies["availability"].return_value = {
        "can_proceed": True,
        "billing_type": "subscription",
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_dependencies["timeout"].return_value = (False, 0)
    mock_dependencies["pr_open"].return_value = True
    mock_dependencies["branch_exists"].return_value = True

    mock_dependencies["chat"].side_effect = [
        ([], [], "tool", {}, 100, 60, True, 10),
        ([], [], "tool", {}, 80, 45, True, 20),
        ([], [], "tool", {}, 50, 30, True, 30),
        ([], [], "tool", {}, 40, 25, True, 40),
        ([], [], "tool", {}, 30, 20, False, 50),
        ([], [], "tool", {}, 20, 15, False, 60),
    ]

    await handle_pr_checkbox_trigger(base_payload)

    mock_dependencies["update_usage"].assert_called_once()
    usage_call = mock_dependencies["update_usage"].call_args.kwargs
    assert usage_call["token_input"] == 320
    assert usage_call["token_output"] == 195
    assert usage_call["is_completed"] is True


@pytest.mark.asyncio
async def test_product_id_not_gitauto_search_text(base_payload):
    """Test search text includes product ID when not gitauto."""
    base_payload["comment"]["body"] = "- [x] Generate Tests - custom-product\n- [x] `src/test.py`"

    with patch("services.webhook.pr_checkbox_handler.PRODUCT_ID", "custom-product"), \
         patch("services.webhook.pr_checkbox_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]"), \
         patch("services.webhook.pr_checkbox_handler.SETTINGS_LINKS", ""), \
         patch("services.webhook.pr_checkbox_handler.extract_selected_files") as mock_extract, \
         patch("services.webhook.pr_checkbox_handler.slack_notify") as mock_slack:

        mock_extract.return_value = ["src/test.py"]

        await handle_pr_checkbox_trigger(base_payload)

        mock_slack.assert_called()


@pytest.mark.asyncio
async def test_complete_successful_flow(base_payload, mock_dependencies):
    """Test complete successful flow from start to finish."""
    mock_dependencies["availability"].return_value = {
        "can_proceed": True,
        "billing_type": "subscription",
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_dependencies["timeout"].return_value = (False, 0)
    mock_dependencies["pr_open"].return_value = True
    mock_dependencies["branch_exists"].return_value = True
    mock_dependencies["chat"].side_effect = [
        ([], [], "tool", {}, 10, 5, False, 10),
        ([], [], "tool", {}, 10, 5, False, 20),
    ]

    await handle_pr_checkbox_trigger(base_payload)

    mock_dependencies["slack"].assert_called()
    assert mock_dependencies["slack"].call_count >= 2

    mock_dependencies["create_request"].assert_called_once()
    mock_dependencies["cancel"].assert_called_once()
    mock_dependencies["empty_commit"].assert_called_once()
    mock_dependencies["update_usage"].assert_called_once()

    final_update_call = mock_dependencies["update_comment"].call_args_list[-1]
    assert "Finished generating tests" in final_update_call.kwargs["body"]


@pytest.mark.asyncio
async def test_credit_billing_with_zero_balance_and_no_sender_id(base_payload, mock_dependencies):
    """Test no email sent when sender_id is missing."""
    base_payload["sender"]["id"] = None

    mock_dependencies["availability"].return_value = {
        "can_proceed": True,
        "billing_type": "credit",
        "user_message": "",
        "log_message": "Proceeding",
    }
    mock_dependencies["timeout"].return_value = (False, 0)
    mock_dependencies["pr_open"].return_value = True
    mock_dependencies["branch_exists"].return_value = True
    mock_dependencies["chat"].side_effect = [
        ([], [], "tool", {}, 10, 5, False, 10),
        ([], [], "tool", {}, 10, 5, False, 20),
    ]

    mock_dependencies["get_owner"].return_value = {
        "id": 11111,
        "credit_balance_usd": 0,
    }

    await handle_pr_checkbox_trigger(base_payload)

    mock_dependencies["insert_credit"].assert_called_once()
    mock_dependencies["get_owner"].assert_called_once()
    mock_dependencies["get_user"].assert_not_called()
    mock_dependencies["send_email"].assert_not_called()
