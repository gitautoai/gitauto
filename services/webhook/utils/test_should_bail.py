# pyright: reportUnusedVariable=false
from unittest.mock import patch

from services.webhook.utils.should_bail import should_bail

MOCK_COST = "services.webhook.utils.should_bail.get_total_cost_for_pr"
MOCK_OOM_OK = "services.webhook.utils.should_bail.is_lambda_oom_approaching"
MOCK_TIMEOUT = "services.webhook.utils.should_bail.is_lambda_timeout_approaching"


@patch("services.webhook.utils.should_bail.update_comment")
@patch("services.webhook.utils.should_bail.check_branch_exists", return_value=True)
@patch("services.webhook.utils.should_bail.is_pull_request_open", return_value=True)
@patch(MOCK_COST, return_value=0.0)
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(False, 60.0))
def test_returns_false_when_all_checks_pass(
    _mock_timeout,
    _mock_oom,
    _mock_cost,
    _mock_pr_open,
    _mock_branch,
    _mock_update,
    create_test_base_args,
):
    base_args = create_test_base_args(pr_number=42, new_branch="feature-branch")
    bail_kwargs = {
        "current_time": 1000.0,
        "phase": "execution",
        "base_args": base_args,
        "slack_thread_ts": None,
        "cost_cap_usd": 6.40,
    }
    assert should_bail(**bail_kwargs) is False


@patch("services.webhook.utils.should_bail.update_comment")
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(True, 540.0))
def test_returns_true_on_timeout(
    _mock_timeout, _mock_oom, _mock_update, create_test_base_args
):
    base_args = create_test_base_args(pr_number=42, new_branch="feature-branch")
    bail_kwargs = {
        "current_time": 1000.0,
        "phase": "execution",
        "base_args": base_args,
        "slack_thread_ts": None,
        "cost_cap_usd": 6.40,
    }
    assert should_bail(**bail_kwargs) is True


@patch("services.webhook.utils.should_bail.update_comment")
@patch("services.webhook.utils.should_bail.check_branch_exists", return_value=True)
@patch("services.webhook.utils.should_bail.is_pull_request_open", return_value=False)
@patch(MOCK_COST, return_value=0.0)
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(False, 60.0))
def test_returns_true_when_pr_closed(
    _mock_timeout,
    _mock_oom,
    _mock_cost,
    _mock_pr_open,
    _mock_branch,
    _mock_update,
    create_test_base_args,
):
    base_args = create_test_base_args(pr_number=42, new_branch="feature-branch")
    bail_kwargs = {
        "current_time": 1000.0,
        "phase": "execution",
        "base_args": base_args,
        "slack_thread_ts": None,
        "cost_cap_usd": 6.40,
    }
    assert should_bail(**bail_kwargs) is True


@patch("services.webhook.utils.should_bail.update_comment")
@patch("services.webhook.utils.should_bail.check_branch_exists", return_value=False)
@patch("services.webhook.utils.should_bail.is_pull_request_open", return_value=True)
@patch(MOCK_COST, return_value=0.0)
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(False, 60.0))
def test_returns_true_when_branch_deleted(
    _mock_timeout,
    _mock_oom,
    _mock_cost,
    _mock_pr_open,
    _mock_branch,
    _mock_update,
    create_test_base_args,
):
    base_args = create_test_base_args(pr_number=42, new_branch="feature-branch")
    bail_kwargs = {
        "current_time": 1000.0,
        "phase": "execution",
        "base_args": base_args,
        "slack_thread_ts": None,
        "cost_cap_usd": 6.40,
    }
    assert should_bail(**bail_kwargs) is True


@patch("services.webhook.utils.should_bail.update_comment")
@patch("services.webhook.utils.should_bail.check_branch_exists")
@patch("services.webhook.utils.should_bail.is_pull_request_open")
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(True, 540.0))
def test_timeout_checked_first(
    _mock_timeout,
    _mock_oom,
    mock_pr_open,
    mock_branch,
    _mock_update,
    create_test_base_args,
):
    base_args = create_test_base_args(pr_number=42, new_branch="feature-branch")
    bail_kwargs = {
        "current_time": 1000.0,
        "phase": "execution",
        "base_args": base_args,
        "slack_thread_ts": None,
        "cost_cap_usd": 6.40,
    }
    assert should_bail(**bail_kwargs) is True
    mock_pr_open.assert_not_called()
    mock_branch.assert_not_called()


