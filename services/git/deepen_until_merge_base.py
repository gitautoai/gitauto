from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def deepen_until_merge_base(clone_dir: str, base_branch: str):
    """Fetch enough history of origin/base_branch that HEAD and origin/base_branch share a visible merge-base.

    Why this exists: GitAuto clones repos with `git clone --depth 1` and fetches PR branches with `git fetch --depth 1`. Both histories are 1-commit deep with no commits in common locally, so any operation that needs the merge-base (git merge, three-dot git diff, etc.) fails with 'no merge base' or similar.

    Strategy: skip if the merge-base is already there. Otherwise exponentially deepen the base branch fetch (100 -> 500 -> 2500 -> 12500). If that loop exhausts without finding a merge-base, fall back to --unshallow as a last resort. --unshallow fetches full history but is slow on big repos (~137s on a 61K-commit repo); --deepen N fetches only N more commits from the shallow boundary, hence the exponential climb.

    Returns True when a merge-base exists at the end (either it already existed or deepening produced one). Returns False when the helper itself raised — the @handle_exceptions wrapper swallows and logs.

    Callers:
    - git_merge_base_into_pr: falls back here when GitHub's Compare API returned behind_by=0 / failed.
    - git_diff: falls back here when three-dot diff syntax fails on a shallow clone (Sentry AGENT-3JQ/3J2/3J3 on gitautoai/website PR 821, 2026-04-20).

    Centralizing the schedule means both callers stay in lockstep when we tune it.
    """
    try:
        run_subprocess(
            ["git", "merge-base", "HEAD", f"origin/{base_branch}"], clone_dir
        )
        logger.info("deepen_until_merge_base: merge-base already present, skipping")
        return True
    except ValueError:
        logger.info(
            "deepen_until_merge_base: merge-base missing, starting exponential deepen"
        )

    depth = 100
    while depth <= 12500:
        logger.info(
            "deepen_until_merge_base: deepening origin/%s by %d", base_branch, depth
        )
        run_subprocess(
            ["git", "fetch", "--deepen", str(depth), "origin", base_branch], clone_dir
        )
        try:
            run_subprocess(
                ["git", "merge-base", "HEAD", f"origin/{base_branch}"], clone_dir
            )
            logger.info("deepen_until_merge_base: merge base found at deepen=%d", depth)
            return True
        except ValueError:
            logger.info(
                "deepen_until_merge_base: merge base not found at deepen=%d", depth
            )
            depth *= 5

    logger.warning(
        "deepen_until_merge_base: exponential deepen exhausted, falling back to --unshallow"
    )
    run_subprocess(["git", "fetch", "--unshallow", "origin", base_branch], clone_dir)
    return True
