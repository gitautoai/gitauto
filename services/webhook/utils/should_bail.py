# Local imports
from services.git.check_branch_exists import check_branch_exists
from services.github.comments.update_comment import update_comment
from services.github.pulls.is_pull_request_open import is_pull_request_open
from services.slack.slack_notify import slack_notify
from services.supabase.llm_requests.get_total_cost_for_pr import get_total_cost_for_pr
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger
from utils.memory.get_oom_message import get_oom_message
from utils.memory.is_lambda_oom_approaching import is_lambda_oom_approaching
from utils.time.get_timeout_message import get_timeout_message
from utils.time.is_lambda_timeout_approaching import is_lambda_timeout_approaching


@handle_exceptions(raise_on_error=True)
def should_bail(
    *,
    current_time: float,
    phase: str,
    base_args: BaseArgs,
    slack_thread_ts: str | None,
    cost_cap_usd: float,
):
    """Check if the loop should stop. Handles logging, comment updates, and slack."""
    owner = base_args["owner"]
    repo = base_args["repo"]
    pr_number = base_args.get("pr_number")
    branch = base_args["new_branch"]
    token = base_args["token"]

    msg: str | None = None

    is_timeout_approaching, elapsed_time = is_lambda_timeout_approaching(current_time)
    if is_timeout_approaching:
        logger.error("Lambda timeout approaching during %s", phase)
        msg = get_timeout_message(elapsed_time, phase)

    else:
        logger.info("Timeout not approaching during %s, checking OOM", phase)
        is_oom_approaching, used_mb = is_lambda_oom_approaching()
        if is_oom_approaching:
            logger.error(
                "Lambda OOM approaching during %s (used=%.1fMB)", phase, used_mb
            )
            msg = get_oom_message(used_mb, phase)

    # Cost cap: bail silently to the user (no PR comment), but notify Slack so we see it.
    if not msg and pr_number:
        total_cost = get_total_cost_for_pr(owner, repo, pr_number)
        logger.debug(
            "Cost check on PR #%s: $%.2f (cap $%.2f)",
            pr_number,
            total_cost,
            cost_cap_usd,
        )
        if total_cost >= cost_cap_usd:
            logger.warning(
                "Cost cap reached on PR #%s during %s: $%.2f >= $%.2f; bailing",
                pr_number,
                phase,
                total_cost,
                cost_cap_usd,
            )
            slack_notify(
                f"Cost cap reached: ${total_cost:.2f} >= ${cost_cap_usd:.2f} cap. "
                f"Stopped {phase} for `{owner}/{repo}#{pr_number}`.",
                slack_thread_ts,
            )
            return True

    if not msg:
        logger.debug("Checking PR/branch liveness for pr_number=%s", pr_number)
        if pr_number and not is_pull_request_open(
            owner=owner, repo=repo, pr_number=pr_number, token=token
        ):
            logger.warning("PR #%s was closed during %s", pr_number, phase)
            msg = (
                f"Process stopped: Pull request #{pr_number} was closed during {phase}."
            )

        elif not check_branch_exists(
            clone_url=base_args["clone_url"], branch_name=branch
        ):
            logger.warning("Branch '%s' was deleted during %s", branch, phase)
            msg = f"Process stopped: Branch '{branch}' was deleted during {phase}."

    if msg:
        update_comment(body=msg, base_args=base_args)
        if slack_thread_ts:
            logger.debug("Posting slack thread for bail")
            slack_notify(f"{msg} in `{owner}/{repo}`", slack_thread_ts)
        logger.info("should_bail returning True for %s: %s", phase, msg)
        return True

    logger.info("should_bail returning False for %s", phase)
    return False
