from unittest.mock import patch
from typing import cast

from services.webhook.issue_handler import create_pr_from_issue
from services.github.types.github_types import GitHubLabeledPayload


@patch("services.webhook.issue_handler.check_availability")
@patch("services.webhook.issue_handler.deconstruct_github_payload")
def test_check_availability_is_called_for_auto_reload_integration(
    mock_deconstruct_github_payload,
    mock_check_availability,
):
    """Test that check_availability is called, which handles auto-reload internally"""
    # Mock the payload deconstruction to return insufficient data to exit early
    mock_base_args = {
        "owner": "test_owner",
        "repo": "test_repo",
        "issue_number": 123,
        "issue_title": "Test Issue",
        "sender_name": "test_sender",
        "installation_id": 456,
        "owner_id": 789,
        "owner_type": "Organization",
        "repo_id": 101112,
        "issue_body": "Test issue body",
        "issuer_name": "test_issuer",
        "new_branch": "gitauto/issue-123",
        "sender_id": 131415,
        "sender_email": "test@example.com",
        "github_urls": [],
        "token": "test_token",
        "is_automation": False,
        "skip_ci": True,
    }
    mock_repo_settings = {}
    mock_deconstruct_github_payload.return_value = (mock_base_args, mock_repo_settings)

    # Mock check_availability to return insufficient credits to exit early
    mock_check_availability.return_value = {
        "can_proceed": False,
        "billing_type": "credit",
        "requests_left": None,
        "credit_balance_usd": 0,
        "period_end_date": None,
        "user_message": "Insufficient credits. Please add more credits to continue.",
        "log_message": "Insufficient credits for test_owner/test_repo",
    }

    # Mock the payload
    test_payload = {
        "action": "labeled",
        "label": {"name": "gitauto-wes"},
        "issue": {"number": 123, "title": "Test Issue"},
        "repository": {"name": "test_repo"},
        "sender": {"login": "test_sender"},
    }

    # We need to mock more dependencies to avoid deep execution
    with patch("services.webhook.issue_handler.slack_notify"), patch(
        "services.webhook.issue_handler.get_stripe_customer_id",
        return_value="cus_test123",
    ), patch("services.webhook.issue_handler.create_stripe_customer"), patch(
        "services.webhook.issue_handler.update_stripe_customer_id"
    ), patch(
        "services.webhook.issue_handler.delete_comments_by_identifiers"
    ), patch(
        "services.webhook.issue_handler.create_comment",
        return_value="https://github.com/test/comment",
    ), patch(
        "services.webhook.issue_handler.update_comment"
    ), patch(
        "services.webhook.issue_handler.render_text", return_value="Test issue body"
    ), patch(
        "services.webhook.issue_handler.create_user_request", return_value=12345
    ):

        # Call the function - it should exit early due to insufficient credits
        # but check_availability should still be called
        create_pr_from_issue(
            payload=cast(GitHubLabeledPayload, test_payload),
            trigger="issue_label",
            input_from="github",
        )

    # Verify check_availability was called - this is where auto-reload logic lives
    mock_check_availability.assert_called_once_with(
        owner_id=789,
        owner_name="test_owner",
        repo_name="test_repo",
        installation_id=456,
        sender_name="test_sender",
    )
