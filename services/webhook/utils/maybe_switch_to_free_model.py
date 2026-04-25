from constants.models import DEFAULT_FREE_MODEL, ModelId
from services.slack.slack_notify import slack_notify
from services.supabase.llm_requests.get_total_cost_for_pr import get_total_cost_for_pr
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(raise_on_error=False, default_return_value=None)
def maybe_switch_to_free_model(
    *,
    owner: str,
    repo: str,
    pr_number: int,
    cost_cap_usd: float,
    model_id: ModelId,
    slack_thread_ts: str | None,
):
    """If the PR has crossed the cost cap and we're not already on the free model, swap to DEFAULT_FREE_MODEL and notify Slack. Returns the (possibly new) model_id."""
    if model_id == DEFAULT_FREE_MODEL:
        logger.info(
            "Already on free model %s; skipping cost-cap swap check", DEFAULT_FREE_MODEL
        )
        return model_id

    total_cost = get_total_cost_for_pr(owner, repo, pr_number)
    logger.info(
        "Cost check on PR #%s: $%.2f (cap $%.2f, model %s)",
        pr_number,
        total_cost,
        cost_cap_usd,
        model_id,
    )
    if total_cost < cost_cap_usd:
        logger.info(
            "Cost under cap on PR #%s ($%.2f < $%.2f); keeping model %s",
            pr_number,
            total_cost,
            cost_cap_usd,
            model_id,
        )
        return model_id

    logger.warning(
        "Cost cap reached on PR #%s: $%.2f >= $%.2f; switching from %s to %s",
        pr_number,
        total_cost,
        cost_cap_usd,
        model_id,
        DEFAULT_FREE_MODEL,
    )
    slack_notify(
        f"Cost cap reached: ${total_cost:.2f} >= ${cost_cap_usd:.2f} cap. "
        f"Switching from `{model_id}` to `{DEFAULT_FREE_MODEL}` for "
        f"`{owner}/{repo}#{pr_number}`.",
        slack_thread_ts,
    )
    return DEFAULT_FREE_MODEL