@patch("services.webhook.utils.should_bail.slack_notify")
@patch("services.webhook.utils.should_bail.update_comment")
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(True, 540.0))
def test_calls_update_comment_on_bail(
    _mock_timeout, _mock_oom, mock_update, _mock_slack, create_test_base_args
):
    base_args = create_test_base_args(pr_number=42, new_branch="feature-branch")
    bail_kwargs = {
        "current_time": 1000.0,
        "phase": "execution",
        "base_args": base_args,
        "slack_thread_ts": None,
        "cost_cap_usd": 6.40,
    }
    should_bail(**bail_kwargs)
    mock_update.assert_called_once()


@patch("services.webhook.utils.should_bail.slack_notify")
@patch("services.webhook.utils.should_bail.update_comment")
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(True, 540.0))
def test_calls_slack_when_thread_ts_provided(
    _mock_timeout, _mock_oom, _mock_update, mock_slack, create_test_base_args
):
    base_args = create_test_base_args(pr_number=42, new_branch="feature-branch")
    should_bail(
        current_time=1000.0,
        phase="execution",
        base_args=base_args,
        slack_thread_ts="ts123",
        cost_cap_usd=6.40,
    )
    mock_slack.assert_called_once()


@patch("services.webhook.utils.should_bail.slack_notify")
@patch("services.webhook.utils.should_bail.update_comment")
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(True, 540.0))
def test_skips_slack_when_thread_ts_is_none(
    _mock_timeout, _mock_oom, _mock_update, mock_slack, create_test_base_args
):
    base_args = create_test_base_args(pr_number=42, new_branch="feature-branch")
    bail_kwargs = {
        "current_time": 1000.0,
        "phase": "execution",
        "base_args": base_args,
        "slack_thread_ts": None,
        "cost_cap_usd": 6.40,
    }
    should_bail(**bail_kwargs)
    mock_slack.assert_not_called()


@patch("services.webhook.utils.should_bail.check_branch_exists", return_value=True)
@patch("services.webhook.utils.should_bail.is_pull_request_open")
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(False, 60.0))
def test_skips_pr_check_when_pr_number_not_set(
    _mock_timeout, _mock_oom, mock_pr_open, _mock_branch, create_test_base_args
):
    args_without_pr_number = create_test_base_args(new_branch="feature-branch")
    # Remove pr_number to simulate it not being set
    del args_without_pr_number["pr_number"]
    result = should_bail(
        current_time=1000.0,
        phase="execution",
        base_args=args_without_pr_number,
        slack_thread_ts=None,
        cost_cap_usd=6.40,
    )
    assert result is False
    mock_pr_open.assert_not_called()


# --- OOM-specific tests ---


@patch("services.webhook.utils.should_bail.update_comment")
@patch(MOCK_OOM_OK, return_value=(True, 1800.0))
@patch(MOCK_TIMEOUT, return_value=(False, 60.0))
def test_returns_true_on_oom(
    _mock_timeout, _mock_oom, _mock_update, create_test_base_args
):
    base_args = create_test_base_args(pr_number=42, new_branch="feature-branch")
    bail_kwargs = {
        "current_time": 1000.0,
        "phase": "execution",
        "base_args": base_args,
        "slack_thread_ts": None,
        "cost_cap_usd": 6.40,
    }
    assert should_bail(**bail_kwargs) is True


@patch("services.webhook.utils.should_bail.update_comment")
@patch("services.webhook.utils.should_bail.check_branch_exists")
@patch("services.webhook.utils.should_bail.is_pull_request_open")
@patch(MOCK_OOM_OK, return_value=(True, 1800.0))
@patch(MOCK_TIMEOUT, return_value=(False, 60.0))
def test_oom_skips_pr_and_branch_checks(
    _mock_timeout,
    _mock_oom,
    mock_pr_open,
    mock_branch,
    _mock_update,
    create_test_base_args,
):
    base_args = create_test_base_args(pr_number=42, new_branch="feature-branch")
    bail_kwargs = {
        "current_time": 1000.0,
        "phase": "execution",
        "base_args": base_args,
        "slack_thread_ts": None,
        "cost_cap_usd": 6.40,
    }
    assert should_bail(**bail_kwargs) is True
    mock_pr_open.assert_not_called()
    mock_branch.assert_not_called()


