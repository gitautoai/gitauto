from datetime import datetime, timezone

from utils.text.text_copy import (
    git_command,
    pull_request_completed,
    request_issue_comment,
)
from config import EMAIL_LINK, PRODUCT_ID
from constants.messages import COMPLETED_PR


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


def test_pull_request_completed_bot_issuer_bot_sender():
    issuer_name = "sentry-io[bot]"
    sender_name = "gitauto-ai[bot]"
    pr_url = "https://github.com/test/repo/pull/1"
    is_automation = False

    result = pull_request_completed(issuer_name, sender_name, pr_url, is_automation)

    expected = f"{COMPLETED_PR} {pr_url} 🚀\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_pull_request_completed_bot_issuer_product_sender():
    issuer_name = "sentry-io[bot]"
    sender_name = f"user-{PRODUCT_ID}"
    pr_url = "https://github.com/test/repo/pull/1"
    is_automation = False

    result = pull_request_completed(issuer_name, sender_name, pr_url, is_automation)

    expected = f"{COMPLETED_PR} {pr_url} 🚀\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_pull_request_completed_bot_issuer_human_sender():
    issuer_name = "sentry-io[bot]"
    sender_name = "human-user"
    pr_url = "https://github.com/test/repo/pull/1"
    is_automation = False

    result = pull_request_completed(issuer_name, sender_name, pr_url, is_automation)

    expected = f"@{sender_name} {COMPLETED_PR} {pr_url} 🚀\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_pull_request_completed_same_issuer_and_sender():
    issuer_name = "test-user"
    sender_name = "test-user"
    pr_url = "https://github.com/test/repo/pull/1"
    is_automation = False

    result = pull_request_completed(issuer_name, sender_name, pr_url, is_automation)

    expected = f"@{issuer_name} {COMPLETED_PR} {pr_url} 🚀\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_pull_request_completed_product_in_sender():
    issuer_name = "test-user"
    sender_name = f"user-{PRODUCT_ID}"
    pr_url = "https://github.com/test/repo/pull/1"
    is_automation = False

    result = pull_request_completed(issuer_name, sender_name, pr_url, is_automation)

    expected = f"@{issuer_name} {COMPLETED_PR} {pr_url} 🚀\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_pull_request_completed_different_issuer_and_sender():
    issuer_name = "test-user1"
    sender_name = "test-user2"
    pr_url = "https://github.com/test/repo/pull/1"
    is_automation = False

    result = pull_request_completed(issuer_name, sender_name, pr_url, is_automation)

    expected = f"@{issuer_name} @{sender_name} {COMPLETED_PR} {pr_url} 🚀\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_pull_request_completed_automation_true():
    issuer_name = "test-user"
    sender_name = "test-user"
    pr_url = "https://github.com/test/repo/pull/1"
    is_automation = True

    result = pull_request_completed(issuer_name, sender_name, pr_url, is_automation)

    expected = f"@{issuer_name} {COMPLETED_PR} {pr_url} 🚀\n\nNote: I automatically create a pull request for an unassigned and open issue in order from oldest to newest once a day at 00:00 UTC, as long as you have remaining automation usage. Should you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    assert result == expected


def test_request_issue_comment_positive_requests():
    requests_left = 5
    sender_name = "test-user"
    end_date = datetime(2025, 5, 1, tzinfo=timezone.utc)

    result = request_issue_comment(requests_left, sender_name, end_date)

    expected = f"\n\n@{sender_name}, You have {requests_left} requests left in this cycle which refreshes on {end_date}.\nIf you have any questions or concerns, please contact us at {EMAIL_LINK}."

    assert result == expected


def test_request_issue_comment_one_request():
    requests_left = 1
    sender_name = "test-user"
    end_date = datetime(2025, 5, 1, tzinfo=timezone.utc)

    result = request_issue_comment(requests_left, sender_name, end_date)

    expected = f"\n\n@{sender_name}, You have {requests_left} request left in this cycle which refreshes on {end_date}.\nIf you have any questions or concerns, please contact us at {EMAIL_LINK}."

    assert result == expected


def test_request_issue_comment_negative_requests():
    requests_left = -3
    sender_name = "test-user"
    end_date = datetime(2025, 5, 1, tzinfo=timezone.utc)

    result = request_issue_comment(requests_left, sender_name, end_date)

    expected = f"\n\n@{sender_name}, You have 0 requests left in this cycle which refreshes on {end_date}.\nIf you have any questions or concerns, please contact us at {EMAIL_LINK}."

    assert result == expected


def test_request_issue_comment_zero_requests():
    requests_left = 0
    sender_name = "test-user"
    end_date = datetime(2025, 5, 1, tzinfo=timezone.utc)

    result = request_issue_comment(requests_left, sender_name, end_date)

    expected = f"\n\n@{sender_name}, You have 0 requests left in this cycle which refreshes on {end_date}.\nIf you have any questions or concerns, please contact us at {EMAIL_LINK}."

    assert result == expected
