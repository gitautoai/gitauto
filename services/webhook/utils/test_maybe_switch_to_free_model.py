# pyright: reportUnusedVariable=false
from unittest.mock import patch

from constants.models import DEFAULT_FREE_MODEL, ClaudeModelId
from services.webhook.utils.maybe_switch_to_free_model import maybe_switch_to_free_model

MOCK_COST = "services.webhook.utils.maybe_switch_to_free_model.get_total_cost_for_pr"
MOCK_SLACK = "services.webhook.utils.maybe_switch_to_free_model.slack_notify"


@patch(MOCK_SLACK)
@patch(MOCK_COST, return_value=7.00)
def test_switches_when_cost_at_or_above_cap(mock_cost, mock_slack):
    result = maybe_switch_to_free_model(
        owner="test-owner",
        repo="test-repo",
        pr_number=42,
        cost_cap_usd=6.40,
        model_id=ClaudeModelId.OPUS_4_7,
        slack_thread_ts="ts123",
    )
    assert result == DEFAULT_FREE_MODEL
    mock_cost.assert_called_once_with("test-owner", "test-repo", 42)
    mock_slack.assert_called_once_with(
        "Cost cap reached: $7.00 >= $6.40 cap. "
        f"Switching from `{ClaudeModelId.OPUS_4_7}` to `{DEFAULT_FREE_MODEL}` for "
        "`test-owner/test-repo#42`.",
        "ts123",
    )


@patch(MOCK_SLACK)
@patch(MOCK_COST, return_value=6.40)
def test_switches_when_cost_equals_cap(mock_cost, mock_slack):
    result = maybe_switch_to_free_model(
        owner="test-owner",
        repo="test-repo",
        pr_number=42,
        cost_cap_usd=6.40,
        model_id=ClaudeModelId.OPUS_4_7,
        slack_thread_ts=None,
    )
    assert result == DEFAULT_FREE_MODEL
    mock_cost.assert_called_once()
    mock_slack.assert_called_once()


@patch(MOCK_SLACK)
@patch(MOCK_COST, return_value=3.00)
def test_keeps_model_when_under_cap(mock_cost, mock_slack):
    result = maybe_switch_to_free_model(
        owner="test-owner",
        repo="test-repo",
        pr_number=42,
        cost_cap_usd=6.40,
        model_id=ClaudeModelId.OPUS_4_7,
        slack_thread_ts="ts123",
    )
    assert result == ClaudeModelId.OPUS_4_7
    mock_cost.assert_called_once()
    mock_slack.assert_not_called()


@patch(MOCK_SLACK)
@patch(MOCK_COST)
def test_skips_check_when_already_on_free_model(mock_cost, mock_slack):
    result = maybe_switch_to_free_model(
        owner="test-owner",
        repo="test-repo",
        pr_number=42,
        cost_cap_usd=1.00,
        model_id=DEFAULT_FREE_MODEL,
        slack_thread_ts="ts123",
    )
    assert result == DEFAULT_FREE_MODEL
    mock_cost.assert_not_called()
    mock_slack.assert_not_called()


@patch(MOCK_SLACK)
@patch(MOCK_COST, return_value=7.00)
def test_slack_thread_ts_passed_through(_mock_cost, mock_slack):
    maybe_switch_to_free_model(
        owner="test-owner",
        repo="test-repo",
        pr_number=42,
        cost_cap_usd=6.40,
        model_id=ClaudeModelId.OPUS_4_7,
        slack_thread_ts=None,
    )
    args, _ = mock_slack.call_args
    assert args[1] is None
