import inspect
from typing import cast
from unittest.mock import patch
from services.webhook.issue_handler import create_pr_from_issue
from services.github.types.github_types import GitHubLabeledPayload


def test_create_pr_from_issue_wrong_label_early_return():
    """Test early return when wrong label is provided"""
    payload_dict = {
        "action": "labeled",
        "label": {"name": "wrong-label"},  # Not "gitauto"
        "issue": {"number": 123, "title": "Test Issue"},
        "repository": {"name": "test_repo"},
    }
    payload = cast(GitHubLabeledPayload, payload_dict)

    lambda_info: dict[str, str | None] = {
        "log_group": "test",
        "log_stream": "test",
        "request_id": "test",
    }

    # Function should complete without errors (early return due to wrong label)
    create_pr_from_issue(
        payload=payload,
        trigger="issue_label",
        input_from="github",
        lambda_info=lambda_info,
    )


@patch("services.webhook.issue_handler.create_user_request")
def test_lambda_info_parameter_exists(mock_create_user_request):
    """Test that the create_pr_from_issue function accepts lambda_info parameter"""

    # This test just verifies the function signature accepts lambda_info
    # without actually running the complex function logic

    payload_dict = {
        "action": "labeled",
        "label": {"name": "wrong-label"},  # This will cause early return
        "issue": {"number": 123, "title": "Test Issue"},
        "repository": {"name": "test_repo"},
    }
    payload = cast(GitHubLabeledPayload, payload_dict)

    lambda_info: dict[str, str | None] = {
        "log_group": "/aws/lambda/pr-agent-prod",
        "log_stream": "2025/09/04/pr-agent-prod[$LATEST]841315c5",
        "request_id": "17921070-5cb6-43ee-8d2e-b5161ae89729",
    }

    # Test with lambda_info
    create_pr_from_issue(
        payload=payload,
        trigger="issue_label",
        input_from="github",
        lambda_info=lambda_info,
    )

    # Test without lambda_info (should default to None)
    create_pr_from_issue(payload=payload, trigger="issue_label", input_from="github")

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


@patch("services.webhook.issue_handler.insert_credit")
@patch("services.webhook.issue_handler.check_branch_exists")
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
@patch("services.webhook.issue_handler.get_owner")
@patch("services.webhook.issue_handler.create_comment")
@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.render_text")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
def test_issue_handler_token_accumulation(
    mock_deconstruct_github_payload,
    mock_render_text,
    mock_check_availability,
    mock_create_comment,
    mock_get_owner,
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
    mock_check_branch_exists,
    mock_insert_credit,
):
    """Test that issue handler accumulates tokens correctly and calls update_usage"""

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
            "issue_title": "Test Issue",
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
    mock_get_remote_file_content_by_url.return_value = ""
    mock_get_latest_remote_commit_sha.return_value = "abc123"
    mock_create_remote_branch.return_value = None

    mock_create_pull_request.return_value = (
        "https://github.com/test/repo/pull/123",
        123,
    )
    mock_create_empty_commit.return_value = None
    mock_check_branch_exists.return_value = True
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

    # Mock chat_with_agent - return False for both is_explored and is_committed to break loop
    mock_chat_with_agent.return_value = (
        [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": "AI response"},
        ],
        [],
        "no_action",
        {},
        75,  # input tokens
        35,  # output tokens
        False,  # is_explored=False (breaks loop when both are False)
        90,
    )

    # Create test payload
    payload = cast(
        GitHubLabeledPayload,
        {
            "action": "labeled",
            "label": {"name": "gitauto"},
            "issue": {"number": 100, "title": "Test Issue", "body": "Test body"},
            "repository": {"name": "test_repo", "full_name": "test_owner/test_repo"},
            "sender": {"login": "test_sender"},
        },
    )

    # Call the function
    create_pr_from_issue(
        payload=payload,
        trigger="issue_comment",
        input_from="github",
        lambda_info={
            "log_group": "/aws/lambda/test",
            "log_stream": "test_stream",
            "request_id": "test_request_123",
        },
    )

    # Verify update_usage was called with accumulated tokens
    mock_update_usage.assert_called_once()
    call_kwargs = mock_update_usage.call_args.kwargs

    assert call_kwargs["usage_id"] == 999
    # chat_with_agent is called twice (explore + commit), each returns 75/35 tokens
    assert call_kwargs["token_input"] == 150  # Two calls: 75 + 75
    assert call_kwargs["token_output"] == 70  # Two calls: 35 + 35
