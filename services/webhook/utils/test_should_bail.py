# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import patch

from services.github.types.github_types import BaseArgs
from services.webhook.utils.should_bail import should_bail

BASE_ARGS = cast(
    BaseArgs,
    {
        "owner": "test-owner",
        "repo": "test-repo",
        "clone_url": "https://x-access-token:test-token@github.com/test-owner/test-repo.git",
        "pr_number": 42,
        "new_branch": "feature-branch",
        "token": "test-token",
    },
)

BAIL_KWARGS = {
    "current_time": 1000.0,
    "phase": "execution",
    "base_args": BASE_ARGS,
    "slack_thread_ts": None,
}

MOCK_OOM_OK = "services.webhook.utils.should_bail.is_lambda_oom_approaching"
MOCK_TIMEOUT = "services.webhook.utils.should_bail.is_lambda_timeout_approaching"


@patch("services.webhook.utils.should_bail.update_comment")
@patch("services.webhook.utils.should_bail.check_branch_exists", return_value=True)
@patch("services.webhook.utils.should_bail.is_pull_request_open", return_value=True)
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(False, 60.0))
def test_returns_false_when_all_checks_pass(
    _mock_timeout, _mock_oom, _mock_pr_open, _mock_branch, _mock_update
):
    assert should_bail(**BAIL_KWARGS) is False


@patch("services.webhook.utils.should_bail.update_comment")
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(True, 540.0))
def test_returns_true_on_timeout(_mock_timeout, _mock_oom, _mock_update):
    assert should_bail(**BAIL_KWARGS) is True


@patch("services.webhook.utils.should_bail.update_comment")
@patch("services.webhook.utils.should_bail.check_branch_exists", return_value=True)
@patch("services.webhook.utils.should_bail.is_pull_request_open", return_value=False)
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(False, 60.0))
def test_returns_true_when_pr_closed(
    _mock_timeout, _mock_oom, _mock_pr_open, _mock_branch, _mock_update
):
    assert should_bail(**BAIL_KWARGS) is True


@patch("services.webhook.utils.should_bail.update_comment")
@patch("services.webhook.utils.should_bail.check_branch_exists", return_value=False)
@patch("services.webhook.utils.should_bail.is_pull_request_open", return_value=True)
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(False, 60.0))
def test_returns_true_when_branch_deleted(
    _mock_timeout, _mock_oom, _mock_pr_open, _mock_branch, _mock_update
):
    assert should_bail(**BAIL_KWARGS) is True


@patch("services.webhook.utils.should_bail.update_comment")
@patch("services.webhook.utils.should_bail.check_branch_exists")
@patch("services.webhook.utils.should_bail.is_pull_request_open")
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(True, 540.0))
def test_timeout_checked_first(
    _mock_timeout, _mock_oom, mock_pr_open, mock_branch, _mock_update
):
    assert should_bail(**BAIL_KWARGS) is True
    mock_pr_open.assert_not_called()
    mock_branch.assert_not_called()


@patch("services.webhook.utils.should_bail.slack_notify")
@patch("services.webhook.utils.should_bail.update_comment")
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(True, 540.0))
def test_calls_update_comment_on_bail(
    _mock_timeout, _mock_oom, mock_update, _mock_slack
):
    should_bail(**BAIL_KWARGS)
    mock_update.assert_called_once()


@patch("services.webhook.utils.should_bail.slack_notify")
@patch("services.webhook.utils.should_bail.update_comment")
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(True, 540.0))
def test_calls_slack_when_thread_ts_provided(
    _mock_timeout, _mock_oom, _mock_update, mock_slack
):
    should_bail(
        current_time=1000.0,
        phase="execution",
        base_args=BASE_ARGS,
        slack_thread_ts="ts123",
    )
    mock_slack.assert_called_once()


@patch("services.webhook.utils.should_bail.slack_notify")
@patch("services.webhook.utils.should_bail.update_comment")
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(True, 540.0))
def test_skips_slack_when_thread_ts_is_none(
    _mock_timeout, _mock_oom, _mock_update, mock_slack
):
    should_bail(**BAIL_KWARGS)
    mock_slack.assert_not_called()


@patch("services.webhook.utils.should_bail.check_branch_exists", return_value=True)
@patch("services.webhook.utils.should_bail.is_pull_request_open")
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(False, 60.0))
def test_skips_pr_check_when_pr_number_not_set(
    _mock_timeout, _mock_oom, mock_pr_open, _mock_branch
):
    args_without_pr_number = cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "clone_url": "https://x-access-token:test-token@github.com/test-owner/test-repo.git",
            "new_branch": "feature-branch",
            "token": "test-token",
        },
    )
    result = should_bail(
        current_time=1000.0,
        phase="execution",
        base_args=args_without_pr_number,
        slack_thread_ts=None,
    )
    assert result is False
    mock_pr_open.assert_not_called()


# --- OOM-specific tests ---


@patch("services.webhook.utils.should_bail.update_comment")
@patch(MOCK_OOM_OK, return_value=(True, 1800.0))
@patch(MOCK_TIMEOUT, return_value=(False, 60.0))
def test_returns_true_on_oom(_mock_timeout, _mock_oom, _mock_update):
    assert should_bail(**BAIL_KWARGS) is True


@patch("services.webhook.utils.should_bail.update_comment")
@patch("services.webhook.utils.should_bail.check_branch_exists")
@patch("services.webhook.utils.should_bail.is_pull_request_open")
@patch(MOCK_OOM_OK, return_value=(True, 1800.0))
@patch(MOCK_TIMEOUT, return_value=(False, 60.0))
def test_oom_skips_pr_and_branch_checks(
    _mock_timeout, _mock_oom, mock_pr_open, mock_branch, _mock_update
):
    assert should_bail(**BAIL_KWARGS) is True
    mock_pr_open.assert_not_called()
    mock_branch.assert_not_called()


@patch("services.webhook.utils.should_bail.update_comment")
@patch(MOCK_OOM_OK, return_value=(True, 1800.0))
@patch(MOCK_TIMEOUT, return_value=(True, 540.0))
def test_timeout_takes_priority_over_oom(_mock_timeout, mock_oom, _mock_update):
    result = should_bail(**BAIL_KWARGS)
    assert result is True
    # OOM check should not be called when timeout is already approaching
    mock_oom.assert_not_called()
