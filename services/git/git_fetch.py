import os

from services.git.resolve_git_locks import resolve_git_locks
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def git_fetch(target_dir: str, clone_url: str, branch: str):
    # Remove stale locks (>10min, crashed Lambda) and wait for fresh ones (concurrent Lambda)
    git_dir = os.path.join(target_dir, ".git")
    resolve_git_locks(git_dir)

    # --depth 1 for shallow fetch to save disk space and time
    # Syntax: git fetch [options] <repository> <refspec>
    try:
        run_subprocess(["git", "fetch", "--depth", "1", clone_url, branch], target_dir)
    except ValueError as err:
        # Stale webhook: branch was deleted (PR closed/merged) before this Lambda picked up the event.
        # Sentry AGENT-3KB and the cascade AGENT-3KC/3KD: foxcom-forms PR 1150 fired 7 days after the gitauto/schedule-* branch had already been removed.
        # Treat it as expected, log info, return False so callers skip the checkout and bail their flow without a Sentry alert.
        if "couldn't find remote ref" in str(err):
            logger.info(
                "git_fetch: branch %s no longer on remote (deleted/closed PR), skipping",
                branch,
            )
            return False
        raise

    logger.info("git fetch completed: %s", target_dir)
    return True
