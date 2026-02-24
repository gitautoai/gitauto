from datetime import datetime, timezone

from utils.text.text_copy import (
    git_command,
    pull_request_completed,
    request_pr_comment,
    UPDATE_COMMENT_FOR_422,
    UPDATE_COMMENT_FOR_RAISED_ERRORS_NO_CHANGES_MADE,
)
from config import EMAIL_LINK, PRODUCT_ID
from constants.urls import SETTINGS_TRIGGERS_URL
from constants.messages import COMPLETED_PR
from constants.urls import DASHBOARD_CREDITS_URL


def test_git_command():
    branch_name = "feature/test-branch"
    result = git_command(branch_name)

    expected = (
        f"\n\n## Test these changes locally\n\n"
        f"```\n"
        f"git fetch origin\n"
        f"git checkout {branch_name}\n"
        f"git pull origin {branch_name}\n"
        f"```"
    )

    assert result == expected


def test_pull_request_completed_bot_creator_bot_sender():
    pr_creator = "sentry-io[bot]"
    sender_name = "gitauto-ai[bot]"
    is_automation = False

    result = pull_request_completed(pr_creator, sender_name, is_automation)

    expected = f"{COMPLETED_PR}\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_pull_request_completed_bot_creator_product_sender():
    pr_creator = "sentry-io[bot]"
    sender_name = f"user-{PRODUCT_ID}"
    is_automation = False

    result = pull_request_completed(pr_creator, sender_name, is_automation)

    expected = f"{COMPLETED_PR}\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_pull_request_completed_bot_creator_human_sender():
    pr_creator = "sentry-io[bot]"
    sender_name = "human-user"
    is_automation = False

    result = pull_request_completed(pr_creator, sender_name, is_automation)

    expected = f"@{sender_name} {COMPLETED_PR}\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_pull_request_completed_same_creator_and_sender():
    pr_creator = "test-user"
    sender_name = "test-user"
    is_automation = False

    result = pull_request_completed(pr_creator, sender_name, is_automation)

    expected = f"@{pr_creator} {COMPLETED_PR}\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_pull_request_completed_product_in_sender():
    pr_creator = "test-user"
    sender_name = f"user-{PRODUCT_ID}"
    is_automation = False

    result = pull_request_completed(pr_creator, sender_name, is_automation)

    expected = f"@{pr_creator} {COMPLETED_PR}\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_pull_request_completed_different_creator_and_sender():
    pr_creator = "test-user1"
    sender_name = "test-user2"
    is_automation = False

    result = pull_request_completed(pr_creator, sender_name, is_automation)

    expected = f"@{pr_creator} @{sender_name} {COMPLETED_PR}\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_pull_request_completed_automation_true():
    pr_creator = "test-user"
    sender_name = "test-user"
    is_automation = True

    result = pull_request_completed(pr_creator, sender_name, is_automation)

    expected = f"@{pr_creator} {COMPLETED_PR}\n\nNote: I automatically create pull requests on a schedule. You can manage your schedule [here]({SETTINGS_TRIGGERS_URL}). Should you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_request_pr_comment_positive_requests():
    requests_left = 5
    sender_name = "test-user"
    end_date = datetime(2025, 5, 1, tzinfo=timezone.utc)

    result = request_pr_comment(requests_left, sender_name, end_date)

    expected = f"\n\n@{sender_name}, You have {requests_left} requests left in this cycle which refreshes on {end_date}.\nIf you have any questions or concerns, please contact us at {EMAIL_LINK}."

    assert result == expected


def test_request_pr_comment_one_request():
    requests_left = 1
    sender_name = "test-user"
    end_date = datetime(2025, 5, 1, tzinfo=timezone.utc)

    result = request_pr_comment(requests_left, sender_name, end_date)

    expected = f"\n\n@{sender_name}, You have {requests_left} request left in this cycle which refreshes on {end_date}.\nIf you have any questions or concerns, please contact us at {EMAIL_LINK}."

    assert result == expected


def test_request_pr_comment_negative_requests():
    requests_left = -3
    sender_name = "test-user"
    end_date = datetime(2025, 5, 1, tzinfo=timezone.utc)

    result = request_pr_comment(requests_left, sender_name, end_date)

    expected = f"\n\n@{sender_name}, You have 0 requests left in this cycle which refreshes on {end_date}.\nIf you have any questions or concerns, please contact us at {EMAIL_LINK}."

    assert result == expected


def test_request_pr_comment_zero_requests():
    requests_left = 0
    sender_name = "test-user"
    end_date = datetime(2025, 5, 1, tzinfo=timezone.utc)

    result = request_pr_comment(requests_left, sender_name, end_date)

    expected = f"\n\n@{sender_name}, You have 0 requests left in this cycle which refreshes on {end_date}.\nIf you have any questions or concerns, please contact us at {EMAIL_LINK}."

    assert result == expected