@patch("services.webhook.utils.should_bail.update_comment")
@patch(MOCK_OOM_OK, return_value=(True, 1800.0))
@patch(MOCK_TIMEOUT, return_value=(True, 540.0))
def test_timeout_takes_priority_over_oom(
    _mock_timeout, mock_oom, _mock_update, create_test_base_args
):
    base_args = create_test_base_args(pr_number=42, new_branch="feature-branch")
    bail_kwargs = {
        "current_time": 1000.0,
        "phase": "execution",
        "base_args": base_args,
        "slack_thread_ts": None,
        "cost_cap_usd": 6.40,
    }
    result = should_bail(**bail_kwargs)
    assert result is True
    # OOM check should not be called when timeout is already approaching
    mock_oom.assert_not_called()


# --- Cost cap tests ---


@patch("services.webhook.utils.should_bail.update_comment")
@patch(MOCK_COST, return_value=7.00)
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(False, 60.0))
def test_returns_true_on_cost_cap(
    _mock_timeout, _mock_oom, _mock_cost, mock_update, create_test_base_args
):
    base_args = create_test_base_args(pr_number=42, new_branch="feature-branch")
    bail_kwargs = {
        "current_time": 1000.0,
        "phase": "execution",
        "base_args": base_args,
        "slack_thread_ts": None,
        "cost_cap_usd": 6.40,
    }
    assert should_bail(**bail_kwargs) is True
    # Cost cap bails silently — no update_comment to customer
    mock_update.assert_not_called()


@patch("services.webhook.utils.should_bail.slack_notify")
@patch("services.webhook.utils.should_bail.update_comment")
@patch(MOCK_COST, return_value=7.00)
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(False, 60.0))
def test_cost_cap_skips_slack(
    _mock_timeout,
    _mock_oom,
    _mock_cost,
    _mock_update,
    mock_slack,
    create_test_base_args,
):
    base_args = create_test_base_args(pr_number=42, new_branch="feature-branch")
    should_bail(
        current_time=1000.0,
        phase="execution",
        base_args=base_args,
        slack_thread_ts="ts123",
        cost_cap_usd=6.40,
    )
    # Cost cap bails silently — no slack notification
    mock_slack.assert_not_called()


@patch("services.webhook.utils.should_bail.check_branch_exists")
@patch("services.webhook.utils.should_bail.is_pull_request_open")
@patch(MOCK_COST, return_value=7.00)
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(False, 60.0))
def test_cost_cap_skips_pr_and_branch_checks(
    _mock_timeout,
    _mock_oom,
    _mock_cost,
    mock_pr_open,
    mock_branch,
    create_test_base_args,
):
    base_args = create_test_base_args(pr_number=42, new_branch="feature-branch")
    bail_kwargs = {
        "current_time": 1000.0,
        "phase": "execution",
        "base_args": base_args,
        "slack_thread_ts": None,
        "cost_cap_usd": 6.40,
    }
    assert should_bail(**bail_kwargs) is True
    mock_pr_open.assert_not_called()
    mock_branch.assert_not_called()


@patch(MOCK_COST)
@patch(MOCK_OOM_OK, return_value=(False, 500.0))
@patch(MOCK_TIMEOUT, return_value=(False, 60.0))
def test_cost_cap_skipped_when_no_pr_number(
    _mock_timeout, _mock_oom, mock_cost, create_test_base_args
):
    args_without_pr = create_test_base_args(new_branch="feature-branch")
    del args_without_pr["pr_number"]
    should_bail(
        current_time=1000.0,
        phase="execution",
        base_args=args_without_pr,
        slack_thread_ts=None,
        cost_cap_usd=6.40,
    )
    # No pr_number → cost check not reached
    mock_cost.assert_not_called()
