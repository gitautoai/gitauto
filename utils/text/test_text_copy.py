from datetime import datetime
import pytest

from utils.text.text_copy import (
    git_command,
    request_limit_reached,
    pull_request_completed,
    request_issue_comment,
)
from config import EMAIL_LINK, PRODUCT_ID
from constants.messages import COMPLETED_PR


def test_git_command():
    branch_name = "feature/test-branch"
    result = git_command(branch_name)
    
    assert "git fetch origin" in result
    assert f"git checkout {branch_name}" in result
    assert f"git pull origin {branch_name}" in result
    assert "## Test these changes locally" in result


def test_request_limit_reached():
    user_name = "test-user"
    request_count = 10
    end_date = datetime(2025, 5, 1, 12, 0, 0)
    
    result = request_limit_reached(user_name, request_count, end_date)
    
    assert f"Hello @{user_name}" in result
    assert f"reached your request limit of {request_count}" in result
    assert "2025-05-01 12:00:00" in result
    assert "subscribing" in result
    assert EMAIL_LINK in result


def test_pull_request_completed_bot_issuer_bot_sender():
    # Test case: both issuer and sender are bots
    issuer_name = "sentry-io[bot]"
    sender_name = "gitauto-ai[bot]"
    pr_url = "https://github.com/org/repo/pull/123"
    is_automation = False
    
    result = pull_request_completed(issuer_name, sender_name, pr_url, is_automation)
    
    assert f"{COMPLETED_PR} {pr_url}" in result
    assert "@" not in result  # No user mentions
    assert EMAIL_LINK in result


def test_pull_request_completed_bot_issuer_product_sender():
    # Test case: issuer is bot and sender contains PRODUCT_ID
    issuer_name = "sentry-io[bot]"
    sender_name = f"user-{PRODUCT_ID}"
    pr_url = "https://github.com/org/repo/pull/123"
    is_automation = False
    
    result = pull_request_completed(issuer_name, sender_name, pr_url, is_automation)
    
    assert f"{COMPLETED_PR} {pr_url}" in result
    assert "@" not in result  # No user mentions
    assert EMAIL_LINK in result


def test_pull_request_completed_bot_issuer_human_sender():
    # Test case: issuer is bot and sender is human
    issuer_name = "sentry-io[bot]"
    sender_name = "human-user"
    pr_url = "https://github.com/org/repo/pull/123"
    is_automation = False
    
    result = pull_request_completed(issuer_name, sender_name, pr_url, is_automation)
    
    assert f"@{sender_name}" in result
    assert f"{COMPLETED_PR} {pr_url}" in result
    assert EMAIL_LINK in result


def test_pull_request_completed_same_issuer_sender():
    # Test case: issuer and sender are the same human
    issuer_name = "human-user"
    sender_name = "human-user"
    pr_url = "https://github.com/org/repo/pull/123"
    is_automation = False
    
    result = pull_request_completed(issuer_name, sender_name, pr_url, is_automation)
    
    assert f"@{issuer_name}" in result
    assert f"{COMPLETED_PR} {pr_url}" in result
    assert EMAIL_LINK in result


def test_pull_request_completed_product_sender():
    # Test case: sender contains PRODUCT_ID
    issuer_name = "human-user"
    sender_name = f"user-{PRODUCT_ID}"
    pr_url = "https://github.com/org/repo/pull/123"
    is_automation = False
    
    result = pull_request_completed(issuer_name, sender_name, pr_url, is_automation)
    
    assert f"@{issuer_name}" in result
    assert f"{COMPLETED_PR} {pr_url}" in result
    assert EMAIL_LINK in result


def test_pull_request_completed_different_issuer_sender():
    # Test case: issuer and sender are different humans
    issuer_name = "issuer-user"
    sender_name = "sender-user"
    pr_url = "https://github.com/org/repo/pull/123"
    is_automation = False
    
    result = pull_request_completed(issuer_name, sender_name, pr_url, is_automation)
    
    assert f"@{issuer_name}" in result
    assert f"@{sender_name}" in result
    assert f"{COMPLETED_PR} {pr_url}" in result
    assert EMAIL_LINK in result


def test_pull_request_completed_automation_true():
    # Test case: is_automation is True
    issuer_name = "human-user"
    sender_name = "sender-user"
    pr_url = "https://github.com/org/repo/pull/123"
    is_automation = True
    
    result = pull_request_completed(issuer_name, sender_name, pr_url, is_automation)
    
    assert f"@{issuer_name}" in result
    assert f"@{sender_name}" in result
    assert f"{COMPLETED_PR} {pr_url}" in result
    assert "automatically create a pull request" in result
    assert EMAIL_LINK in result


def test_request_issue_comment_positive_requests():
    # Test case: positive number of requests left
    requests_left = 5
    sender_name = "test-user"
    end_date = datetime(2025, 5, 1, 12, 0, 0)
    
    result = request_issue_comment(requests_left, sender_name, end_date)
    
    assert f"@{sender_name}" in result
    assert f"You have {requests_left} requests left" in result
    assert "2025-05-01 12:00:00" in result
    assert EMAIL_LINK in result


def test_request_issue_comment_one_request():
    # Test case: exactly one request left (singular form)
    requests_left = 1
    sender_name = "test-user"
    end_date = datetime(2025, 5, 1, 12, 0, 0)
    
    result = request_issue_comment(requests_left, sender_name, end_date)
    
    assert f"@{sender_name}" in result
    assert "You have 1 request left" in result  # No plural 's'
    assert "2025-05-01 12:00:00" in result
    assert EMAIL_LINK in result


def test_request_issue_comment_negative_requests():
    # Test case: negative number of requests left (should be converted to 0)
    requests_left = -3
    sender_name = "test-user"
    end_date = datetime(2025, 5, 1, 12, 0, 0)
    
    result = request_issue_comment(requests_left, sender_name, end_date)
    
    assert f"@{sender_name}" in result
    assert "You have 0 requests left" in result
    assert "2025-05-01 12:00:00" in result
    assert EMAIL_LINK in result


def test_request_issue_comment_zero_requests():
    # Test case: zero requests left
    requests_left = 0
    sender_name = "test-user"
    end_date = datetime(2025, 5, 1, 12, 0, 0)
    
    result = request_issue_comment(requests_left, sender_name, end_date)
    
    assert f"@{sender_name}" in result
    assert "You have 0 requests left" in result
    assert "2025-05-01 12:00:00" in result
    assert EMAIL_LINK in result