def test_request_pr_comment_credit_user():
    requests_left = 5  # This should be ignored when is_credit_user=True
    sender_name = "test-user"
    end_date = datetime(2025, 5, 1, tzinfo=timezone.utc)
    is_credit_user = True
    credit_balance_usd = 100

    result = request_pr_comment(
        requests_left, sender_name, end_date, is_credit_user, credit_balance_usd
    )

    expected = f"\n\n@{sender_name}, You have ${credit_balance_usd} in credits remaining. [View credits]({DASHBOARD_CREDITS_URL})\nIf you have any questions or concerns, please contact us at {EMAIL_LINK}."

    assert result == expected


def test_request_pr_comment_credit_user_zero_balance():
    requests_left = 10  # This should be ignored when is_credit_user=True
    sender_name = "test-user"
    end_date = datetime(2025, 5, 1, tzinfo=timezone.utc)
    is_credit_user = True
    credit_balance_usd = 0

    result = request_pr_comment(
        requests_left, sender_name, end_date, is_credit_user, credit_balance_usd
    )

    expected = f"\n\n@{sender_name}, You have ${credit_balance_usd} in credits remaining. [View credits]({DASHBOARD_CREDITS_URL})\nIf you have any questions or concerns, please contact us at {EMAIL_LINK}."

    assert result == expected


def test_request_pr_comment_credit_user_default_balance():
    requests_left = 5
    sender_name = "test-user"
    end_date = datetime(2025, 5, 1, tzinfo=timezone.utc)
    is_credit_user = True
    # credit_balance_usd defaults to 0

    result = request_pr_comment(requests_left, sender_name, end_date, is_credit_user)

    expected = f"\n\n@{sender_name}, You have $0 in credits remaining. [View credits]({DASHBOARD_CREDITS_URL})\nIf you have any questions or concerns, please contact us at {EMAIL_LINK}."

    assert result == expected


def test_git_command_with_special_characters():
    branch_name = "feature/fix-bug-#123"
    result = git_command(branch_name)

    expected = (
        f"\n\n## Test these changes locally\n\n"
        f"```\n"
        f"git fetch origin\n"
        f"git checkout {branch_name}\n"
        f"git pull origin {branch_name}\n"
        f"```"
    )

    assert result == expected


def test_git_command_empty_branch_name():
    branch_name = ""
    result = git_command(branch_name)

    expected = (
        f"\n\n## Test these changes locally\n\n"
        f"```\n"
        f"git fetch origin\n"
        f"git checkout {branch_name}\n"
        f"git pull origin {branch_name}\n"
        f"```"
    )

    assert result == expected


def test_update_comment_constants():
    # Test that the constants are properly formatted and contain expected content
    assert EMAIL_LINK in UPDATE_COMMENT_FOR_422
    assert "I'm a bit lost here!" in UPDATE_COMMENT_FOR_422
    assert "feedback or need help?" in UPDATE_COMMENT_FOR_422
    assert EMAIL_LINK in UPDATE_COMMENT_FOR_RAISED_ERRORS_NO_CHANGES_MADE
    assert (
        "No changes were detected" in UPDATE_COMMENT_FOR_RAISED_ERRORS_NO_CHANGES_MADE
    )
    assert "feedback or need help?" in UPDATE_COMMENT_FOR_RAISED_ERRORS_NO_CHANGES_MADE


def test_pull_request_completed_automation_bot_creator_bot_sender():
    pr_creator = "sentry-io[bot]"
    sender_name = "gitauto-ai[bot]"
    is_automation = True

    result = pull_request_completed(pr_creator, sender_name, is_automation)

    expected = f"{COMPLETED_PR}\n\nNote: I automatically create pull requests on a schedule. You can manage your schedule [here]({SETTINGS_TRIGGERS_URL}). Should you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_pull_request_completed_automation_different_users():
    pr_creator = "test-user1"
    sender_name = "test-user2"
    is_automation = True

    result = pull_request_completed(pr_creator, sender_name, is_automation)

    expected = f"@{pr_creator} @{sender_name} {COMPLETED_PR}\n\nNote: I automatically create pull requests on a schedule. You can manage your schedule [here]({SETTINGS_TRIGGERS_URL}). Should you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_pull_request_completed_edge_case_product_id_in_creator():
    pr_creator = f"user-{PRODUCT_ID}-test"
    sender_name = "different-user"
    is_automation = False

    result = pull_request_completed(pr_creator, sender_name, is_automation)

    # Since PRODUCT_ID is in sender_name condition, but not in pr_creator condition,
    # this should fall into the "different creator and sender" case
    expected = f"@{pr_creator} @{sender_name} {COMPLETED_PR}\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_pull_request_completed_empty_names():
    pr_creator = ""
    sender_name = ""
    is_automation = False

    result = pull_request_completed(pr_creator, sender_name, is_automation)
    # Empty names should be treated as same creator and sender
    expected = f"@ {COMPLETED_PR}\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected
