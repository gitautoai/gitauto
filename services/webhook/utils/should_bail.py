# Local imports
from services.github.branches.check_branch_exists import check_branch_exists
from services.github.comments.update_comment import update_comment
from services.github.pulls.is_pull_request_open import is_pull_request_open
from services.github.types.github_types import BaseArgs
from services.slack.slack_notify import slack_notify
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
        msg = get_timeout_message(elapsed_time, phase)
        logger.error(msg)

    else:
        is_oom_approaching, used_mb = is_lambda_oom_approaching()
        if is_oom_approaching:
            msg = get_oom_message(used_mb, phase)
            logger.error(msg)

    if not msg:
        if pr_number and not is_pull_request_open(
            owner=owner, repo=repo, pr_number=pr_number, token=token
        ):
            msg = (
                f"Process stopped: Pull request #{pr_number} was closed during {phase}."
            )
            logger.warning(msg)

        elif not check_branch_exists(
            owner=owner, repo=repo, branch_name=branch, token=token
        ):
            msg = f"Process stopped: Branch '{branch}' was deleted during {phase}."
            logger.warning(msg)

    if msg:
        update_comment(body=msg, base_args=base_args)
        if slack_thread_ts:
            slack_notify(f"{msg} in `{owner}/{repo}`", slack_thread_ts)
        return True

    return False
